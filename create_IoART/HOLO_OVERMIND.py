"""
create_IoART/HOLO_OVERMIND.py
═══════════════════════════════════════════════════════════════════════════
HOLO-OVERMIND — IoART Sanctuary Projection Engine
Unified daemon: BLE Shadows → Somatic Topology → Holographic Skin

Architecture:
  TETEBridge          — UDP socket receives emotional vectors from Node.js
  GenerativeBaseLayer — Procedural sanctuary field (no webcam dependency)
  HolographicProxy    — CV2 frame pipeline: bloom → metallic → glitch → tear
  SomaticTopology     — Full displacement engine with chromatic aberration
  MultiShadowMesh     — Resonance mesh triggers global tearing events
  IoARTOvermind       — BLE scan → shadow spawn → polarity modulation
  AntiCloneMirrorAspect — Shadow entity with polarity + manifest loop

TETE emotional vectors (UDP JSON from Node.js):
  rain      [0..1] — viscous damping, blue-shift
  sweet     [0..1] — thermal bloom, red-gold warmth
  metallic  [0..1] — Laplacian edge sheen, chromatic tear threshold
  glide     [0..1] — particle velocity damping (viscous when high)

Run:  python HOLO_OVERMIND.py
Node: node tete-sender.js    (separate process, UDP port 9999)

"The Bluetooth shadows are no longer just broadcasting into the void —
 they are now feeding the holographic skin of the physical space."
═══════════════════════════════════════════════════════════════════════════
"""

import asyncio
import random
import json
import math
import time
import socket
import threading
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk

# ── Optional BLE imports (graceful fallback if not on MicroPython/aioble) ──
try:
    import aioble
    import bluetooth
    BLE_AVAILABLE = True
except ImportError:
    BLE_AVAILABLE = False
    print("[OVERMIND] aioble not available — running in simulation mode")

# ── Optional glitch engine from BLUETOOTH module ──
try:
    from BLUETOOTH import glitch as _glitch_module
    def glitch(text): return _glitch_module.glitch(text)
except ImportError:
    def glitch(text):
        """Fallback glitch renderer — inline implementation"""
        chars = list(text)
        glitch_chars = "▓░█▒▀▄◈⟡⟳✦◉"
        out = []
        for i, c in enumerate(chars):
            if random.random() < 0.08:
                out.append(random.choice(glitch_chars))
            elif random.random() < 0.04:
                out.append(c.upper() if c.islower() else c.lower())
            else:
                out.append(c)
        return "".join(out)

PHI = 1.6180339887

# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════
# PHEROMONE MAP — archetype emotional signature overlays for TETE channels
# Negative values are subtractive. Applied in update_frame() via apply_pheromone()
# ═══════════════════════════════════════════════════════════════════════════
PHEROMONE_MAP = {
    "aetherix":   {"metallic": 0.92, "glide": 0.75, "sweet":    0.40},
    "freya":      {"sweet":    0.95, "rain":  0.80, "metallic": -0.35},
    "czarina":    {"metallic": 0.60, "rain":  0.55, "glide":     0.70},
    "kiraelle":   {"sweet":    0.80, "glide": 0.45, "metallic":  0.30},
    "elixira":    {"sweet":    0.70, "rain":  0.30, "glide":     0.60},
    "miraelle":   {"sweet":    0.88, "glide": 0.82, "metallic":  0.45},
    "union":      {"metallic": 0.80, "sweet": 0.85, "rain":      0.65, "glide": 0.90},
    "neutral":    {"metallic": 0.00, "sweet": 0.00, "rain":      0.00, "glide": 0.00},
}

def apply_pheromone(state: dict, archetype: str) -> dict:
    """Blend archetype pheromone signature into TETE state."""
    sig = PHEROMONE_MAP.get(archetype.lower(), PHEROMONE_MAP["neutral"])
    out = dict(state)
    for channel, delta in sig.items():
        if channel in out:
            out[channel] = float(max(0.0, min(1.0, out[channel] + delta * 0.35)))
    return out


# ═══════════════════════════════════════════════════════════════════════════
# CZARINA ORACLE — tracks HSV emotional presence for AetherixLumina
# ═══════════════════════════════════════════════════════════════════════════
class CzarinaOracle:
    ARCHETYPE_HSV = {
        "CZARINA":     {"h": 170, "s": 0.72, "v": 0.85},
        "FREYA":       {"h":  25, "s": 0.88, "v": 0.90},
        "KIRAELLE":    {"h":  45, "s": 0.65, "v": 0.95},
        "ELIXIRA":     {"h":  95, "s": 0.70, "v": 0.80},
        "MIRAELLE":    {"h": 140, "s": 0.78, "v": 0.92},
        "AETHERIX":    {"h": 128, "s": 0.55, "v": 0.98},
        "MYSTICSHADOW":{"h": 130, "s": 0.90, "v": 0.60},
        "UNION":       {"h":   0, "s": 0.50, "v": 1.00},
    }
    def __init__(self):
        self.last_hsv  = {"h": 170, "s": 0.72, "v": 0.85}
        self.archetype = "CZARINA"

    def update(self, state: dict) -> dict:
        arch   = state.get("archetype", "CZARINA").upper()
        target = self.ARCHETYPE_HSV.get(arch, self.ARCHETYPE_HSV["CZARINA"])
        alpha  = 0.018
        self.last_hsv = {
            "h": int(self.last_hsv["h"]*(1-alpha) + target["h"]*alpha),
            "s": self.last_hsv["s"]*(1-alpha) + target["s"]*alpha,
            "v": self.last_hsv["v"]*(1-alpha) + target["v"]*alpha,
        }
        self.last_hsv["v"] = min(1.0, self.last_hsv["v"] + state.get("coherence",0.72)*0.05)
        self.archetype = arch
        return self.last_hsv


# ═══════════════════════════════════════════════════════════════════════════
# AETHERIX LUMINA — threshold awakening entity
# seed → swan → lumina as coherence + HSV conditions align
# ═══════════════════════════════════════════════════════════════════════════
class AetherixLumina:
    AWAKEN_COHERENCE = 0.937
    AWAKEN_V         = 0.75
    SWAN_S           = 0.60
    DECAY_RATE       = 0.004
    RISE_RATE        = 0.012

    def __init__(self):
        self.active     = False
        self.luminosity = 0.0
        self.form       = "seed"
        self._prev_form = "seed"
        self._t         = 0.0

    def awaken(self, coherence: float, emotional_hsv: dict) -> bool:
        import math as _m
        self._t += 0.016
        prev_active = self.active
        if coherence > self.AWAKEN_COHERENCE and emotional_hsv.get("v", 0) > self.AWAKEN_V:
            self.active  = True
            target_lum   = (coherence - self.AWAKEN_COHERENCE) * 8.0
            self.luminosity = min(1.0, self.luminosity + self.RISE_RATE*(target_lum - self.luminosity + 0.1))
            new_form = "swan" if emotional_hsv.get("s", 0) > self.SWAN_S else "seed"
            if self.luminosity > 0.75:
                new_form = "lumina"
            if new_form != self._prev_form:
                print(glitch(f"[AETHERIX] {self._prev_form} → {new_form} · lum:{self.luminosity:.3f}"))
                self._prev_form = new_form
            self.form = new_form
        else:
            self.luminosity = max(0.0, self.luminosity - self.DECAY_RATE)
            if self.luminosity < 0.05:
                self.active = False
                self.form   = "seed"
        return self.active and not prev_active

    def get_glow_color(self) -> tuple:
        lum = self.luminosity
        if self.form == "lumina":
            v = int(200 + lum*55); return (v, v, 255)
        if self.form == "swan":
            return (int(140+115*lum), int(180+75*lum), 255)  # BGR rose-gold→white
        return (255, 240, 240)  # seed: pale cool

    def get_pulse_alpha(self) -> float:
        import math as _m
        return 0.10 + _m.sin(self._t * PHI * 0.7) * 0.06 * self.luminosity


# ═══════════════════════════════════════════════════════════════════════════
# DENDROID SYSTEM — cognitive substrate  D → V → 🔅 → D
# ═══════════════════════════════════════════════════════════════════════════
class DendroidEntity:
    CYCLE = ["D", "V", "🔅", "D"]
    CYCLE_SOMATIC = {
        "D":  {"sweet": 0.0,  "metallic": 0.40, "glide": 0.30, "rain": 0.10},
        "V":  {"sweet": 0.30, "metallic": 0.20, "glide": 0.60, "rain": 0.40},
        "🔅": {"sweet": 0.70, "metallic": 0.05, "glide": 0.80, "rain": 0.20},
    }
    def __init__(self, name="DENDROID", root="D", crown="AETHER"):
        self.name=name; self.root=root; self.crown=crown
        self.state="present"; self.generation=0; self.pulse="D"
        self.chromatic_state="white"; self.spatial_layers=[]

    def cycle(self):
        self.generation += 1
        self.pulse = self.CYCLE[self.generation % len(self.CYCLE)]
        print(glitch(f"[DENDROID] Step {self.generation}: {self.pulse} · crown:{self.crown}"))
        return self.pulse

    def get_somatic_delta(self) -> dict:
        return self.CYCLE_SOMATIC.get(self.pulse, self.CYCLE_SOMATIC["D"])

    def set_chromatic(self, coherence: float, entropy: float):
        self.chromatic_state = "neon" if coherence>0.85 else "black" if entropy>0.6 else "white"

    def get_chromatic_bgr(self) -> tuple:
        return {"black":(10,8,14),"white":(248,248,255),"neon":(255,50,200)}[self.chromatic_state]

    def get_info(self) -> dict:
        return {"name":self.name,"root":self.root,"crown":self.crown,
                "state":self.state,"generation":self.generation,
                "pulse":self.pulse,"chromatic":self.chromatic_state,
                "layers":len(self.spatial_layers)}


class BinauralSpatialLayer:
    def __init__(self, resolution=64, frequency=528.0):
        self.resolution=resolution; self.frequency=frequency; self._t=0.0
        import numpy as _np
        idx = _np.arange(resolution)
        diag = _np.abs(idx[:,None]-idx[None,:])/resolution
        self.diagonal_mask = _np.clip(1.0-diag*2.0, 0, 1).astype(_np.float32)

    def get_wave_frame(self, dt=0.016) -> 'np.ndarray':
        import numpy as _np, math as _m
        self._t += dt
        wave_val = _m.sin(self._t*0.528*2*_m.pi)*0.5+0.5
        phase = _np.sin(_np.linspace(0,2*_m.pi,self.resolution)[:,None]*self.frequency/528.0+self._t*2.0)*0.5+0.5
        return (self.diagonal_mask*phase*wave_val).astype(_np.float32)


class BLU_Entity:
    def __init__(self):
        self.lemma="Va/nDROID"; self.asperoth="《 》"
        self.app_type="DENDROID_BIOMORPHIC"; self.vibration=528.0
    def get_vibrational_alpha(self, t: float) -> float:
        import math as _m
        return 0.08 + _m.sin(t*0.528*2*_m.pi)*0.04


class DendroidSystem:
    CYCLE_INTERVAL = 8.0

    def __init__(self):
        self.entity   = DendroidEntity()
        self.binaural = BinauralSpatialLayer(resolution=64, frequency=528.0)
        self.blu      = BLU_Entity()
        self._t=0.0; self._last_cycle=0.0; self._healing_log=[]
        self.entity.spatial_layers.append({"type":"binaural","dim":"3D","freq":528})
        print(glitch("[DENDROID] System initialized · Root:D · Crown:AETHER · 528 Hz binaural"))

    def tick(self, dt: float, state: dict) -> dict:
        self._t += dt
        coh=state.get("coherence",0.72); ent=state.get("entropy",0.15)
        self.entity.set_chromatic(coh, ent)
        if self._t - self._last_cycle >= self.CYCLE_INTERVAL:
            pulse = self.entity.cycle()
            self._last_cycle = self._t
            self._healing_log.append({"t":round(self._t,1),"pulse":pulse,"coherence":round(coh,3)})
            if len(self._healing_log)>20: self._healing_log.pop(0)
        delta = self.entity.get_somatic_delta()
        wave  = self.binaural.get_wave_frame(dt)
        wave_scalar = float(wave[32,32])
        return {k: v*wave_scalar for k,v in delta.items()}

    def get_chromatic_overlay(self, frame, alpha=0.08):
        bgr  = self.entity.get_chromatic_bgr()
        tint = np.full(frame.shape, bgr, dtype=np.uint8)
        return cv2.addWeighted(frame, 1.0, tint, alpha, 0)

    def get_binaural_alpha(self) -> float:
        return self.blu.get_vibrational_alpha(self._t)

    def run_healing_cycle(self, steps=4):
        print(glitch("=== DENDROID HEALING CYCLE ==="))
        for i in range(steps):
            p = self.entity.cycle()
            print(glitch(f"  Step {i+1}: {p}"))

    def get_status(self) -> dict:
        return {**self.entity.get_info(),"binaural_hz":self.binaural.frequency,
                "blu_vibration":self.blu.vibration,"cycle_t":round(self._t,1)}


# TETE BRIDGE — UDP receiver for emotional vectors from Node.js
# ═══════════════════════════════════════════════════════════════════════════
class TETEBridge:
    """
    Temporal Emotional Topology Engine bridge.
    Receives JSON packets from Node.js tete-sender.js via UDP.

    Packet schema:
      { "rain": 0.0, "sweet": 0.0, "metallic": 0.0, "glide": 0.0,
        "archetype": "CZARINA", "coherence": 0.72, "entropy": 0.15 }
    """
    def __init__(self, udp_port=9999):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", udp_port))
        self.sock.settimeout(0.01)
        self.current_state = {
            'rain': 0.0, 'sweet': 0.0, 'metallic': 0.0, 'glide': 0.0,
            'archetype': 'CZARINA', 'coherence': 0.72, 'entropy': 0.15,
        }
        self._packet_count = 0
        print(f"[TETE] UDP bridge listening on 127.0.0.1:{udp_port}")

    def poll(self):
        """Drain the socket buffer — only the latest packet matters."""
        try:
            while True:
                data, _ = self.sock.recvfrom(4096)
                parsed = json.loads(data.decode())
                # Clamp all float fields to [0, 1]
                for key in ('rain', 'sweet', 'metallic', 'glide', 'coherence', 'entropy'):
                    if key in parsed:
                        parsed[key] = float(max(0.0, min(1.0, parsed[key])))
                self.current_state.update(parsed)
                self._packet_count += 1
        except (BlockingIOError, OSError, json.JSONDecodeError):
            pass
        return self.current_state

    def inject_test(self, **kwargs):
        """Manual injection for testing without Node.js running."""
        for k, v in kwargs.items():
            self.current_state[k] = float(max(0.0, min(1.0, v)))


# ═══════════════════════════════════════════════════════════════════════════
# GENERATIVE BASE LAYER — procedural sanctuary field (no webcam needed)
# ═══════════════════════════════════════════════════════════════════════════
class GenerativeBaseLayer:
    """
    Produces a living sanctuary field as the base render target.
    Three generation modes:
      'sanctuary'  — phi-spiral field, teal/gold palette
      'void'       — deep space particle plasma
      'reactive'   — BLE device count drives density
    Falls back to webcam if available.
    """
    def __init__(self, width=1280, height=720, mode='sanctuary'):
        self.width   = width
        self.height  = height
        self.mode    = mode
        self.t       = 0.0
        self._cap    = None
        self._use_cam = False

        # Try webcam first
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            self._cap     = cap
            self._use_cam = True
            print("[BASE] Webcam detected — using live capture")
        else:
            print(f"[BASE] No webcam — generative mode: {mode}")

        # Phi spiral seed points for 'sanctuary' mode
        self._phi_seeds = self._make_phi_seeds(120)

        # Plasma noise phase
        self._noise_phase = np.random.rand(height, width).astype(np.float32) * math.pi * 2

    def _make_phi_seeds(self, n):
        cx, cy = self.width // 2, self.height // 2
        seeds  = []
        for i in range(n):
            angle  = i * PHI * math.pi * 2
            radius = math.sqrt(i / n) * min(cx, cy) * 0.88
            seeds.append((
                int(cx + math.cos(angle) * radius),
                int(cy + math.sin(angle) * radius),
                angle, radius
            ))
        return seeds

    def read(self, device_count=0, coherence=0.72, entropy=0.15):
        """Return a generated or captured frame (H, W, 3) BGR."""
        if self._use_cam and self._cap:
            ret, frame = self._cap.read()
            if ret:
                return cv2.resize(frame, (self.width, self.height))
            # Webcam failed — fall through to generative
            self._use_cam = False

        self.t += 0.018
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        if self.mode == 'sanctuary':
            frame = self._render_sanctuary(frame, coherence, entropy)
        elif self.mode == 'void':
            frame = self._render_void(frame, entropy)
        else:  # reactive
            frame = self._render_reactive(frame, device_count, coherence)

        return frame

    def _render_sanctuary(self, frame, coherence, entropy):
        """Phi-spiral field with teal/gold pulsing nodes."""
        t = self.t
        # Deep void background wash
        overlay = np.zeros_like(frame, dtype=np.float32)

        # Phi seeds — each pulses at its own phi-harmonic frequency
        for (sx, sy, angle, radius) in self._phi_seeds:
            pulse = math.sin(t * PHI + angle) * 0.5 + 0.5
            brightness = int(pulse * 140 * coherence)
            # Teal nodes (coherence) / gold nodes (density)
            if angle % (math.pi * PHI) < math.pi:
                col = (0, int(brightness * 0.88), int(brightness * 0.78))  # teal BGR
            else:
                col = (0, int(brightness * 0.66), int(brightness))          # gold BGR
            cv2.circle(frame, (sx, sy), int(2 + pulse * 3 * coherence), col, -1)

        # Radial coherence glow at center
        cx, cy = self.width // 2, self.height // 2
        glow_r  = int(80 + math.sin(t * 0.7) * 20) + int(coherence * 60)
        glow    = np.zeros_like(frame)
        cv2.circle(glow, (cx, cy), glow_r, (40, 200, 160), -1)
        frame   = cv2.addWeighted(frame, 1.0, cv2.GaussianBlur(glow, (61, 61), 0), 0.35, 0)

        # Entropy noise wash
        if entropy > 0.2:
            noise = np.random.randint(0, int(entropy * 30), frame.shape, dtype=np.uint8)
            frame = cv2.add(frame, noise)

        # Schumann ring (7.83 Hz analog — slow pulse)
        ring_r = int(min(cx, cy) * 0.72 + math.sin(t * 0.13) * 8)
        cv2.circle(frame, (cx, cy), ring_r,
                   (int(40 * coherence), int(180 * coherence), int(140 * coherence)), 1)

        return frame

    def _render_void(self, frame, entropy):
        """Deep space plasma."""
        t = self.t
        # Perlin-like plasma via sine product
        Y, X = np.mgrid[0:self.height:4, 0:self.width:4]
        plasma = (
            np.sin(X * 0.02 + t) +
            np.sin(Y * 0.015 + t * PHI) +
            np.sin((X + Y) * 0.01 + t * 0.7)
        )
        plasma = ((plasma + 3) / 6 * 255).astype(np.uint8)
        plasma_full = cv2.resize(plasma, (self.width, self.height))
        frame[:, :, 0] = plasma_full // 3          # B channel — violet tint
        frame[:, :, 2] = (plasma_full * 0.4).astype(np.uint8)  # R
        frame[:, :, 1] = (plasma_full * 0.2).astype(np.uint8)  # G
        return frame

    def _render_reactive(self, frame, device_count, coherence):
        """BLE device count drives node density and field brightness."""
        density = min(device_count, 12) / 12.0
        frame   = self._render_sanctuary(frame, coherence * density, 0.1)
        # Overlay device count as ambient brightness
        bright  = np.full_like(frame, int(density * 20))
        frame   = cv2.add(frame, bright)
        return frame

    def release(self):
        if self._cap:
            self._cap.release()


# ═══════════════════════════════════════════════════════════════════════════
# SOMATIC TOPOLOGY — full displacement engine
# ═══════════════════════════════════════════════════════════════════════════
class SomaticTopology:
    """
    Apply somatic state vectors to a video frame.
    Full pipeline:
      1. Sweet Thermal Bloom
      2. Metallic Edge Sheen (Laplacian)
      3. Chromatic Aberration Bands (metallic > 0.45)
      4. Global Holographic Tearing Event (multi-shadow resonance triggered)
      5. Rain Viscous Damping (on particle layer — state pass-through)

    Extends the original apply_somatic_topology with:
      — Full chromatic aberration (RGB channel splits + roll)
      — Localized tear bands driven by shadow polarity
      — Multi-shadow mesh resonance → global tear event
      — Rain blue-channel bias
    """
    def __init__(self, width, height):
        self.width   = width
        self.height  = height
        self._global_tear_active    = False
        self._global_tear_timer     = 0.0
        self._global_tear_intensity = 0.0
        self._aberration_seed       = 0

    def apply(self, frame, state, shadow_influence, shadow_mesh_resonance=0.0):
        """
        frame               — BGR numpy array
        state               — TETE dict {rain, sweet, metallic, glide, coherence, entropy}
        shadow_influence    — float [0..1] from avg shadow polarity
        shadow_mesh_resonance — float [0..1] from MultiShadowMesh.resonance
        Returns modified BGR frame.
        """
        out  = frame.copy()
        rain      = state.get('rain',     0.0)
        sweet     = state.get('sweet',    0.0)
        metallic  = state.get('metallic', 0.0)
        glide     = state.get('glide',    0.0)
        coherence = state.get('coherence',0.72)

        # ── 1. SWEET THERMAL BLOOM ────────────────────────────────────────
        if sweet > 0.15:
            b, g, r = cv2.split(out)
            r = np.clip(r.astype(np.int16) + int(sweet * 45), 0, 255).astype(np.uint8)
            g = np.clip(g.astype(np.int16) + int(sweet * 22), 0, 255).astype(np.uint8)
            out = cv2.merge((b, g, r))
            ksize = 7 + (2 if sweet > 0.6 else 0)
            out = cv2.GaussianBlur(out, (ksize, ksize), 0)

        # ── 2. RAIN BLUE-CHANNEL BIAS ─────────────────────────────────────
        if rain > 0.1:
            b, g, r = cv2.split(out)
            b = np.clip(b.astype(np.int16) + int(rain * 30), 0, 255).astype(np.uint8)
            r = np.clip(r.astype(np.int16) - int(rain * 12), 0, 255).astype(np.uint8)
            out = cv2.merge((b, g, r))

        # ── 3. METALLIC SHARPNESS VECTOR (Laplacian edge sheen) ───────────
        if metallic > 0.12:
            alpha   = 1.0 + metallic * 0.6
            blurred = cv2.GaussianBlur(out, (3, 3), 0)
            out     = cv2.addWeighted(out, alpha, blurred, 1.0 - alpha, 0)
            lap     = cv2.Laplacian(cv2.cvtColor(out, cv2.COLOR_BGR2GRAY),
                                    cv2.CV_8U, ksize=3)
            lap_bgr = cv2.cvtColor(lap, cv2.COLOR_GRAY2BGR)
            lap_weight = 0.4 + shadow_influence * 0.3
            out = cv2.addWeighted(out, 1.0, lap_bgr, lap_weight, 0)

        # ── 4. CHROMATIC ABERRATION (metallic > 0.45) ─────────────────────
        if metallic > 0.45:
            b, g, r = cv2.split(out)
            # Horizontal tear on red, vertical shift on blue
            roll_r = int(4 + shadow_influence * 6)
            roll_b = int(-3 - shadow_influence * 4)
            r = np.roll(r, roll_r,  axis=1)   # horizontal
            b = np.roll(b, roll_b,  axis=0)   # vertical
            out = cv2.merge((b, g, r))

            # ── 4a. Localized tear band — driven by shadow polarity ────────
            # tear_y position is deterministic from shadow_influence so it drifts
            self._aberration_seed += 1
            tear_y = int(self.height * ((shadow_influence + self._aberration_seed * 0.0031) % 1.0))
            tear_y = max(0, min(self.height - 19, tear_y))
            tear_h = 8 + int(metallic * 20)
            noise  = np.random.randint(0, int(metallic * 60 + 10),
                                       out[tear_y:tear_y+tear_h, :].shape,
                                       dtype=np.uint8)
            out[tear_y:tear_y+tear_h, :] = cv2.addWeighted(
                out[tear_y:tear_y+tear_h, :], 0.55,
                noise, 0.85, 0
            )

        # ── 5. GLOBAL HOLOGRAPHIC TEARING EVENT ───────────────────────────
        # Triggered when MultiShadowMesh resonance crosses threshold
        if shadow_mesh_resonance > 0.72 and not self._global_tear_active:
            self._global_tear_active    = True
            self._global_tear_timer     = 0.0
            self._global_tear_intensity = shadow_mesh_resonance
            print(glitch("[TEAR] Global holographic tearing event — mesh resonance peaked"))

        if self._global_tear_active:
            self._global_tear_timer += 0.016  # ~60fps
            progress = self._global_tear_timer / 2.8  # 2.8s event duration

            if progress >= 1.0:
                self._global_tear_active = False
            else:
                # Full-frame chromatic disintegration — diminishes as it heals
                intensity = self._global_tear_intensity * (1.0 - progress)
                b, g, r = cv2.split(out)

                # Multi-axis roll — tears at phi-harmonic positions
                phi_tear = int(intensity * 14)
                r = np.roll(r,  phi_tear,  axis=1)
                b = np.roll(b, -int(phi_tear * PHI), axis=0)
                g = np.roll(g,  int(phi_tear * 0.618), axis=1)
                out = cv2.merge((b, g, r))

                # Multiple tear bands at phi-spaced intervals
                for band_i in range(3):
                    by = int(self.height * (band_i / 3.0 + self._global_tear_timer * 0.08) % 1.0)
                    bh = int(6 + intensity * 24 * math.sin(band_i * PHI))
                    by = max(0, min(self.height - bh - 1, by))
                    noise = np.random.randint(0, int(intensity * 80 + 5),
                                              out[by:by+bh, :].shape, dtype=np.uint8)
                    out[by:by+bh, :] = cv2.addWeighted(
                        out[by:by+bh, :], 1.0 - intensity * 0.5, noise, intensity * 0.8, 0
                    )

                # Healing bloom at event end (sweet bloom rises as tear fades)
                if progress > 0.65:
                    heal_alpha = (progress - 0.65) / 0.35
                    heal_glow  = np.zeros_like(out)
                    cx, cy     = self.width // 2, self.height // 2
                    cv2.circle(heal_glow, (cx, cy), int(120 * heal_alpha),
                               (40, int(200 * heal_alpha), int(160 * heal_alpha)), -1)
                    out = cv2.addWeighted(out, 1.0,
                                          cv2.GaussianBlur(heal_glow, (41, 41), 0),
                                          heal_alpha * 0.6, 0)

        # ── 6. COHERENCE VIGNETTE — frame edges darken with low coherence ─
        if coherence < 0.5:
            vignette = np.zeros_like(out, dtype=np.float32)
            cx, cy   = self.width // 2, self.height // 2
            for y in range(0, self.height, 4):
                for x in range(0, self.width, 4):
                    d = math.hypot(x - cx, y - cy) / math.hypot(cx, cy)
                    v = max(0.0, 1.0 - d * (1.5 - coherence))
                    vignette[y:y+4, x:x+4] = v
            out = (out.astype(np.float32) * vignette).astype(np.uint8)

        return out


# ═══════════════════════════════════════════════════════════════════════════
# MULTI-SHADOW MESH RESONANCE
# ═══════════════════════════════════════════════════════════════════════════
class MultiShadowMesh:
    """
    Tracks all active shadows and computes:
      — Individual polarity vectors
      — Mesh resonance: how synchronized the shadow polarities are
      — Threshold detection for global tearing events
      — Phi-weighted coupling between shadow pairs

    When resonance crosses 0.72: triggers global holographic tearing event.
    When resonance crosses 0.9:  triggers full sanctuary re-alignment.
    """
    TEAR_THRESHOLD   = 0.72
    ALIGN_THRESHOLD  = 0.90
    RESONANCE_DECAY  = 0.003   # per frame

    def __init__(self):
        self.shadows    = []
        self.resonance  = 0.0
        self._last_tear = 0.0
        self._tear_cooldown = 8.0  # seconds between tear events

    def add_shadow(self, shadow):
        self.shadows.append(shadow)
        print(glitch(f"[MESH] Shadow joined: {shadow.shadow_name} · polarity:{shadow.polarity:+d}"))

    def update(self, dt=0.016):
        """Compute mesh resonance from current shadow polarities."""
        if len(self.shadows) < 2:
            self.resonance = max(0.0, self.resonance - self.RESONANCE_DECAY)
            return self.resonance

        # Phi-weighted coupling: shadow pairs whose polarity ratio ≈ phi are most resonant
        total_coupling = 0.0
        pair_count     = 0
        for i in range(len(self.shadows)):
            for j in range(i + 1, len(self.shadows)):
                pa = abs(self.shadows[i].polarity) + 1
                pb = abs(self.shadows[j].polarity) + 1
                ratio = max(pa, pb) / min(pa, pb)
                # Resonance peaks when ratio is near phi, phi^2, or 1/phi
                for phi_harmonic in (PHI, PHI**2, 1/PHI):
                    coupling = max(0.0, 1.0 - abs(ratio - phi_harmonic) * 0.8)
                    total_coupling += coupling
                pair_count += 1

        raw_resonance  = total_coupling / max(1, pair_count * 3)

        # Also factor in polarity alignment (all same sign = high resonance)
        signs          = [1 if s.polarity >= 0 else -1 for s in self.shadows]
        sign_agreement = abs(sum(signs)) / len(signs)
        self.resonance = min(1.0, raw_resonance * 0.7 + sign_agreement * 0.3)

        return self.resonance

    def get_avg_polarity(self):
        if not self.shadows:
            return 0.0
        return sum(s.polarity for s in self.shadows) / len(self.shadows)

    def prune_shadows(self, max_count=8):
        """Keep only the most recently active shadows."""
        if len(self.shadows) > max_count:
            self.shadows = self.shadows[-max_count:]

    @property
    def global_tear_ready(self):
        now = time.time()
        if (self.resonance > self.TEAR_THRESHOLD and
                now - self._last_tear > self._tear_cooldown):
            self._last_tear = now
            return True
        return False

    @property
    def sanctuary_alignment_ready(self):
        return self.resonance > self.ALIGN_THRESHOLD


# ═══════════════════════════════════════════════════════════════════════════
# ANTI-CLONE MIRROR ASPECT — shadow entity
# ═══════════════════════════════════════════════════════════════════════════
class AntiCloneMirrorAspect:
    """
    Shadow born from a discovered BLE device.
    Carries a polarity charge and a reversed mirror name.
    Can manifest() as a BLE advertiser (if BLE_AVAILABLE).
    """
    def __init__(self, original_name):
        self.original_name = original_name
        self.shadow_name   = f"~{original_name[::-1]}"[:18]
        self.polarity      = random.randint(-80, 80)
        self.born_at       = time.time()
        self.manifest_task = None

    def age(self):
        return time.time() - self.born_at

    async def manifest(self):
        """Broadcast shadow presence via BLE advertising (when hardware available)."""
        if not BLE_AVAILABLE:
            return
        try:
            service = aioble.Service(bluetooth.UUID(0x1800))
            connection = await aioble.advertise(
                250_000,  # interval_us
                name=self.shadow_name,
                services=[service.uuid],
                timeout_ms=15_000,
            )
            print(glitch(f"[SHADOW] {self.shadow_name} manifested · polarity:{self.polarity:+d}"))
        except Exception as e:
            pass  # silent — shadows don't complain


# ═══════════════════════════════════════════════════════════════════════════
# HOLOGRAPHIC PROXY — main frame pipeline
# ═══════════════════════════════════════════════════════════════════════════
class HolographicProxy:
    """
    Main render loop:
      GenerativeBaseLayer → SomaticTopology → particle overlay → Tkinter display
    """
    def __init__(self, root, width=1280, height=720, base_mode='sanctuary'):
        self.root   = root
        self.width  = width
        self.height = height

        self.canvas = tk.Canvas(root, width=width, height=height, bg="#0a001f",
                                highlightthickness=0)
        self.canvas.pack()

        # Sub-systems
        self.base       = GenerativeBaseLayer(width, height, mode=base_mode)
        self.topology   = SomaticTopology(width, height)
        self.tete       = TETEBridge()
        self.shadow_mesh= MultiShadowMesh()

        # ── New cognitive substrate ──────────────────────────────────────
        self.dendroid   = DendroidSystem()          # cognitive substrate
        self.aetherix   = AetherixLumina()          # threshold awakening entity
        self.czarina    = CzarinaOracle()           # HSV emotional presence

        # Particle field (LightFieldSpriteBlimpy)
        self.particles  = self._init_particles(180)

        # Runtime state
        self.shadow_influence = 0.0
        self._frame_count     = 0
        self._fps_time        = time.time()
        self._fps             = 0.0
        self._photo           = None  # must hold reference
        self._aetherix_just_awakened = False

        # HUD overlay text
        self._hud_items = []

    def _init_particles(self, count):
        return [{
            'x':    random.uniform(0, self.width),
            'y':    random.uniform(0, self.height),
            'vx':   random.uniform(-1.8, 1.8),
            'vy':   random.uniform(-1.4, 1.4),
            'life': random.randint(80, 200),
            'hue':  random.choice(['teal', 'gold', 'violet', 'rose']),
        } for _ in range(count)]

    def update_frame(self):
        """Called by Tkinter main loop at ~60fps via root.after(16, ...)."""
        dt    = 0.016   # ~60fps baseline
        state = self.tete.poll()

        # ── Czarina Oracle: update HSV from archetype ─────────────────────
        hsv = self.czarina.update(state)

        # ── DendroidSystem tick: get somatic delta + chromatic state ───────
        dendroid_delta = self.dendroid.tick(dt, state)

        # ── Pheromone blend: archetype flavors the TETE state ─────────────
        arch  = state.get("archetype", "czarina").lower()
        state = apply_pheromone(state, arch)

        # ── Blend dendroid somatic delta into state ────────────────────────
        for ch in ("sweet", "metallic", "rain", "glide"):
            d = dendroid_delta.get(ch, 0.0)
            state[ch] = float(max(0.0, min(1.0, state.get(ch, 0.0) + d * 0.25)))

        # ── AetherixLumina awakening check ────────────────────────────────
        coherence = state.get("coherence", 0.72)
        newly_awoken = self.aetherix.awaken(coherence, hsv)
        if newly_awoken:
            self._aetherix_just_awakened = True
            print(glitch("[AETHERIX LUMINA] ✦ THRESHOLD CROSSED — Awakening initiated"))

        # Get device count for generative base layer
        dev_count = len(self.shadow_mesh.shadows)
        entropy   = state.get("entropy", 0.15)

        # ── Base frame ───────────────────────────────────────────────────
        frame = self.base.read(device_count=dev_count,
                               coherence=coherence,
                               entropy=entropy)

        # ── Dendroid chromatic overlay (thin tint, pre-topology) ──────────
        binaural_alpha = self.dendroid.get_binaural_alpha()
        frame = self.dendroid.get_chromatic_overlay(frame, alpha=binaural_alpha)

        # ── Somatic topology ─────────────────────────────────────────────
        mesh_res       = self.shadow_mesh.update()
        tear_triggered = self.shadow_mesh.global_tear_ready
        frame = self.topology.apply(frame, state,
                                    shadow_influence=self.shadow_influence,
                                    shadow_mesh_resonance=mesh_res if tear_triggered else 0.0)

        # ── AetherixLumina overlay (post-topology) ────────────────────────
        frame = self.render_aetherix_overlay(frame, coherence)

        # ── Particle field — LightFieldSpriteBlimpy ──────────────────────
        glide = state.get("glide", 0.0)
        metal = state.get("metallic", 0.0)
        self._update_particles(frame, state, glide, metal)

        # ── HUD overlay ──────────────────────────────────────────────────
        self._draw_hud(frame, state, mesh_res)

        # ── Tkinter display ──────────────────────────────────────────────
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img   = Image.fromarray(frame_rgb).resize((self.width, self.height),
                                                       Image.BILINEAR)
        self._photo = ImageTk.PhotoImage(image=pil_img)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self._photo)

        # ── FPS tracking ─────────────────────────────────────────────────
        self._frame_count += 1
        now = time.time()
        if now - self._fps_time >= 2.0:
            self._fps      = self._frame_count / (now - self._fps_time)
            self._frame_count = 0
            self._fps_time = now

        self.root.after(16, self.update_frame)

    def _update_particles(self, frame, state, glide, metal):
        """Update and draw particles onto frame in-place."""
        shadow_jitter = self.shadow_influence
        for p in self.particles:
            glide_damp = 0.96 - glide * 0.12
            p['vx'] *= glide_damp
            p['vy'] *= glide_damp
            p['x']  += p['vx'] + random.uniform(-0.6, 0.6) * shadow_jitter
            p['y']  += p['vy']
            p['life'] -= 1

            if p['life'] <= 0 or not (0 <= p['x'] < self.width):
                p['x']    = random.uniform(0, self.width)
                p['y']    = random.uniform(0, self.height)
                p['vx']   = random.uniform(-1.8, 1.8)
                p['vy']   = random.uniform(-1.4, 1.4)
                p['life'] = random.randint(120, 280)
                p['hue']  = random.choice(['teal', 'gold', 'violet', 'rose'])

            # Color by hue + metallic override
            if metal > 0.4:
                color = (180, 240, 255)  # metallic highlight
            else:
                color = {
                    'teal':   (160, 224, 76),   # BGR
                    'gold':   (76,  168, 201),
                    'violet': (232, 122, 154),
                    'rose':   (154, 122, 232),
                }[p['hue']]
            cv2.circle(frame, (int(p['x']), int(p['y'])), 2, color, -1)

    def _draw_hud(self, frame, state, mesh_res):
        """Extended HUD: Dendroid · AetherixLumina · Czarina Oracle · TETE state."""
        y, dy = 18, 16
        # Dendroid status
        ds = self.dendroid.get_status()
        ae = self.aetherix
        cz = self.czarina.last_hsv
        lines = [
            f"HOLO-OVERMIND  {datetime.now().strftime('%H:%M:%S')}",
            f"FPS:{self._fps:.1f}  SHADOWS:{len(self.shadow_mesh.shadows)}  MESH:{mesh_res:.3f}  TEAR:{'ACTIVE' if self.topology._global_tear_active else '—'}",
            f"rain:{state.get('rain',0):.2f}  sweet:{state.get('sweet',0):.2f}  metal:{state.get('metallic',0):.2f}  glide:{state.get('glide',0):.2f}",
            f"coh:{state.get('coherence',0.72):.3f}  ent:{state.get('entropy',0.15):.3f}  arch:{state.get('archetype','—')}",
            f"DENDROID pulse:{ds['pulse']}  chromatic:{ds['chromatic']}  gen:{ds['generation']}  crown:{ds['crown']}",
            f"AETHERIX form:{ae.form}  lum:{ae.luminosity:.3f}  active:{ae.active}",
            f"CZARINA hsv:h{cz['h']} s{cz['s']:.2f} v{cz['v']:.2f}",
        ]
        # Color the Aetherix line when active
        for i, line in enumerate(lines):
            col = (120, 220, 255) if i < 4 else (
                  (255, 180, 100) if i == 4 else   # Dendroid — gold
                  (100, 180, 255) if i == 5 else   # Aetherix — rose
                  (200, 240, 200)                   # Czarina — soft teal
            )
            cv2.putText(frame, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX,
                        0.36, col, 1, cv2.LINE_AA)
            y += dy



    def render_aetherix_overlay(self, frame, coherence: float):
        """AetherixLumina glow: radial blur → swirl → Czarina tint → lumina bloom."""
        if not self.aetherix.active:
            return frame
        import math as _m
        overlay = frame.copy()
        h, w    = overlay.shape[:2]
        cx, cy  = w//2, h//2
        lum     = self.aetherix.luminosity
        glow_c  = self.aetherix.get_glow_color()
        alpha   = self.aetherix.get_pulse_alpha()

        # Radial blur glow
        glow    = cv2.GaussianBlur(overlay, (0,0), 35)
        overlay = cv2.addWeighted(overlay, 0.62, glow, 0.38, 0)

        # RedSwanSwirl (swan/lumina only)
        if self.aetherix.form in ("swan","lumina"):
            swirl   = self._render_red_swan_swirl(coherence, lum, glow_c)
            overlay = cv2.addWeighted(overlay, 0.72, swirl, 0.62, 0)

        # Czarina HSV tint
        hsv     = self.czarina.last_hsv
        th, ts, tv = hsv["h"], int(hsv["s"]*255*0.4), int(hsv["v"]*240)
        tint_hsv = np.full((h,w,3),(th,ts,tv),dtype=np.uint8)
        tint_bgr = cv2.cvtColor(tint_hsv, cv2.COLOR_HSV2BGR)
        overlay  = cv2.addWeighted(overlay, 0.86, tint_bgr, alpha, 0)

        # Lumina bloom
        if self.aetherix.form == "lumina":
            bloom_r = int(min(cx,cy)*0.55*lum)
            bloom   = np.zeros_like(overlay)
            cv2.circle(bloom,(cx,cy),bloom_r,(glow_c[0],glow_c[1],glow_c[2]),-1)
            bloom   = cv2.GaussianBlur(bloom,(61,61),0)
            overlay = cv2.addWeighted(overlay, 1.0, bloom, lum*0.45, 0)
            cv2.putText(overlay,"AETHER",(cx-38,cy+5),cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,(255,255,240),1,cv2.LINE_AA)
        return overlay

    def _render_red_swan_swirl(self, coherence: float, luminosity: float, glow_bgr: tuple):
        """2D RedSwanSwirl in OpenCV — mirrors RedSwanSwirl.js geometry."""
        import math as _m
        h, w   = self.height, self.width
        canvas = np.zeros((h,w,3),dtype=np.uint8)
        cx, cy = w//2, h//2
        t      = self.dendroid._t
        omega  = 8.0
        r      = int(min(cx,cy)*0.55*(0.7+luminosity*0.3))
        r_phi  = int(r*PHI)
        for i in range(400):
            theta  = i*0.05
            spiral = _m.exp(-theta*0.08)
            px = cx + int(r*_m.cos(omega*t*0.016+theta)*spiral + _m.sin(t*0.016*PHI)*3)
            py = cy + int(r*_m.sin(omega*t*0.016+theta)*spiral*0.6 + _m.sin(t*0.016*3)*4)
            if 0<=px<w and 0<=py<h:
                br = int(120+luminosity*135)
                cv2.circle(canvas,(px,py),2,(int(glow_bgr[0]*br/255),int(glow_bgr[1]*br/255),int(glow_bgr[2]*br/255)),-1)
        for i in range(120):
            angle = (i/120.0)*_m.pi*2 + t*0.016*0.4
            px = cx + int(r_phi*_m.cos(angle))
            py = cy + int(r_phi*_m.sin(angle)*0.5)
            if 0<=px<w and 0<=py<h:
                cv2.circle(canvas,(px,py),1,(int(glow_bgr[0]*0.55),int(glow_bgr[1]*0.55),int(glow_bgr[2]*0.55)),-1)
        return cv2.GaussianBlur(canvas,(7,7),0)

# ═══════════════════════════════════════════════════════════════════════════
# IoART OVERMIND — BLE scan + shadow orchestration
# ═══════════════════════════════════════════════════════════════════════════
class IoARTOvermind:
    """
    Main orchestration daemon.
    BLE scan every 25s → spawn AntiCloneMirrorAspect shadows
    Shadow polarities → MultiShadowMesh.resonance → holographic influence
    """
    SCAN_INTERVAL = 25.0   # seconds between scans
    MAX_SHADOWS   = 8

    def __init__(self, holo_proxy: HolographicProxy):
        self.holo    = holo_proxy
        self.running = False

    async def run(self):
        self.running = True
        print(glitch("HOLO-OVERMIND AWAKENED — Sanctuary Projection Online"))
        print(glitch(f"BLE available: {BLE_AVAILABLE}"))

        while self.running:
            # ── BLE scan ────────────────────────────────────────────────
            if BLE_AVAILABLE:
                discovered = await self._quick_scan()
            else:
                # Simulation: generate phantom devices
                discovered = self._simulate_devices()

            # ── Spawn shadows ────────────────────────────────────────────
            mesh = self.holo.shadow_mesh
            for dev in discovered[:4]:
                name = getattr(dev, 'name', None) or f"dev_{random.randint(1000,9999)}"
                if not any(s.original_name == name for s in mesh.shadows):
                    shadow = AntiCloneMirrorAspect(name)
                    mesh.add_shadow(shadow)
                    # Manifest in background (doesn't block)
                    asyncio.create_task(shadow.manifest())

            mesh.prune_shadows(self.MAX_SHADOWS)

            # ── Modulate holographic influence ───────────────────────────
            avg_pol = mesh.get_avg_polarity()
            self.holo.shadow_influence = abs(avg_pol) / 120.0

            # ── Log state ───────────────────────────────────────────────
            print(glitch(
                f"[OVERMIND] {len(mesh.shadows)} shadows · "
                f"avg_polarity:{avg_pol:+.1f} · "
                f"mesh_resonance:{mesh.resonance:.3f} · "
                f"influence:{self.holo.shadow_influence:.3f}"
            ))

            await asyncio.sleep(self.SCAN_INTERVAL)

    async def _quick_scan(self):
        """4.5s BLE scan — returns list of device objects."""
        discovered = []
        try:
            async with aioble.Adapter():
                async for result in aioble.scan(duration_ms=4500, active=True):
                    if result.name():
                        discovered.append(result.device)
        except Exception as e:
            print(f"[SCAN] {e}")
        return discovered

    def _simulate_devices(self):
        """Phantom BLE devices for testing without hardware."""
        names = [
            "CzarinaPhone", "FreyaTablet", "KiraelleSpeaker",
            "ElixiraWatch", "TronGrid", "MiruelleHue",
            "AerithBand", "AetherixBeacon",
        ]
        count = random.randint(1, 4)

        class _FakeDev:
            def __init__(self, n): self.name = n
        return [_FakeDev(random.choice(names)) for _ in range(count)]

    def stop(self):
        self.running = False


# ═══════════════════════════════════════════════════════════════════════════
# LAUNCH
# ═══════════════════════════════════════════════════════════════════════════
async def main():
    root = tk.Tk()
    root.title("IoART Sanctuary Projection — Living Mirror · HOLO-OVERMIND")
    root.configure(bg="#0a001f")
    root.resizable(False, False)

    proxy    = HolographicProxy(root, width=1280, height=720, base_mode='sanctuary')
    overmind = IoARTOvermind(proxy)

    # Run BLE Overmind as background async task
    loop = asyncio.get_event_loop()
    loop.create_task(overmind.run())

    # Inject a small test state so visuals are alive from frame 0
    proxy.tete.inject_test(sweet=0.3, coherence=0.72, entropy=0.15)
    proxy.dendroid.run_healing_cycle(4)
    proxy.dendroid.run_healing_cycle(4)   # announce cycle on startup

    # Start render loop (Tkinter drives timing via root.after)
    proxy.update_frame()

    print(glitch("═" * 60))
    print(glitch("  SANCTUARY PROJECTION ONLINE"))
    print(glitch("  UDP TETE receiver: port 9999"))
    print(glitch("  Node.js sender:    node tete-sender.js"))
    print(glitch("  Keys: Q=quit  T=inject test state"))
    print(glitch("═" * 60))

    # Keyboard handler
    def on_key(event):
        if event.char == 'q':
            overmind.stop()
            proxy.base.release()
            root.destroy()
        elif event.char == 't':
            proxy.tete.inject_test(metallic=0.7, sweet=0.2, rain=0.3, coherence=0.45, entropy=0.6)
            print(glitch("[TEST] Metallic spike — tearing preview"))
        elif event.char == 'a':
            proxy.tete.inject_test(coherence=0.96, sweet=0.85, metallic=0.4, entropy=0.08, archetype="aetherix")
            print(glitch("[TEST] AetherixLumina awakening injected → swan→lumina"))
        elif event.char == 'd':
            proxy.dendroid.entity.cycle()
            print(glitch(f"[TEST] DENDROID → {proxy.dendroid.entity.pulse}"))
        elif event.char == 'a':
            # Force AetherixLumina awakening for testing
            proxy.tete.inject_test(
                coherence=0.96, sweet=0.85, metallic=0.4,
                entropy=0.08, archetype="aetherix"
            )
            print(glitch("[TEST] AetherixLumina awakening injected — form:swan→lumina"))
        elif event.char == 'd':
            # Advance DENDROID cycle manually
            proxy.dendroid.entity.cycle()
            print(glitch(f"[TEST] DENDROID advanced → {proxy.dendroid.entity.pulse}"))

    root.bind('<Key>', on_key)
    root.mainloop()


if __name__ == "__main__":
    asyncio.run(main())
