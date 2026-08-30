"""
Direct hardware detection and diagnostic test for connected Razer devices.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import hid
import time
from services.razer_control.server.protocol import (
    RAZER_VID,
    list_razer_devices,
    create_razer_report,
    build_dpi_args,
    build_polling_rate_args,
    build_static_led_args,
    send_to_razer,
)

def run_hardware_diagnostics():
    print("=" * 60)
    print("【雷蛇硬件直通探测与通信测试】")
    print("=" * 60)

    # 1. 枚举设备
    devices = list_razer_devices()
    print(f"1. 系统扫描结果: 检测到 {len(devices)} 个雷蛇 HID 接口\n")

    if not devices:
        print("[-] 未检测到任何雷蛇设备！请确认鼠标已插入 USB 接口。")
        return

    for idx, dev in enumerate(devices):
        print(f"[{idx+1}] 设备型号: {dev['product_string']}")
        print(f"    厂商: {dev['manufacturer_string']} (VID: {dev['vendor_id_hex']})")
        print(f"    产品 ID (PID): {dev['product_id_hex']}")
        print(f"    接口编号 (Interface): #{dev['interface_number']}")
        print(f"    UsagePage: 0x{dev['usage_page']:04X}, Usage: 0x{dev['usage']:04X}")
        print(f"    控制接口候选: {'★ 是 (推荐)' if dev['is_control_interface'] else '否'}")
        print(f"    路径: {dev['path']}")
        print("-" * 50)

    # 2. 测试对每个接口进行打开和通信探测
    print("\n2. 尝试与设备接口建立 HID Feature Report 通信:")
    
    # 构造一条读取或设置 DPI 的测试帧 (1600 DPI)
    cls, cmd, args = build_dpi_args(1600)
    report = create_razer_report(cls, cmd, args)
    wire_data = b"\x00" + report

    success_interfaces = []

    for idx, dev in enumerate(devices):
        path = dev["path"]
        path_bytes = path.encode("utf-8") if isinstance(path, str) else path
        dev_handle = None
        try:
            dev_handle = hid.device()
            dev_handle.open_path(path_bytes)
            print(f"\n[接口 #{dev['interface_number']} - {dev['product_string']}] -> 成功打开 HID 句柄")
            
            # 发送 Feature Report
            dev_handle.send_feature_report(wire_data)
            time.sleep(0.05)
            
            # 读取 ACK
            resp = dev_handle.get_feature_report(0x00, 91)
            resp_bytes = bytes(resp)
            status_byte = resp_bytes[1] if len(resp_bytes) > 1 else -1
            print(f"  -> 发送 90-Byte Payload 成功")
            print(f"  -> 收到设备响应 ({len(resp_bytes)} 字节): 状态码 = 0x{status_byte:02X} ({'0x02 SUCCESS' if status_byte == 0x02 else 'OTHER'})")
            print(f"  -> 响应 Hex 前缀: {resp_bytes[:16].hex()}")
            
            dev_handle.close()
            success_interfaces.append(dev)
        except Exception as e:
            print(f"  -> 通信异常: {e}")
            if dev_handle:
                try:
                    dev_handle.close()
                except Exception:
                    pass

    print("\n" + "=" * 60)
    if success_interfaces:
        print(f"【测试通过】已成功与雷蛇鼠标（{success_interfaces[0]['product_string']}）完成 HID 双向通信！")
    else:
        print("【提示】未能在当前接口完成通信，可能需要检查雷云是否完全独占了句柄。")
    print("=" * 60)


if __name__ == "__main__":
    run_hardware_diagnostics()
