import hid
import time

def probe():
    devs = hid.enumerate(0x1532)
    print(f"Total Razer interfaces: {len(devs)}")
    for idx, d in enumerate(devs):
        path = d["path"]
        print(f"\n--- Interface [{idx}] #number: {d.get('interface_number')}, usage_page: {d.get('usage_page')}, usage: {d.get('usage')} ---")
        try:
            h = hid.device()
            h.open_path(path)
            
            # Test 1: Get Firmware version (0x00, 0x81)
            # Test 2: Get Serial (0x00, 0x82)
            # Test 3: Get Device Mode (0x00, 0x84)
            # Test 4: Get DPI (0x04, 0x85)
            # Test 5: Get Polling rate (0x00, 0x85)
            # Test 6: Get LED State (0x03, 0x80)
            
            queries = [
                ("Get Firmware Version", 0x00, 0x81, [0x00, 0x00]),
                ("Get Serial", 0x00, 0x82, [0x00]*22),
                ("Get Device Mode", 0x00, 0x84, [0x00, 0x00]),
                ("Get DPI (0x04, 0x85)", 0x04, 0x85, [0x00, 0x00, 0x00, 0x00, 0x00]),
                ("Get DPI (0x04, 0x81)", 0x04, 0x81, [0x00, 0x00, 0x00, 0x00]),
                ("Get Poll Rate (0x00, 0x85)", 0x00, 0x85, [0x00]),
                ("Get LED State (0x03, 0x80)", 0x03, 0x80, [0x01, 0x01]),
                ("Get LED State (0x0F, 0x82)", 0x0F, 0x82, [0x01, 0x01]),
            ]
            
            for name, cmd_class, cmd_id, args in queries:
                for trans_id in [0x1F, 0xFF, 0x3F, 0x00]:
                    report = bytearray(90)
                    report[1] = trans_id
                    report[4] = len(args)
                    report[5] = cmd_class
                    report[6] = cmd_id
                    for i, a in enumerate(args):
                        report[7+i] = a
                    checksum = 0
                    for b in report[2:88]:
                        checksum ^= b
                    report[88] = checksum
                    
                    try:
                        h.send_feature_report(b"\x00" + bytes(report))
                        time.sleep(0.02)
                        resp = h.get_feature_report(0x00, 91)
                        st = resp[1] if len(resp) > 1 else -1
                        if st == 0x02: # SUCCESS!
                            print(f"  >>> [SUCCESS 0x02] {name} trans=0x{trans_id:02X} -> Resp: {bytes(resp)[:20].hex()}")
                        elif st != 0x05: # Not just not supported
                            print(f"  [*] {name} trans=0x{trans_id:02X} -> status: 0x{st:02X}, resp: {bytes(resp)[:16].hex()}")
                    except Exception as err:
                        pass
            h.close()
        except Exception as e:
            print(f"  Cannot open interface: {e}")

if __name__ == "__main__":
    probe()
