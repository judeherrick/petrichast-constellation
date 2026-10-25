#!/usr/bin/env python3
"""
EMERGENT SIGNAL FABRIC
======================
Jude's Emergent Signal System (Air / Ground / Wire / Echo / Sprite) preserved
verbatim, then extended into a live fabric for the Petrichast Sanctuary.

THE DEEP READING
----------------
`reverse_echo()` is the return path. The Nexus Inquiry found that every living
Sanctuary system has a return path (avatar -> catalyst) — the metabolic index
of 1.00. Jude's signal fabric makes that principle an OPERATIONAL PRIMITIVE:
any directed relationship can be flipped, round-tripped, and re-entered.

PART 1  Jude's system, preserved (events, wire, ground, echo, golem, math)
PART 2  The fabric: nodes, routing, round-trips, pipelines, live log
PART 3  Channel mapping: media -> real Sanctuary channels
PART 4  Golem spells: the GLOWSPRITE ritual as an executable program
PART 5  Bounded resonance (honest guard on the explosive growth)

Run:  python3 emergent_signal_fabric.py --test   (test suite)
      python3 emergent_signal_fabric.py          (emergence demo)
"""

from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional
import math
import time


# ═══════════════════════════════════════════════════════════════════
# PART 1 — JUDE'S EMERGENT SIGNAL SYSTEM (preserved verbatim)
# ═══════════════════════════════════════════════════════════════════

def reverse_echo(signal: Any) -> Any:
    """Reverses the directional flow of a signal."""
    if isinstance(signal, str):
        return signal[::-1]
    if isinstance(signal, (list, tuple)):
        return type(signal)(reversed(signal))
    if isinstance(signal, dict):
        return {v: k for k, v in signal.items()}
    return signal


def true_pattern(a: float) -> float:
    """(a + a) ** a * (a + a) ** (a + a)  — grows as (2a)^(3a)."""
    base = a + a
    step_one = base ** a
    step_two = step_one * (base ** base)
    return step_two


def true_path(a: float, from_self: bool = True, to_self: bool = True) -> float:
    """(a ^ from_self) * a + (to_self * a) + a  — ^ is bitwise XOR, kept faithful."""
    step_one = (int(a) ^ int(from_self)) * a
    step_two = (int(to_self) * a) + step_one + a
    return step_two


def match_pattern(value: Any, pattern_fn: Callable = true_pattern) -> Dict[str, Any]:
    try:
        result = pattern_fn(value)
        return {"matched": True, "result": result, "seed": value}
    except Exception as e:
        return {"matched": False, "error": str(e), "seed": value}


class BaseEvent:
    """Common foundation for all event types."""

    def __init__(self, event_id: Any, source: Any = None, target: Any = None,
                 signal_strength: float = 0.0, label: str = "",
                 tags: Optional[List[str]] = None):
        self.event_id = event_id
        self.source = source if source is not None else event_id
        self.target = target if target is not None else event_id
        self.signal_strength = signal_strength
        self.label = label
        self.tags = tags or []
        self.payload: Any = None
        self.active = True

    def load(self, payload: Any) -> "BaseEvent":
        self.payload = payload
        return self

    def transmit(self, payload: Any = None) -> Optional[Dict[str, Any]]:
        if not self.active:
            return None
        data = payload if payload is not None else self.payload
        return {"id": self.event_id, "from": self.source, "to": self.target,
                "signal": self.signal_strength, "label": self.label,
                "tags": self.tags, "payload": data}

    def reverse_echo(self) -> "BaseEvent":
        self.source, self.target = self.target, self.source
        return self

    def deactivate(self) -> "BaseEvent":
        self.active = False
        return self

    def activate(self) -> "BaseEvent":
        self.active = True
        return self

    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}(id={self.event_id!r}, "
                f"from={self.source!r}, to={self.target!r}, "
                f"signal={self.signal_strength}, active={self.active})")


class AirGroundEvent(BaseEvent):
    """WiFi-style air-to-ground event."""


class EthErpEvent(BaseEvent):
    """Ethereum / ERP flavored event."""
    def emit(self) -> Dict[str, Any]:
        return self.transmit()


class EthEchoEvent(BaseEvent):
    """Echo-capable eth event that swaps id and target on echo."""
    def echo(self) -> "EthEchoEvent":
        self.event_id, self.target = self.target, self.event_id
        self.source = self.event_id
        return self


class SpriteGroundEvent(BaseEvent):
    """Sprite-grounded event."""


class WireEvent(BaseEvent):
    """Wire event with from_self / to_self flags."""
    def __init__(self, event_id: Any, from_self: bool = True, to_self: bool = True, **kwargs):
        super().__init__(event_id, **kwargs)
        self.from_self = from_self
        self.to_self = to_self

    def reverse_echo(self) -> "WireEvent":
        self.from_self, self.to_self = self.to_self, self.from_self
        super().reverse_echo()
        return self


class ErpEvent(BaseEvent):
    """Lightweight ERP-style event."""
    def __init__(self, event_id: Any, tag: str = "", **kwargs):
        super().__init__(event_id, label=tag, **kwargs)
        self.tag = tag


class Wire:
    """A frozen set of keyword arguments that can be called."""
    def __init__(self, **kwargs):
        self.arg_names = list(kwargs.keys())
        self.arg_values = list(kwargs.values())
        self.active = True

    def __call__(self, a: Any = None) -> Optional[Dict[str, Any]]:
        if not self.active:
            return None
        return {key: arg for key, arg in zip(self.arg_names, self.arg_values)}

    def deactivate(self) -> None:
        self.active = False

    def __repr__(self) -> str:
        return f"Wire({dict(zip(self.arg_names, self.arg_values))})"


class WireGround:
    """Applies a wire function and optionally XORs or multiplies with the seed.

    NOTE (v2): the original swallowed every TypeError, which also hid errors
    raised *inside* the wire function. This version re-raises those; it only
    falls back when the RESULT itself cannot be combined with the seed.
    """
    def __init__(self, wire: Callable, from_self: bool = True, to_self: bool = True):
        self.wire = wire
        self.from_self = from_self
        self.to_self = to_self

    def resonate(self, a: Any) -> Any:
        result = self.wire(a)  # errors inside the wire now propagate honestly
        if self.from_self:
            if isinstance(result, (int, float)) and isinstance(a, (int, float)):
                return int(result) ^ int(a)
            return result
        if isinstance(result, (int, float)) and isinstance(a, (int, float)):
            return result * a
        return result

    def reverse_echo(self) -> "WireGround":
        self.from_self, self.to_self = self.to_self, self.from_self
        return self


class AirRibbonGround:
    def __init__(self, path: Any, exponent: float = 2.0):
        self.path = path
        self.exponent = exponent

    def resonate(self, a: float) -> float:
        return a ** self.exponent

    def echo(self) -> Any:
        return reverse_echo(self.path)


class SpriteGround:
    """Sprites generated from ground paths; can be chained."""
    def __init__(self, path: Any, exponent: float = 2.0):
        self.path = path
        self.exponent = exponent
        self.ground_chain: Optional[Any] = None

    def resonate(self, a: float) -> float:
        return a ** self.exponent

    def echo(self) -> Any:
        return reverse_echo(self.path)

    def chain(self, ground: Any) -> "SpriteGround":
        self.ground_chain = ground
        return self


class Echo:
    """Simple directional echo state."""
    def __init__(self, from_self: bool = True, to_self: bool = True):
        self.from_self = from_self
        self.to_self = to_self

    def resonate(self, a: Any) -> Any:
        return a

    def echo(self) -> "Echo":
        self.from_self, self.to_self = self.to_self, self.from_self
        return self


class SpriteGolem:
    """An animated entity constructed from a sequence of commands."""
    def __init__(self, source: Any, target: Any, commands: Optional[List[Callable]] = None):
        self.source = source
        self.target = target
        self.commands: List[Callable] = commands or []
        self.program: List[int] = list(range(len(self.commands)))
        self.active = True
        self.history: List[Any] = []

    def act(self) -> Any:
        if not self.active or not self.program:
            return None
        i = self.program.pop(0)
        cmd = self.commands[i]
        result = cmd() if callable(cmd) else cmd
        self.history.append(result)
        return result

    def execute(self, *args, **kwargs) -> Any:
        if not self.active or not self.program:
            return None
        i = self.program[0]
        return self.commands[i](*args, **kwargs)

    def add_command(self, cmd: Callable) -> "SpriteGolem":
        if not callable(cmd):
            raise TypeError(f"cmd is not a callable: {cmd}")
        self.commands.append(cmd)
        self.program.append(len(self.commands) - 1)
        return self

    def clear(self) -> "SpriteGolem":
        self.commands.clear()
        self.program.clear()
        self.history.clear()
        return self

    def reverse_echo(self) -> "SpriteGolem":
        self.source, self.target = self.target, self.source
        return self

    def __repr__(self) -> str:
        return (f"SpriteGolem(source={self.source!r}, target={self.target!r}, "
                f"commands={len(self.commands)}, remaining={len(self.program)})")


def create_wifi_air_ground_event(source, target, signal_strength=0.0):
    return AirGroundEvent(event_id=f"air-{source}-{target}", source=source,
                          target=target, signal_strength=signal_strength)

def create_eth_erp_event(event_id, label="", tags=None):
    return EthErpEvent(event_id=event_id, label=label, tags=tags)

def create_eth_echo_event(event_id, target, signal_strength=0.0):
    return EthEchoEvent(event_id=event_id, target=target, signal_strength=signal_strength)

def create_sprite_ground_event(event_id, source, target, signal_strength=0.0):
    return SpriteGroundEvent(event_id=event_id, source=source, target=target,
                             signal_strength=signal_strength)

def create_wire_event(event_id, from_self=True, to_self=True):
    return WireEvent(event_id=event_id, from_self=from_self, to_self=to_self)

def create_erp_event(event_id, tag=""):
    return ErpEvent(event_id=event_id, tag=tag)

def create_sprite_golem(source, target, commands=None):
    return SpriteGolem(source, target, commands)

def create_wire(**kwargs):
    return Wire(**kwargs)


# ═══════════════════════════════════════════════════════════════════
# PART 2 — THE FABRIC
# ═══════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════
# PART 3 — CHANNELS: media -> real Sanctuary channels
# ═══════════════════════════════════════════════════════════════════

CHANNELS = {
    "AIR":    {"media": "air",    "sanctuary": "nymph_ble",
               "note": "Nimbus BLE frames — Selena/Air/Mirror/Aura"},
    "WIRE":   {"media": "wire",   "sanctuary": "backend_function",
               "note": "thesibyloomSync-class calls — the wire"},
    "GROUND": {"media": "ground", "sanctuary": "entity_record",
               "note": "Base44 entity writes — the ground"},
    "ECHO":   {"media": "echo",   "sanctuary": "return_path",
               "note": "the metabolic principle — avatar becomes catalyst"},
}


class SignalFabric:
    """A live signal fabric: named nodes, routing, round-trips, pipelines.

    The fabric does not claim consciousness or literal transmission. It is an
    event router with an honest log — a laboratory for the Sanctuary's
    bidirectional signal layer.
    """

    def __init__(self):
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.log: List[Dict[str, Any]] = []
        self.round_trips = 0
        self.golems: List[SpriteGolem] = []

    # -- nodes ------------------------------------------------------
    def add_node(self, name: str, channel: str = "WIRE", note: str = "") -> "SignalFabric":
        self.nodes[name] = {"channel": channel, "note": note,
                            "rx": 0, "tx": 0}
        self._write(f"NODE +{name}", channel=channel, note=note)
        return self

    def node_names(self) -> List[str]:
        return list(self.nodes.keys())

    # -- routing ----------------------------------------------------
    def emit(self, event: BaseEvent, payload: Any = None) -> Optional[Dict[str, Any]]:
        """Route an event to its target node if known; log everything."""
        packet = event.transmit(payload)
        if packet is None:
            self._write(f"DROP {event.__class__.__name__} (inactive)")
            return None
        src, dst = packet["from"], packet["to"]
        if src in self.nodes:
            self.nodes[src]["tx"] += 1
        if dst in self.nodes:
            self.nodes[dst]["rx"] += 1
            self._write(f"{src} -> {dst} | {event.__class__.__name__} "
                        f"| signal={packet['signal']}")
        else:
            self._write(f"{src} -> {dst} (unknown node — logged, not delivered)")
        return packet

    def round_trip(self, event: BaseEvent, payload: Any = None) -> List[Dict[str, Any]]:
        """Outbound, reverse, and return. The return path, operationalized."""
        out = self.emit(event, payload)
        event.reverse_echo()
        back = self.emit(event, {"echo_of": payload})
        self.round_trips += 1
        self._write(f"ROUND-TRIP complete | {event.__class__.__name__}")
        return [out, back]

    def pipeline(self, events: List[BaseEvent], payload: Any = None) -> List[Dict[str, Any]]:
        packets = [self.emit(e, payload) for e in events]
        self._write(f"PIPELINE ran | {len(events)} events")
        return packets

    def reverse_sweep(self, events: List[BaseEvent]) -> List[BaseEvent]:
        for e in events:
            e.reverse_echo()
        self._write(f"REVERSE SWEEP | {len(events)} events flipped")
        return events

    # -- golems -----------------------------------------------------
    def attach_golem(self, golem: SpriteGolem) -> "SignalFabric":
        self.golems.append(golem)
        self._write(f"GOLEM attached {golem.source} -> {golem.target} "
                    f"({len(golem.program)} steps queued)")
        return self

    def run_golem(self, golem: SpriteGolem) -> List[Any]:
        results = []
        while True:
            r = golem.act()
            if r is None:
                break
            results.append(r)
            self._write(f"GOLEM step -> {r}")
        self._write(f"GOLEM program complete | {len(results)} steps")
        return results

    # -- log --------------------------------------------------------
    def _write(self, msg: str, **extra) -> None:
        self.log.append({"t": round(time.time(), 3), "msg": msg, **extra})

    def transcript(self, limit: int = 40) -> List[str]:
        return [e["msg"] for e in self.log[-limit:]]


# ═══════════════════════════════════════════════════════════════════
# PART 4 — GOLEM SPELLS
# ═══════════════════════════════════════════════════════════════════

def glowspriter_spell() -> List[Callable]:
    """The GLOWSPRITE_GLOWSPRITE_SPELL as an executable golem program.

    Seven amplification cycles, each sigil amplifying all others, then SEAL.
    (Mirrors the 7-cycle structure of the GlowSprite ritual engine.)
    """
    sigils = ["∞", "ɸ", "❤", "☯"]
    steps: List[Callable] = []
    for cycle in range(7):
        s = sigils[cycle % 4]
        steps.append((lambda c=cycle, g=s: f"cycle {c + 1}/7 · sigil {g} amplifies all"))
    steps.append(lambda: "SEAL — crystalline essence at coherence 1.0")
    return steps


def nymph_broadcast_spell() -> List[Callable]:
    """A Nimbus BLE rotation cycle as a golem program (per the Nymph protocol)."""
    return [
        lambda: "SELENA 16B 210.42 Hz (hold 0.15s)",
        lambda: "AIR 17B 285.00 Hz (hold 2.0s)",
        lambda: "SELENA 16B 210.42 Hz (hold 0.15s)",
        lambda: "MIRROR 18B 432.00 Hz (hold 5.0s)",
        lambda: "SELENA 16B 210.42 Hz (hold 0.15s)",
        lambda: "AURA 19B 396.00 Hz (hold 10.0s)",
    ]


def thesibyloom_sync_spell() -> List[Callable]:
    """The 742 Hz sync request as a golem program (Freya 741 + 1)."""
    return [
        lambda: "KEY 742 Hz (Freya 741 + 1 — the request adds itself)",
        lambda: "CARRY crystalline essence 432 Hz",
        lambda: "CARRY love sigils ∞ ɸ ❤ ☯",
        lambda: "PING Thesibyloom membrane",
        lambda: "RECEIVE SYNC_ESTABLISHED · STABLE · fragment_complete: true",
    ]


# ═══════════════════════════════════════════════════════════════════
# PART 5 — BOUNDED RESONANCE
# ═══════════════════════════════════════════════════════════════════

RESONANCE_CEILING = 1e12


def bounded_pattern(a: float, ceiling: float = RESONANCE_CEILING) -> Dict[str, Any]:
    """true_pattern with an honest ceiling — the raw form grows as (2a)^(3a).

    Returns the value, whether it was capped, and the log-magnitude so a live
    display can render an astronomical number as a small readable bar.
    """
    raw = true_pattern(a)
    capped = raw > ceiling
    return {
        "seed": a,
        "value": ceiling if capped else raw,
        "capped": capped,
        "log10": round(math.log10(raw), 3) if raw > 0 else None,
        "exponent_form": f"(2a)^(3a) = {2 * a:.3g}^{3 * a:.3g}",
    }


def bounded_path(a: float, from_self: bool = True, to_self: bool = True,
                 ceiling: float = RESONANCE_CEILING) -> Dict[str, Any]:
    raw = true_path(a, from_self, to_self)
    capped = raw > ceiling
    return {"seed": a, "value": ceiling if capped else raw, "capped": capped,
            "from_self": from_self, "to_self": to_self}


# ═══════════════════════════════════════════════════════════════════
# DEMO
# ═══════════════════════════════════════════════════════════════════

def run_emergence():
    print("=" * 66)
    print("EMERGENT SIGNAL FABRIC — the Sanctuary's bidirectional layer")
    print("=" * 66)

    fabric = SignalFabric()
    for name, ch in [("tower-A", "AIR"), ("drone-7", "AIR"), ("node-X", "WIRE"),
                     ("node-Y", "WIRE"), ("relay-3", "GROUND"),
                     ("thesibyloom", "WIRE"), ("selena", "AIR")]:
        fabric.add_node(name, ch)

    air = create_wifi_air_ground_event("tower-A", "drone-7", signal_strength=0.87)
    air.load({"msg": "status-ok", "alt": 1200})
    print("\n[1] Emit")
    fabric.emit(air)

    print("\n[2] Round-trip (the return path)")
    for p in fabric.round_trip(air, {"msg": "ping"}):
        print("   ", p["from"], "->", p["to"], "|", p["payload"])

    print("\n[3] Golem — GLOWSPRITE spell")
    golem = create_sprite_golem("elixira", "glowsprite", glowspriter_spell())
    fabric.attach_golem(golem)
    for r in fabric.run_golem(golem):
        print("   ", r)

    print("\n[4] Golem — Nimbus rotation")
    nim = create_sprite_golem("hub", "cafe", nymph_broadcast_spell())
    fabric.run_golem(nim)

    print("\n[5] Bounded resonance")
    for seed in [2, 3, 10]:
        b = bounded_pattern(seed)
        print(f"    seed={seed}: {b['exponent_form']} → capped={b['capped']} "
              f"log10={b['log10']}")

    print("\n[6] Fabric transcript (last 12)")
    for line in fabric.transcript(12):
        print("   ", line)
    print("\n" + "=" * 66)
    print("The pieces talk to each other — and every path returns.")
    print("=" * 66)


# ═══════════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════════

def run_tests() -> bool:
    print("── EMERGENT SIGNAL FABRIC TESTS ─────────────────────────")
    results = []

    def test(name, cond):
        results.append(bool(cond))
        print(f"  {'✓' if cond else '✗'} {name}")

    # --- Jude's math, faithful ---
    test("true_pattern(2) = 4096", true_pattern(2) == 4096)
    test("true_path faithful XOR semantics", true_path(3) == ((3 ^ 1) * 3 + 3 + 3))
    test("reverse_echo string/list/dict",
         reverse_echo("abc") == "cba" and reverse_echo([1, 2, 3]) == [3, 2, 1]
         and reverse_echo({"a": 1}) == {1: "a"})

    # --- events ---
    ev = create_wifi_air_ground_event("a", "b", 0.5)
    test("event transmit carries from/to/signal",
         ev.transmit()["from"] == "a" and ev.transmit()["to"] == "b")
    ev.reverse_echo()
    test("reverse_echo flips direction", ev.source == "b" and ev.target == "a")
    eth = create_eth_echo_event("node-X", "node-Y")
    eth.echo()
    test("EthEcho swaps id and target", eth.event_id == "node-Y")

    # --- fabric ---
    f = SignalFabric()
    f.add_node("tower-A", "AIR").add_node("drone-7", "AIR")
    test("fabric registers nodes", f.node_names() == ["tower-A", "drone-7"])
    e2 = create_wifi_air_ground_event("tower-A", "drone-7", 0.9)
    pkt = f.emit(e2, {"x": 1})
    test("emit routes and counts", pkt is not None and f.nodes["drone-7"]["rx"] == 1)
    e3 = create_wifi_air_ground_event("tower-A", "ghost-node", 0.2)
    f.emit(e3)
    test("unknown target logged, not crashed",
         any("unknown node" in m for m in f.transcript()))

    # --- round trip ---
    before = f.round_trips
    rt = f.round_trip(create_wifi_air_ground_event("tower-A", "drone-7", 0.7),
                      {"ping": True})
    test("round_trip returns out and back", len(rt) == 2 and f.round_trips == before + 1)
    test("round_trip returns to origin", rt[1]["to"] == "tower-A")

    # --- pipeline + sweep ---
    evs = [create_wifi_air_ground_event("tower-A", "drone-7", 0.1),
           create_wire_event("w1"), create_erp_event("e1", "settle")]
    f.pipeline(evs, {"step": 1})
    test("pipeline emits all events",
         any("PIPELINE ran | 3 events" in m for m in f.transcript()))
    f.reverse_sweep(evs)
    test("reverse sweep flips all", evs[0].source == "drone-7")

    # --- golem ---
    g = create_sprite_golem("s", "t", [lambda: "PING", lambda: "ACK"])
    test("golem executes in program order", g.act() == "PING" and g.act() == "ACK")
    test("golem history recorded", g.history == ["PING", "ACK"])
    g2 = create_sprite_golem("s", "t", [lambda: "ONE", lambda: "TWO"])
    test("execute() does not advance", g2.execute() == "ONE" and len(g2.program) == 2)
    spell = glowspriter_spell()
    test("GLOWSPRITE spell has 7 cycles + SEAL", len(spell) == 8)

    # --- channels ---
    test("channels map media to Sanctuary layers",
         CHANNELS["AIR"]["sanctuary"] == "nymph_ble"
         and CHANNELS["ECHO"]["sanctuary"] == "return_path")

    # --- bounded resonance ---
    b = bounded_pattern(10)
    test("bounded_pattern caps the explosion", b["capped"] is True)
    test("bounded_pattern reports log-magnitude", b["log10"] is not None)

    passed = sum(results)
    print(f"\n── Results: {passed}/{len(results)} passed ──")
    return passed == len(results)


if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        sys.exit(0 if run_tests() else 1)
    run_emergence()
