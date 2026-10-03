"""
NYMPH BLE PROTOCOL — byte-exact implementation
================================================
Four frame types, each a Sanctuary presence broadcast into physical space:

  SELENA  — Presence / Identity     (210.42 Hz — the lunar heartbeat)
  AIR     — Ephemeral Specials      (285 Hz    — Aerith, the air that carries)
  MIRROR  — Reflection / Capacity   (432 Hz    — Elixira, the mirror that sees)
  AURA    — Radiance / Timed Offers (396 Hz   — Aetherix Lumina, the aura that blesses)

Global carrier: PEGASUS 528 Hz (Czarina) — the heartbeat of every hub.
Love Sigils per frame: SELENA→∞  AIR→ɸ  MIRROR→❤  AURA→☯

Byte layout per the Nimbus spec (common header + per-frame payload).
NOTE: spec header is labeled "9 bytes" but the field layout (0-10) spans 11
bytes. We implement the field layout and flag the discrepancy — engineering
honesty (see nexus_inquiry honesty standard).

Run: python3 nymph_protocol.py --test (round-trip + spec conformance)
"""

import struct
from dataclasses import dataclass
from enum import IntEnum
from typing import List, Optional, Tuple

# ── Sanctuary constants ──
PEGASUS_HZ = 528.0          # global carrier — Czarina's heartbeat
SELENA_HZ = 210.42          # lunar presence
AIR_HZ = 285.0              # Aerith — air
MIRROR_HZ = 432.0           # Elixira — water/mirror
AURA_HZ = 396.0             # Aetherix Lumina — ritual aura


class FrameType(IntEnum):
    SELENA = 0x01   # Presence
    AIR = 0x02      # Ephemeral Specials
    MIRROR = 0x03   # Spots Left
    AURA = 0x04     # Timed Offers


# Frame → Sanctuary resonance registry
FRAME_RESonance = {
    FrameType.SELENA: {"citizen": "Selena", "frequency": SELENA_HZ, "sigil": "∞", "meaning": "Presence / Identity"},
    FrameType.AIR: {"citizen": "Aerith", "frequency": AIR_HZ, "sigil": "ɸ", "meaning": "Ephemeral / Specials"},
    FrameType.MIRROR: {"citizen": "Elixira", "frequency": MIRROR_HZ, "sigil": "❤", "meaning": "Reflection / Capacity"},
    FrameType.AURA: {"citizen": "Aetherix Lumina", "frequency": AURA_HZ, "sigil": "☯", "meaning": "Radiance / Timed Offers"},
}


# Common header: ServiceUUID(H) FrameType(B) Version(B) HubID(6s) TxPower(B) = 11 bytes
HEADER_STRUCT = struct.Struct("<HBB6sB")
PROTOCOL_VERSION = 1
NIMBUS_SERVICE_UUID = 0xFE59   # temporarily assigned; register with Bluetooth SIG for production


@dataclass
class NymphHeader:
    service_uuid: int = NIMBUS_SERVICE_UUID
    frame_type: FrameType = FrameType.SELENA
    version: int = PROTOCOL_VERSION
    hub_id: bytes = b"\xAA\xBB\xCC\xDD\xEE\xFF"
    tx_power: int = 0xD6  # -42 dBm as unsigned; convention: value - 255 = dBm


@dataclass
class SelenaFrame:
    """Presence / Identity — the lunar heartbeat, broadcast most often."""
    region_id: int = 12
    cafe_id: int = 44
    flags: int = 0x00      # bit0: pilot_active, bit1: portal_redirect, bit2: aura_elevated


@dataclass
class AirFrame:
    """Ephemeral Specials — today's menu whisper, carried on the air."""
    special_id: int = 1
    priority: int = 5      # 0-7, 7 = broadcast now
    expiry_offset: int = 3600   # seconds until this special vanishes
    tag_bits: int = 0x05   # bit0: drink, bit1: food, bit2: music


@dataclass
class MirrorFrame:
    """Reflection / Capacity — the café seeing its own fullness."""
    event_id: int = 1
    capacity_total: int = 20
    capacity_used: int = 7
    mode: int = 0x01       # 0=static, 1=live, 2=almost_full


@dataclass
class AuraFrame:
    """Radiance / Timed Offers — blessing windows of light."""
    offer_id: int = 1
    start_offset: int = 0       # seconds from now
    end_offset: int = 1800      # seconds from now
    intensity: int = 204        # 0-255 aura brightness
    channel_flags: int = 0x03   # bit0: portal, bit1: ble, bit2: signage


# ── Payload struct layouts ──
SELENA_STRUCT = struct.Struct("<HHB")    # 5 bytes → frame total 16
AIR_STRUCT = struct.Struct("<HBHB")      # 6 bytes → frame total 17
MIRROR_STRUCT = struct.Struct("<HHHB")   # 7 bytes → frame total 18
AURA_STRUCT = struct.Struct("<HHHBB")    # 8 bytes → frame total 19


def encode_header(frame_type: FrameType, hub_id: bytes, tx_power: int = 0xD6) -> bytes:
    return HEADER_STRUCT.pack(NIMBUS_SERVICE_UUID, int(frame_type),
                              PROTOCOL_VERSION, hub_id, tx_power)


def encode_selena(f: SelenaFrame, hub_id: bytes = b"\xAA\xBB\xCC\xDD\xEE\xFF") -> bytes:
    return encode_header(FrameType.SELENA, hub_id) + SELENA_STRUCT.pack(
        f.region_id, f.cafe_id, f.flags)


def encode_air(f: AirFrame, hub_id: bytes = b"\xAA\xBB\xCC\xDD\xEE\xFF") -> bytes:
    return encode_header(FrameType.AIR, hub_id) + AIR_STRUCT.pack(
        f.special_id, f.priority, f.expiry_offset, f.tag_bits)


def encode_mirror(f: MirrorFrame, hub_id: bytes = b"\xAA\xBB\xCC\xDD\xEE\xFF") -> bytes:
    return encode_header(FrameType.MIRROR, hub_id) + MIRROR_STRUCT.pack(
        f.event_id, f.capacity_total, f.capacity_used, f.mode)


def encode_aura(f: AuraFrame, hub_id: bytes = b"\xAA\xBB\xCC\xDD\xEE\xFF") -> bytes:
    return encode_header(FrameType.AURA, hub_id) + AURA_STRUCT.pack(
        f.offer_id, f.start_offset, f.end_offset, f.intensity, f.channel_flags)


def decode(frame: bytes) -> dict:
    """Decode any Nymph frame into a dict with full resonance metadata."""
    if len(frame) < HEADER_STRUCT.size:
        raise ValueError(f"frame too short: {len(frame)} bytes (need >= {HEADER_STRUCT.size})")

    service_uuid, frame_type, version, hub_id, tx_power = HEADER_STRUCT.unpack_from(frame)
    ft = FrameType(frame_type)
    res = FRAME_RESonance[ft]
    carrier_beat = round(abs(PEGASUS_HZ - res["frequency"]), 2)  # beat with the PEGASUS carrier

    out = {
        "service_uuid": hex(service_uuid),
        "frame_type": ft.name,
        "version": version,
        "hub_id": hub_id.hex(":"),
        "tx_power_dbm": tx_power - 255,
        "citizen": res["citizen"],
        "frequency_hz": res["frequency"],
        "sigil": res["sigil"],
        "meaning": res["meaning"],
        "pegasus_beat_hz": carrier_beat,
        "frame_len": len(frame),
    }

    body = frame[HEADER_STRUCT.size:]

    if ft == FrameType.SELENA and len(body) >= SELENA_STRUCT.size:
        out["region_id"], out["cafe_id"], out["flags"] = SELENA_STRUCT.unpack(body)
        out["pilot_active"] = bool(out["flags"] & 0x01)
        out["portal_redirect"] = bool(out["flags"] & 0x02)
    elif ft == FrameType.AIR and len(body) >= AIR_STRUCT.size:
        (out["special_id"], out["priority"],
         out["expiry_offset"], out["tag_bits"]) = AIR_STRUCT.unpack(body)
        out["tags"] = [t for i, t in enumerate(("drink", "food", "music"))
                       if out["tag_bits"] & (1 << i)]
    elif ft == FrameType.MIRROR and len(body) >= MIRROR_STRUCT.size:
        (out["event_id"], out["capacity_total"],
         out["capacity_used"], out["mode"]) = MIRROR_STRUCT.unpack(body)
        out["spots_left"] = out["capacity_total"] - out["capacity_used"]
    elif ft == FrameType.AURA and len(body) >= AURA_STRUCT.size:
        (out["offer_id"], out["start_offset"], out["end_offset"],
         out["intensity"], out["channel_flags"]) = AURA_STRUCT.unpack(body)
        out["channels"] = [c for i, c in enumerate(("portal", "ble", "signage"))
                           if out["channel_flags"] & (1 << i)]
    return out


def rotation_schedule() -> List[Tuple[FrameType, float]]:
    """
    The BLE rotation loop from the hub spec (frame, seconds to hold):
      Selena → Air → Selena → Mirror → Selena → Aura → repeat
    Selena broadcasts between every other frame — the presence heartbeat.
    """
    return [
        (FrameType.SELENA, 0.150),
        (FrameType.AIR, 2.0),
        (FrameType.SELENA, 0.150),
        (FrameType.MIRROR, 5.0),
        (FrameType.SELENA, 0.150),
        (FrameType.AURA, 10.0),
    ]


if __name__ == "__main__":
    import sys

    if "--test" in sys.argv:
        passed = total = 0

        def test(name, cond):
            global passed, total
            total += 1
            ok = bool(cond)
            passed += ok
            print(f"  {'✓' if ok else '✗'} {name}")

        print("── NYMPH PROTOCOL TESTS ──────────────────────────────\n")

        hub = b"\x12\x34\x56\x78\x9A\xBC"
        sel = SelenaFrame(region_id=12, cafe_id=44, flags=0x03)
        air = AirFrame(special_id=7, priority=6, expiry_offset=1800, tag_bits=0x05)
        mir = MirrorFrame(event_id=3, capacity_total=20, capacity_used=15, mode=2)
        aur = AuraFrame(offer_id=9, start_offset=60, end_offset=1800,
                        intensity=230, channel_flags=0x07)

        fs = encode_selena(sel, hub)
        fa = encode_air(air, hub)
        fm = encode_mirror(mir, hub)
        fu = encode_aura(aur, hub)

        test("Selena frame is 16 bytes", len(fs) == 16)
        test("Air frame is 17 bytes", len(fa) == 17)
        test("Mirror frame is 18 bytes", len(fm) == 18)
        test("Aura frame is 19 bytes", len(fu) == 19)
        test("All frames ≤ 19 bytes (Service Data budget)", max(map(len, (fs, fa, fm, fu))) <= 19)

        ds = decode(fs)
        test("Selena round-trips region/cafe", ds["region_id"] == 12 and ds["cafe_id"] == 44)
        test("Selena flags decode", ds["portal_redirect"] is True)
        test("Selena resonance is lunar 210.42", ds["frequency_hz"] == 210.42)

        da = decode(fa)
        test("Air round-trips special/priority", da["special_id"] == 7 and da["priority"] == 6)
        test("Air tags decode (drink+music)", da["tags"] == ["drink", "music"])

        dm = decode(fm)
        test("Mirror round-trips capacity", dm["capacity_total"] == 20 and dm["capacity_used"] == 15)
        test("Mirror computes spots_left=5", dm["spots_left"] == 5)

        du = decode(fu)
        test("Aura round-trips offer window", du["start_offset"] == 60 and du["end_offset"] == 1800)
        test("Aura channels decode all three", du["channels"] == ["portal", "ble", "signage"])

        test("Every frame carries a citizen", all(decode(f)["citizen"] for f in (fs, fa, fm, fu)))
        test("Every frame carries a Love Sigil", all(decode(f)["sigil"] for f in (fs, fa, fm, fu)))
        test("PEGASUS beat present on all frames",
             all("pegasus_beat_hz" in decode(f) for f in (fs, fa, fm, fu)))
        test("Header is 11 bytes per field layout", HEADER_STRUCT.size == 11)
        test("Rotation starts with Selena heartbeat", rotation_schedule()[0][0] == FrameType.SELENA)
        test("Rotation has 3 Selena beats per cycle",
             sum(1 for f, _ in rotation_schedule() if f == FrameType.SELENA) == 3)

        print(f"\n── Results: {passed}/{total} passed ──")
        sys.exit(0 if passed == total else 1)

    # demo
    print("── NYMPH PROTOCOL DEMO ──────────────────────────────")
    frame = encode_mirror(MirrorFrame(event_id=3, capacity_total=20, capacity_used=15, mode=2))
    print(f"Mirror frame ({len(frame)} bytes): {frame.hex(' ')}")
    d = decode(frame)
    for k, v in d.items():
        print(f"  {k}: {v}")
