"""
Razer HID 90-byte Feature Report Protocol Encoder and Communication Driver.
Verified with OpenRazer kernel driver specification:
- byte 0: Status (0x00)
- byte 1: Transaction ID (0xFF / 0x3F)
- byte 2..3: Remaining Packets (0x00, 0x00 - __be16)
- byte 4: Protocol Type (0x00)
- byte 5: Data Size (len(arguments))
- byte 6: Command Class
- byte 7: Command ID
- byte 8..87: Arguments payload (up to 80 bytes)
- byte 88: XOR Checksum (Byte 2 to Byte 87 XOR)
- byte 89: Reserved (0x00)
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
CMD_CLASS_MOUSE = 0x02
CMD_CLASS_CLASSIC_LED = 0x03
CMD_CLASS_PERFORMANCE = 0x04
CMD_CLASS_LIGHTING = 0x0F

CMD_ID_SET_POLLING_RATE = 0x05
CMD_ID_SET_POLLING_RATE2 = 0x40
CMD_ID_SET_DPI = 0x05
CMD_ID_SET_LIGHTING = 0x02
CMD_ID_SET_LED_STATE = 0x00
CMD_ID_SET_LED_BRIGHTNESS = 0x03
CMD_ID_SET_DEVICE_MODE = 0x04
CMD_ID_GET_FIRMWARE = 0x81
CMD_ID_GET_SERIAL = 0x82

# 存储区域常量 (VARSTORE 固化至板载闪存, NOSTORE 临时生效)
NOSTORE = 0x00
VARSTORE = 0x01

# LED 灯区常量
ZERO_LED = 0x00
SCROLL_WHEEL_LED = 0x01
BATTERY_LED = 0x03
LOGO_LED = 0x04
BACKLIGHT_LED = 0x05

# 响应状态码定义
STATUS_NEW = 0x00
STATUS_BUSY = 0x01
STATUS_SUCCESS = 0x02
STATUS_FAILURE = 0x03
STATUS_TIMEOUT = 0x04
STATUS_NOT_SUPPORTED = 0x05

# 单色绿光/单色设备 PID 清单 (如 DeathAdder Essential RZ01-0385 / 0x0098)
SINGLE_COLOR_DEVICES = {
    0x0098: {"name": "Razer DeathAdder Essential (2021 / RZ01-0385)", "color": "green", "leds": [LOGO_LED]},
    0x006C: {"name": "Razer DeathAdder Essential", "color": "green", "leds": [LOGO_LED, SCROLL_WHEEL_LED]},
    0x0071: {"name": "Razer DeathAdder Essential (White Edition)", "color": "white", "leds": [LOGO_LED]},
    0x0037: {"name": "Razer DeathAdder 2013", "color": "green", "leds": [LOGO_LED, SCROLL_WHEEL_LED]},
    0x0038: {"name": "Razer DeathAdder 1800", "color": "blue", "leds": [LOGO_LED]},
    0x0054: {"name": "Razer DeathAdder 3500", "color": "green", "leds": [LOGO_LED]},
    0x004F: {"name": "Razer DeathAdder 2000", "color": "green", "leds": [LOGO_LED]},
}


def create_razer_report(command_class: int, command_id: int, arguments: List[int], transaction_id: int = 0xFF) -> bytes:
    """
    构造雷蛇标准的 90 字节 Feature Report 报文：
    - byte 0: 状态标志 (0x00)
    - byte 1: 事务 ID (0xFF / 0x3F / 0x1F)
    - byte 2..3: 剩余数据包数 (__be16, 0x00, 0x00)
    - byte 4: 协议类型 (0x00)
    - byte 5: 参数长度 (len(arguments))
    - byte 6: 命令类别 (command_class)
    - byte 7: 命令 ID (command_id)
    - byte 8..8+len-1: 参数载荷 (从第 8 字节开始)
    - byte 88: 校验和 (从 byte 2 到 byte 87 的异或和 XOR Checksum)
    - byte 89: 尾部填充 (0x00)
    """
    report = bytearray(90)
    report[0] = 0x00
    report[1] = transaction_id & 0xFF
    report[2] = 0x00
    report[3] = 0x00
    report[4] = 0x00
    report[5] = len(arguments) & 0xFF
    report[6] = command_class & 0xFF
    report[7] = command_id & 0xFF

    for i, val in enumerate(arguments):
        if 8 + i < 88:
            report[8 + i] = val & 0xFF

    # 计算从第 2 字节到第 87 字节的异或和
    checksum = 0
    for b in report[2:88]:
        checksum ^= b
    report[88] = checksum
    report[89] = 0x00

    return bytes(report)


def build_dpi_packets(dpi: int, dpi_y: Optional[int] = None, pid: Optional[int] = None) -> List[Tuple[int, int, List[int], int]]:
    """
    构造 DPI 设置报文 (0x04, 0x05)
    返回: List[(cmd_class, cmd_id, args, transaction_id)]
    """
    dpi = max(100, min(35000, dpi))
    dpi_y = dpi if dpi_y is None else max(100, min(35000, dpi_y))

    dpi_x_h = (dpi >> 8) & 0xFF
    dpi_x_l = dpi & 0xFF
    dpi_y_h = (dpi_y >> 8) & 0xFF
    dpi_y_l = dpi_y & 0xFF

    # 7-Byte VARSTORE 协议 [VARSTORE(0x01), X高, X低, Y高, Y低, 0x00, 0x00]
    args_7byte = [VARSTORE, dpi_x_h, dpi_x_l, dpi_y_h, dpi_y_l, 0x00, 0x00]
    return [
        (CMD_CLASS_PERFORMANCE, CMD_ID_SET_DPI, args_7byte, 0xFF)
    ]


def build_polling_rate_packets(rate_hz: int) -> List[Tuple[int, int, List[int], int]]:
    """构造回报率设置报文 (0x00, 0x05)"""
    rate_map_std = {1000: 0x01, 500: 0x02, 125: 0x08}
    val_std = rate_map_std.get(rate_hz, 0x01)

    return [
        (CMD_CLASS_DEVICE, CMD_ID_SET_POLLING_RATE, [val_std], 0xFF)
    ]


CMD_ID_SET_BRIGHTNESS = 0x04

def build_lighting_packets(
    enabled: bool,
    mode: str = "static",
    brightness: int = 100,
    r: int = 0,
    g: int = 255,
    b: int = 0,
    pid: Optional[int] = None
) -> List[Tuple[int, int, List[int], int]]:
    """
    构造雷蛇灯效报文：
    - 支持亮度调节 (0% ~ 100% -> 0 ~ 255) (0x0F, 0x04)
    - 支持常亮模式 Static (0x0F, 0x02)
    - 支持呼吸模式 Breathing (0x0F, 0x02)
    - 支持彻底熄灭 (None / Brightness 0)
    """
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))
    brightness_pct = max(0, min(100, brightness))
    raw_brightness = int(brightness_pct * 255 / 100)

    if pid and pid in SINGLE_COLOR_DEVICES:
        target_leds = SINGLE_COLOR_DEVICES[pid].get("leds", [LOGO_LED])
    else:
        target_leds = [LOGO_LED]

    packets = []

    if enabled and brightness_pct > 0:
        for led_id in target_leds:
            # 1. 亮度设置 (Class 0x0F, ID 0x04, [VARSTORE, led_id, raw_brightness])
            args_brightness = [VARSTORE, led_id, raw_brightness]
            packets.append((CMD_CLASS_LIGHTING, CMD_ID_SET_BRIGHTNESS, args_brightness, 0x3F))

            # 2. 灯效模式设置 (Class 0x0F, ID 0x02)
            if mode == "breathing":
                # 呼吸模式: [VARSTORE(0x01), led_id, 0x02, 0x01, 0x00, 0x01, r, g, b]
                args_breathing = [VARSTORE, led_id, 0x02, 0x01, 0x00, 0x01, r, g, b]
                packets.append((CMD_CLASS_LIGHTING, CMD_ID_SET_LIGHTING, args_breathing, 0x3F))
            else:
                # 静态常亮模式: [VARSTORE(0x01), led_id, 0x01, 0x00, 0x00, 0x01, r, g, b]
                args_static = [VARSTORE, led_id, 0x01, 0x00, 0x00, 0x01, r, g, b]
                packets.append((CMD_CLASS_LIGHTING, CMD_ID_SET_LIGHTING, args_static, 0x3F))
    else:
        for led_id in target_leds:
            # 1. 亮度归零
            args_brightness_zero = [VARSTORE, led_id, 0x00]
            packets.append((CMD_CLASS_LIGHTING, CMD_ID_SET_BRIGHTNESS, args_brightness_zero, 0x3F))

            # 2. 扩展矩阵彻底熄灭: [VARSTORE(0x01), led_id, 0x00, 0x00, 0x00, 0x00]
            args_ext_none = [VARSTORE, led_id, 0x00, 0x00, 0x00, 0x00]
            packets.append((CMD_CLASS_LIGHTING, CMD_ID_SET_LIGHTING, args_ext_none, 0x3F))

    return packets


def list_razer_devices() -> List[Dict[str, Any]]:
    """扫描系统当前已连接的所有雷蛇 HID 设备并标注特性"""
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
        pid = d.get("product_id", 0)

        # 设备特性分析
        is_single_color = pid in SINGLE_COLOR_DEVICES
        dev_spec = SINGLE_COLOR_DEVICES.get(pid, {})
        color_scheme = dev_spec.get("color", "rgb")

        # 判断是否为硬件控制首选接口 (优先 MI_00 / 接口 0)
        is_control_interface = (interface_num == 0) or ("MI_00" in path_str)

        devices.append({
            "path": path_str,
            "vendor_id": d.get("vendor_id", RAZER_VID),
            "vendor_id_hex": f"0x{d.get('vendor_id', RAZER_VID):04X}",
            "product_id": pid,
            "product_id_hex": f"0x{pid:04X}",
            "product_string": d.get("product_string", "Unknown Razer Device"),
            "manufacturer_string": d.get("manufacturer_string", "Razer"),
            "serial_number": d.get("serial_number", ""),
            "release_number": d.get("release_number", 0),
            "interface_number": interface_num,
            "usage_page": usage_page,
            "usage": usage,
            "bus_type": d.get("bus_type", 0),
            "is_control_interface": is_control_interface,
            "is_single_color": is_single_color,
            "color_scheme": color_scheme,
            "supported_leds": ["Logo 氛围灯", "滚轮灯"] if (LOGO_LED in dev_spec.get("leds", [])) else ["全域灯效"]
        })

    # 优先将最合适的控制接口（接口 0 / MI_00）排在首位
    devices.sort(key=lambda x: (0 if (x["interface_number"] == 0 or "MI_00" in x["path"]) else 1, x["interface_number"]))
    return devices


def send_packets_to_device(packets: List[Tuple[int, int, List[int], int]], target_path: Optional[str] = None, target_pid: Optional[int] = None) -> Dict[str, Any]:
    """
    向目标雷蛇设备逐帧下发控制报文并读取状态
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

    candidates = []
    if target_path:
        candidates = [d for d in all_devices if d["path"] == target_path]
    elif target_pid is not None:
        candidates = [d for d in all_devices if d["product_id"] == target_pid]

    if not candidates:
        candidates = sorted(all_devices, key=lambda x: (0 if (x["interface_number"] == 0 or "MI_00" in x["path"]) else 1, x["interface_number"]))

    last_err = None
    target_dev_name = None
    target_pid_hex = None
    best_status = -1
    best_resp_hex = ""

    for dev_meta in candidates:
        dev_handle = None
        try:
            dev_handle = hid.device()
            raw_path = dev_meta.get("path", "")
            path_arg = raw_path.encode("utf-8") if isinstance(raw_path, str) else raw_path
            dev_handle.open_path(path_arg)
            target_dev_name = dev_meta["product_string"]
            target_pid_hex = dev_meta["product_id_hex"]

            # 遍历协议报文列表，依次写入硬件
            any_success = False
            last_status = -1
            for cmd_class, cmd_id, args, trans_id in packets:
                report_payload = create_razer_report(cmd_class, cmd_id, args, trans_id)
                wire_data = b"\x00" + report_payload

                dev_handle.send_feature_report(wire_data)
                time.sleep(0.04)

                response = dev_handle.get_feature_report(0x00, 91)
                if response:
                    status_byte = response[1] if len(response) > 1 else -1
                    last_status = status_byte
                    best_resp_hex = bytes(response).hex()
                    if status_byte in (STATUS_SUCCESS, STATUS_NEW):
                        any_success = True
                        best_status = status_byte

            dev_handle.close()
            dev_handle = None

            status_names = {
                STATUS_SUCCESS: "SUCCESS (0x02)",
                STATUS_BUSY: "BUSY (0x01)",
                STATUS_FAILURE: "FAILURE (0x03)",
                STATUS_TIMEOUT: "TIMEOUT (0x04)",
                STATUS_NOT_SUPPORTED: "NOT_SUPPORTED (0x05)"
            }
            final_status = best_status if any_success else last_status
            status_name = status_names.get(final_status, f"STATUS_0x{final_status:02X}")
            is_success = any_success or (final_status == STATUS_SUCCESS)

            return {
                "success": is_success,
                "status_code": final_status,
                "status_name": status_name,
                "message": f"指令已成功生效于硬件: {target_dev_name}" if is_success else f"设备返回状态: {status_name}",
                "device_name": target_dev_name,
                "device_pid": target_pid_hex,
                "interface_number": dev_meta["interface_number"],
                "response_hex": best_resp_hex[:64] + ("..." if len(best_resp_hex) > 64 else "")
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
        "message": f"与雷蛇设备通信异常: {last_err}",
        "device_name": target_dev_name or (candidates[0]["product_string"] if candidates else None),
        "response_hex": None
    }
