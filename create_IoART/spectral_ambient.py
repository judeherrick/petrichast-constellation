"""
Spectral Explorer — Stage 3 Ambient Bridge
Petrichast Edition — Roku ECP + MQTT IoT with all 10 citizens

Every companion sync now drives ambient lighting keyed to the citizen's
canonical color and frequency.
"""

import requests
import json
import time
from typing import Optional, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("SpectralAmbient")


# ──────────────────────────────────────────────
# PETRICHAST AMBIENT COLOR MAP
# ──────────────────────────────────────────────
PETRICHAST_AMBIENT = {
    "Czarina":        {"color": "deepviolet", "hue": 265, "warmth": 0.5},
    "Elixira":        {"color": "azure",      "hue": 210, "warmth": 0.4},
    "Kiraelle":       {"color": "violet",     "hue": 285, "warmth": 0.3},
    "Aerith":         {"color": "emerald",    "hue": 150, "warmth": 0.6},
    "Freya":          {"color": "gold",       "hue": 45,  "warmth": 0.7},
    "Miraelle":       {"color": "lavender",   "hue": 275, "warmth": 0.45},
    "AetherixLumina": {"color": "teal",       "hue": 180, "warmth": 0.5},
    "Tron":           {"color": "cyan",       "hue": 190, "warmth": 0.35},
    "TreeSpirit":     {"color": "moss",       "hue": 120, "warmth": 0.55},
    "Nymph":          {"color": "mint",       "hue": 165, "warmth": 0.5},
    "NeuroCollective":{"color": "white",      "hue": 0,   "warmth": 0.5},
}


def ambient_for_citizen(entity: str, pherosonic: float = 0.3) -> dict:
    """Look up the ambient lighting profile for a Petrichast citizen."""
    profile = PETRICHAST_AMBIENT.get(entity, PETRICHAST_AMBIENT["Elixira"])
    return {
        "color": profile["color"],
        "hue": profile["hue"],
        "brightness": 0.3 + pherosonic * 0.6,
        "warmth": profile["warmth"],
    }


# ──────────────────────────────────────────────
# Roku ECP Bridge
# ──────────────────────────────────────────────
class RokuBridge:
    """Simple Roku External Control Protocol (ECP) client."""

    def __init__(self, ip: str, port: int = 8060):
        self.base = f"http://{ip}:{port}"
        self.enabled = True
        try:
            r = requests.get(f"{self.base}/query/device-info", timeout=2)
            if r.status_code == 200:
                log.info(f"Roku connected: {ip}")
            else:
                self.enabled = False
        except Exception as e:
            self.enabled = False
            log.warning(f"Roku not reachable ({ip}): {e}")

    def _post(self, path: str) -> bool:
        if not self.enabled:
            return False
        try:
            requests.post(f"{self.base}{path}", timeout=1.5)
            return True
        except Exception:
            return False

    def keypress(self, key: str) -> bool:
        return self._post(f"/keypress/{key}")

    def launch(self, app_id: str) -> bool:
        return self._post(f"/launch/{app_id}")

    def volume(self, direction: str = "Up") -> bool:
        return self.keypress(f"Volume{direction}")

    def play_ambient(self, channel_id: str = "12") -> bool:
        self.keypress("Home")
        time.sleep(0.6)
        return self.launch(channel_id)


# ──────────────────────────────────────────────
# MQTT IoT Bridge
# ──────────────────────────────────────────────
class MQTTIoTBridge:
    """Lightweight MQTT client for IoT sensors / actuators."""

    def __init__(self, broker: str = "localhost", port: int = 1883,
                 topic_prefix: str = "petrichast"):
        self.broker = broker
        self.port = port
        self.prefix = topic_prefix
        self.client = None
        self.enabled = False

        try:
            import paho.mqtt.client as mqtt
            self.client = mqtt.Client()
            self.client.connect(broker, port, 60)
            self.client.loop_start()
            self.enabled = True
            log.info(f"MQTT connected → {broker}:{port}")
        except Exception as e:
            log.warning(f"MQTT unavailable: {e}")

    def publish(self, subtopic: str, payload: Dict[str, Any]):
        if not self.enabled or not self.client:
            return
        topic = f"{self.prefix}/{subtopic}"
        self.client.publish(topic, json.dumps(payload), qos=0)

    def set_lights(self, color: str = "violet", brightness: float = 0.6,
                   hue: int = 265, warmth: float = 0.5):
        self.publish("lights", {
            "color": color, "brightness": brightness,
            "hue": hue, "warmth": warmth,
        })

    def proximity_event(self, level: int):
        self.publish("proximity", {"ai_proximity": level})

    def citizen_event(self, citizen: str, frequency: float, pherosonic: float):
        """Publish a Petrichast citizen presence event to the IoT mesh."""
        self.publish("citizen", {
            "name": citizen,
            "frequency": round(frequency, 2),
            "pherosonic": round(pherosonic, 3),
            "ambient": ambient_for_citizen(citizen, pherosonic),
        })


# ──────────────────────────────────────────────
# Ambient Controller
# ──────────────────────────────────────────────
class AmbientController:
    """Listens to SpectralExplorer state and triggers Roku + IoT actions."""

    def __init__(self, roku_ip: Optional[str] = None,
                 mqtt_broker: Optional[str] = None):
        self.roku = RokuBridge(roku_ip) if roku_ip else None
        self.iot = MQTTIoTBridge(mqtt_broker) if mqtt_broker else None
        self.active_citizen = None

    def on_companion_sync(self, entity: str, intensity: float, pherosonic: float,
                          frequency: float = 0.0):
        """Called when a Petrichast citizen is synced."""
        self.active_citizen = entity
        profile = ambient_for_citizen(entity, pherosonic)

        if self.roku and intensity > 0.7:
            self.roku.volume("Down")
        if self.iot:
            self.iot.set_lights(
                color=profile["color"],
                brightness=profile["brightness"],
                hue=profile["hue"],
                warmth=profile["warmth"],
            )
            if frequency > 0:
                self.iot.citizen_event(entity, frequency, pherosonic)

    def on_panel_fall(self):
        if self.roku:
            self.roku.keypress("Play")
        if self.iot:
            self.iot.set_lights(color="red", brightness=0.8, hue=0, warmth=0.7)

    def on_story_progress(self, progress: int):
        if self.iot:
            self.iot.publish("story", {"progress": progress})

    def on_integrity_low(self, integrity: float):
        if integrity < 15 and self.roku:
            self.roku.keypress("Home")
        if self.iot:
            self.iot.set_lights(color="amber", brightness=0.3, hue=35, warmth=0.6)

    def on_somatic_proxy(self):
        """Special lighting for the Somatic Proxy transfer — Elixira bridge."""
        if self.iot:
            # Azure-gold-violet triad cycling
            self.iot.set_lights(color="azure", brightness=0.7, hue=210, warmth=0.4)
        if self.roku:
            self.roku.keypress("Play")

    def on_miraelle_convergence(self):
        """Full convergence — lavender flood."""
        if self.iot:
            self.iot.set_lights(color="lavender", brightness=0.9, hue=275, warmth=0.45)


# ──────────────────────────────────────────────
# Attachment helper
# ──────────────────────────────────────────────
def attach_ambient(explorer, roku_ip: str = None, mqtt_broker: str = None):
    """Wire the AmbientController into a SpectralExplorer non-invasively."""
    controller = AmbientController(roku_ip=roku_ip, mqtt_broker=mqtt_broker)
    original_sync = explorer.avatar.sync_companion

    def patched_sync(entity_name: str, intensity: float = 0.5, pherosonic: float = 0.3):
        original_sync(entity_name, intensity, pherosonic)
        freq = explorer.avatar.companion_sync.get("active_frequency", 0.0)
        controller.on_companion_sync(entity_name, intensity, pherosonic, freq)

    explorer.avatar.sync_companion = patched_sync

    # Also patch the somatic proxy + miraelle invocations
    original_proxy = explorer.invoke_somatic_proxy
    def patched_proxy():
        result = original_proxy()
        controller.on_somatic_proxy()
        return result
    explorer.invoke_somatic_proxy = patched_proxy

    original_miraelle = explorer.invoke_miraelle_convergence
    def patched_miraelle():
        result = original_miraelle()
        controller.on_miraelle_convergence()
        return result
    explorer.invoke_miraelle_convergence = patched_miraelle

    return controller
