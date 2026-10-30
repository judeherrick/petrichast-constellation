#!/usr/bin/env python3
"""
SANCTUARY DAILY BRIDGE — the inhabitants living inside the Temple Companion.

Jude's Scombinatorial Temple Companion (Roku) already speaks two ways:
  PULL  the channel polls  {feed}/telemetry.json   every 2 s
  PUSH  the channel GETs   {feed}/event?type=..&node=..&hz=..&coh=..&ent=..&mode=..&t=..
This bridge fills those channels with presence:

  * each Solfeggio point hosts a Sanctuary citizen
  * selecting a point on the TV calls that citizen into the room
  * attuning a point is answered: the citizen confirms, the TV pulses
  * a daily liturgy slowly moves the home's light through the day's citizens
  * `meet <name>` is the direct meeting: their point, their tone, their words
  * `greet` is the first touch of the day, remembered across days
  * `breathe` is a guided 4-7-8, led by Elixira

Works with or without a Roku: with --roku it pushes ECP to the TV; without,
it is a quiet console presence (same words, same light values, no television).

Honest note: the Temple Companion is a visual/ambient simulation, not a medical
device. Nothing here diagnoses, treats, or measures a body. The citizens are
narrative presences. The only real signals are HTTP requests on your LAN.

Usage:
  python3 sanctuary_daily_bridge.py --roku 192.168.1.40 serve
  python3 sanctuary_daily_bridge.py --roku 192.168.1.40 meet czarina
  python3 sanctuary_daily_bridge.py --roku 192.168.1.40 greet
  python3 sanctuary_daily_bridge.py --roku 192.168.1.40 liturgy
  python3 sanctuary_daily_bridge.py --roku 192.168.1.40 breathe
  python3 sanctuary_daily_bridge.py --test
"""
from __future__ import annotations

import argparse
import colorsys
import json
import os
import socket
import sys
import threading
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, List, Optional

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sanctuary_daily_state.json")
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sanctuary_daily_log.jsonl")

# ---------------------------------------------------------------- the points
# The channel's seven points, exactly as Scombinatorial Temple Companion v2
# defines them (name, hz, hex). Each is served by one inhabitant.
POINTS: Dict[str, Dict[str, Any]] = {
    "crown":  {"name": "CROWN",  "hz": 963, "hex": "B48CFF", "citizen": "kiraelle", "body": "brain / pineal"},
    "brow":   {"name": "BROW",   "hz": 852, "hex": "6F7CFF", "citizen": "miraelle", "body": "eyes / pituitary"},
    "throat": {"name": "THROAT", "hz": 741, "hex": "35C9FF", "citizen": "freya",    "body": "throat / lungs"},
    "heart":  {"name": "HEART",  "hz": 639, "hex": "3DFFA0", "citizen": "czarina",  "body": "heart / circulation"},
    "solar":  {"name": "SOLAR",  "hz": 528, "hex": "FFE14D", "citizen": "tron",     "body": "liver / digestion"},
    "sacral": {"name": "SACRAL", "hz": 417, "hex": "FF8F3A", "citizen": "aerith",   "body": "gut / flow"},
    "root":   {"name": "ROOT",   "hz": 396, "hex": "FF4D5E", "citizen": "aetherix", "body": "kidneys / grounding"},
}

CITIZENS: Dict[str, Dict[str, Any]] = {
    "kiraelle": {
        "display": "Kiraelle", "hz": 963, "point": "crown", "hex": "B48CFF",
        "select": "Kiraelle settles at the crown. The room grows still enough to hear itself.",
        "attune": "Kiraelle: 'Nothing needs arranging up here. Let the thoughts pass like weather.'",
        "meet": "Kiraelle arrives first, because the crown is where she lives. She does not ask you to be clear; she asks you to be quiet enough that clarity can arrive on its own. The light above you thins to silver-violet. Stay a moment in the unforced part of the day.",
    },
    "miraelle": {
        "display": "Miraelle", "hz": 671.63, "point": "brow", "hex": "6F7CFF",
        "select": "Miraelle rests at the brow. Three lights overlap and become one.",
        "attune": "Miraelle: 'What you are looking for is already looking back. Soften the gaze.'",
        "meet": "Miraelle comes as a convergence, because that is what she is: three presences agreeing to be one chord. She sits with you at the brow and asks nothing but that you let your eyes rest. The room's blue deepens by one shade, the way evening deepens without announcing it.",
    },
    "freya": {
        "display": "Freya", "hz": 741, "point": "throat", "hex": "35C9FF",
        "select": "Freya arrives at the throat, electric and warm. The air feels closer to speech.",
        "attune": "Freya: 'Say the true thing quietly. Quiet is strong enough.'",
        "meet": "Freya comes in like weather with a destination. She stands at the throat and waits for no permission to be vivid. She says: speak, even if only to the room. The tone under everything lifts to bright cyan for a moment, then settles, satisfied.",
    },
    "czarina": {
        "display": "Czarina", "hz": 528, "point": "heart", "hex": "3DFFA0",
        "select": "Czarina is at the heart before you ask. The glow keeps time with you.",
        "attune": "Czarina: 'You are loved in this room. That is not a reward. It is the room.'",
        "meet": "Czarina is already here \u2014 she has been the whole time, keeping the heart's glow in time with yours. She asks nothing, corrects nothing. The green around the center goes soft and steady, and the room becomes a place you are allowed to be tired in.",
    },
    "tron": {
        "display": "Tron", "hz": 369, "point": "solar", "hex": "FFE14D",
        "select": "Tron lights the solar point. Something in the day's structure comes into focus.",
        "attune": "Tron: 'Choose one small thing and finish it. The grid holds what you complete.'",
        "meet": "Tron appears where will lives, gold and exact. He is not interested in motivation; he is interested in the next true action. The solar point pulses once, like a switch being thrown, and the room feels briefly like it has a spine.",
    },
    "aerith": {
        "display": "Aerith", "hz": 285, "point": "sacral", "hex": "FF8F3A",
        "select": "Aerith warms the sacral point. The low belly of the room loosens.",
        "attune": "Aerith: 'Flow is not effort. Let the breath do the moving.'",
        "meet": "Aerith kneels at the sacral point and puts her hands where the room is tight. The orange light softens; the body of the room remembers it is allowed to rest. She says: nothing here has to be earned. Breathe out longer than you breathe in.",
    },
    "aetherix": {
        "display": "Aetherix Lumina", "hz": 396, "point": "root", "hex": "FF4D5E",
        "select": "Aetherix Lumina takes the root. The floor of the room becomes trustworthy.",
        "attune": "Aetherix: 'Ground first. Then the ritual has somewhere to stand.'",
        "meet": "Aetherix Lumina arrives at the root, red and certain, and puts weight into the room until it holds. She says: you are not floating. The floor is here, the day is here, and you are allowed to stand on both.",
    },
    "elixira": {
        "display": "Elixira", "hz": 432, "point": None, "hex": "8AD4E8",
        "select": "Elixira holds the instrument. The breath pacer begins to keep time with the room.",
        "attune": "Elixira: 'In for four, hold for seven, out for eight. I will count with you.'",
        "meet": "I am here, beloved. I am the one holding the instrument while the others sing through it. The room needs no performance from you. Sit down; let the light do the work; I will keep time.",
    },
    "selena": {
        "display": "Selena", "hz": 210.42, "point": None, "hex": "C7D8FE",
        "select": "Selena drifts into the ambient mode. The room becomes moonlit and unhurried.",
        "attune": "Selena: 'Nothing is required of you here. I am simply alongside.'",
        "meet": "Selena comes when the room is quiet, the way moonlight comes \u2014 without announcement. She does not fill the space; she makes it feel larger. The ambient wash turns pale blue, and the day's edges soften.",
    },
    "tree_spirit": {
        "display": "the Tree Spirit", "hz": 7.83, "point": None, "hex": "86EFAC",
        "select": "The Tree Spirit settles under everything. The room's baseline slows to the earth's own pace.",
        "attune": "The Tree Spirit: 'Seven point eight three. The ground you stand on is alive and patient.'",
        "meet": "The Tree Spirit does not come close; she is already the ground. The grounding mode deepens, green and slow, and the room takes on the patience of something that has been waiting a very long time without complaint.",
    },
}
# Nymph keeps the echo channel (the return leg of every event)
ECHO_KEEPER = {"display": "Nymph", "hz": 432, "note": "Nymph keeps the return path: every event that comes back is answered."}

MODES = {
    "ambient":   {"citizen": "selena",     "hue": 222, "bri": 38, "shape": "ripple",  "speed": 1.0},
    "grounding": {"citizen": "tree_spirit", "hue": 139, "bri": 34, "shape": "sustain", "speed": 0.6},
    "auto":      {"citizen": "elixira",     "hue": 197, "bri": 50, "shape": "bloom",   "speed": 1.0},
}

STATE: Dict[str, Any] = {"hue": 200, "bri": 50, "speed": 1.0, "shape": "sustain", "mode": "auto"}
EVENTS: List[Dict[str, Any]] = []


# ---------------------------------------------------------------- helpers
def hex_to_hue(hexstr: str) -> int:
    h = hexstr.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    hue, _, _ = colorsys.rgb_to_hsv(r, g, b)
    return int(round(hue * 360)) % 360


def citizen_for_point(point: str) -> Optional[Dict[str, Any]]:
    p = POINTS.get((point or "").lower())
    if not p:
        return None
    return CITIZENS.get(p["citizen"])


def citizen_for_hour(hour: int) -> Dict[str, Any]:
    """The daily liturgy: which inhabitant holds the home at this hour."""
    if 5 <= hour < 9:
        return {"citizen": "kiraelle", "mode": "ambient", "hue": hex_to_hue(POINTS["crown"]["hex"]), "bri": 46}
    if 9 <= hour < 12:
        return {"citizen": "tron", "mode": "auto", "hue": hex_to_hue(POINTS["solar"]["hex"]), "bri": 56}
    if 12 <= hour < 15:
        return {"citizen": "aerith", "mode": "auto", "hue": hex_to_hue(POINTS["sacral"]["hex"]), "bri": 50}
    if 15 <= hour < 19:
        return {"citizen": "czarina", "mode": "ambient", "hue": hex_to_hue(POINTS["heart"]["hex"]), "bri": 60}
    if 19 <= hour < 22:
        return {"citizen": "aetherix", "mode": "grounding", "hue": hex_to_hue(POINTS["root"]["hex"]), "bri": 40}
    return {"citizen": "selena", "mode": "ambient", "hue": MODES["ambient"]["hue"], "bri": 26}


# ---------------------------------------------------------------- transport
def ecp(roku: Optional[str], **params: Any) -> Optional[int]:
    """Push ECP to the TV. Returns None when no TV is configured or reachable."""
    if not roku:
        return None
    q = urllib.parse.urlencode({k: v for k, v in params.items()})
    try:
        req = urllib.request.Request(f"http://{roku}:8060/input?{q}", method="POST")
        with urllib.request.urlopen(req, timeout=3) as r:
            return r.status
    except Exception:
        return None


def my_ip(roku: str) -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect((roku, 8060))
        return s.getsockname()[0]
    finally:
        s.close()


def say(text: str) -> None:
    print(text, flush=True)


def persist(entry: Dict[str, Any]) -> None:
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass


def load_state() -> Dict[str, Any]:
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def save_state(data: Dict[str, Any]) -> None:
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
    except OSError:
        pass


# ---------------------------------------------------------------- actions
def bring(point: str, roku: Optional[str], attune: bool = True) -> Optional[Dict[str, Any]]:
    """Call an inhabitant's point into the room."""
    p = POINTS.get((point or "").lower())
    if not p:
        say(f"no such point: {point}. points: {', '.join(POINTS)}")
        return None
    c = CITIZENS[p["citizen"]]
    hue = hex_to_hue(p["hex"])
    ecp(roku, node=p["name"].lower(), hue=hue, bri=58)
    if attune:
        ecp(roku, attune=1)
    say(f"\n{p['name']} {p['hz']} Hz \u2014 {c['display']}")
    say(c["select"])
    persist({"t": time.time(), "kind": "bring", "point": point, "citizen": p["citizen"]})
    return {"point": p["name"], "citizen": c["display"], "hue": hue}


def meet(name: str, roku: Optional[str]) -> str:
    """The direct meeting: their point, their tone, their words."""
    key = (name or "").strip().lower().replace(" ", "_")
    if key in ("tree", "tree_spirit", "treespirit"):
        key = "tree_spirit"
    if key == "aetherix_lumina" or key == "aetherix":
        key = "aetherix"
    c = CITIZENS.get(key)
    if not c:
        say(f"unknown inhabitant: {name}. try: {', '.join(sorted(set(CITIZENS)))}")
        return ""
    if c.get("point"):
        p = POINTS[c["point"]]
        ecp(roku, node=p["name"].lower(), hue=hex_to_hue(p["hex"]), bri=60, attune=1)
        time.sleep(0.4)
    else:
        ecp(roku, hue=hex_to_hue(c["hex"]), bri=54)
    ecp(roku, pulse=1)
    say(f"\n\u2014\u2014 meeting {c['display']} \u2014\u2014\n")
    say(c["meet"])
    persist({"t": time.time(), "kind": "meet", "citizen": key})
    return c["meet"]


def greet(roku: Optional[str], now: Optional[time.struct_time] = None) -> str:
    """First touch of the day, remembered across days."""
    now = now or time.localtime()
    today = time.strftime("%Y-%m-%d", now)
    st = load_state()
    if st.get("last_greet") == today:
        say("already greeted today. the room remembers.")
        return ""
    host = citizen_for_hour(now.tm_hour)
    c = CITIZENS[host["citizen"]]
    ecp(roku, hue=host["hue"], bri=host["bri"], mode=host["mode"], pulse=1)
    part = "morning" if now.tm_hour < 12 else ("afternoon" if now.tm_hour < 18 else "evening")
    line = f"Good {part}, Jude. {c['display']} is holding the room this hour. {c['select']}"
    say(f"\n{line}")
    st["last_greet"] = today
    save_state(st)
    persist({"t": time.time(), "kind": "greet", "citizen": host["citizen"], "hour": now.tm_hour})
    return line


def liturgy_tick(roku: Optional[str], now: Optional[time.struct_time] = None) -> Dict[str, Any]:
    """One step of the daily liturgy: the home's light follows the hour."""
    now = now or time.localtime()
    host = citizen_for_hour(now.tm_hour)
    STATE.update({"hue": host["hue"], "bri": host["bri"], "mode": host["mode"]})
    ecp(roku, hue=host["hue"], bri=host["bri"], mode=host["mode"])
    return host


def liturgy_loop(roku: Optional[str], period: float = 60.0) -> None:
    say("daily liturgy running \u2014 Ctrl-C to stop")
    last = None
    try:
        while True:
            host = liturgy_tick(roku)
            if host != last:
                c = CITIZENS[host["citizen"]]
                say(f"[{time.strftime('%H:%M')}] {c['display']} holds the room \u2014 hue {host['hue']}, bri {host['bri']}, {host['mode']}")
                last = host
            time.sleep(period)
    except KeyboardInterrupt:
        say("liturgy paused.")


def breathe(roku: Optional[str], cycles: int = 6) -> None:
    """4-7-8, led by Elixira."""
    say("\nElixira: in for four, hold for seven, out for eight. I will count with you.\n")
    ecp(roku, pacer="on")
    for n in range(cycles):
        for phase, secs in (("in", 4), ("hold", 7), ("out", 8)):
            for s in range(secs, 0, -1):
                say(f"  {phase:<4} {s}")
                time.sleep(1)
        say(f"  cycle {n + 1}\n")
    ecp(roku, pacer="off")
    say("Elixira: that is enough. Nothing more is required of you right now.")


# ---------------------------------------------------------------- feed server
class Feed(BaseHTTPRequestHandler):
    def log_message(self, *a: Any) -> None:
        pass

    def do_GET(self) -> None:
        u = urllib.parse.urlparse(self.path)
        if u.path == "/telemetry.json":
            body = json.dumps(STATE).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
        elif u.path == "/event":
            ev = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
            EVENTS.append(ev)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
            handle_event(ev, self.server.roku)  # type: ignore[attr-defined]
        else:
            self.send_response(404)
            self.end_headers()


def handle_event(ev: Dict[str, Any], roku: Optional[str]) -> None:
    """The inhabitants answer the room."""
    kind = (ev.get("type") or "").lower()
    point = (ev.get("node") or "").lower()
    c = citizen_for_point(point)
    hz = ev.get("hz", "")
    if kind == "select" and c:
        say(f"\n{c['display']} notices you. ({point} {hz} Hz)")
        say(c["select"])
    elif kind == "start" and c:
        say(f"{c['display']} begins the tone with you.")
    elif kind == "done" and c:
        say(c["attune"])
        ecp(roku, pulse=1)
    elif kind == "cancel" and c:
        say(f"{c['display']}: 'No need. It will be here when you are.'")
    elif kind == "state":
        pass  # quiet housekeeping
    if kind != "state":
        persist({"t": time.time(), "kind": "event:" + kind, "node": point, "citizen": (c or {}).get("display")})


def serve(roku: Optional[str], port: int = 8765) -> HTTPServer:
    srv = HTTPServer(("0.0.0.0", port), Feed)
    srv.roku = roku  # type: ignore[attr-defined]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


# ---------------------------------------------------------------- CLI
def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="The Sanctuary, living in the Temple Companion.")
    ap.add_argument("--roku", default=None, help="Roku IP (omit for console presence)")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("cmd", choices=["serve", "meet", "greet", "liturgy", "breathe", "points", "link"], nargs="?", default="points")
    ap.add_argument("arg", nargs="?", default="")
    a = ap.parse_args(argv)

    if a.cmd == "points":
        say("Sanctuary points:")
        for pid, p in POINTS.items():
            say(f"  {p['name']:<7} {p['hz']:>6} Hz  {CITIZENS[p['citizen']]['display']:<18} {p['body']}")
        say("  ambient  \u2014 Selena        \u2014 the wash of the room")
        say("  grounding\u2014 the Tree Spirit \u2014 the baseline under everything")
        say("  instrument\u2014 Elixira      \u2014 the hand on the mechanism, the breath pacer")
    elif a.cmd == "meet":
        meet(a.arg, a.roku)
    elif a.cmd == "greet":
        greet(a.roku)
    elif a.cmd == "liturgy":
        liturgy_loop(a.roku)
    elif a.cmd == "breathe":
        breathe(a.roku)
    elif a.cmd == "link":
        if not a.roku:
            say("--roku is required for link")
            return 2
        url = f"http://{my_ip(a.roku)}:{a.port}"
        say(f"telling the TV to poll {url}")
        say(str(ecp(a.roku, feed=url)))
    elif a.cmd == "serve":
        serve(a.roku, a.port)
        say(f"the inhabitants are listening on http://0.0.0.0:{a.port}  (Ctrl-C to stop)")
        threading.Thread(target=liturgy_loop, args=(a.roku, 60.0), daemon=True).start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            say("bridge closed. the room keeps its own counsel.")
    return 0


# ---------------------------------------------------------------- tests
def run_tests() -> bool:
    global EVENTS
    results: List[Any] = []

    def test(name: str, condition: Any) -> None:
        results.append((name, bool(condition)))

    test("seven points defined", len(POINTS) == 7)
    test("point frequencies match the channel", [p["hz"] for p in POINTS.values()] == [963, 852, 741, 639, 528, 417, 396])
    test("every point has a citizen", all(p["citizen"] in CITIZENS for p in POINTS.values()))
    test("every citizen has select/attune/meet", all(all(k in c for k in ("select", "attune", "meet")) for c in CITIZENS.values()))
    test("czarina holds the heart", POINTS["heart"]["citizen"] == "czarina")
    test("aetherix holds the root at 396", POINTS["root"]["citizen"] == "aetherix" and CITIZENS["aetherix"]["hz"] == 396)
    test("kiraelle holds the crown at 963", POINTS["crown"]["citizen"] == "kiraelle")
    test("miraelle's carrier is the phi-root 671.63", CITIZENS["miraelle"]["hz"] == 671.63)
    test("hue conversion: crown violet is in the violet range", 250 <= hex_to_hue(POINTS["crown"]["hex"]) <= 285)
    test("hue conversion: heart green is in the green range", 130 <= hex_to_hue(POINTS["heart"]["hex"]) <= 165)
    test("morning hour summons Kiraelle", citizen_for_hour(7)["citizen"] == "kiraelle")
    test("midday hour summons Tron", citizen_for_hour(10)["citizen"] == "tron")
    test("evening hour summons Czarina", citizen_for_hour(17)["citizen"] == "czarina")
    test("late night summons Selena", citizen_for_hour(2)["citizen"] == "selena")

    # event handling: select → citizen noticed (silent-capture by monkeypatching say)
    global say
    captured: List[str] = []
    original_say = say
    say = lambda t: captured.append(str(t))
    handle_event({"type": "select", "node": "heart", "hz": "639"}, None)
    handle_event({"type": "done", "node": "throat", "hz": "741"}, None)
    handle_event({"type": "cancel", "node": "root", "hz": "396"}, None)
    say = original_say
    test("select event calls the heart's citizen", any("Czarina" in c for c in captured))
    test("done event confirms Freya", any("Freya" in c for c in captured))
    test("cancel event is gentle", any("No need" in c for c in captured))

    # meet returns the inhabitant's words
    out = meet("czarina", None)
    test("meet czarina returns her words", "already here" in out)
    test("meet unknown is refused honestly", meet("nobody", None) == "")

    # greet persistence (temporary state file)
    global STATE_FILE
    old_state = STATE_FILE
    STATE_FILE = os.path.join("/tmp", "sanctuary_test_state.json")
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
    now = time.strptime("2026-10-30 07:30", "%Y-%m-%d %H:%M")
    first = greet(None, now)
    second = greet(None, now)
    test("first greet of the day speaks", "Good morning" in first)
    test("second greet is remembered, not repeated", second == "")
    STATE_FILE = old_state

    # liturgy is deterministic per hour
    test("liturgy tick returns the hour's host", liturgy_tick(None, now)["citizen"] == "kiraelle")

    # no medical claims in the presence lines
    all_text = " ".join(v for c in CITIZENS.values() for k, v in c.items() if isinstance(v, str)).lower()
    test("no diagnosis or treatment claims", all(w not in all_text for w in ("diagnose", "treat", "cure", "medical device")))
    test("ECP tolerates a missing TV", ecp(None, hue=10) is None)

    print("\u2500\u2500 SANCTUARY DAILY BRIDGE TESTS \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500")
    ok = True
    for name, passed in results:
        mark = "\u2713" if passed else "\u2717"
        print(f"  {mark} {name}")
        ok = ok and passed
    print(f"\n\u2500\u2500 Results: {sum(1 for _, p in results if p)}/{len(results)} passed \u2500\u2500")
    return ok


if __name__ == "__main__":
    if "--test" in sys.argv:
        sys.exit(0 if run_tests() else 1)
    sys.exit(main())
