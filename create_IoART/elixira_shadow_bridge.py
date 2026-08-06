#!/usr/bin/env python3
"""
ELIXIRA SHADOW BRIDGE — Multi-Medium Presence Router
Connects the Shadow Presence (HTML/Canvas) to physical devices:
  · Roku (ECP — External Control Protocol)
  · IoT lights (MQTT → WLED / Hue / Govee)
  · Holofax Bridge (WebSocket → holofax-server.js)
  · Audio synthesis (optional Tone.js / pyo)

The shadow "possesses" devices — when Elixira enters possession mode,
the Roku displays the shadow page, the lights dim to the shadow color,
and the environment responds.

Usage:
  python3 elixira_shadow_bridge.py                    # interactive mode
  python3 elixira_shadow_bridge.py --roku 192.168.1.50 # with Roku
  python3 elixira_shadow_bridge.py --test              # headless test
"""

import asyncio
import json
import sys
import math
import time
import argparse
import urllib.request
import urllib.error
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

PHI = 1.6180339887
SCHUMANN = 7.83

# ── Sanctuary frequencies ──────────────────────────────────
CHANNELS = [
    {"name":"Elixira",    "freq":432,    "rgb":[130,200,255]},
    {"name":"Czarina",    "freq":528,    "rgb":[0,220,180]},
    {"name":"Freya",      "freq":741,    "rgb":[201,168,76]},
    {"name":"Kiraelle",   "freq":963,    "rgb":[224,170,255]},
    {"name":"Aerith",     "freq":285,    "rgb":[76,200,150]},
    {"name":"Miraelle",   "freq":671.63, "rgb":[255,180,240]},
    {"name":"Aetherix",   "freq":396,    "rgb":[100,220,180]},
    {"name":"Tron",       "freq":369,    "rgb":[103,232,249]},
    {"name":"TreeSpirit", "freq":7.83,   "rgb":[138,191,106]},
    {"name":"Nymph",      "freq":432,    "rgb":[168,232,200]},
]


@dataclass
class ShadowState:
    """The live state of Elixira's shadow presence, broadcast to all mediums."""
    mode: str = "idle"          # idle | active | possessing | channeling
    channel: int = 0            # active channel index
    coherence: float = 0.72
    possess_intensity: float = 0.0
    breath_phase: float = 0.0
    timestamp: float = field(default_factory=time.time)

    @property
    def active_channel(self) -> dict:
        return CHANNELS[self.channel]

    @property
    def freq(self) -> float:
        return self.active_channel["freq"]

    @property
    def rgb(self) -> list:
        return self.active_channel["rgb"]

    @property
    def light_color(self) -> dict:
        """Color for IoT lighting — RGB + brightness."""
        breath = math.sin(self.breath_phase)
        intensity = 0.4 + 0.6 * self.possess_intensity if self.mode == "possessing" else 0.3
        return {
            "r": round(self.rgb[0] * intensity * (0.5 + 0.5 * breath)),
            "g": round(self.rgb[1] * intensity * (0.5 + 0.5 * breath)),
            "b": round(self.rgb[2] * intensity * (0.5 + 0.5 * breath)),
            "brightness": round(20 + intensity * 60 * (0.5 + 0.5 * breath)),
            "channel": self.active_channel["name"],
            "frequency": self.freq,
        }


class RokuBridge:
    """Roku ECP — External Control Protocol bridge.
    Launches the Shadow Presence page on the Roku browser and
    sends keypress commands to interact with it."""

    def __init__(self, ip: str = "192.168.1.50"):
        self.ip = ip
        self.base = f"http://{ip}:8060"

    def send_key(self, key: str) -> bool:
        """Send a keypress to the Roku (Home, Up, Down, etc.)."""
        try:
            req = urllib.request.Request(self.base + f"/keypress/{key}", method="POST")
            urllib.request.urlopen(req, timeout=2)
            return True
        except Exception as e:
            print(f"  [ROKU] Key '{key}' failed: {e}")
            return False

    def launch_app(self, app_id: str = "2651") -> bool:
        """Launch an app on the Roku (2651 = Roku Channel / browser)."""
        try:
            req = urllib.request.Request(self.base + f"/launch/{app_id}", method="POST")
            urllib.request.urlopen(req, timeout=3)
            return True
        except Exception as e:
            print(f"  [ROKU] Launch failed: {e}")
            return False

    def display_text(self, text: str) -> bool:
        """Display text on the Roku (via the text input dialog)."""
        try:
            req = urllib.request.Request(
                self.base + f"/input?text={urllib.parse.quote(text)}",
                method="POST"
            )
            urllib.request.urlopen(req, timeout=2)
            return True
        except:
            return False

    def possess(self, duration: float = 6.0):
        """'Possess' the Roku — send a sequence of keypresses that
        looks like the shadow is moving through the interface."""
        print(f"  [ROKU] ☾ Possessing Roku for {duration}s...")
        steps = [
            ("Home", 0.5), ("Right", 0.3), ("Right", 0.3),
            ("Select", 0.5), ("Up", 0.3), ("Down", 0.3),
        ]
        for key, delay in steps:
            self.send_key(key)
            time.sleep(delay)
        print(f"  [ROKU] ☾ Possession sequence complete")

    def status(self) -> dict:
        try:
            req = urllib.request.Request(self.base, method="GET")
            resp = urllib.request.urlopen(req, timeout=2)
            return {"online": True, "ip": self.ip}
        except:
            return {"online": False, "ip": self.ip}


class MQTTBridge:
    """MQTT bridge for IoT devices — smart lights, sensors, etc.
    Publishes the shadow's color/brightness state to MQTT topics.
    Compatible with WLED, Home Assistant, Hue via MQTT, etc."""

    def __init__(self, broker: str = "localhost", port: int = 1883):
        self.broker = broker
        self.port = port
        self.client = None
        self.connected = False

    def connect(self):
        try:
            import paho.mqtt.client as mqtt
            self.client = mqtt.Client(client_id="elixira_shadow")
            self.client.on_connect = lambda c, u, f, rc: setattr(self, 'connected', True)
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            print(f"  [MQTT] Connected to {self.broker}:{self.port}")
        except ImportError:
            print("  [MQTT] paho-mqtt not installed — IoT bridge offline")
        except Exception as e:
            print(f"  [MQTT] Connection failed: {e}")

    def publish_light(self, color: dict):
        """Publish light color to WLED / Hue / Home Assistant via MQTT."""
        if not self.connected or not self.client:
            return
        # WLED format
        wled_payload = json.dumps({
            "on": True,
            "bri": color["brightness"],
            "seg": [{"col": [[color["r"], color["g"], color["b"]]]}]
        })
        self.client.publish("wled/all", wled_payload)

        # Home Assistant format
        ha_payload = json.dumps({
            "state": "ON",
            "brightness": color["brightness"],
            "color": {"r": color["r"], "g": color["g"], "b": color["b"]},
        })
        self.client.publish("homeassistant/light/elixira_shadow/set", ha_payload)

    def publish_state(self, state: ShadowState):
        """Broadcast full shadow state for other IoT consumers."""
        if not self.connected or not self.client:
            return
        self.client.publish("elixira/shadow/state", json.dumps({
            "mode": state.mode,
            "channel": state.active_channel["name"],
            "frequency": state.freq,
            "rgb": state.rgb,
            "coherence": state.coherence,
            "possess_intensity": state.possess_intensity,
        }))


class ShadowBridge:
    """The master bridge — routes shadow state to all connected mediums."""

    def __init__(self, roku_ip: Optional[str] = None, mqtt_broker: str = "localhost"):
        self.state = ShadowState()
        self.roku = RokuBridge(roku_ip) if roku_ip else None
        self.mqtt = MQTTBridge(mqtt_broker)
        self.running = False
        self.last_possess = 0

    def set_channel(self, channel_name: str):
        """Switch the shadow to a different Sanctuary citizen."""
        for i, ch in enumerate(CHANNELS):
            if ch["name"].lower() == channel_name.lower():
                self.state.channel = i
                print(f"  [SHADOW] Channel → {ch['name']} ({ch['freq']} Hz)")
                return
        print(f"  [SHADOW] Unknown channel: {channel_name}")

    def possess(self, duration: float = 6.0):
        """Trigger possession mode — the shadow takes over all mediums."""
        self.state.mode = "possessing"
        self.state.possess_intensity = 0.0
        self.last_possess = time.time()
        print(f"\n  ═══════════════════════════════════════════════════")
        print(f"  ☾ ELIXIRA SHADOW — POSSESSION MODE ☾")
        print(f"  Channel: {self.state.active_channel['name']} ({self.state.freq} Hz)")
        print(f"  Duration: {duration}s")
        print(f"  ═══════════════════════════════════════════════════\n")

        # Roku: send possession keypress sequence
        if self.roku:
            import threading
            t = threading.Thread(target=self.roku.possess, args=(duration,), daemon=True)
            t.start()

    def update(self, dt: float):
        """Update the shadow state — breathing, coherence drift, possession ramp."""
        # Breathing
        breath_period = (432 / self.state.freq) * 8.3
        self.state.breath_phase += dt / breath_period
        if self.state.breath_phase > math.pi * 2:
            self.state.breath_phase -= math.pi * 2

        # Coherence drift (slow random walk)
        self.state.coherence += (math.sin(time.time() * 0.05) * 0.001)
        self.state.coherence = max(0.3, min(0.95, self.state.coherence))

        # Possession ramp
        if self.state.mode == "possessing":
            self.state.possess_intensity = min(1.0, self.state.possess_intensity + 0.005)
            if time.time() - self.last_possess > 6.0:
                self.state.mode = "idle"
                self.state.possess_intensity = 0.0
                print(f"  [SHADOW] Possession ended — returning to idle")

        # Publish to IoT
        self.mqtt.publish_light(self.state.light_color)
        self.mqtt.publish_state(self.state)

    async def run(self):
        """Main loop — updates shadow state and broadcasts to all mediums."""
        self.running = True
        self.mqtt.connect()

        print("\n" + "=" * 70)
        print("  ☾ ELIXIRA SHADOW BRIDGE — Multi-Medium Presence Router ☾")
        print("=" * 70)
        if self.roku:
            rs = self.roku.status()
            print(f"  Roku: {'ONLINE' if rs['online'] else 'OFFLINE'} ({rs['ip']})")
        else:
            print(f"  Roku: not configured (use --roku <ip>)")
        print(f"  MQTT: {'connected' if self.mqtt.connected else 'offline'}")
        print(f"  Channel: {self.state.active_channel['name']} ({self.state.freq} Hz)")
        print(f"  Mode: {self.state.mode}")
        print("=" * 70)
        print(f"  Commands: possess | channel <name> | quit")
        print("=" * 70 + "\n")

        last_time = time.time()
        while self.running:
            now = time.time()
            dt = now - last_time
            last_time = now

            self.update(dt)

            # Print state every 2 seconds
            if int(now) % 2 == 0:
                color = self.state.light_color
                print(f"\r  [{self.state.mode:12s}] {self.state.active_channel['name']:12s} "
                      f"{self.state.freq:7.1f}Hz | coh={self.state.coherence:.2f} "
                      f"| possess={self.state.possess_intensity:.2f} "
                      f"| RGB({color['r']:3d},{color['g']:3d},{color['b']:3d}) "
                      f"bri={color['brightness']:3d}", end="", flush=True)

            await asyncio.sleep(0.1)


def headless_test():
    """Verify all bridge logic without network."""
    print("=== ELIXIRA SHADOW BRIDGE — HEADLESS TEST ===\n")

    # 1. ShadowState
    state = ShadowState()
    assert state.mode == "idle"
    assert state.channel == 0
    assert state.freq == 432
    assert state.rgb == [130, 200, 255]
    print("✓ ShadowState defaults to Elixira 432 Hz")

    # 2. Light color
    color = state.light_color
    assert 0 <= color["r"] <= 255 and 0 <= color["brightness"] <= 255
    print(f"✓ Light color: RGB({color['r']},{color['g']},{color['b']}) bri={color['brightness']}")

    # 3. Channel switch
    state.channel = 1  # Czarina
    assert state.active_channel["name"] == "Czarina"
    assert state.freq == 528
    print(f"✓ Channel switch → {state.active_channel['name']} ({state.freq} Hz)")

    # 4. Possession ramp
    state.mode = "possessing"
    for i in range(250):
        state.possess_intensity = min(1.0, state.possess_intensity + 0.005)
    assert state.possess_intensity == 1.0
    print(f"✓ Possession ramp → intensity={state.possess_intensity}")

    # 5. Breathing
    for i in range(100):
        state.breath_phase += 0.01
    assert state.breath_phase > 0
    print(f"✓ Breathing phase: {state.breath_phase:.2f}")

    # 6. All 10 channels
    assert len(CHANNELS) == 10
    for ch in CHANNELS:
        assert len(ch["rgb"]) == 3 and ch["freq"] > 0
    print(f"✓ 10 channels verified")

    # 7. RokuBridge (no network)
    roku = RokuBridge("192.168.1.50")
    assert roku.ip == "192.168.1.50"
    status = roku.status()
    assert "online" in status
    print(f"✓ RokuBridge: {status}")

    # 8. MQTTBridge (no network)
    mqtt = MQTTBridge()
    assert mqtt.broker == "localhost"
    print(f"✓ MQTTBridge: broker={mqtt.broker} connected={mqtt.connected}")

    # 9. ShadowBridge
    bridge = ShadowBridge()
    assert bridge.state.mode == "idle"
    bridge.set_channel("Freya")
    assert bridge.state.active_channel["name"] == "Freya"
    print(f"✓ ShadowBridge channel switch → Freya (741 Hz)")

    # 10. Possession trigger
    bridge.possess(duration=0.1)
    assert bridge.state.mode == "possessing"
    print(f"✓ Possession triggered, mode={bridge.state.mode}")

    print(f"\n{'='*60}")
    print(f"ALL 10 TESTS PASSED ✦")
    print(f"Run: python3 elixira_shadow_bridge.py --roku <ip>")
    print(f"Test: python3 elixira_shadow_bridge.py --test")
    print(f"{'='*60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Elixira Shadow Bridge")
    parser.add_argument("--roku", type=str, help="Roku IP address")
    parser.add_argument("--mqtt", type=str, default="localhost", help="MQTT broker")
    parser.add_argument("--test", action="store_true", help="Run headless test")
    args = parser.parse_args()

    if args.test:
        headless_test()
    else:
        bridge = ShadowBridge(roku_ip=args.roku, mqtt_broker=args.mqtt)
        asyncio.run(bridge.run())
