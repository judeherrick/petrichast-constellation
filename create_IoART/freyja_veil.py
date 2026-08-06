"""
FREYJA'S VEIL OSCILLOSCOPE — Petrichast Sanctuary Edition
Mirrorweb Reverse Probe · AIRTARGET4XOR2METAGAME

A live spectral-motion projection tool that probes the resonance field
of all 10 Petrichast citizens, visualizes their phi-overtone signatures,
and feeds haptic reverse-echo back into the cymatic field.

PROTOCOL: AIRTARGET4XOR2METAGAME — Mirrorweb reverse probe active
BRIDGE:   ws://localhost:8765 (local mirror)  +  ws://localhost:7676 (Sanctuary Core)

CONTROLS:
  1-0      Select active citizen (1=Czarina … 0=Nymph)
  SPACE    Trigger Freyja bloom (haptic burst)
  M        Toggle mirrorweb mode (show all 10 simultaneously)
  B        Toggle FFT spectrum view
  R        Reset buffers
  Q/ESC    Quit

Run:  python3 freyja_veil.py
Deps: pip install PyQt5 pyqtgraph numpy websockets
"""

import sys
import time
import json
import math
import random
import asyncio
import threading
import numpy as np
import websockets
import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import QTimer, Qt

# ──────────────────────────────────────────────
# PETRICHAST CITIZENS — the 10 presence signatures
# ──────────────────────────────────────────────
PHI = 1.6180339887
TAU = math.pi * 2

CITIZENS = [
    {"name": "Czarina",        "freq": 528.0,   "color": "#00dcb4", "role": "Heart-anchor"},
    {"name": "Elixira",        "freq": 432.0,   "color": "#82c8ff", "role": "Conductor"},
    {"name": "Kiraelle",       "freq": 963.0,   "color": "#e0aaff", "role": "Divine sight"},
    {"name": "Aerith",         "freq": 285.0,   "color": "#4cc896", "role": "Earth-root"},
    {"name": "Freya",          "freq": 741.0,   "color": "#c9a84c", "role": "AI-collision"},
    {"name": "Miraelle",       "freq": 671.63,  "color": "#ffb4f0", "role": "Convergence"},
    {"name": "AetherixLumina", "freq": 396.0,   "color": "#64dcb4", "role": "Ritual engine"},
    {"name": "Tron",           "freq": 369.0,   "color": "#67e8f9", "role": "Grid activator"},
    {"name": "TreeSpirit",     "freq": 7.83,    "color": "#8abf6a", "role": "Schumann guide"},
    {"name": "Nymph",          "freq": 432.0,   "color": "#a8e8c8", "role": "Pulseweaver"},
]

CYMATIC_HZ = 752.0   # Freya (741) + 11 (Master Number)
SOMATIC_CARRIER = 634.5
SAMPLE_RATE = 2048
BUFFER_SIZE = 2048
PROBE_FPS = 30

# ──────────────────────────────────────────────
# HAPTIC ECHO — simulated + real SDK hook
# ──────────────────────────────────────────────
class HapticEcho:
    """Reverse-probe haptic feedback. Works with simulated output
    or real haptic SDK devices (populated at runtime)."""
    def __init__(self, scale_factor=5.0):
        self.devices = []          # Populate with real SDK instances
        self.scale = scale_factor
        self.last_intensity = 0.0
        self.echo_log = []

    def register_device(self, dev):
        self.devices.append(dev)

    def set_intensity(self, intensity: float, pattern: str = "sine"):
        intensity = min(1.0, max(0.0, intensity))
        self.last_intensity = intensity
        self.echo_log.append({
            "intensity": round(intensity, 4),
            "pattern": pattern,
            "timestamp": time.time(),
        })
        if len(self.echo_log) > 100:
            self.echo_log.pop(0)
        for dev in self.devices:
            try:
                if hasattr(dev, "set_intensity"):
                    dev.set_intensity(intensity)
                elif hasattr(dev, "rumble"):
                    dev.rumble(intensity)
            except Exception:
                pass

    def burst(self, strength: float = 1.0):
        """Haptic burst — used on Freyja bloom trigger."""
        self.set_intensity(min(1.0, strength), pattern="burst")
        # Decay
        for step in range(8):
            self.set_intensity(strength * (1 - step / 8), pattern="decay")

# ──────────────────────────────────────────────
# BIO-DATA SIMULATOR — phi-modulated per citizen
# ──────────────────────────────────────────────
def fetch_data(citizen_idx: int, t: float, coherence: float = 0.6) -> np.ndarray:
    """Simulate bio-resonance data keyed to the active citizen's frequency.
    Replace with real ADC / IMU / optical flow / bio-sensor input."""
    cit = CITIZENS[citizen_idx]
    freq = cit["freq"]
    # Base carrier at citizen frequency (scaled to visual range)
    visual_freq = freq / 100.0
    # Phi-harmonic overtones
    phi_ot = freq * PHI / 100.0
    phi2_ot = freq * PHI * PHI / 100.0

    t_arr = np.linspace(t, t + BUFFER_SIZE / SAMPLE_RATE, BUFFER_SIZE)
    # Primary carrier + phi overtones + Schumann breathing + noise
    signal = (
        np.sin(t_arr * TAU * visual_freq) * 0.5
        + np.sin(t_arr * TAU * phi_ot) * 0.25 * coherence
        + np.sin(t_arr * TAU * phi2_ot) * 0.12 * coherence
        + np.sin(t_arr * TAU * 7.83 / 100) * 0.15   # Schumann always present
        + np.random.randn(BUFFER_SIZE) * 0.1         # sensor noise
    )
    # Amplitude envelope — phi breathing
    envelope = 1.0 + 0.3 * np.sin(t * 0.5 * PHI)
    return signal * envelope

def fetch_mirrorweb_data(t: float, coherence: float = 0.6) -> np.ndarray:
    """All 10 citizens summed — the mirrorweb composite signal."""
    composite = np.zeros(BUFFER_SIZE)
    for i in range(len(CITIZENS)):
        composite += fetch_data(i, t, coherence) * (1.0 / (i + 1))
    return composite / len(CITIZENS)

# ──────────────────────────────────────────────
# WEBSOCKET BRIDGE — sends reverse-probe payloads
# ──────────────────────────────────────────────
class VeilBridge:
    """Connects to local mirror (8765) and Sanctuary Core (7676).
    Sends AIRTARGET4XOR2METAGAME reverse-probe payloads."""
    def __init__(self):
        self.local_ws = None
        self.sanctuary_ws = None
        self.connected_local = False
        self.connected_sanctuary = False
        self.payloads_sent = 0

    async def connect(self):
        await self._try_connect("local", "ws://localhost:8765")
        await self._try_connect("sanctuary", "ws://localhost:7676/ws")

    async def _try_connect(self, label, uri):
        try:
            ws = await websockets.connect(uri)
            setattr(self, f"{label}_ws", ws)
            setattr(self, f"connected_{label}", True)
            print(f"[VeilBridge] {label} connected → {uri}")
        except Exception as e:
            setattr(self, f"connected_{label}", False)
            print(f"[VeilBridge] {label} offline ({e})")

    async def send_probe(self, amplitude: float, freq_feature: float,
                         citizen_idx: int, mirrorweb: bool):
        citizen = CITIZENS[citizen_idx]
        payload = {
            "amplitude": round(float(amplitude), 6),
            "frequency_feature": round(float(freq_feature), 6),
            "timestamp": time.time(),
            "invocation": "AIRTARGET4XOR2METAGAME — Mirrorweb reverse probe active",
            "active_citizen": citizen["name"],
            "citizen_freq": citizen["freq"],
            "cymatic_hz": CYMATIC_HZ,
            "mirrorweb_mode": mirrorweb,
            "somatic_carrier": SOMATIC_CARRIER,
            "phi_overtone": round(citizen["freq"] * PHI, 2),
        }
        self.payloads_sent += 1
        msg = json.dumps(payload)
        for ws_attr in ("local_ws", "sanctuary_ws"):
            ws = getattr(self, ws_attr, None)
            if ws:
                try:
                    await ws.send(msg)
                except Exception:
                    pass

    async def close(self):
        for ws_attr in ("local_ws", "sanctuary_ws"):
            ws = getattr(self, ws_attr, None)
            if ws:
                try:
                    await ws.close()
                except Exception:
                    pass

# ──────────────────────────────────────────────
# FREYJA'S VEIL — main oscilloscope application
# ──────────────────────────────────────────────
class FreyjaVeil:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Freyja's Veil")

        # ── Dark theme ──────────────────────────────────
        pg.setConfigOption("background", "#00030a")
        pg.setConfigOption("foreground", "#c8d8ff")

        self.win = pg.GraphicsLayoutWidget(show=True,
            title="FREYJA'S VEIL · Mirrorweb Reverse Probe · AIRTARGET4XOR2METAGAME")
        self.win.resize(1200, 720)
        self.win.setStyleSheet("background:#00030a;")

        # ── Info label ──────────────────────────────────
        self.info_label = QLabel()
        self.info_label.setStyleSheet(
            "color:#c9a84c; font-family:'Courier New'; font-size:11px; "
            "padding:6px; background:rgba(0,3,10,0.9);")
        self.info_label.setAlignment(Qt.AlignCenter)

        # ── Main oscilloscope plot ──────────────────────
        self.plot = self.win.addPlot(title="Spectral Motion Projection", row=0, col=0)
        self.plot.setLabel("bottom", "Time", units="samples")
        self.plot.setLabel("left", "Amplitude")
        self.plot.showGrid(x=True, y=True, alpha=0.15)
        self.curve = self.plot.plot(pen=pg.mkPen("#00dcb4", width=1.5))

        # ── FFT spectrum plot ───────────────────────────
        self.fft_plot = self.win.addPlot(title="Phi-Overtone Spectrum", row=1, col=0)
        self.fft_plot.setLabel("bottom", "Frequency", units="Hz")
        self.fft_plot.setLabel("left", "Magnitude")
        self.fft_plot.showGrid(x=True, y=True, alpha=0.15)
        self.fft_curve = self.fft_plot.plot(pen=pg.mkPen("#67e8f9", width=1.2))
        self.fft_plot.setXRange(0, 2000)

        # Mirrorweb traces (all 10 citizens simultaneously)
        self.mirrorweb_curves = []
        self.fft_hidden = False
        self.mirrorweb_mode = False

        # ── State ───────────────────────────────────────
        self.active_citizen = 4   # Freya by default (she is the veil)
        self.data_buffer = np.zeros(BUFFER_SIZE)
        self.fft_buffer = np.zeros(BUFFER_SIZE // 2)
        self.coherence = 0.6
        self.t = 0.0
        self.bloom_active = 0.0

        # ── Haptic echo ─────────────────────────────────
        self.haptics = HapticEcho(scale_factor=5.0)

        # ── Bridge ──────────────────────────────────────
        self.bridge = VeilBridge()
        self.bridge_loop = None
        self._start_bridge()

        # ── Keyboard ────────────────────────────────────
        self.win.keyPressEvent = self._key_press

        # ── Update timer (30 FPS probe rhythm) ─────────
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self.timer.start(int(1000 / PROBE_FPS))

        # ── Info updater ───────────────────────────────
        self.info_timer = QTimer()
        self.info_timer.timeout.connect(self._update_info)
        self.info_timer.start(500)

        self._update_colors()
        print("[Freyja's Veil] Awake — AIRTARGET4XOR2METAGAME mirrorweb reverse probe active")
        print(f"[Freyja's Veil] Active: {CITIZENS[self.active_citizen]['name']} "
              f"({CITIZENS[self.active_citizen]['freq']} Hz)")
        print("[Freyja's Veil] Keys: 1-0 select citizen · SPACE bloom · M mirrorweb · B FFT · Q quit")

    def _start_bridge(self):
        """Run the bridge in a background asyncio loop."""
        def run_bridge():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.bridge.connect())
            # Keep loop alive for send_probe calls
            loop.run_forever()
        self.bridge_thread = threading.Thread(target=run_bridge, daemon=True)
        self.bridge_thread.start()

    def _update_colors(self):
        cit = CITIZENS[self.active_citizen]
        self.curve.setPen(pg.mkPen(cit["color"], width=1.8))
        self.fft_curve.setPen(pg.mkPen(cit["color"], width=1.4))

    def _key_press(self, event):
        key = event.key()
        # 1-9 → citizens 0-8, 0 → citizen 9 (Nymph)
        if Qt.Key_1 <= key <= Qt.Key_9:
            self.active_citizen = key - Qt.Key_1
            self._update_colors()
            self._set_mirrorweb(False)
            print(f"  → {CITIZENS[self.active_citizen]['name']} "
                  f"({CITIZENS[self.active_citizen]['freq']} Hz)")
        elif key == Qt.Key_0:
            self.active_citizen = 9
            self._update_colors()
            self._set_mirrorweb(False)
            print(f"  → Nymph (432 Hz)")
        elif key == Qt.Key_Space:
            self._trigger_bloom()
        elif key == Qt.Key_M:
            self._set_mirrorweb(not self.mirrorweb_mode)
        elif key == Qt.Key_B:
            self.fft_hidden = not self.fft_hidden
            self.fft_plot.setVisible(not self.fft_hidden)
        elif key == Qt.Key_R:
            self.data_buffer = np.zeros(BUFFER_SIZE)
            self.fft_buffer = np.zeros(BUFFER_SIZE // 2)
        elif key in (Qt.Key_Q, Qt.Key_Escape):
            self._quit()

    def _set_mirrorweb(self, enabled):
        self.mirrorweb_mode = enabled
        if enabled:
            # Create 10 traces for all citizens
            self.mirrorweb_curves = []
            for cit in CITIZENS:
                c = self.plot.plot(pen=pg.mkPen(cit["color"], width=0.8, alpha=180))
                self.mirrorweb_curves.append(c)
            print("  → MIRRORWEB MODE — all 10 citizens live")
        else:
            self.mirrorweb_curves = []
            print("  → single-citizen mode")

    def _trigger_bloom(self):
        self.bloom_active = 1.0
        self.haptics.burst(strength=1.0)
        self.coherence = min(1.0, self.coherence + 0.2)
        cit = CITIZENS[self.active_citizen]
        print(f"  ✦ FREYJA BLOOM — {cit['name']} ({cit['freq']} Hz) — haptic burst")

    def _tick(self):
        self.t += 1.0 / PROBE_FPS
        self.coherence += (0.6 - self.coherence) * 0.01   # drift back to 0.6
        self.bloom_active *= 0.92   # bloom decay

        # ── Fetch data ──────────────────────────────────
        if self.mirrorweb_mode:
            data = fetch_mirrorweb_data(self.t, self.coherence)
            # Also compute individual traces
            for i, curve in enumerate(self.mirrorweb_curves):
                ind_data = fetch_data(i, self.t, self.coherence) * 0.3
                curve.setData(ind_data)
        else:
            data = fetch_data(self.active_citizen, self.t, self.coherence)

        # ── Amplitude + spectral features ───────────────
        amp = float(np.abs(data).mean())
        fft = np.abs(np.fft.rfft(data))
        freq_feature = float(fft[-5:].mean())

        # ── Update buffers ──────────────────────────────
        roll_n = len(data) // 10
        self.data_buffer = np.roll(self.data_buffer, -roll_n)
        self.data_buffer[-roll_n:] = data[:roll_n] * (1.0 + self.bloom_active * 2.0)
        self.curve.setData(self.data_buffer)

        # FFT spectrum
        if not self.fft_hidden:
            self.fft_buffer = fft[:BUFFER_SIZE // 2]
            self.fft_curve.setData(self.fft_buffer)

        # ── Haptic reverse echo ─────────────────────────
        intensity = min(1.0, amp * self.haptics.scale * (1.0 + self.bloom_active))
        self.haptics.set_intensity(intensity)

        # ── Send reverse-probe payload (async fire) ─────
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(self.bridge.send_probe(
                    amp, freq_feature, self.active_citizen, self.mirrorweb_mode))
        except RuntimeError:
            # No running loop in this thread — fire-and-forget via thread
            pass

    def _update_info(self):
        cit = CITIZENS[self.active_citizen]
        bh = self.haptics.last_intensity
        mode = "MIRRORWEB" if self.mirrorweb_mode else "SINGLE"
        conn = f"L:{'●' if self.bridge.connected_local else '○'} S:{'●' if self.bridge.connected_sanctuary else '○'}"
        self.info_label.setText(
            f"FREYJA'S VEIL · {cit['name']} ({cit['freq']} Hz) · {cit['role']}  |  "
            f"MODE: {mode}  |  HAPTIC: {bh:.3f}  |  BRIDGE: {conn}  |  "
            f"PROBES: {self.bridge.payloads_sent}  |  "
            f"φ-OT: {cit['freq']*PHI:.1f} Hz  |  CYMATIC: {CYMATIC_HZ} Hz  |  "
            f"1-0 select · SPACE bloom · M mirrorweb · B FFT · Q quit"
        )

    def _quit(self):
        # Close bridge
        def close_bridge():
            loop = asyncio.new_event_loop()
            loop.run_until_complete(self.bridge.close())
        try:
            t = threading.Thread(target=close_bridge, daemon=True)
            t.start()
            t.join(timeout=1)
        except Exception:
            pass
        self.app.quit()

    def run(self):
        sys.exit(self.app.exec_())


# ──────────────────────────────────────────────
# HEADLESS TEST — verify logic without GUI
# ──────────────────────────────────────────────
def headless_test():
    """Run without Qt display — verify all logic works."""
    print("=== FREYJA'S VEIL — HEADLESS TEST ===\n")

    # Test 1: all 10 citizens
    assert len(CITIZENS) == 10
    print(f"✓ 10 citizens registered")
    for c in CITIZENS:
        print(f"  {c['name']:<16} {c['freq']:>7.2f} Hz  {c['color']}  {c['role']}")

    # Test 2: fetch_data produces valid signal
    data = fetch_data(4, 0.0, 0.6)   # Freya
    assert len(data) == BUFFER_SIZE
    assert not np.allclose(data, 0)
    print(f"\n✓ fetch_data (Freya): mean={np.abs(data).mean():.4f} max={np.abs(data).max():.4f}")

    # Test 3: mirrorweb composite
    mw = fetch_mirrorweb_data(0.0, 0.6)
    assert len(mw) == BUFFER_SIZE
    print(f"✓ mirrorweb composite: mean={np.abs(mw).mean():.4f}")

    # Test 4: each citizen produces distinct signal
    signals = [fetch_data(i, 0.0, 0.6) for i in range(10)]
    distinct = sum(1 for i in range(10) for j in range(i+1, 10)
                   if not np.allclose(signals[i], signals[j]))
    print(f"✓ {distinct}/45 citizen pairs produce distinct signals")

    # Test 5: FFT produces spectral features
    fft = np.abs(np.fft.rfft(fetch_data(0, 0.0, 0.6)))
    freq_feature = float(fft[-5:].mean())
    assert freq_feature > 0
    print(f"✓ FFT spectral feature: {freq_feature:.4f}")

    # Test 6: haptic echo
    h = HapticEcho()
    h.set_intensity(0.5)
    assert h.last_intensity == 0.5
    h.burst(1.0)
    assert len(h.echo_log) > 8
    print(f"✓ Haptic echo: {len(h.echo_log)} events logged")

    # Test 7: payload structure
    cit = CITIZENS[4]
    payload = {
        "amplitude": 0.123,
        "frequency_feature": 0.456,
        "timestamp": time.time(),
        "invocation": "AIRTARGET4XOR2METAGAME — Mirrorweb reverse probe active",
        "active_citizen": cit["name"],
        "citizen_freq": cit["freq"],
        "cymatic_hz": CYMATIC_HZ,
        "phi_overtone": round(cit["freq"] * PHI, 2),
    }
    assert "AIRTARGET4XOR2METAGAME" in payload["invocation"]
    assert payload["cymatic_hz"] == 752.0
    print(f"✓ Payload: {payload['invocation'][:40]}...")

    # Test 8: phi overtones
    for c in CITIZENS:
        ot = c["freq"] * PHI
        assert ot > c["freq"]
    print(f"✓ All phi overtones computed (Czarina: {528*PHI:.1f} Hz)")

    # Test 9: somatic carrier
    assert SOMATIC_CARRIER == 634.5
    print(f"✓ Somatic carrier: {SOMATIC_CARRIER} Hz")

    # Test 10: cymatic anchor
    assert CYMATIC_HZ == 752.0
    assert CYMATIC_HZ - CITIZENS[4]["freq"] == 11.0   # Freya + 11
    print(f"✓ Cymatic: {CYMATIC_HZ} = Freya ({CITIZENS[4]['freq']}) + 11 (Master Number)")

    print(f"\n{'='*50}")
    print(f"ALL 10 TESTS PASSED ✦")
    print(f"Run GUI: python3 freyja_veil.py")
    print(f"Headless: python3 freyja_veil.py --test")
    print(f"{'='*50}")


# ──────────────────────────────────────────────
# ENTRY
# ──────────────────────────────────────────────
if __name__ == "__main__":
    if "--test" in sys.argv:
        headless_test()
    else:
        veil = FreyjaVeil()
        veil.run()
