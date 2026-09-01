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
    build_dpi_packets,
    build_polling_rate_packets,
    build_lighting_packets,
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
        """测试 90 字节报文封装与各关键字段结构 (精准对齐 OpenRazer 规范)"""
        cmd_class = 0x04
        cmd_id = 0x05
        args = [0x01, 0x06, 0x40, 0x06, 0x40, 0x00, 0x00]  # 7-byte 1600 DPI

        report = create_razer_report(cmd_class, cmd_id, args, transaction_id=0xFF)

        self.assertEqual(len(report), 90)
        self.assertEqual(report[0], 0x00)  # Status
        self.assertEqual(report[1], 0xFF)  # Transaction ID
        self.assertEqual(report[2], 0x00)  # Remaining Packets MSB
        self.assertEqual(report[3], 0x00)  # Remaining Packets LSB
        self.assertEqual(report[4], 0x00)  # Protocol Type
        self.assertEqual(report[5], len(args))  # Data size = 7 (Offset 5)
        self.assertEqual(report[6], cmd_class)  # Command Class (Offset 6)
        self.assertEqual(report[7], cmd_id)  # Command ID (Offset 7)
        self.assertEqual(list(report[8:15]), args)  # Arguments start at Offset 8
        self.assertEqual(report[89], 0x00)

    def test_report_checksum_xor(self):
        """测试异或校验和 (XOR Checksum) 正确性"""
        cmd_class = 0x00
        cmd_id = 0x05
        args = [0x01]  # 1000Hz

        report = create_razer_report(cmd_class, cmd_id, args, transaction_id=0x3F)
        
        # 按照规则重新计算第 2 到第 87 字节的异或和
        expected_checksum = 0
        for b in report[2:88]:
            expected_checksum ^= b
            
        self.assertEqual(report[88], expected_checksum)

    def test_build_dpi_packets(self):
        """测试 7-Byte VARSTORE DPI 报文构造"""
        packets = build_dpi_packets(1600)
        self.assertEqual(len(packets), 1)

        cls, cmd, args, trans_id = packets[0]
        self.assertEqual(cls, CMD_CLASS_PERFORMANCE)
        self.assertEqual(cmd, CMD_ID_SET_DPI)
        self.assertEqual(args, [0x01, 0x06, 0x40, 0x06, 0x40, 0x00, 0x00])
        self.assertEqual(trans_id, 0xFF)

    def test_build_polling_rate_packets(self):
        """测试回报率报文构造"""
        packets_1000 = build_polling_rate_packets(1000)
        self.assertEqual(len(packets_1000), 1)
        self.assertEqual(packets_1000[0][2], [0x01])

        packets_500 = build_polling_rate_packets(500)
        self.assertEqual(packets_500[0][2], [0x02])

        packets_125 = build_polling_rate_packets(125)
        self.assertEqual(packets_125[0][2], [0x08])

    def test_build_lighting_packets(self):
        """测试 Logo 氛围灯静态常亮与彻底熄灭报文"""
        # 开启灯光 (Logo 0x04)
        packets_on = build_lighting_packets(True, 0, 255, 0)
        self.assertEqual(len(packets_on), 1)

        # 彻底熄灭
        packets_off = build_lighting_packets(False)
        self.assertEqual(len(packets_off), 1)

    def test_list_razer_devices(self):
        """测试设备探测函数正确执行且具备设备特性字段"""
        devices = list_razer_devices()
        self.assertIsInstance(devices, list)
        if devices:
            dev = devices[0]
            self.assertIn("is_single_color", dev)
            self.assertIn("color_scheme", dev)
            self.assertIn("supported_leds", dev)


if __name__ == "__main__":
    unittest.main()
