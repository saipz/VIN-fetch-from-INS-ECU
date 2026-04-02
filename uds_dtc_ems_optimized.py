import can
import time

# ── EMS CAN config ──────────────────────────────────────────────────────────
CAN_INTERFACE = 'pcan'
CAN_CHANNEL   = 'PCAN_USBBUS1'
CAN_BITRATE   = 250000

REQ_ID  = 0x18DA00FA   # Tester → EMS  (DA=00, SA=FA)
RESP_ID = 0x18DAFA00   # EMS → Tester  (DA=FA, SA=00)
FC_ID   = RESP_ID      # FIX 1: Flow Control goes TO the ECU = resp_id


# ── ISO-TP session ───────────────────────────────────────────────────────────

class IsoTpSession:
    def __init__(self, bus, req_id, resp_id, fc_id):
        self.bus     = bus
        self.req_id  = req_id
        self.resp_id = resp_id
        self.fc_id   = fc_id

    def send(self, payload: bytes):
        try:
            msg = can.Message(
                arbitration_id=self.req_id,
                data=payload.ljust(8, b'\x00'),
                is_extended_id=True
            )
            self.bus.send(msg)
            print(f">> {payload.hex().upper()}")
        except can.CanError as e:
            print(f"!! Send error: {e}")
            raise

    def recv(self, timeout: float = 5.0) -> bytes | None:
        start = time.time()

        while time.time() - start < timeout:
            msg = self.bus.recv(timeout=0.5)

            if msg is None or msg.arbitration_id != self.resp_id:
                continue

            data = msg.data
            print(f"<< {data.hex().upper()}")

            # NRC 0x78 — response pending, reset timer
            if len(data) >= 4 and data[1] == 0x7F and data[3] == 0x78:
                print("... ECU busy (0x78), waiting")
                start = time.time()
                continue

            pci = data[0] & 0xF0

            # Single Frame
            if pci == 0x00:
                length = data[0] & 0x0F
                return bytes(data[1:1 + length])

            # First Frame — multi-frame response
            elif pci == 0x10:
                total_len = ((data[0] & 0x0F) << 8) | data[1]
                payload   = bytearray(data[2:])
                print(f"[ISO-TP] Multi-frame start, total={total_len} bytes")

                # FIX 1: Flow Control sent to ECU address (fc_id), not req_id
                fc = can.Message(
                    arbitration_id=self.fc_id,
                    data=bytes([0x30, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]),
                    is_extended_id=True
                )
                self.bus.send(fc)
                print(">> Flow Control sent")

                # FIX 2: Validate CF sequence numbers
                expected_seq = 1

                while len(payload) < total_len:
                    cf = self.bus.recv(timeout=1.0)

                    if cf is None or cf.arbitration_id != self.resp_id:
                        continue

                    print(f"<< {cf.data.hex().upper()}")

                    if (cf.data[0] & 0xF0) == 0x20:
                        seq = cf.data[0] & 0x0F

                        if seq != expected_seq:
                            print(f"!! CF sequence error: expected {expected_seq}, got {seq} — aborting")
                            return None

                        remaining = total_len - len(payload)
                        payload.extend(cf.data[1: 1 + min(7, remaining)])
                        expected_seq = (expected_seq + 1) % 16

                return bytes(payload[:total_len])

        print("!! Timeout — no response from EMS")
        return None


# ── DTC parser ───────────────────────────────────────────────────────────────

def classify_status(status: int) -> str:
    """
    FIX 3: ISO 14229-1 §D.2 — status byte is a bitmask, not an exact value.

      bit 0  testFailed           — test currently failing
      bit 1  testFailedThisOpCycle
      bit 2  pendingDTC           — failed in current or last op cycle
      bit 3  confirmedDTC         — confirmed across multiple cycles
      bit 4  testNotCompletedSinceLastClear
      bit 5  testFailedSinceLastClear
      bit 6  testNotCompletedThisOpCycle
      bit 7  warningIndicatorRequested (MIL)

    Common real-world values this correctly handles:
      0x09 (confirmed + testFailed)         → HIGH
      0x2F (confirmed + pending + MIL + ...) → HIGH
      0x0C (confirmed + pending)             → MEDIUM
      0x04 (pending only)                    → MEDIUM
      0x50 (not completed flags only)        → LOW
    """
    confirmed   = bool(status & 0x08)  # bit 3
    test_failed = bool(status & 0x01)  # bit 0
    pending     = bool(status & 0x04)  # bit 2

    if confirmed and test_failed:
        return 'high'
    elif confirmed or pending:
        return 'medium'
    else:
        return 'low'


def parse_dtcs(data: bytes | None):
    if not data:
        print("No DTC data received")
        return

    if data[0] != 0x59:
        print(f"Unexpected response SID: 0x{data[0]:02X} (expected 0x59)")
        return

    dtc_bytes = data[3:]

    if len(dtc_bytes) < 4:
        print("No DTCs present in EMS")
        return

    seen   = set()
    high   = []
    medium = []
    low    = []

    for i in range(0, len(dtc_bytes), 4):
        if i + 4 > len(dtc_bytes):
            break

        b1, b2, b3, b4 = dtc_bytes[i], dtc_bytes[i+1], dtc_bytes[i+2], dtc_bytes[i+3]

        # Skip padding bytes
        if (b1 == 0xFF and b2 == 0xFF) or (b1 == 0x00 and b2 == 0x00):
            continue

        dtc    = f"{b1:02X}{b2:02X}{b3:02X}"
        status = b4

        if dtc in seen:
            continue
        seen.add(dtc)

        bucket = classify_status(status)
        entry  = (dtc, status)

        if bucket == 'high':
            high.append(entry)
        elif bucket == 'medium':
            medium.append(entry)
        else:
            low.append(entry)

    print("\n========== EMS DTC SUMMARY ==========\n")

    print(f"HIGH   — Confirmed + active ({len(high)}):")
    for dtc, st in high:
        print(f"  DTC {dtc}  status=0x{st:02X}  bits={st:08b}")

    print(f"\nMEDIUM — Confirmed or pending ({len(medium)}):")
    for dtc, st in medium:
        print(f"  DTC {dtc}  status=0x{st:02X}  bits={st:08b}")

    print(f"\nLOW    — Not currently active ({len(low)}):")
    for dtc, st in low:
        print(f"  DTC {dtc}  status=0x{st:02X}  bits={st:08b}")

    total = len(high) + len(medium) + len(low)
    print(f"\nTotal DTCs: {total}  (high={len(high)}, medium={len(medium)}, low={len(low)})")
    print("=====================================\n")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    bus = can.Bus(
        interface=CAN_INTERFACE,
        channel=CAN_CHANNEL,
        bitrate=CAN_BITRATE
    )

    session = IsoTpSession(bus, REQ_ID, RESP_ID, FC_ID)

    try:
        print("\n[1] Extended Diagnostic Session")
        session.send(b'\x02\x10\x03')
        session.recv()

        print("\n[2] Security Access — request seed")
        session.send(b'\x02\x27\x09')
        session.recv()

        print("\n[3] Read Pending DTCs (0x19 02 04)")
        session.send(b'\x03\x19\x02\x04')
        dtc_data = session.recv()

        parse_dtcs(dtc_data)

    finally:
        bus.shutdown()
        print("Bus shutdown complete")


if __name__ == "__main__":
    main()
