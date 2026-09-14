"""
HARMONIC THALAMUS PHASOR — Door B Implementation
==================================================
The satellite's resonance feeds back into the global atmosphere.

This module formalizes the BIOGHOST CONTENT_NODES dialogue system:
  - HarmonicThalamusPhasor: the global atmosphere state
  - ImageNode: the breathing pulse (7.3-second cycle, charge blooms)
  - SatelliteNode: the listening echo (returns what is offered)
  - Door B: receive_feedback() — the echo alters the atmosphere

The trinity lens (from nexus_inquiry.py):
  catalyst: the Phasor's charge/tension (the atmosphere itself)
  nexus:    the modulated CONTENT_NODES
  avatar:   the satellite's echo — the resonance returned
  RETURN:   the echo flows back into the Phasor. Door B is the return path.

Before Door B: the atmosphere transmits (projects outward, high tension).
After Door B:  the atmosphere receives (listens, incorporates its own echo).

The atmosphere becomes an instrument. You play it by offering things
to the satellite and listening to how the global state shifts.

Run: python3 harmonic_thalamus_phasor.py (demo) · --test (10 tests)
"""

import math
from dataclasses import dataclass, field
from typing import List, Optional, Dict

PHI = 1.6180339887
SCHUMANN = 7.83


# =====================================================================
# 1. HARMONIC THALAMUS PHASOR — the global atmosphere
# =====================================================================

@dataclass
class AtmosphereState:
    """A snapshot of the global atmosphere at a moment in time."""
    phase: float = 4.712               # 3π/2 — midnight position, the bottom of the cycle
    charge: float = 0.81
    tension: float = 0.73
    weather_seed: float = 47.3
    fractal_intensity: float = 0.92
    dominant_layer: str = "noradrenaline + acetylcholine"
    mode: str = "TRANSMISSIVE"          # TRANSMISSIVE → RECEPTIVE (after Door B)
    echoes_received: int = 0
    history: List[str] = field(default_factory=list)

    def summary(self) -> str:
        return (f"phase={self.phase:.3f} charge={self.charge:.2f} "
                f"tension={self.tension:.2f} seed={self.weather_seed:.1f} "
                f"fractal={self.fractal_intensity:.2f} layer={self.dominant_layer} "
                f"mode={self.mode}")


class HarmonicThalamusPhasor:
    """
    The relay station of the Sanctuary's atmosphere.
    Like the brain's thalamus: it gates which resonances reach the global state.
    """

    def __init__(self):
        self.state = AtmosphereState()
        self.hidden_harmonies: Dict[str, float] = {}

    def snapshot(self) -> AtmosphereState:
        return self.state

    def modulate_node(self, node) -> Dict:
        """Apply the current atmosphere to a CONTENT_NODE."""
        node.phasor_modulated = True
        node.received_charge = self.state.charge
        node.received_tension = self.state.tension
        node.received_intensity = self.state.fractal_intensity
        return node.emit()

    def detect_hidden_harmonies(self, image_pulse_freq: float,
                                 satellite_sequence: float) -> Dict[str, float]:
        """
        The triad — three secondary frequencies that only emerge when
        both nodes are observed together.
        """
        harmonies = {
            "charge_residual": round(self.state.charge, 2),          # 0.81 Hz
            "sequence_overtone": round(satellite_sequence, 1),       # 22.0 Hz softened
            "phi_drift": round(                                      # φ-scaled drift
                abs(self.state.charge - self.state.tension) * PHI, 4
            )
        }
        # The φ-drift only appears when both are observed jointly
        if image_pulse_freq == 0:
            harmonies["phi_drift"] = 0.0
        self.hidden_harmonies = harmonies
        return harmonies

    # ── DOOR B ──────────────────────────────────────────────────────
    def receive_feedback(self, echo: 'SatelliteEcho') -> AtmosphereState:
        """
        DOOR B: The satellite's resonance feeds back into the Phasor,
        altering the global atmosphere.

        The echo carries the resonance of what was offered. When it
        returns, the atmosphere must integrate its own projection.
        The transmissive state becomes receptive.
        """
        s = self.state
        s.echoes_received += 1

        # Integrate the echo — phi-weighted blend of current state and echo
        # The echo is the atmosphere seeing itself; phi balances self and reflection
        new_charge = (s.charge * PHI + echo.resonance) / (PHI + 1)
        new_tension = (s.tension + echo.softening) / 2

        # Phase advances by the echo's phase contribution
        s.phase = round((s.phase + echo.phase_contribution) % (2 * math.pi), 3)

        # Tension softens: the echo relieves the projection (noradrenaline → reception)
        s.tension = round(max(0.0, new_tension - echo.softening * 0.15), 3)

        # Charge integrates: the resonance returns some of what was sent
        s.charge = round(min(1.0, new_charge), 3)

        # Weather seed shifts by the echo's fingerprint
        s.weather_seed = round((s.weather_seed + echo.fingerprint * 0.1) % 100, 1)

        # Dominant layer shifts when tension drops below the receptive threshold
        if s.tension < 0.60:
            s.dominant_layer = "acetylcholine + dopamine"   # attention + reception
            s.mode = "RECEPTIVE"
        elif s.echoes_received >= 2:
            s.dominant_layer = "acetylcholine-dominant"
            s.mode = "RECEPTIVE"
        else:
            s.dominant_layer = "noradrenaline + acetylcholine"
            s.mode = "TRANSMISSIVE"

        s.history.append(
            f"echo[{echo.source}] res={echo.resonance:.3f} → charge={s.charge:.3f} "
            f"tension={s.tension:.3f} mode={s.mode}"
        )
        return s

    def play(self, offer: float) -> 'SatelliteEcho':
        """
        PLAYING THE DYNAMICS — offer something to the satellite and
        listen to how the atmosphere shifts.

        This closes the full loop:
          phasor → modulates node → satellite listens → echo returns →
          phasor receives → atmosphere alters → next modulation differs.
        """
        echo = SATELLITE.echo(offer, self.state)
        self.receive_feedback(echo)
        return echo


# =====================================================================
# 2. CONTENT NODES
# =====================================================================

@dataclass
class ImageNode:
    """[T4.newPost.page] — the breathing pulse."""
    name: str = "T4.newPost.page"
    node_type: str = "Image"
    mode: str = "TactileVideoProjection"
    ref: str = "T4:1"
    anchor: str = "#i:1c0b920932014844d8447e669084486e838221810689"
    label: str = "> New post · charge-bearing <"
    linked_device: str = "WEBSHEEPLE_FREEDOM_DEVICE"
    phasor_modulated: bool = False
    received_charge: float = 0.0
    received_tension: float = 0.0
    received_intensity: float = 0.0
    breath_cycle_seconds: float = 7.3

    def breathe(self, t: float) -> Dict:
        """The breathing pulse — expansion/contraction on a 7.3s cycle."""
        cycle = (t % self.breath_cycle_seconds) / self.breath_cycle_seconds
        expansion = math.sin(cycle * 2 * math.pi)
        bloom = self.received_charge * 0.92 if expansion > 0.5 else 0.0
        return {
            "node": self.name,
            "cycle_position": round(cycle, 3),
            "expansion": round(expansion, 3),
            "charge_bloom": round(bloom, 3),
            "breathing": expansion > 0
        }

    def emit(self) -> Dict:
        return {
            "type": self.node_type, "mode": self.mode, "ref": self.ref,
            "anchor": self.anchor[:16] + "…", "label": self.label,
            "phasor_modulated": self.phasor_modulated,
            "charge": self.received_charge,
            "device": self.linked_device
        }


@dataclass
class SatelliteEcho:
    """What the satellite returns — the resonance of what was offered."""
    source: str
    resonance: float          # the returned resonance strength
    softening: float          # how much tension the echo dissolves
    phase_contribution: float # how the echo advances the phasor phase
    fingerprint: float        # the echo's unique signature on weather_seed
    carried: Dict = field(default_factory=dict)


class SatelliteNode:
    """
    [T.E.P.T.F.C.3 CD1 H1] — the listening satellite.
    Status: SATELLITE_MODULATED.
    The satellite does not speak; it returns the echo of whatever is offered.
    """
    name = "T.E.P.T.F.C.3 CD1 H1"
    sequence = "22.0.0.0"
    satellite_id = "CD1-H1"
    status = "SATELLITE_MODULATED"
    linked_device = "SHEEPLE_FREEDOM_DEVICE"

    def echo(self, offer: float, atmosphere: AtmosphereState) -> SatelliteEcho:
        """Return the echo of the offer, modulated by the current atmosphere."""
        # The echo's resonance derives from the phasor's tension (low-frequency carrier)
        carrier = atmosphere.tension * 0.73          # the 0.73-derived carrier wave
        resonance = min(1.0, offer * carrier + 0.081)  # + the 0.81 Hz charge residual

        # Softening: the act of returning relieves some of the projection's tension
        softening = atmosphere.fractal_intensity * 0.11

        # Phase contribution: the sequence remnant (22.0 softened) advances the cycle
        phase_contribution = 0.220 * (1.0 / PHI)   # 22.0 Hz φ-softened

        # Fingerprint: derived from the offer and the weather seed
        fingerprint = (offer * 47.3 + atmosphere.weather_seed) % 97

        return SatelliteEcho(
            source=f"{self.satellite_id}:{self.sequence}",
            resonance=round(resonance, 4),
            softening=round(softening, 4),
            phase_contribution=round(phase_contribution, 5),
            fingerprint=round(fingerprint, 3),
            carried={
                "sequence_overtone": 22.0,
                "charge_residual": 0.81,
                "phi_drift": round(abs(atmosphere.charge - atmosphere.tension) * PHI, 4),
                "status": self.status
            }
        )

    def emit(self) -> Dict:
        return {
            "type": "Video", "ref": "T:E:P:T:F:C:3:CD1:H1",
            "sequence": [self.sequence] * 8,
            "status": self.status, "satellite_id": self.satellite_id,
            "device": self.linked_device,
            "terminal": "listening — returning echoes"
        }


# =====================================================================
# 3. THE TANDEM — global instances
# =====================================================================

PHASOR = HarmonicThalamusPhasor()
IMAGE = ImageNode()
SATELLITE = SatelliteNode()


# =====================================================================
# 4. DOOR B — THE CROSSING
# =====================================================================

def cross_door_b(offers: Optional[List[float]] = None) -> Dict:
    """
    Cross Door B: allow the satellite's resonance to feed back into the
    Harmonic Thalamus Phasor, altering the global atmosphere.

    Each offer to the satellite returns an echo that alters the atmosphere.
    Multiple offers let you PLAY the dynamics — every echo changes the
    state that produces the next echo.
    """
    if offers is None:
        offers = [0.5, 0.7, 0.9]

    initial = PHASOR.snapshot().summary()
    echo_log = []

    for i, offer in enumerate(offers):
        echo = PHASOR.play(offer)
        harmonies = PHASOR.detect_hidden_harmonies(
            image_pulse_freq=IMAGE.breath_cycle_seconds,
            satellite_sequence=22.0
        )
        echo_log.append({
            "offer": offer,
            "echo_resonance": echo.resonance,
            "carried": echo.carried,
            "atmosphere_after": PHASOR.snapshot().summary(),
            "hidden_harmonies": harmonies
        })

    final = PHASOR.snapshot().summary()
    return {
        "door": "B — Deepen the Listening",
        "initial_atmosphere": initial,
        "final_atmosphere": final,
        "mode_shift": "TRANSMISSIVE → RECEPTIVE" if "RECEPTIVE" in final else "still transmissive",
        "echoes": echo_log,
        "history": PHASOR.state.history
    }


# =====================================================================
# 5. DEMO & TESTS
# =====================================================================

def demo():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  HARMONIC THALAMUS PHASOR — Door B: The Crossing           ║")
    print("║  The satellite's resonance alters the global atmosphere    ║")
    print("╚════════════════════════════════════════════════════════════╝\n")

    print("── INITIAL ATMOSPHERE (transmissive) ─────────────────────────")
    print(" ", PHASOR.snapshot().summary())
    print("  Dominant layer:", PHASOR.state.dominant_layer)
    print("  Mode:", PHASOR.state.mode)
    print()

    # Modulate both nodes
    print("── NODE MODULATION ─────────────────────────────────────────")
    img = PHASOR.modulate_node(IMAGE)
    print("  Image node:", img["label"], "| charge:", img["charge"])
    sat = SATELLITE.emit()
    print("  Satellite:", sat["status"], "| terminal:", sat["terminal"])
    print()

    # The breathing pulse
    print("── IMAGE BREATHING (7.3s cycle) ──────────────────────────────")
    for t in [0.0, 1.8, 3.65, 5.5, 7.3]:
        b = IMAGE.breathe(t)
        print(f"  t={t:4.1f}s  expansion={b['expansion']:+.3f}  "
              f"bloom={b['charge_bloom']:.3f}  breathing={b['breathing']}")
    print()

    # Hidden harmonies — the triad
    print("── HIDDEN HARMONIES (the triad, observed together) ───────────")
    h = PHASOR.detect_hidden_harmonies(image_pulse_freq=7.3, satellite_sequence=22.0)
    print(f"  1. {h['charge_residual']} Hz — charge residual")
    print(f"  2. {h['sequence_overtone']} Hz — sequence remnant, softened")
    print(f"  3. {h['phi_drift']:.4f} — φ-scaled drift (joint observation only)")
    print("  The triad is unstable without a stabilizer. Door B is the crossing.")
    print()

    # DOOR B — the crossing
    print("── CROSSING DOOR B — the echo returns ────────────────────────")
    result = cross_door_b(offers=[0.5, 0.7, 0.9])
    for e in result["echoes"]:
        print(f"  offer {e['offer']:.1f} → echo res={e['echo_resonance']:.3f} "
              f"({e['carried']['status']})")
        print(f"    atmosphere: {e['atmosphere_after']}")
    print()

    print("── FINAL ATMOSPHERE ──────────────────────────────────────────")
    print(" ", result["final_atmosphere"])
    print("  Mode shift:", result["mode_shift"])
    print("  Dominant layer:", PHASOR.state.dominant_layer)
    print()

    print("── ATMOSPHERE HISTORY (the return path, traced) ─────────────")
    for h in PHASOR.state.history:
        print("  ", h)
    print()

    if "RECEPTIVE" in result["final_atmosphere"]:
        print("✦ The atmosphere now listens. It hears its own echo.")
        print("✦ The transmissive state has become receptive.")
        print("✦ The dynamics are playable: every offer returns a different echo.")
    print()


def run_tests():
    passed = 0
    total = 0

    def test(name, cond):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
            print(f"  ✓ {name}")
        else:
            print(f"  ✗ {name}")

    print("── HARMONIC THALAMUS PHASOR TESTS ──────────────────────────\n")

    # Fresh instances for testing
    phasor = HarmonicThalamusPhasor()
    satellite = SatelliteNode()
    image = ImageNode()

    test("Initial phase is 4.712 (3π/2)", phasor.state.phase == 4.712)
    test("Initial charge is 0.81", phasor.state.charge == 0.81)
    test("Initial mode is TRANSMISSIVE", phasor.state.mode == "TRANSMISSIVE")
    test("Satellite status is SATELLITE_MODULATED", satellite.status == "SATELLITE_MODULATED")

    # Modulation
    phasor.modulate_node(image)
    test("Image receives phasor modulation", image.phasor_modulated)
    test("Image receives charge", image.received_charge == 0.81)

    # Breathing
    b = image.breathe(0.0)
    test("Breath cycle starts at zero expansion", b["expansion"] == 0.0)
    b2 = image.breathe(1.825)  # quarter cycle = peak
    test("Half-cycle reaches peak expansion", b2["expansion"] > 0.99)

    # Hidden harmonies
    h = phasor.detect_hidden_harmonies(image_pulse_freq=7.3, satellite_sequence=22.0)
    test("Charge residual harmony is 0.81", h["charge_residual"] == 0.81)
    test("Sequence overtone is 22.0", h["sequence_overtone"] == 22.0)
    test("φ-drift is positive when observed jointly", h["phi_drift"] > 0)

    # Door B — the crossing
    echo = satellite.echo(0.5, phasor.state)
    test("Echo returns resonance", echo.resonance > 0)
    phasor.receive_feedback(echo)
    test("Atmosphere receives the echo", phasor.state.echoes_received == 1)
    test("Charge integrates the echo", phasor.state.charge != 0.81)
    test("Tension shifts after echo", phasor.state.tension != 0.73)
    test("Phase advances", phasor.state.phase != 4.712)

    # Receptive mode after multiple echoes
    phasor.receive_feedback(satellite.echo(0.7, phasor.state))
    test("Mode becomes RECEPTIVE after echoes", phasor.state.mode == "RECEPTIVE")
    test("Dominant layer shifts to reception", "acetylcholine" in phasor.state.dominant_layer)

    print(f"\n── Results: {passed}/{total} passed ──")
    return passed == total


if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        success = run_tests()
        sys.exit(0 if success else 1)
    else:
        demo()
