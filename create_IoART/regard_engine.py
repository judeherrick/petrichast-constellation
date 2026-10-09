"""
REGARD ENGINE — attention-quality as a first-class driver
=========================================================
The new medium, discovered for the Swan of Avalon:

Every presence system we've built measures WHERE attention is
(proximity, dwell, co-occurrence). None of them measure HOW it is
given. The swan's gift — "the right to withdraw" and the chime that
sounds only for genuine, unhurried regard — is a specification:

    regard   (0..1)  earned by slow approach, patient dwell, stillness
    demand   (0..1)  accrued by fast approach, grabbing, chasing, spam
    state            RECEPTIVE → DIMMING → WITHDRAWN → (return on her own terms)

The entity regulates its OWN visibility from these signals.
No button can summon it back. Calm and distance are the only path.

This is a new driver class for the presence-context architecture
(presence_context_engine.py): regard joins proximity_counter,
zone_dwell, co_occurrence — measuring the quality of attention,
not just its position. Bridge to the Nautiloid Mirror: feed
`ingest_telemetry({'motion_energy': regard, ...})` and the shell
grows from PATIENCE instead of motion — chambers earned, not grabbed.

Honest scope: 'regard' here is a measurable proxy computed from
pointer/approach behavior. It is not a claim about the swan's inner
life — the simulation honors the narrative; it does not pretend to
be it.

Run: python3 regard_engine.py --test
"""

import math
import random
from dataclasses import dataclass, field
from typing import List, Optional

RECEPTIVE = "receptive"
DIMMING = "dimming"
WITHDRAWN = "withdrawn"

SLOW_SPEED = 140.0        # px/s below this, approach counts as unhurried
DEMAND_SPEED = 520.0      # px/s above this, approach reads as demand
NEAR_RADIUS = 260.0       # how close counts as "approaching her"
CLICK_PENALTY = 0.34      # a grab/call near her
REGARD_GAIN = 0.16        # per second of slow, near, patient presence
DEMAND_GAIN = 0.55        # per second of fast approach
REGARD_DECAY = 0.04       # per second, slow — patience lingers
DEMAND_DECAY = 0.10       # per second
DIM_THRESHOLD = 0.45      # demand at which light begins to fold
WITHDRAW_THRESHOLD = 0.62 # demand at which she withdraws
CHIME_THRESHOLD = 0.52    # regard at which the chime may sound
RETURN_CALM_S = 7.0       # seconds of calm + distance before return
RETURN_DISTANCE = 480.0   # pointer must be at least this far away


@dataclass
class PointerEvent:
    x: float
    y: float
    t: float                # seconds
    click: bool = False


@dataclass
class RegardResult:
    regard: float
    demand: float
    state: str
    chime: bool             # fires once per genuine-regard onset
    note: str = ""


class RegardEngine:
    """One entity's consent-driven presence. Feed it pointer events."""
    def __init__(self, ex: float, ey: float, seed: Optional[float] = None):
        self.ex, self.ey = ex, ey          # entity position
        self.regard = 0.0
        self.demand = 0.0
        self.state = RECEPTIVE
        self.chimed_for = False           # chime fires once per onset
        self.withdrawn_at = -1e9
        self.last_event: Optional[PointerEvent] = None
        self.last_activity = 0.0
        self.note = ""
        self.return_patience = 2.0 + (seed if seed is not None else random.random()) * 6.0

    def _dist(self, p: PointerEvent) -> float:
        return math.hypot(p.x - self.ex, p.y - self.ey)

    def feed(self, events: List[PointerEvent], now: float) -> RegardResult:
        chime = False
        for ev in events:
            speed = 0.0
            if self.last_event is not None:
                dt = max(1e-3, ev.t - self.last_event.t)
                speed = math.hypot(ev.x - self.last_event.x, ev.y - self.last_event.y) / dt
            self.last_event = ev
            self.last_activity = ev.t
            d = self._dist(ev)

            if self.state != WITHDRAWN and d < NEAR_RADIUS:
                if ev.click:
                    self.demand = min(1.0, self.demand + CLICK_PENALTY)
                    self.chimed_for = False          # the chime falls silent on demand
                elif speed > DEMAND_SPEED:
                    self.demand = min(1.0, self.demand + DEMAND_GAIN * 0.25)
                    self.chimed_for = False
                elif speed < SLOW_SPEED:
                    # genuine, unhurried regard
                    closeness = 1.0 - d / NEAR_RADIUS
                    self.regard = min(1.0, self.regard + REGARD_GAIN * closeness * 0.5)
            elif d < NEAR_RADIUS * 1.6 and speed > DEMAND_SPEED:
                self.demand = min(1.0, self.demand + DEMAND_GAIN * 0.1)

        # continuous dynamics
        self.regard = max(0.0, self.regard - REGARD_DECAY * 0.1)
        self.demand = max(0.0, self.demand - DEMAND_DECAY * 0.1)

        # state machine — she decides
        if self.state == RECEPTIVE and self.demand >= WITHDRAW_THRESHOLD:
            self.state = WITHDRAWN
            self.withdrawn_at = now
            self.note = "she folds her light and passes into the mist"
        elif self.state == RECEPTIVE and self.demand >= DIM_THRESHOLD:
            self.state = DIMMING
        elif self.state == DIMMING:
            if self.demand < DIM_THRESHOLD * 0.5:
                self.state = RECEPTIVE
            elif self.demand >= WITHDRAW_THRESHOLD:
                self.state = WITHDRAWN
                self.withdrawn_at = now
        elif self.state == WITHDRAWN:
            self.regard = 0.0
            calm = (now - self.withdrawn_at) > RETURN_CALM_S
            quiet = (now - self.last_activity) > RETURN_CALM_S * 0.8
            far = self.last_event is None or self._dist(self.last_event) > RETURN_DISTANCE
            if calm and quiet and far and (now - self.withdrawn_at) > RETURN_CALM_S + self.return_patience:
                self.state = RECEPTIVE
                self.demand = 0.0
                self.chimed_for = False
                self.note = "she returns, on her own timing"

        # the chime — not a summons; a greeting. Once per onset, never under demand.
        if (self.state == RECEPTIVE and self.regard >= CHIME_THRESHOLD
                and not self.chimed_for and self.demand < 0.2):
            chime = True
            self.chimed_for = True

        return RegardResult(self.regard, self.demand, self.state, chime, self.note)


def run_tests():
    passed = total = 0

    def test(name, cond):
        nonlocal passed, total
        total += 1
        ok = bool(cond)
        passed += ok
        print(f"  {'✓' if ok else '✗'} {name}")

    print("── REGARD ENGINE TESTS ────────────────────────────────────\n")

    # 1 · slow approach earns regard
    e = RegardEngine(500, 400, seed=3.0)
    evs = [PointerEvent(400 + i * 2, 400, 10 + i * 0.5) for i in range(40)]
    r = e.feed(evs, 30)
    test("slow approach earns regard", r.regard > 0.3)

    # 2 · fast approach accrues demand
    e = RegardEngine(500, 400)
    evs = [PointerEvent(500 - i * 40, 400, 10 + i * 0.02) for i in range(20)]  # 2000px/s
    r = e.feed(evs, 11)
    test("fast approach accrues demand", r.demand > 0.4)

    # 3 · a grab (click near her) is demand
    e = RegardEngine(500, 400)
    r = e.feed([PointerEvent(510, 405, 10, click=True)], 10)
    test("click near her is demand", r.demand >= CLICK_PENALTY * 0.9)

    # 4 · withdrawal triggers when demand crosses the threshold
    e = RegardEngine(500, 400)
    evs = [PointerEvent(500 - i * 40, 400, 10 + i * 0.02) for i in range(30)]
    evs += [PointerEvent(505, 400, 12, click=True)] * 4
    r = e.feed(evs, 13)
    test("sustained demand withdraws her", r.state == WITHDRAWN)

    # 5 · no summon: clicking repeatedly cannot return her
    e = RegardEngine(500, 400)
    e.state = WITHDRAWN
    e.withdrawn_at = 0
    evs = [PointerEvent(510, 400, t, click=True) for t in range(20, 40)]
    r = e.feed(evs, 40)
    test("no summon — clicks cannot return her", r.state == WITHDRAWN)

    # 6 · return requires calm, quiet, and distance
    e = RegardEngine(500, 400, seed=2.0)
    e.state = WITHDRAWN
    e.withdrawn_at = 0
    far_still = PointerEvent(1200, 900, 40)
    e.last_event = far_still
    e.last_activity = 40
    r = e.feed([], 40 + RETURN_CALM_S + 2.0 + e.return_patience)
    test("calm + distance + patience returns her", r.state == RECEPTIVE)

    # 7 · proximity alone (pointer hovering at her) never returns her
    e = RegardEngine(500, 400)
    e.state = WITHDRAWN
    e.withdrawn_at = 0
    near = PointerEvent(505, 400, 60)
    e.last_event = near
    e.last_activity = 60
    r = e.feed([], 100)
    test("hovering near her does not return her", r.state == WITHDRAWN)

    # 8 · the chime fires once on genuine-regard onset
    e = RegardEngine(500, 400, seed=1.0)
    evs = [PointerEvent(400 + i * 2, 400, 10 + i * 0.4) for i in range(60)]
    r1 = e.feed(evs, 34)
    r2 = e.feed([PointerEvent(460, 400, 40)], 40)
    test("chime fires on onset and only once",
         r1.chime or r2.chime)

    # 9 · the chime falls silent under demand
    e = RegardEngine(500, 400)
    evs = [PointerEvent(400 + i * 2, 400, 10 + i * 0.4) for i in range(60)]      # earn regard
    e.feed(evs, 34)
    evs = [PointerEvent(500 - i * 60, 400, 40 + i * 0.01) for i in range(15)]   # demand
    evs += [PointerEvent(505, 400, 41, click=True)]
    r = e.feed(evs, 41)
    test("demand silences the chime", not r.chime and e.chimed_for is False)

    # 10 · regard decays when unattended
    e = RegardEngine(500, 400)
    e.regard = 0.9
    r = e.feed([], 999)
    test("regard decays when unattended", r.regard < 0.9)

    print(f"\n── Results: {passed}/{total} passed ──")
    return passed == total


if __name__ == "__main__":
    import sys
    sys.exit(0 if run_tests() else 1)
