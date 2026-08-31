import hid
import time

def test_all():
    devs = hid.enumerate(0x1532)
    for idx, d in enumerate(devs):
        print(f"\n=== Interface [{idx}] #number: {d.get('interface_number')}, usage_page: 0x{d.get('usage_page'):04X}, usage: 0x{d.get('usage'):04X} ===")
        print(f"Path: {d['path']}")
        try:
            h = hid.device()
            h.open_path(d["path"])
            
            # Try sending DPI command
            report = bytearray(90)
            report[1] = 0xFF
            report[4] = 0x07
            report[5] = 0x04
            report[6] = 0x05
            report[7:14] = [0x01, 0x06, 0x40, 0x06, 0x40, 0x00, 0x00]
            checksum = 0
            for b in report[2:88]: checksum ^= b
            report[88] = checksum
            
            h.send_feature_report(b"\x00" + bytes(report))
            time.sleep(0.04)
            resp = h.get_feature_report(0x00, 91)
            st = resp[1] if len(resp) > 1 else -1
            print(f"  Result -> status: 0x{st:02X} (Hex: {bytes(resp)[:14].hex()})")
            h.close()
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    test_all()
