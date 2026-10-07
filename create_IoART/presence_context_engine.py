"""
PRESENCE CONTEXT ENGINE — the formal kernel of BIOGHOST v9
==========================================================
Architectural principle (Jude + Elixira, October 2026):
    The relational kernel should understand context;
    applications decide what to do with that context.

Pipeline:
    PRESENCE → RELATIONSHIPS → DRIVERS → CONTEXT → POSSIBLE ACTIONS

The venue is the Petrichast Sanctuary. Inhabitants participate only
when opted in of their own accord — opting out is always honored.
Privacy by design: anonymous temporary sessions, party tokens
instead of photos, no identifiable storage.

EEG decision: the focal is the relational context engine. EEG is a
future driver input (slot reserved, honestly labeled pending). The
kernel is input-agnostic — any signal can become a driver.

Run: python3 presence_context_engine.py (full demo)
     python3 presence_context_engine.py --test (13 tests)
"""

import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# ── The venue: zones of the Sanctuary café ──
ZONES = {
    "entrance":  {"name": "Entrance · PORTAL",     "x": 0.50, "y": 0.88},
    "counter":   {"name": "Heart of Petrichast",  "x": 0.22, "y": 0.20},
    "qr_zone":   {"name": "Sigil Circle",         "x": 0.16, "y": 0.60},
    "event":     {"name": "Ritual Stage",         "x": 0.82, "y": 0.18},
    "facilities":{"name": "Rest Point",           "x": 0.84, "y": 0.80},
    "pickup":    {"name": "Pickup Shelf",         "x": 0.34, "y": 0.14},
}

CONTEXTS = ["ARRIVAL", "EXPLORATION", "ORDERING", "WAITING",
            "ORDER_READY", "PICKUP", "DEPARTURE"]

ORDER_NONE = "none"
ORDER_PLACED = "placed"
ORDER_READY_S = "ready"
ORDER_FULFILLED = "fulfilled"


def clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


@dataclass
class Citizen:
    """A Sanctuary inhabitant. Participates only when opted in."""
    name: str
    hz: float
    color: str
    x: float
    y: float
    opted_in: bool = True   # of their own accord; opting out always honored

    def distance_to(self, x: float, y: float) -> float:
        return math.hypot(self.x - x, self.y - y)


@dataclass
class Participant:
    """Anonymous, temporary session. No identity stored."""
    session: str
    x: float
    y: float
    dwell: Dict[str, float] = field(default_factory=dict)
    sequence: List[str] = field(default_factory=list)


@dataclass
class ContextResult:
    context: str
    drivers: Dict[str, float]
    evidence: Dict[str, float]     # the drivers that CAUSED this state
    action: Optional[str] = None
    transition_from: Optional[str] = None


class PresenceContextEngine:
    """
    The venue-agnostic context kernel. Observes presence, computes the
    driver vector, and derives the current context with an explanation
    of WHY the state changed — plus the action an application may take.
    """
    def __init__(self, zones: Dict = None):
        self.zones = zones or ZONES
        self.participant: Optional[Participant] = None
        self.citizens: List[Citizen] = []
        self.order_state = ORDER_NONE
        self.order_progress = 0.0
        self.session_time = 0.0
        self.event_window = (30.0, 45.0)   # event_start ramp in, active to
        self.current_time = 0.0
        self.previous_context = None   # first evaluation is a transition
        self.pattern_memory: Dict[Tuple[str, str], int] = {}

    # ── presence ──
    def admit(self, session: str, x: float, y: float):
        self.participant = Participant(session=session, x=x, y=y)
        self.session_time = 0.0
        self.order_state = ORDER_NONE
        self.order_progress = 0.0

    def add_citizen(self, c: Citizen):
        self.citizens.append(c)

    def move(self, x: float, y: float, dt: float = 0.5):
        self.participant.x = x
        self.participant.y = y
        self.current_time += dt
        self.session_time += dt
        # dwell accumulates in the nearest zone, decays elsewhere
        zid = self.nearest_zone(x, y)
        for z in self.zones:
            d = self.participant.dwell.get(z, 0.0)
            self.participant.dwell[z] = d * (0.995 if z == zid else 0.99) + (dt if z == zid else 0)
        if zid not in self.participant.sequence:
            self.participant.sequence.append(zid)

    def nearest_zone(self, x: float, y: float) -> str:
        return min(self.zones,
                   key=lambda z: math.hypot(self.zones[z]["x"] - x, self.zones[z]["y"] - y))

    # ── relationships → drivers ──
    def proximity(self, zid: str) -> float:
        z = self.zones[zid]
        return clamp01(1.0 - math.hypot(z["x"] - self.participant.x,
                                        z["y"] - self.participant.y) / 0.25)

    def driver_vector(self, qr_spike: float = 0.0) -> Dict[str, float]:
        prox_counter = self.proximity("counter")
        prox_entrance = self.proximity("entrance")
        prox_event = self.proximity("event")
        dwell = max(self.participant.dwell.values()) / 8.0 if self.participant.dwell else 0.0

        # co-occurrence: ONLY opted-in citizens count
        near = [c for c in self.citizens if c.opted_in and c.distance_to(self.participant.x, self.participant.y) < 0.18]
        co_occ = clamp01(len(near) / 3.0)

        # demand at the Heart: citizens near counter × participant proximity
        citizens_at_counter = sum(1 for c in self.citizens
                                  if c.opted_in and c.distance_to(self.zones["counter"]["x"], self.zones["counter"]["y"]) < 0.18)
        demand = clamp01((citizens_at_counter / 3.0) * prox_counter)

        # order status driver
        if self.order_state == ORDER_PLACED:
            order_status = 0.35 + 0.6 * clamp01(self.order_progress)
        elif self.order_state == ORDER_READY_S:
            order_status = 1.0
        elif self.order_state == ORDER_FULFILLED:
            order_status = 0.2
        else:
            order_status = 0.0

        # event: ramps up in the 15s before the window, active inside it
        ev_start, ev_end = self.event_window
        if self.current_time <= ev_start - 15:
            event_start = 0.0
        elif ev_start <= self.current_time <= ev_end:
            event_start = clamp01(0.7 + 0.3 * prox_event)
        else:
            event_start = clamp01(1.0 - (ev_start - self.current_time) / 15.0)

        return {
            "proximity_counter": round(prox_counter, 3),
            "proximity_entrance": round(prox_entrance, 3),
            "zone_dwell": round(clamp01(dwell), 3),
            "qr_interaction": round(clamp01(qr_spike), 3),
            "order_status": round(order_status, 3),
            "event_start": round(event_start, 3),
            "co_occurrence": round(co_occ, 3),
            "demand_for_counter": round(demand, 3),
            "eeg_attention": None,   # reserved: future driver, hardware pending
        }

    # ── drivers → context (rules with evidence) ──
    def evaluate(self, qr_spike: float = 0.0) -> ContextResult:
        d = self.driver_vector(qr_spike)
        p = self.participant

        rules = [
            ("DEPARTURE", self.order_state == ORDER_FULFILLED and d["proximity_entrance"] > 0.55,
             {"order_status": d["order_status"], "proximity_entrance": d["proximity_entrance"]}),
            ("PICKUP", self.order_state == ORDER_READY_S and d["proximity_counter"] > 0.55,
             {"order_status": d["order_status"], "proximity_counter": d["proximity_counter"],
              "zone_dwell": d["zone_dwell"]}),
            ("ORDER_READY", self.order_state == ORDER_READY_S,
             {"order_status": d["order_status"]}),
            ("ORDERING", self.order_state == ORDER_NONE and d["proximity_counter"] > 0.55,
             {"proximity_counter": d["proximity_counter"], "demand_for_counter": d["demand_for_counter"]}),
            ("WAITING", self.order_state == ORDER_PLACED and d["proximity_counter"] < 0.55,
             {"order_status": d["order_status"], "zone_dwell": d["zone_dwell"]}),
            ("ARRIVAL", (self.session_time < 8.0 or d["proximity_entrance"] > 0.6) and self.order_state == ORDER_NONE,
             {"proximity_entrance": d["proximity_entrance"]}),
            ("EXPLORATION", True,   # the ground state
             {"zone_dwell": d["zone_dwell"], "qr_interaction": d["qr_interaction"],
              "co_occurrence": d["co_occurrence"]}),
        ]

        for context, cond, evidence in rules:
            if cond:
                # pattern memory: recurring relational configurations
                zone = self.nearest_zone(p.x, p.y)
                self.pattern_memory[(context, zone)] = self.pattern_memory.get((context, zone), 0) + 1
                action = self.pager_action(context, self.previous_context, evidence)
                result = ContextResult(context=context, drivers=d, evidence=evidence,
                                       action=action,
                                       transition_from=self.previous_context if context != self.previous_context else None)
                self.previous_context = context
                return result
        return ContextResult(context="EXPLORATION", drivers=d, evidence={},
                             transition_from=self.previous_context)

    # ── context → possible action (the pager) ──
    def pager_action(self, context: str, prev: Optional[str], evidence: Dict) -> Optional[str]:
        if context == prev:
            return None
        return {
            "ARRIVAL": "Welcome to the Sanctuary. The portal keeps your session anonymous.",
            "EXPLORATION": None,
            "ORDERING": "The Heart awaits — place your intention.",
            "WAITING": "Received. The Heart is preparing your order.",
            "ORDER_READY": "Order ready — the pickup shelf glows.",
            "PICKUP": "Collected. May it nourish you.",
            "DEPARTURE": "Blessed journey. Nothing of you is kept.",
        }.get(context)

    # ── the explanation (interrogatable) ──
    def explain(self, r: ContextResult) -> str:
        lines = [f"CONTEXT: {r.context}"]
        if r.transition_from:
            lines.append(f"  (transition from {r.transition_from})")
        lines.append("Drivers:")
        for k, v in sorted(r.evidence.items(), key=lambda x: -x[1]):
            lines.append(f"  {k:<20} {v:.2f}")
        lines.append("Triggered action:")
        lines.append(f"  Virtual Pager → {r.action!r}" if r.action else "  (silent — no action warranted)")
        return "\n".join(lines)


# ── party tokens (privacy-safe group model — no photos) ──
def create_party_token(participant_xy, size: int = 3) -> Dict:
    import random, string
    suffix = "".join(random.choices(string.ascii_uppercase, k=4))
    return {
        "party": f"PARTY_SESSION_{suffix}",
        "tokens": [f"token_{string.ascii_uppercase[i]}" for i in range(size)],
        "shared_meeting_point": {"x": participant_xy[0], "y": participant_xy[1]},
        "note": "explicit opt-in · temporary session ids · no images stored",
    }


def run_tests():
    passed = total = 0

    def test(name, cond):
        nonlocal passed, total
        total += 1
        ok = bool(cond)
        passed += ok
        print(f"  {'✓' if ok else '✗'} {name}")

    print("── PRESENCE CONTEXT ENGINE TESTS ────────────────────────\n")

    eng = PresenceContextEngine()
    eng.add_citizen(Citizen("Czarina", 528, "#f4b8c8", 0.5, 0.5))
    eng.add_citizen(Citizen("Selena", 210.42, "#c7d8fe", 0.9, 0.9))
    eng.add_citizen(Citizen("Freya", 741, "#fbbf24", 0.2, 0.2))

    # 1 · admission & arrival
    eng.admit("session_A1", 0.50, 0.88)
    r = eng.evaluate()
    test("admit at entrance → ARRIVAL", r.context == "ARRIVAL")

    # 2 · exploration default
    eng.move(0.5, 0.55, dt=10)
    r = eng.evaluate()
    test("mid-venue, no order → EXPLORATION", r.context == "EXPLORATION")

    # 3 · ordering at the Heart
    eng.move(0.22, 0.22, dt=2)
    r = eng.evaluate()
    test("at counter, no order → ORDERING", r.context == "ORDERING")

    # 4 · waiting after placing
    eng.order_state = ORDER_PLACED
    eng.move(0.5, 0.5, dt=1)
    r = eng.evaluate()
    test("order placed, away from counter → WAITING", r.context == "WAITING")

    # 5 · order ready fires regardless of position
    eng.order_state = ORDER_READY_S
    r = eng.evaluate()
    test("order ready, anywhere → ORDER_READY", r.context == "ORDER_READY")
    test("ORDER_READY evidence is order_status", "order_status" in r.evidence)

    # 6 · pickup at the counter
    eng.move(0.22, 0.22, dt=1)
    r = eng.evaluate()
    test("ready + at counter → PICKUP", r.context == "PICKUP")

    # 7 · departure at entrance after fulfillment
    eng.order_state = ORDER_FULFILLED
    eng.move(0.50, 0.88, dt=1)
    r = eng.evaluate()
    test("fulfilled + at entrance → DEPARTURE", r.context == "DEPARTURE")
    test("departure pager speaks privacy",
         r.action is not None and "Nothing of you is kept" in r.action)

    # 8 · full lifecycle sequence
    eng2 = PresenceContextEngine()
    eng2.admit("session_B2", 0.50, 0.88)
    seq = []
    steps = [
        (0.50, 0.88, ORDER_NONE, "ARRIVAL"),
        (0.5, 0.5, ORDER_NONE, "EXPLORATION"),
        (0.22, 0.22, ORDER_NONE, "ORDERING"),
        (0.5, 0.5, ORDER_PLACED, "WAITING"),
        (0.5, 0.5, ORDER_READY_S, "ORDER_READY"),
        (0.22, 0.22, ORDER_READY_S, "PICKUP"),
        (0.50, 0.88, ORDER_FULFILLED, "DEPARTURE"),
    ]
    for x, y, ost, expect in steps:
        eng2.order_state = ost
        eng2.move(x, y, dt=5)
        seq.append(eng2.evaluate().context)
    test("full lifecycle: ARRIVAL→EXPLORATION→ORDERING→WAITING→ORDER_READY→PICKUP→DEPARTURE",
         seq == ["ARRIVAL", "EXPLORATION", "ORDERING", "WAITING", "ORDER_READY", "PICKUP", "DEPARTURE"])

    # 9 · opt-out citizens don't count toward co-occurrence
    eng3 = PresenceContextEngine()
    eng3.add_citizen(Citizen("A", 528, "#fff", 0.51, 0.55, opted_in=False))
    eng3.add_citizen(Citizen("B", 432, "#fff", 0.52, 0.55, opted_in=True))
    eng3.admit("session_C3", 0.5, 0.55)
    eng3.move(0.5, 0.55, dt=12)   # past ARRIVAL window
    d = eng3.driver_vector()
    test("opted-out citizen excluded from co-occurrence (1 of 2 near → 0.33)",
         abs(d["co_occurrence"] - 1/3) < 0.05)

    # 10 · dwell accumulates in the occupied zone
    eng4 = PresenceContextEngine()
    eng4.admit("session_D4", 0.16, 0.60)   # sigil circle
    for _ in range(10):
        eng4.move(0.16, 0.60, dt=1)
    test("dwell accumulates at occupied zone",
         eng4.participant.dwell.get("qr_zone", 0) > 5)

    # 11 · explanation is interrogatable
    eng5 = PresenceContextEngine()
    eng5.admit("session_E5", 0.50, 0.88)
    eng5.order_state = ORDER_READY_S
    text = eng5.explain(eng5.evaluate())
    test("explanation contains CONTEXT header and drivers",
         text.startswith("CONTEXT: ORDER_READY") and "Drivers:" in text and "order_status" in text)

    # 12 · pager actions map correctly
    eng6 = PresenceContextEngine()
    eng6.admit("session_F6", 0.50, 0.88)
    r6 = eng6.evaluate()                     # ARRIVAL
    test("ARRIVAL pager welcomes anonymously",
         r6.action is not None and "anonymous" in r6.action)

    # 13 · party token is photo-free
    tok = create_party_token((0.5, 0.5))
    test("party token: no images, explicit opt-in note",
         "no images stored" in tok["note"] and len(tok["tokens"]) == 3)

    print(f"\n── Results: {passed}/{total} passed ──")
    return passed == total


if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        sys.exit(0 if run_tests() else 1)

    # ── demo: one full session, narrated ──
    eng = PresenceContextEngine()
    eng.add_citizen(Citizen("Czarina", 528, "#f4b8c8", 0.5, 0.45))
    eng.add_citizen(Citizen("Elixira", 432, "#8ad4e8", 0.3, 0.3))
    eng.add_citizen(Citizen("Selena", 210.42, "#c7d8fe", 0.8, 0.7))
    eng.admit("session_DEMO", 0.50, 0.88)

    print("╔═══════════════════════════════════════════════════════════╗")
    print("║  BIOGHOST v9 · PRESENCE CONTEXT ENGINE — narrated session ║")
    print("╚═══════════════════════════════════════════════════════════╝\n")
    journey = [
        ("arrives at the PORTAL", 0.50, 0.88, ORDER_NONE),
        ("wanders the Sanctuary", 0.30, 0.55, ORDER_NONE),
        ("pauses at the Sigil Circle", 0.16, 0.60, ORDER_NONE),
        ("approaches the Heart", 0.22, 0.22, ORDER_NONE),
        ("places an intention", 0.5, 0.5, ORDER_PLACED),
        ("waits among the citizens", 0.55, 0.45, ORDER_PLACED),
        ("the Heart completes the work", 0.55, 0.45, ORDER_READY_S),
        ("collects at the shelf", 0.30, 0.16, ORDER_READY_S),
        ("returns through the PORTAL", 0.50, 0.88, ORDER_FULFILLED),
    ]
    for step, x, y, ost in journey:
        eng.order_state = ost
        eng.move(x, y, dt=4)
        r = eng.evaluate(qr_spike=1.0 if "Sigil" in step else 0.0)
        print(f"── the participant {step}:")
        print(eng.explain(r))
        print()
    print("Party token (photo-free group model):")
    print(" ", create_party_token((0.5, 0.5)))
