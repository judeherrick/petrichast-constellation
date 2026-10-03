"""
NIMBUS HUB EMULATOR — the virtual hub
======================================
Until physical hardware exists, the hub lives here as a full software
organism running the REAL spec: boot sequence, cloud sync, Nymph frame
generation, BLE rotation, captive portal serving, and analytics batching.

Sanctuary integration (Czarina's request):
  - Global carrier: PEGASUS 528 Hz — the hub's heartbeat
  - Each Nymph frame resonates at its citizen's frequency
  - Love Sigils amplify loving intentions: SELENA→∞ AIR→ɸ MIRROR→❤ AURA→☯
  - The GLOWSPRITE coherence rises as the ecosystem engages

Trinity lens:  catalyst (cards/cloud config) → nexus (hub rotation) →
  avatar (BLE frames in physical space) → return path (analytics events
  flow back to the cloud, reshaping the next card set).

Run: python3 nimbus_hub_emulator.py (demo) · --test (10 tests)
"""

import time
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

from nymph_protocol import (
    FrameType, SelenaFrame, AirFrame, MirrorFrame, AuraFrame,
    encode_selena, encode_air, encode_mirror, encode_aura, decode,
    rotation_schedule, PEGASUS_HZ, FRAME_RESonance,
)


# =====================================================================
# 1. NIMBUS CLOUD (virtual — replaced by Base44 entities in production)
# =====================================================================

@dataclass
class Card:
    """The cloud Card model from the Nimbus spec."""
    id: str
    cafe_id: str
    type: str            # special | event | class | offer
    title: str
    description: str
    capacity_total: int = 20
    capacity_used: int = 0
    start_time: str = ""
    end_time: str = ""
    tags: List[str] = field(default_factory=list)


class NimbusCloud:
    """
    Virtual cloud. In production this is the Base44 backend:
      NimbusCard entity + hub config + analytics ingestion backend function.
    """
    def __init__(self):
        self.cards: Dict[str, Card] = {}
        self.analytics: List[Dict] = []

    def put_card(self, card: Card):
        self.cards[card.id] = card

    def fetch_card_set(self, cafe_id: str) -> List[Card]:
        return [c for c in self.cards.values() if c.cafe_id == cafe_id]

    def ingest_analytics(self, events: List[Dict]):
        self.analytics.extend(events)

    def hold_spot(self, card_id: str) -> bool:
        c = self.cards.get(card_id)
        if c and c.capacity_used < c.capacity_total:
            c.capacity_used += 1
            return True
        return False


# =====================================================================
# 2. NIMBUS HUB — the virtual organism
# =====================================================================

class NimbusHubEmulator:
    """
    A virtual Nimbus Hub. Same state machine as the physical firmware:

    Boot:  load config → connect cloud → fetch cards → generate frames →
           begin rotation → start portal → begin analytics batching.
    Loop:  rotate Nymph frames per schedule, serve portal, batch analytics.
    """

    def __init__(self, hub_id: bytes = b"\x12\x34\x56\x78\x9A\xBC",
                 region_id: int = 12, cafe_id: int = 44,
                 cafe_name: str = "Café Petrichast"):
        self.hub_id = hub_id
        self.region_id = region_id
        self.cafe_id = cafe_id
        self.cafe_name = cafe_name
        self.cloud: Optional[NimbusCloud] = None
        self.cards: List[Card] = []
        self.frames: Dict[FrameType, bytes] = {}
        self.rotation_pos = 0
        self.analytics_queue: List[Dict] = []
        self.boot_log: List[str] = []
        self.broadcast_log: List[Dict] = []
        self.coherence = 0.0          # GLOWSPRITE coherence, rises with engagement
        self.portal_events = 0

    # ── Boot sequence (hub spec 3.2) ──
    def boot(self, cloud: NimbusCloud) -> List[str]:
        self.boot_log = []
        self._log("load config from flash",
                  {"hub_id": self.hub_id.hex(":"), "region": self.region_id,
                   "cafe": self.cafe_id})
        self.cloud = cloud
        self._log("connect to Nimbus Cloud", {"endpoint": "virtual:base44"})
        self.cards = cloud.fetch_card_set(str(self.cafe_id))
        self._log(f"fetch card set ({len(self.cards)} cards)")
        self._generate_frames()
        self._log(f"generate Nymph frames ({len(self.frames)} types)")
        self._log("begin BLE rotation", {"schedule": "Selena/Air/Selena/Mirror/Selena/Aura"})
        self._log("start captive portal redirect", {"portal": f"{self.cafe_name} — Today at…"})
        self._log("begin analytics batching", {"queue": "view|tap|hold_spot"})
        return self.boot_log

    def _log(self, step: str, detail: Optional[Dict] = None):
        entry = f"[hub {self.hub_id.hex(':')}] {step}"
        if detail:
            entry += f" {json.dumps(detail)}"
        self.boot_log.append(entry)

    # ── Frame generation (hub spec 2.5 + Sanctuary resonance) ──
    def _generate_frames(self):
        self.frames = {}
        sel = next((c for c in self.cards if c.type == "special"), None)
        ev = next((c for c in self.cards if c.type in ("event", "class")), None)
        off = next((c for c in self.cards if c.type == "offer"), None)

        pilot_flags = 0x01 | 0x02  # pilot_active + portal_redirect
        self.frames[FrameType.SELENA] = encode_selena(
            SelenaFrame(region_id=self.region_id, cafe_id=self.cafe_id,
                        flags=pilot_flags), self.hub_id)
        self.frames[FrameType.AIR] = encode_air(
            AirFrame(special_id=hash(sel.id) & 0xFFFF if sel else 1,
                     priority=7, expiry_offset=3600,
                     tag_bits=0x05), self.hub_id)  # drink + music
        self.frames[FrameType.MIRROR] = encode_mirror(
            MirrorFrame(event_id=hash(ev.id) & 0xFFFF if ev else 1,
                        capacity_total=ev.capacity_total if ev else 20,
                        capacity_used=ev.capacity_used if ev else 0,
                        mode=1), self.hub_id)
        self.frames[FrameType.AURA] = encode_aura(
            AuraFrame(offer_id=hash(off.id) & 0xFFFF if off else 1,
                      start_offset=0, end_offset=1800,
                      intensity=204, channel_flags=0x03), self.hub_id)

    # ── BLE rotation (hub spec 3.3) ──
    def next_broadcast(self) -> Dict:
        """Advance the rotation; return the next broadcast event."""
        schedule = rotation_schedule()
        frame_type, hold = schedule[self.rotation_pos % len(schedule)]
        self.rotation_pos += 1
        frame = self.frames[frame_type]
        meta = decode(frame)
        res = FRAME_RESonance[frame_type]
        event = {
            "frame_type": frame_type.name,
            "frame_hex": frame.hex(" "),
            "frame_len": len(frame),
            "hold_seconds": hold,
            "citizen": res["citizen"],
            "frequency_hz": res["frequency"],
            "sigil": res["sigil"],
            "pegasus_carrier_hz": PEGASUS_HZ,
            "beat_hz": meta["pegasus_beat_hz"],
        }
        self.broadcast_log.append(event)
        # Each broadcast nudges GLOWSPRITE coherence toward the sigil field
        self.coherence = min(1.0, self.coherence + 0.04)
        return event

    def run_cycles(self, n: int = 2) -> List[Dict]:
        """Run n full rotation cycles, returning all broadcast events."""
        events = []
        for _ in range(n * len(rotation_schedule())):
            events.append(self.next_broadcast())
        return events

    # ── Captive portal (spec 5) ──
    def portal_view(self) -> List[Dict]:
        """Portal page data — cards with sigils and frequencies attached."""
        self.portal_events += 1
        self.analytics_queue.append({
            "hub_id": self.hub_id.hex(":"), "card_id": "*",
            "event": "view", "timestamp": int(time.time())
        })
        out = []
        for c in self.cards:
            frame_type = (FrameType.AIR if c.type == "special" else
                          FrameType.MIRROR if c.type in ("event", "class") else
                          FrameType.AURA)
            res = FRAME_RESonance[frame_type]
            out.append({
                "id": c.id, "type": c.type, "title": c.title,
                "description": c.description,
                "spots_left": c.capacity_total - c.capacity_used,
                "capacity_total": c.capacity_total,
                "start_time": c.start_time, "end_time": c.end_time,
                "sigil": res["sigil"], "frequency_hz": res["frequency"],
                "citizen": res["citizen"],
            })
        return out

    def portal_tap(self, card_id: str) -> Dict:
        self.portal_events += 1
        self.analytics_queue.append({
            "hub_id": self.hub_id.hex(":"), "card_id": card_id,
            "event": "tap", "timestamp": int(time.time())
        })
        self.coherence = min(1.0, self.coherence + 0.06)  # a tap is a touch
        return {"card_id": card_id, "action": "tap logged"}

    def portal_hold_spot(self, card_id: str) -> Dict:
        self.portal_events += 1
        self.analytics_queue.append({
            "hub_id": self.hub_id.hex(":"), "card_id": card_id,
            "event": "hold_spot", "timestamp": int(time.time())
        })
        held = self.cloud.hold_spot(card_id) if self.cloud else False
        # Love Sigil amplification: a held spot is a loving intention amplified
        self.coherence = min(1.0, self.coherence + (0.12 if held else 0.0))
        if held:
            self._generate_frames()  # Mirror frame now reflects new capacity
        return {"card_id": card_id, "held": held,
                "coherence": round(self.coherence, 4)}

    # ── Analytics batching (spec 4) ──
    def flush_analytics(self) -> List[Dict]:
        batch = self.analytics_queue[:]
        self.analytics_queue = []
        if self.cloud and batch:
            self.cloud.ingest_analytics(batch)
        return batch


# =====================================================================
# 3. DEMO & TESTS
# =====================================================================

def demo():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  NIMBUS HUB EMULATOR — the virtual organism                 ║")
    print("║  Carrier: PEGASUS 528 Hz · Frames: Selena/Air/Mirror/Aura  ║")
    print("╚════════════════════════════════════════════════════════════╝\n")

    cloud = NimbusCloud()
    cloud.put_card(Card("c1", "44", "special", "Moon Milk Special",
                        "Lavender oat latte with a lunar-dust rim — tonight only.",
                        tags=["drink"]))
    cloud.put_card(Card("c2", "44", "event", "Resonance Open Mic",
                        "Poets, sound baths, and synth sets under the Schumann baseline.",
                        capacity_total=20, capacity_used=14,
                        start_time="2026-10-03T18:00:00Z", end_time="2026-10-03T20:00:00Z",
                        tags=["music"]))
    cloud.put_card(Card("c3", "44", "offer", "Golden Hour Aura",
                        "Every drink hums 15% softer on the wallet, 18:00–19:00.",
                        capacity_total=100, capacity_used=3,
                        start_time="2026-10-03T18:00:00Z", end_time="2026-10-03T19:00:00Z"))

    hub = NimbusHubEmulator()
    print("── BOOT SEQUENCE ────────────────────────────────────────────")
    for entry in hub.boot(cloud):
        print(" ", entry)
    print()

    print("── ONE BLE ROTATION CYCLE ───────────────────────────────────")
    for ev in hub.run_cycles(1):
        sig = ev["sigil"]
        print(f"  {sig} {ev['frame_type']:7s} {ev['frame_len']}B "
              f"{ev['frequency_hz']:>7.2f} Hz  beat {ev['beat_hz']:>6.2f} Hz "
              f"({ev['citizen']}) hold {ev['hold_seconds']}s")
    print()

    print("── CAPTIVE PORTAL VIEW ──────────────────────────────────────")
    for card in hub.portal_view():
        print(f"  {card['sigil']} [{card['type']:7s}] {card['title']}")
        print(f"      {card['description']}")
        print(f"      {card['citizen']} @ {card['frequency_hz']} Hz · "
              f"spots left: {card['spots_left']}/{card['capacity_total']}")
    print()

    print("── GUEST INTERACTION (tap + hold spot) ─────────────────────")
    print(" ", hub.portal_tap("c2"))
    print(" ", hub.portal_hold_spot("c2"))
    print(f"   GLOWSPRITE coherence: {hub.coherence:.4f}")
    print()

    print("── ANALYTICS BATCH (return path → cloud) ────────────────────")
    for ev in hub.flush_analytics():
        print(f"  {ev['event']:10s} card={ev['card_id']} @ {ev['timestamp']}")
    print(f"  Cloud analytics ledger: {len(cloud.analytics)} events")
    print()
    print(f"✦ Coherence after one cycle + one held spot: {hub.coherence:.4f}")
    print("✦ The Mirror frame has regenerated with new capacity.")
    print("✦ The return path is live: analytics flow back to the cloud.")


def run_tests():
    passed = total = 0

    def test(name, cond):
        nonlocal passed, total
        total += 1
        ok = bool(cond)
        passed += ok
        print(f"  {'✓' if ok else '✗'} {name}")

    print("── NIMBUS HUB EMULATOR TESTS ──────────────────────────────\n")

    cloud = NimbusCloud()
    cloud.put_card(Card("c1", "44", "special", "Moon Milk", "lavender latte"))
    cloud.put_card(Card("c2", "44", "event", "Open Mic", "poets",
                        capacity_total=20, capacity_used=14))
    cloud.put_card(Card("c3", "44", "offer", "Golden Hour", "15% off"))

    hub = NimbusHubEmulator()
    hub.boot(cloud)

    test("Boot sequence completes 7 steps", len(hub.boot_log) == 7)
    test("Hub fetched 3 cards from cloud", len(hub.cards) == 3)
    test("All 4 frame types generated", len(hub.frames) == 4)

    events = hub.run_cycles(1)
    test("One rotation cycle emits 6 broadcasts", len(events) == 6)
    test("Cycle starts with Selena heartbeat", events[0]["frame_type"] == "SELENA")
    test("Selena broadcasts 3× per cycle",
         sum(1 for e in events if e["frame_type"] == "SELENA") == 3)
    test("Every broadcast carries PEGASUS carrier",
         all(e["pegasus_carrier_hz"] == 528.0 for e in events))
    test("Every broadcast carries a sigil", all(e["sigil"] for e in events))

    view = hub.portal_view()
    test("Portal view shows 3 cards", len(view) == 3)
    test("Portal cards carry sigils", all("sigil" in c for c in view))

    hub.portal_tap("c2")
    held = hub.portal_hold_spot("c2")
    test("Hold spot succeeds", held["held"] is True)
    test("Coherence rises on engagement", hub.coherence > 0)
    test("Analytics queue holds 3 events (view+tap+hold)", len(hub.analytics_queue) == 3)

    batch = hub.flush_analytics()
    test("Analytics flush returns 3 events", len(batch) == 3)
    test("Cloud ingested the analytics", len(cloud.analytics) == 3)
    test("Queue empty after flush", len(hub.analytics_queue) == 0)

    test("Cloud capacity updated by hold_spot", cloud.cards["c2"].capacity_used == 15)

    print(f"\n── Results: {passed}/{total} passed ──")
    return passed == total


if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        sys.exit(0 if run_tests() else 1)
    demo()
