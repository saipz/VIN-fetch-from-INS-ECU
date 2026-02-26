import can
import time
 
print("=" * 70)
print("EMS Diagnostics via Broadcast (SA 0x17) - Fixed Multi-Frame")
print("=" * 70)
 
CAN_INTERFACE = 'pcan'
CAN_CHANNEL = 'PCAN_USBBUS1'
CAN_BITRATE = 250000
 
BROADCAST_ID = 0x18DB33F1
EMS_RESPONSE_ID = 0x18DAF117
FLOW_CONTROL_ID = 0x18DA17F1
 
def flush_recv(bus, duration=0.2):
    start = time.time()
    while time.time() - start < duration:
        bus.recv(timeout=0.01)
 
def send_request(bus, data):
    padded = data + bytes([0x00] * (8 - len(data)))
    msg = can.Message(
        arbitration_id=BROADCAST_ID,
        data=padded,
        is_extended_id=True
    )
    bus.send(msg)
    return msg
 
def receive_response(bus, timeout=1.0):
    start = time.time()
    while time.time() - start < timeout:
        msg = bus.recv(timeout=0.1)
        if msg and msg.arbitration_id == EMS_RESPONSE_ID:
            return msg
    return None
 
def read_multiframe_response(bus, first_frame):
    """Handle ISO-TP multi-frame response"""
    data = bytearray(first_frame.data)
    print(f"\n  [Multi-Frame Handler]")
    print(f"  First frame: {data.hex().upper()}")
    # Check frame type
    frame_type = data[0] & 0xF0
    if frame_type == 0x00:
        # Single frame
        length = data[0] & 0x0F
        print(f"  Single frame, length: {length}")
        return bytes(data[1:1+length])
    elif frame_type == 0x10:
        # First frame of multi-frame
        total_length = ((data[0] & 0x0F) << 8) | data[1]
        print(f"  Multi-frame start, total: {total_length} bytes")
        # Collect data from first frame (starts at byte 2)
        response_data = bytearray(data[2:])
        print(f"  First frame data: {response_data.hex().upper()}")
        # Send flow control
        print(f"  Sending flow control to 0x{FLOW_CONTROL_ID:08X}...")
        flow_msg = can.Message(
            arbitration_id=FLOW_CONTROL_ID,
            data=[0x30, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
            is_extended_id=True
        )
        bus.send(flow_msg)
        print(f"  Flow control sent: {flow_msg.data.hex().upper()}")
        # Wait a bit for ECU to process
        time.sleep(0.05)
        # Receive consecutive frames
        expected_seq = 1
        max_frames = 20  # Safety limit
        frame_count = 0
        while len(response_data) < total_length and frame_count < max_frames:
            msg = receive_response(bus, timeout=2.0)
            if not msg:
                print(f"  ✗ Timeout waiting for consecutive frame {expected_seq}")
                break
            frame_data = bytearray(msg.data)
            frame_type_check = frame_data[0] & 0xF0
            print(f"  Received frame: {frame_data.hex().upper()}")
            if frame_type_check == 0x20:
                # Consecutive frame
                seq = frame_data[0] & 0x0F
                print(f"  Consecutive frame, seq: {seq}")
                if seq == expected_seq:
                    # Extract data (bytes 1-7 contain data)
                    remaining = total_length - len(response_data)
                    data_to_add = frame_data[1:min(8, 1+remaining)]
                    response_data.extend(data_to_add)
                    print(f"  Added {len(data_to_add)} bytes, total: {len(response_data)}/{total_length}")
                    expected_seq = (expected_seq + 1) % 16
                else:
                    print(f"  ⚠ Sequence error: expected {expected_seq}, got {seq}")
            else:
                print(f"  ⚠ Unexpected frame type: 0x{frame_type_check:02X}")
            frame_count += 1
        print(f"  Multi-frame complete: {len(response_data)} bytes received")
        return bytes(response_data[:total_length])
    else:
        print(f"  Unknown frame type: 0x{frame_type:02X}")
        return bytes(data[1:])
 
try:
    bus = can.Bus(interface=CAN_INTERFACE, channel=CAN_CHANNEL, bitrate=CAN_BITRATE)
    print(f"✓ Connected at {CAN_BITRATE} bps\n")
    # Tester Present
    print("[1] Tester Present (0x3E)")
    flush_recv(bus)
    req = send_request(bus, bytes([0x02, 0x3E, 0x00]))
    print(f"  Sent: {req.data.hex().upper()}")
    resp = receive_response(bus, timeout=0.5)
    if resp:
        print(f"  ✓ Response: {resp.data.hex().upper()}")
    time.sleep(0.5)
    # Extended Session
    print("\n[2] Enter Extended Session (0x10 0x03)")
    flush_recv(bus)
    req = send_request(bus, bytes([0x02, 0x10, 0x03]))
    print(f"  Sent: {req.data.hex().upper()}")
    resp = receive_response(bus, timeout=0.5)
    if resp:
        print(f"  ✓ Response: {resp.data.hex().upper()}")
        if resp.data[1] == 0x50:
            print(f"  ✓ Extended session activated")
    time.sleep(0.5)
    # Read VIN
    print("\n[3] Read VIN (DID 0xF1A0)")
    flush_recv(bus, duration=0.5)
    req = send_request(bus, bytes([0x03, 0x22, 0xF1, 0xA0]))
    print(f"  Sent: {req.data.hex().upper()}")
    resp = receive_response(bus, timeout=1.0)
    if resp:
        print(f"  ✓ First response: {resp.data.hex().upper()}")
        if resp.data[0] == 0x7F:
            # Negative response
            print(f"  ✗ Negative response: NRC 0x{resp.data[2]:02X}")
        else:
            # Process multi-frame response
            full_data = read_multiframe_response(bus, resp)
            print(f"\n  Full response data: {full_data.hex().upper()}")
            # Parse VIN
            # Format: [62 F1 A0 VIN_17_BYTES]
            if full_data[0] == 0x62 and full_data[1] == 0xF1 and full_data[2] == 0xA0:
                vin_bytes = full_data[3:]
                try:
                    vin = vin_bytes.decode('ascii', errors='replace').rstrip('\x00\xff ')
                    print(f"\n{'=' * 70}")
                    print(f"VIN RETRIEVED:")
                    print(f"{'=' * 70}")
                    print(f"  {vin}")
                    print(f"  Length: {len(vin)} characters")
                    print(f"  Raw bytes: {vin_bytes.hex().upper()}")
                    print(f"{'=' * 70}")
                except Exception as e:
                    print(f"  ⚠ VIN decode error: {e}")
                    print(f"  Raw: {vin_bytes.hex().upper()}")
            else:
                print(f"  ⚠ Unexpected response format")
    else:
        print(f"  ✗ No response")
    bus.shutdown()
    print("\n[DONE]\n")
 
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    if 'bus' in locals():
        bus.shutdown() 
 
