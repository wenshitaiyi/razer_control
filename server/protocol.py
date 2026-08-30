"""
Razer HID 90-byte Feature Report Protocol Encoder and Communication Driver.
"""
import time
from typing import List, Dict, Any, Optional, Tuple

try:
    import hid
except ImportError:
    hid = None

RAZER_VID = 0x1532

# 指令类与指令标识常量
CMD_CLASS_DEVICE = 0x00
CMD_CLASS_PERFORMANCE = 0x04
CMD_CLASS_LIGHTING = 0x0F

CMD_ID_SET_POLLING_RATE = 0x05
CMD_ID_SET_DPI = 0x05
CMD_ID_SET_LIGHTING = 0x02

# 响应状态码定义
STATUS_NEW = 0x00
STATUS_BUSY = 0x01
STATUS_SUCCESS = 0x02
STATUS_FAILURE = 0x03
STATUS_TIMEOUT = 0x04
STATUS_NOT_SUPPORTED = 0x05


def create_razer_report(command_class: int, command_id: int, arguments: List[int]) -> bytes:
    """
    构造雷蛇标准的 90 字节 Feature Report 报文：
    - byte 0: 状态标志 (0x00)
    - byte 1: 事务 ID (0xFF)
    - byte 2: 剩余数据包数 (0x00)
    - byte 3: 协议版本 (0x00)
    - byte 4: 参数长度 (len(arguments))
    - byte 5: 命令类别 (command_class)
    - byte 6: 命令 ID (command_id)
    - byte 7..7+len-1: 参数载荷
    - byte 88: 校验和 (从 byte 2 到 byte 87 的异或和 XOR Checksum)
    - byte 89: 尾部填充 (0x00)
    """
    report = bytearray(90)
    report[0] = 0x00
    report[1] = 0xFF
    report[2] = 0x00
    report[3] = 0x00
    report[4] = len(arguments)
    report[5] = command_class & 0xFF
    report[6] = command_id & 0xFF

    for i, val in enumerate(arguments):
        if 7 + i < 88:
            report[7 + i] = val & 0xFF

    # 计算从第 2 字节到第 87 字节的异或和
    checksum = 0
    for b in report[2:88]:
        checksum ^= b
    report[88] = checksum
    report[89] = 0x00

    return bytes(report)


def build_dpi_args(dpi: int, dpi_y: Optional[int] = None) -> Tuple[int, int, List[int]]:
    """构造 DPI 设置参数 (0x04, 0x05)"""
    dpi = max(100, min(35000, dpi))
    dpi_y = dpi if dpi_y is None else max(100, min(35000, dpi_y))
    
    dpi_x_h = (dpi >> 8) & 0xFF
    dpi_x_l = dpi & 0xFF
    dpi_y_h = (dpi_y >> 8) & 0xFF
    dpi_y_l = dpi_y & 0xFF

    # 载荷格式: [保留/模式标识, X高位, X低位, Y高位, Y低位]
    args = [0x00, dpi_x_h, dpi_x_l, dpi_y_h, dpi_y_l]
    return CMD_CLASS_PERFORMANCE, CMD_ID_SET_DPI, args


def build_polling_rate_args(rate_hz: int) -> Tuple[int, int, List[int]]:
    """构造回报率设置参数 (0x00, 0x05)"""
    rate_map = {
        1000: 0x01,
        500: 0x02,
        125: 0x08
    }
    val = rate_map.get(rate_hz, 0x01)
    return CMD_CLASS_DEVICE, CMD_ID_SET_POLLING_RATE, [val]


def build_static_led_args(r: int, g: int, b: int, led_id: int = 0x01) -> Tuple[int, int, List[int]]:
    """构造静态 RGB 灯效设置参数 (0x0F, 0x02)"""
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))
    # 0x01: Logo 主灯, 0x01: 静态模式, R, G, B
    args = [led_id & 0xFF, 0x01, r, g, b]
    return CMD_CLASS_LIGHTING, CMD_ID_SET_LIGHTING, args


def build_turn_off_led_args(led_id: int = 0x01) -> Tuple[int, int, List[int]]:
    """构造关闭灯效设置参数 (0x0F, 0x02)"""
    # 0x01: Logo 主灯, 0x00: 关闭
    args = [led_id & 0xFF, 0x00]
    return CMD_CLASS_LIGHTING, CMD_ID_SET_LIGHTING, args


def list_razer_devices() -> List[Dict[str, Any]]:
    """扫描系统当前已连接的所有雷蛇 HID 设备"""
    if not hid:
        return []

    try:
        raw_devices = hid.enumerate(RAZER_VID)
    except Exception:
        return []

    devices = []
    seen_paths = set()

    for d in raw_devices:
        path_bytes = d.get("path", b"")
        path_str = path_bytes.decode("utf-8", errors="ignore") if isinstance(path_bytes, bytes) else str(path_bytes)
        
        if path_str in seen_paths:
            continue
        seen_paths.add(path_str)

        interface_num = d.get("interface_number", -1)
        usage_page = d.get("usage_page", 0)
        usage = d.get("usage", 0)
        
        # 判断该接口是否适合用于下发控制指令
        is_control_interface = interface_num in (0, 1, 2) or usage_page in (1, 0xFF00, 0x0C)

        devices.append({
            "path": path_str,
            "path_bytes": path_bytes,
            "vendor_id": d.get("vendor_id", RAZER_VID),
            "vendor_id_hex": f"0x{d.get('vendor_id', RAZER_VID):04X}",
            "product_id": d.get("product_id", 0),
            "product_id_hex": f"0x{d.get('product_id', 0):04X}",
            "product_string": d.get("product_string", "Unknown Razer Device"),
            "manufacturer_string": d.get("manufacturer_string", "Razer"),
            "serial_number": d.get("serial_number", ""),
            "release_number": d.get("release_number", 0),
            "interface_number": interface_num,
            "usage_page": usage_page,
            "usage": usage,
            "bus_type": d.get("bus_type", 0),
            "is_control_interface": is_control_interface
        })

    return devices


def send_to_razer(command_class: int, command_id: int, arguments: List[int], target_path: Optional[str] = None, target_pid: Optional[int] = None) -> Dict[str, Any]:
    """
    向目标雷蛇设备发送 90 字节 Feature Report 并接收 ACK
    """
    if not hid:
        return {
            "success": False,
            "status_code": -1,
            "status_name": "HID_LIB_MISSING",
            "message": "Python hidapi 库未安装或加载失败",
            "device_name": None,
            "response_hex": None
        }

    all_devices = list_razer_devices()
    if not all_devices:
        return {
            "success": False,
            "status_code": -1,
            "status_name": "DEVICE_NOT_FOUND",
            "message": "未检测到任何已连接的雷蛇设备",
            "device_name": None,
            "response_hex": None
        }

    # 筛选候选设备接口
    candidates = []
    if target_path:
        candidates = [d for d in all_devices if d["path"] == target_path]
    elif target_pid is not None:
        candidates = [d for d in all_devices if d["product_id"] == target_pid]
    
    if not candidates:
        # 默认使用控制接口优先级排序
        candidates = sorted(all_devices, key=lambda x: (0 if x["is_control_interface"] else 1, x["interface_number"]))

    report_payload = create_razer_report(command_class, command_id, arguments)
    # Windows HIDAPI 要求首字节附带 Report ID (0x00) + 90 字节 Payload
    wire_data = b"\x00" + report_payload

    last_err = None
    target_used = None

    for dev_meta in candidates:
        dev_handle = None
        try:
            dev_handle = hid.device()
            path_arg = dev_meta["path_bytes"] if isinstance(dev_meta["path_bytes"], bytes) else dev_meta["path"].encode("utf-8")
            dev_handle.open_path(path_arg)
            
            # 发送 Feature Report
            dev_handle.send_feature_report(wire_data)
            time.sleep(0.04)
            
            # 读取设备 ACK 响应 (91 字节，包含开头的 Report ID)
            response = dev_handle.get_feature_report(0x00, 91)
            dev_handle.close()
            dev_handle = None
            
            target_used = dev_meta["product_string"]
            resp_hex = bytes(response).hex() if response else ""
            status_byte = response[1] if len(response) > 1 else -1

            status_names = {
                STATUS_SUCCESS: "SUCCESS",
                STATUS_BUSY: "BUSY",
                STATUS_FAILURE: "FAILURE",
                STATUS_TIMEOUT: "TIMEOUT",
                STATUS_NOT_SUPPORTED: "NOT_SUPPORTED"
            }
            status_name = status_names.get(status_byte, f"STATUS_0x{status_byte:02X}")

            # response[1] == 0x02 表示成功，部分设备即使未严格返回 0x02 但正常接收无报错也算成功
            is_success = (status_byte == STATUS_SUCCESS) or (len(response) > 0 and status_byte != STATUS_FAILURE)

            return {
                "success": is_success,
                "status_code": status_byte,
                "status_name": status_name,
                "message": f"指令已成功写入设备: {target_used}" if is_success else f"设备返回响应: {status_name}",
                "device_name": target_used,
                "device_pid": f"0x{dev_meta['product_id']:04X}",
                "interface_number": dev_meta["interface_number"],
                "response_hex": resp_hex[:64] + ("..." if len(resp_hex) > 64 else "")
            }
        except Exception as e:
            last_err = str(e)
            if dev_handle:
                try:
                    dev_handle.close()
                except Exception:
                    pass
            continue

    return {
        "success": False,
        "status_code": -1,
        "status_name": "COMMUNICATION_ERROR",
        "message": f"与雷蛇设备通信失败 (可能被雷云独占或权限受限): {last_err}",
        "device_name": target_used or (candidates[0]["product_string"] if candidates else None),
        "response_hex": None
    }
