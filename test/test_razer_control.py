"""
Unit and Protocol tests for razer_control service.
"""
import os
import sys
import unittest
from pathlib import Path

# 添加项目根目录到 sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.razer_control.server.protocol import (
    create_razer_report,
    build_dpi_args,
    build_polling_rate_args,
    build_static_led_args,
    build_turn_off_led_args,
    CMD_CLASS_PERFORMANCE,
    CMD_CLASS_DEVICE,
    CMD_CLASS_LIGHTING,
    CMD_ID_SET_DPI,
    CMD_ID_SET_POLLING_RATE,
    CMD_ID_SET_LIGHTING,
    list_razer_devices
)


class TestRazerControlProtocol(unittest.TestCase):
    def test_create_razer_report_length_and_structure(self):
        """测试 90 字节报文封装与各关键字段结构"""
        cmd_class = 0x04
        cmd_id = 0x05
        args = [0x00, 0x06, 0x40, 0x06, 0x40] # 1600 DPI

        report = create_razer_report(cmd_class, cmd_id, args)
        
        self.assertEqual(len(report), 90)
        self.assertEqual(report[0], 0x00)  # Status
        self.assertEqual(report[1], 0xFF)  # Transaction ID
        self.assertEqual(report[2], 0x00)  # Remaining Packets
        self.assertEqual(report[3], 0x00)  # Protocol Type
        self.assertEqual(report[4], len(args))  # Data size = 5
        self.assertEqual(report[5], cmd_class)
        self.assertEqual(report[6], cmd_id)
        self.assertEqual(list(report[7:12]), args)
        self.assertEqual(report[89], 0x00)

    def test_report_checksum_xor(self):
        """测试异或校验和 (XOR Checksum) 正确性"""
        cmd_class = 0x00
        cmd_id = 0x05
        args = [0x01] # 1000Hz

        report = create_razer_report(cmd_class, cmd_id, args)
        
        # 按照规则重新计算第 2 到第 87 字节的异或和
        expected_checksum = 0
        for b in report[2:88]:
            expected_checksum ^= b
            
        self.assertEqual(report[88], expected_checksum)

    def test_build_dpi_args(self):
        """测试 DPI 转换与高低字节拆分"""
        # 1600 = 0x0640 -> high=0x06, low=0x40
        cls, cmd, args = build_dpi_args(1600)
        self.assertEqual(cls, CMD_CLASS_PERFORMANCE)
        self.assertEqual(cmd, CMD_ID_SET_DPI)
        self.assertEqual(args, [0x00, 0x06, 0x40, 0x06, 0x40])

        # 800 = 0x0320 -> high=0x03, low=0x20
        cls, cmd, args = build_dpi_args(800)
        self.assertEqual(args, [0x00, 0x03, 0x20, 0x03, 0x20])

        # 独立 X/Y 轴: X=1600, Y=800
        cls, cmd, args = build_dpi_args(1600, 800)
        self.assertEqual(args, [0x00, 0x06, 0x40, 0x03, 0x20])

    def test_build_polling_rate_args(self):
        """测试回报率映射 (1000Hz->0x01, 500Hz->0x02, 125Hz->0x08)"""
        cls, cmd, args_1000 = build_polling_rate_args(1000)
        self.assertEqual(cls, CMD_CLASS_DEVICE)
        self.assertEqual(cmd, CMD_ID_SET_POLLING_RATE)
        self.assertEqual(args_1000, [0x01])

        _, _, args_500 = build_polling_rate_args(500)
        self.assertEqual(args_500, [0x02])

        _, _, args_125 = build_polling_rate_args(125)
        self.assertEqual(args_125, [0x08])

    def test_build_lighting_args(self):
        """测试灯效参数与关灯模式"""
        # 静态绿色 RGB (0, 255, 0)
        cls, cmd, args_led = build_static_led_args(0, 255, 0)
        self.assertEqual(cls, CMD_CLASS_LIGHTING)
        self.assertEqual(cmd, CMD_ID_SET_LIGHTING)
        self.assertEqual(args_led, [0x01, 0x01, 0, 255, 0])

        # 彻底关灯
        cls, cmd, args_off = build_turn_off_led_args()
        self.assertEqual(cls, CMD_CLASS_LIGHTING)
        self.assertEqual(cmd, CMD_ID_SET_LIGHTING)
        self.assertEqual(args_off, [0x01, 0x00])

    def test_list_razer_devices(self):
        """测试设备探测函数不会崩溃并返回列表"""
        devices = list_razer_devices()
        self.assertIsInstance(devices, list)


if __name__ == "__main__":
    unittest.main()
