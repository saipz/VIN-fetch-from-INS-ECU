import can
import time
 
CAN_INTERFACE = 'pcan'
CAN_CHANNEL = 'PCAN_USBBUS1'
CAN_BITRATE = 250000
 
BROADCAST_ID    = 0x18DB33F1
EMS_RESPONSE_ID = 0x18DAF100   # SA=0x00 = EMS
FLOW_CONTROL_ID = 0x18DA00F1   # DA=0x00 = EMS
 
def flush_recv(bus, duration=0.3):
    start = time.time()
    while time.time() - start < duration:
        bus.recv(timeout=0.01)
 
def send_request(bus, arb_id, data):
    padded = data + bytes([0x00] * (8 - len(data)))
    msg = can.Message(arbitration_id=arb_id, data=padded, is_extended_id=True)
    bus.send(msg)
    return msg
 
def receive_response(bus, expected_id, timeout=1.0):
    start = time.time()
    while time.time() - start < timeout:
        msg = bus.recv(timeout=0.1)
        if msg and msg.arbitration_id == expected_id:
            return msg
    return None
 
bus = can.Bus(interface=CAN_INTERFACE, channel=CAN_CHANNEL, bitrate=CAN_BITRATE)
print(f"✓ Connected\n")
 
# --- Step 1: Tester Present ---
print("[1] Tester Present")
flush_recv(bus)
send_request(bus, BROADCAST_ID, bytes([0x02, 0x3E, 0x00]))
resp = receive_response(bus, EMS_RESPONSE_ID, timeout=1.0)
if resp:
    print(f"  ✓ Response: {resp.data.hex().upper()}")
else:
    print(f"  ✗ No response from SA 0x00")
time.sleep(0.3)
 
# --- Step 2: Extended Session ---
print("\n[2] Extended Diagnostic Session")
flush_recv(bus)
send_request(bus, BROADCAST_ID, bytes([0x02, 0x10, 0x03]))
resp = receive_response(bus, EMS_RESPONSE_ID, timeout=1.0)
if resp:
    print(f"  ✓ Response: {resp.data.hex().upper()}")
    if resp.data[1] == 0x50:
        print(f"  ✓ Extended session active")
    elif resp.data[1] == 0x7F:
        print(f"  ✗ Negative response NRC: 0x{resp.data[2]:02X}")
time.sleep(0.3)
 
# --- Step 3: Read VIN ---
print("\n[3] Read VIN (0xF1A0)")
flush_recv(bus, duration=0.5)
send_request(bus, BROADCAST_ID, bytes([0x03, 0x22, 0xF1, 0xA0]))
resp = receive_response(bus, EMS_RESPONSE_ID, timeout=1.5)
 
if resp:
    print(f"  ✓ Response: {resp.data.hex().upper()}")
    frame_type = resp.data[0] & 0xF0
 
    if resp.data[1] == 0x7F:
        print(f"  ✗ Negative NRC: 0x{resp.data[3]:02X}")
 
    elif frame_type == 0x10:  # Multi-frame
        total_length = ((resp.data[0] & 0x0F) << 8) | resp.data[1]
        print(f"  Multi-frame: {total_length} bytes total")
        response_data = bytearray(resp.data[2:])
 
        # Send Flow Control to EMS specifically
        fc = can.Message(
            arbitration_id=FLOW_CONTROL_ID,
            data=[0x30, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
            is_extended_id=True
        )
        bus.send(fc)
        print(f"  Flow Control sent → 0x{FLOW_CONTROL_ID:08X}")
 
        # Collect consecutive frames
        expected_seq = 1
        while len(response_data) < total_length:
            cf = receive_response(bus, EMS_RESPONSE_ID, timeout=2.0)
            if not cf:
                print("  ✗ Timeout on consecutive frame")
                break
            seq = cf.data[0] & 0x0F
            if cf.data[0] & 0xF0 == 0x20:
                remaining = total_length - len(response_data)
                response_data.extend(cf.data[1:min(8, 1 + remaining)])
                print(f"  CF seq={seq}: {cf.data.hex().upper()} ({len(response_data)}/{total_length})")
                expected_seq = (expected_seq + 1) % 16
 
        full = bytes(response_data[:total_length])
        if full[0] == 0x62 and full[1] == 0xF1 and full[2] == 0xA0:
            vin = full[3:].decode('ascii', errors='replace').rstrip('\x00\xff ')
            print(f"\n{'='*60}")
            print(f"  EMS VIN: {vin}")
            print(f"{'='*60}")
 
    elif frame_type == 0x00:  # Single frame
        length = resp.data[0] & 0x0F
        full = bytes(resp.data[1:1+length])
        if full[0] == 0x62:
            vin = full[3:].decode('ascii', errors='replace').rstrip('\x00\xff ')
            print(f"\n  EMS VIN: {vin}")
else:
    print("  ✗ No response — EMS may not support 0xF1A0")
    print("  Try DID 0xF190 (standard VIN DID) instead")
 
bus.shutdown()
print("\n[DONE]")