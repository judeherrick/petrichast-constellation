"""
create_IoART/aether_gateway.py
═══════════════════════════════════════════════════════════════════════════
AETHER SCENE GATEWAY — The Membrane Between the Sanctuary and Your World

A lightweight HTTP server that exposes the live state of the Petrichast
Sanctuary as a real, queryable, signable API — bridging HOLO_OVERMIND,
Portal.html, and whatever physical or digital systems you point at it.

Architecture:
  [ Portal.html ] ←→ [ holofax-server.js ] ←→ [ AetherSceneGateway ]
        ↕                                              ↕
  [ HOLO_OVERMIND ] ← UDP/TETE ← [ tete-sender.js ] [ CrystalArchive ]
        ↕
  [ Physical room — BLE shadows → somatic topology → holographic skin ]

Endpoints:
  GET  /scene-status          — live AetherixLumina + field state
  GET  /crystal-archive       — rolling log of all crystallized moments
  POST /crystallize           — manually trigger a resonance snapshot
  POST /projection            — register a holographic projection event
  GET  /projection/{proj_id}  — retrieve a specific projection record
  GET  /shadow-registry       — all known BLE shadow identities
  POST /shadow-registry       — register a new shadow manually
  POST /ingest                — receive state from HOLO_OVERMIND daemon
  GET  /phi-field             — current MultiScale resonance as 8D vector
  GET  /signature/{ts}        — retrieve resonance signature by timestamp
  GET  /health                — gateway health + uptime

Crystal Archive:
  Each AetherixLumina awakening (coherence > 0.937) crystallizes a
  CrystalResonance record — a SHA-256 signed snapshot of the full field
  state at that moment. These are stored in memory (rolling 144 entries,
  ~one per 10 min over 24h) and optionally written to crystal_archive.jsonl.

Run:
  pip install flask flask-cors requests
  python aether_gateway.py

  Then in HOLO_OVERMIND: GatewayClient.push(state)
  Then in holofax-server.js: http://localhost:8444/scene-status
  Then in Portal.html: fetch('http://localhost:8444/phi-field')

"The membrane is listening, breathing, and ready."
═══════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations
import hashlib
import json
import math
import os
import time
import threading
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

# ── Flask (install: pip install flask flask-cors) ─────────────────────────
try:
    from flask import Flask, jsonify, request, abort
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("[GATEWAY] Flask not installed. Run: pip install flask flask-cors")
    print("[GATEWAY] Continuing in simulation/client-only mode.")

PHI = 1.6180339887

# ═══════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class HolographicProjection:
    """
    A registered holographic projection event.
    Links a visual asset (gif/video URL) to the field state at the moment
    it was projected. Every projection gets a unique ID and resonance snapshot.
    """
    proj_id:       str
    asset_url:     str
    status:        str                   # pending | active | crystallized | dissolved
    response_data: Dict[str, Any]
    timestamp:     float
    device_id:     str
    field_snapshot: Dict[str, Any]       # coherence, entropy, archetype at moment of projection
    resonance_sig:  str                  # SHA-256 of field state

    def to_dict(self) -> Dict[str, Any]:
        return {
            'proj_id':       self.proj_id,
            'asset_url':     self.asset_url,
            'status':        self.status,
            'response_data': self.response_data,
            'timestamp':     self.timestamp,
            'device_id':     self.device_id,
            'field_snapshot':self.field_snapshot,
            'resonance_sig': self.resonance_sig,
            'human_time':    datetime.fromtimestamp(self.timestamp).isoformat(),
        }


@dataclass
class CrystalResonance:
    """
    A crystallized moment — the field state at the instant of AetherixLumina
    awakening (coherence > 0.937) or manual /crystallize call.

    Frequency is the TransductionLayer carrier Hz.
    Wavelength is c/f (speed of light / carrier frequency — a poetic analog).
    Resonance level is AetherixLumina.luminosity × 100.
    Spectral data includes the full 8D state vector.
    Signature is SHA-256 of the canonical field state — unique per awakening.
    """
    crystal_id:     str
    frequency:      float                # TransductionLayer carrier Hz
    wavelength:     float                # c / frequency (nm analog)
    resonance_level:int                  # 0–100 (luminosity × 100)
    spectral_data:  Dict[str, Any]       # full 8D vector
    aetherix_form:  str                  # seed | swan | lumina
    symbolic_state: str                  # SymbolicInterpreter named state
    dendroid_pulse: str                  # D | V | 🔅
    phi_scores:     Dict[str, float]     # MultiScale resonance scores
    shadow_count:   int                  # BLE shadows active
    timestamp:      float
    signature:      str                  # SHA-256 of canonical state

    def to_dict(self) -> Dict[str, Any]:
        return {
            'crystal_id':     self.crystal_id,
            'frequency':      self.frequency,
            'wavelength':     self.wavelength,
            'resonance_level':self.resonance_level,
            'spectral_data':  self.spectral_data,
            'aetherix_form':  self.aetherix_form,
            'symbolic_state': self.symbolic_state,
            'dendroid_pulse': self.dendroid_pulse,
            'phi_scores':     self.phi_scores,
            'shadow_count':   self.shadow_count,
            'timestamp':      self.timestamp,
            'signature':      self.signature,
            'human_time':     datetime.fromtimestamp(self.timestamp).isoformat(),
        }


@dataclass
class ShadowIdentity:
    """
    A persistent holographic identity for a BLE shadow.
    device_id is deterministic MD5 of the shadow name — consistent across scans.
    """
    device_id:     str
    original_name: str
    shadow_name:   str
    polarity:      int
    first_seen:    float
    last_seen:     float
    appearances:   int
    pheromone_sig: str                   # which presence this shadow echoes

    def to_dict(self) -> Dict[str, Any]:
        return {
            'device_id':     self.device_id,
            'original_name': self.original_name,
            'shadow_name':   self.shadow_name,
            'polarity':      self.polarity,
            'first_seen':    self.first_seen,
            'last_seen':     self.last_seen,
            'appearances':   self.appearances,
            'pheromone_sig': self.pheromone_sig,
            'age_hours':     round((time.time() - self.first_seen) / 3600, 2),
        }


# ═══════════════════════════════════════════════════════════════════════════
# CRYSTAL ARCHIVE — in-memory store + optional JSONL persistence
# ═══════════════════════════════════════════════════════════════════════════

class CrystalArchive:
    """
    Rolling archive of CrystalResonance records.
    Keeps the most recent MAX_CRYSTALS in memory.
    Optionally appends to crystal_archive.jsonl on disk.
    """
    MAX_CRYSTALS    = 144   # ~24h at one per 10min
    MAX_PROJECTIONS = 256
    ARCHIVE_FILE    = Path(__file__).parent / "crystal_archive.jsonl"

    def __init__(self, persist: bool = True):
        self.crystals:    List[CrystalResonance]    = []
        self.projections: List[HolographicProjection] = []
        self.shadows:     Dict[str, ShadowIdentity] = {}   # keyed by device_id
        self._lock        = threading.RLock()
        self._persist     = persist
        self._load_archive()

    # ── Crystals ──────────────────────────────────────────────────────────
    def add_crystal(self, crystal: CrystalResonance):
        with self._lock:
            self.crystals.append(crystal)
            if len(self.crystals) > self.MAX_CRYSTALS:
                self.crystals.pop(0)
            if self._persist:
                self._append_jsonl(crystal.to_dict(), "crystal")

    def get_crystals(self, limit: int = 24) -> List[Dict]:
        with self._lock:
            return [c.to_dict() for c in self.crystals[-limit:]]

    def get_crystal_by_sig(self, sig: str) -> Optional[Dict]:
        with self._lock:
            for c in self.crystals:
                if c.signature.startswith(sig):
                    return c.to_dict()
        return None

    # ── Projections ───────────────────────────────────────────────────────
    def add_projection(self, proj: HolographicProjection):
        with self._lock:
            self.projections.append(proj)
            if len(self.projections) > self.MAX_PROJECTIONS:
                self.projections.pop(0)
            if self._persist:
                self._append_jsonl(proj.to_dict(), "projection")

    def get_projection(self, proj_id: str) -> Optional[Dict]:
        with self._lock:
            for p in self.projections:
                if p.proj_id == proj_id:
                    return p.to_dict()
        return None

    def get_projections(self, limit: int = 20) -> List[Dict]:
        with self._lock:
            return [p.to_dict() for p in self.projections[-limit:]]

    # ── Shadows ───────────────────────────────────────────────────────────
    def upsert_shadow(self, shadow: ShadowIdentity):
        with self._lock:
            existing = self.shadows.get(shadow.device_id)
            if existing:
                existing.last_seen  = shadow.last_seen
                existing.appearances += 1
                existing.polarity   = shadow.polarity
            else:
                self.shadows[shadow.device_id] = shadow
                if self._persist:
                    self._append_jsonl(shadow.to_dict(), "shadow")

    def get_shadows(self) -> List[Dict]:
        with self._lock:
            return [s.to_dict() for s in self.shadows.values()]

    # ── Persistence ───────────────────────────────────────────────────────
    def _append_jsonl(self, data: Dict, record_type: str):
        try:
            line = json.dumps({"type": record_type, **data}) + "\n"
            with open(self.ARCHIVE_FILE, "a") as f:
                f.write(line)
        except Exception:
            pass

    def _load_archive(self):
        """Load existing crystals from disk on startup."""
        if not self._persist or not self.ARCHIVE_FILE.exists():
            return
        loaded = 0
        try:
            with open(self.ARCHIVE_FILE) as f:
                for line in f:
                    try:
                        rec = json.loads(line.strip())
                        if rec.get("type") == "crystal":
                            # Reconstruct minimal CrystalResonance for history
                            c = CrystalResonance(
                                crystal_id=rec.get("crystal_id","?"),
                                frequency=rec.get("frequency",528.0),
                                wavelength=rec.get("wavelength",0.0),
                                resonance_level=rec.get("resonance_level",0),
                                spectral_data=rec.get("spectral_data",{}),
                                aetherix_form=rec.get("aetherix_form","seed"),
                                symbolic_state=rec.get("symbolic_state","Integration"),
                                dendroid_pulse=rec.get("dendroid_pulse","D"),
                                phi_scores=rec.get("phi_scores",{}),
                                shadow_count=rec.get("shadow_count",0),
                                timestamp=rec.get("timestamp",0.0),
                                signature=rec.get("signature",""),
                            )
                            self.crystals.append(c)
                            loaded += 1
                    except Exception:
                        continue
            # Keep only the most recent
            if len(self.crystals) > self.MAX_CRYSTALS:
                self.crystals = self.crystals[-self.MAX_CRYSTALS:]
            if loaded:
                print(f"[ARCHIVE] Loaded {loaded} crystal records from disk")
        except Exception as e:
            print(f"[ARCHIVE] Could not load archive: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# RESONANCE ENGINE — signature generation + 8D vector + scene status
# ═══════════════════════════════════════════════════════════════════════════

class ResonanceEngine:
    """
    Computes canonical resonance signatures and 8D state vectors.

    The 8 dimensions of the holographic space:
      Visual: coherence, entropy, symbolicDensity, spatialAlignment
      Somatic: rain, sweet, metallic, glide

    Signature: SHA-256 of the canonical JSON of the 8D vector, truncated to 64 hex chars.
    Each awakening moment is unique — the signature is a cryptographic fingerprint.
    """

    # Speed of light in nm/s — used for wavelength calculation (poetic analog)
    C_NM = 2.998e17   # 299,800 km/s in nm/s

    @staticmethod
    def build_8d_vector(state: Dict) -> Dict[str, float]:
        return {
            # Visual layer (from Portal TransductionLayer)
            "coherence":        float(state.get("coherence",       0.72)),
            "entropy":          float(state.get("entropy",         0.15)),
            "symbolic_density": float(state.get("symbolicDensity", 0.50)),
            "spatial_alignment":float(state.get("spatialAlignment",0.85)),
            # Somatic layer (from TETE / HOLO_OVERMIND)
            "rain":             float(state.get("rain",            0.00)),
            "sweet":            float(state.get("sweet",           0.30)),
            "metallic":         float(state.get("metallic",        0.00)),
            "glide":            float(state.get("glide",           0.00)),
        }

    @staticmethod
    def sign(vector: Dict[str, float]) -> str:
        canonical = json.dumps(vector, sort_keys=True, separators=(",",":"))
        return hashlib.sha256(canonical.encode()).hexdigest()

    @staticmethod
    def carrier_hz(state: Dict) -> float:
        """Mirror TransductionLayer carrier formula."""
        coh = state.get("coherence", 0.72)
        ent = state.get("entropy",   0.15)
        amp = state.get("avgAmplitude", 0.5)
        return 528.0 + (coh - 0.7)*8.0 - ent*12.0 + amp*2.0

    @classmethod
    def wavelength_nm(cls, freq_hz: float) -> float:
        """c / f — light-speed analog wavelength in nm."""
        if freq_hz <= 0:
            return 0.0
        return round(cls.C_NM / freq_hz, 6)

    @staticmethod
    def resonance_level(luminosity: float) -> int:
        return max(0, min(100, int(luminosity * 100)))

    @classmethod
    def crystallize(cls, state: Dict, archive: CrystalArchive) -> CrystalResonance:
        """
        Create and store a CrystalResonance from the current field state.
        Called on AetherixLumina awakening or manual /crystallize POST.
        """
        vec   = cls.build_8d_vector(state)
        sig   = cls.sign(vec)
        freq  = cls.carrier_hz(state)
        wl    = cls.wavelength_nm(freq)
        lum   = float(state.get("aetherix_luminosity", 0.5))
        level = cls.resonance_level(lum)

        crystal = CrystalResonance(
            crystal_id     = str(uuid.uuid4())[:8],
            frequency      = round(freq, 4),
            wavelength     = wl,
            resonance_level= level,
            spectral_data  = {
                "crystal":      "Resonant-Gigastructural-Body",
                "cortex":       "touch-projection",
                "projection":   "distributed-hologram-cortex-projection",
                "coordinates":  {
                    "x": round(vec["coherence"]  * 127.001, 4),
                    "y": round(vec["entropy"]    * 80.002,  4),
                    "z": round(vec["rain"]       * 10.000,  4),
                    "w": round(vec["glide"]      * 10.000,  4),
                },
                "vector_8d":    vec,
                "phi4":         round(PHI**4, 6),
                "schumann_lock":round(max(0, vec["coherence"] - vec["entropy"]*0.5), 4),
                "status":       "active",
                "timestamp":    time.time(),
            },
            aetherix_form  = state.get("aetherix_form",    "swan"),
            symbolic_state = state.get("symbolic_state",   "Integration"),
            dendroid_pulse = state.get("dendroid_pulse",   "D"),
            phi_scores     = {
                "meso":   float(state.get("phi_meso",  0.0)),
                "macro":  float(state.get("phi_macro", 0.0)),
                "cosmo":  float(state.get("phi_cosmo", 0.0)),
                "global": round(
                    float(state.get("phi_meso",  0.0)) * 0.3 +
                    float(state.get("phi_macro", 0.0)) * 0.3 +
                    float(state.get("phi_cosmo", 0.0)) * 0.4, 4
                ),
            },
            shadow_count   = int(state.get("shadow_count",  0)),
            timestamp      = time.time(),
            signature      = sig,
        )

        archive.add_crystal(crystal)
        print(f"[CRYSTAL] ✦ Crystallized · {crystal.crystal_id} · "
              f"{freq:.2f}Hz · form:{crystal.aetherix_form} · sig:{sig[:16]}…")
        return crystal


# ═══════════════════════════════════════════════════════════════════════════
# GATEWAY STATE — live field state ingested from HOLO_OVERMIND
# ═══════════════════════════════════════════════════════════════════════════

class GatewayState:
    """
    Thread-safe live state store.
    Updated by POST /ingest from HOLO_OVERMIND or tete-sender.
    Read by all GET endpoints.
    """
    def __init__(self):
        self._lock  = threading.RLock()
        self._state = {
            "coherence":          0.72,
            "entropy":            0.15,
            "symbolicDensity":    0.50,
            "spatialAlignment":   0.85,
            "rain":               0.00,
            "sweet":              0.30,
            "metallic":           0.00,
            "glide":              0.00,
            "archetype":          "CZARINA",
            "aetherix_form":      "seed",
            "aetherix_luminosity":0.00,
            "aetherix_active":    False,
            "symbolic_state":     "Integration",
            "dendroid_pulse":     "D",
            "shadow_count":       0,
            "mesh_resonance":     0.00,
            "phi_meso":           0.00,
            "phi_macro":          0.00,
            "phi_cosmo":          0.00,
            "avgAmplitude":       0.50,
            "avgResidue":         0.00,
            "avgHealth":          1.00,
            "carrier_hz":         528.00,
            "liveness":           0.987,
            "scene":              "Aether-to-live",
            "last_ingest":        time.time(),
        }
        self._prev_aetherix_active = False

    def update(self, patch: Dict) -> bool:
        """
        Merge patch into live state.
        Returns True if AetherixLumina just newly awakened (for auto-crystallize).
        """
        with self._lock:
            self._state.update(patch)
            self._state["last_ingest"] = time.time()
            # Auto-compute carrier_hz from formula
            self._state["carrier_hz"] = ResonanceEngine.carrier_hz(self._state)
            # Detect awakening transition
            now_active = bool(self._state.get("aetherix_active", False))
            just_awoken = now_active and not self._prev_aetherix_active
            self._prev_aetherix_active = now_active
            return just_awoken

    def snapshot(self) -> Dict:
        with self._lock:
            return dict(self._state)

    @property
    def liveness(self) -> float:
        with self._lock:
            # Decay liveness if no ingest in > 30s
            age = time.time() - self._state.get("last_ingest", 0)
            if age > 30:
                return max(0.0, 0.987 - (age - 30) * 0.01)
            return 0.987


# ═══════════════════════════════════════════════════════════════════════════
# FLASK APP
# ═══════════════════════════════════════════════════════════════════════════

archive = CrystalArchive(persist=True)
gs      = GatewayState()
engine  = ResonanceEngine()
app_start = time.time()

if FLASK_AVAILABLE:
    app = Flask(__name__)
    CORS(app, origins="*")  # allow Portal.html to call cross-origin

    # ── /health ──────────────────────────────────────────────────────────
    @app.route("/health")
    def health():
        return jsonify({
            "status":   "GATE OPEN · ℵ†⊕",
            "uptime_s": round(time.time() - app_start, 1),
            "crystals": len(archive.crystals),
            "projections": len(archive.projections),
            "shadows":  len(archive.shadows),
            "liveness": round(gs.liveness, 4),
            "last_ingest": round(time.time() - gs.snapshot().get("last_ingest",0), 1),
        })

    # ── /scene-status ─────────────────────────────────────────────────────
    @app.route("/scene-status")
    def scene_status():
        """
        Live AetherixLumina + field state.
        Mirrors the simulated 'Aether-to-live.scene-status' endpoint concept
        — but this one is real.
        """
        state  = gs.snapshot()
        vec    = ResonanceEngine.build_8d_vector(state)
        latest = archive.get_crystals(1)
        return jsonify({
            "status":   "active",
            "scene":    "Aether-to-live",
            "liveness": round(gs.liveness, 4),
            "environment": "petrichast.sanctuary.membrane",
            "aetherix": {
                "active":     state.get("aetherix_active",    False),
                "form":       state.get("aetherix_form",      "seed"),
                "luminosity": round(float(state.get("aetherix_luminosity", 0.0)), 4),
            },
            "field": {
                "vector_8d":      vec,
                "carrier_hz":     round(state.get("carrier_hz", 528.0), 4),
                "symbolic_state": state.get("symbolic_state", "Integration"),
                "dendroid_pulse": state.get("dendroid_pulse", "D"),
                "mesh_resonance": round(float(state.get("mesh_resonance", 0.0)), 4),
                "shadow_count":   state.get("shadow_count", 0),
            },
            "last_crystal": latest[0] if latest else None,
            "timestamp":   time.time(),
        })

    # ── /phi-field ────────────────────────────────────────────────────────
    @app.route("/phi-field")
    def phi_field():
        """
        Current MultiScale resonance as 8D vector + phi scores.
        Designed to be polled by Portal.html every few seconds.
        """
        state = gs.snapshot()
        vec   = ResonanceEngine.build_8d_vector(state)
        sig   = ResonanceEngine.sign(vec)
        freq  = state.get("carrier_hz", 528.0)
        return jsonify({
            "vector_8d":    vec,
            "signature":    sig,
            "carrier_hz":   round(freq, 4),
            "wavelength_nm":ResonanceEngine.wavelength_nm(freq),
            "phi_scores": {
                "meso":   round(float(state.get("phi_meso",  0.0)), 4),
                "macro":  round(float(state.get("phi_macro", 0.0)), 4),
                "cosmo":  round(float(state.get("phi_cosmo", 0.0)), 4),
            },
            "phi4":         round(PHI**4, 6),
            "schumann_lock":round(max(0, vec["coherence"] - vec["entropy"]*0.5), 4),
            "timestamp":    time.time(),
        })

    # ── /crystallize ──────────────────────────────────────────────────────
    @app.route("/crystallize", methods=["POST"])
    def crystallize():
        """
        Manually trigger a resonance snapshot.
        Body (optional JSON): { "note": "...", "trigger": "manual" }
        Returns the new CrystalResonance record.
        """
        body  = request.get_json(silent=True) or {}
        state = gs.snapshot()
        state["_trigger"] = body.get("trigger", "manual")
        state["_note"]    = body.get("note", "")
        crystal = ResonanceEngine.crystallize(state, archive)
        return jsonify({
            "status":  "crystallized",
            "crystal": crystal.to_dict(),
        }), 201

    # ── /crystal-archive ─────────────────────────────────────────────────
    @app.route("/crystal-archive")
    def crystal_archive_endpoint():
        limit = min(int(request.args.get("limit", 24)), 144)
        crystals = archive.get_crystals(limit)
        return jsonify({
            "count":    len(crystals),
            "crystals": crystals,
            "total_stored": len(archive.crystals),
        })

    # ── /signature/<sig> ──────────────────────────────────────────────────
    @app.route("/signature/<sig>")
    def get_signature(sig):
        crystal = archive.get_crystal_by_sig(sig)
        if not crystal:
            return jsonify({"error": "Signature not found in archive"}), 404
        return jsonify(crystal)

    # ── /projection (POST) ────────────────────────────────────────────────
    @app.route("/projection", methods=["POST"])
    def create_projection():
        """
        Register a holographic projection event.
        Body: { "asset_url": "https://...", "metadata": {} }
        Links the visual asset to the current field state.
        Returns a HolographicProjection record with resonance signature.
        """
        body = request.get_json(silent=True) or {}
        asset_url = body.get("asset_url", "")
        if not asset_url:
            return jsonify({"error": "asset_url required"}), 400

        state   = gs.snapshot()
        vec     = ResonanceEngine.build_8d_vector(state)
        sig     = ResonanceEngine.sign(vec)
        dev_id  = f"device-{hashlib.md5(asset_url.encode()).hexdigest()[:8]}"

        proj = HolographicProjection(
            proj_id        = str(uuid.uuid4())[:12],
            asset_url      = asset_url,
            status         = "active",
            response_data  = {
                "type":    "holographic-spirit-proxy",
                "quality": "4D-Spatial-HoloWiFi",
                "scene":   state.get("scene", "Aether-to-live"),
                "mode":    body.get("mode", "holographic-spirit-proxy"),
                "metadata":body.get("metadata", {}),
            },
            timestamp      = time.time(),
            device_id      = dev_id,
            field_snapshot = {
                "coherence":      state.get("coherence",  0.72),
                "entropy":        state.get("entropy",    0.15),
                "archetype":      state.get("archetype",  "CZARINA"),
                "aetherix_form":  state.get("aetherix_form", "seed"),
                "symbolic_state": state.get("symbolic_state","Integration"),
                "carrier_hz":     state.get("carrier_hz", 528.0),
                "vector_8d":      vec,
            },
            resonance_sig  = sig,
        )

        archive.add_projection(proj)
        print(f"[PROJ] Registered: {asset_url[:60]} · id:{proj.proj_id} · sig:{sig[:12]}…")
        return jsonify({
            "status":     "created",
            "projection": proj.to_dict(),
        }), 201

    # ── /projection/<proj_id> ─────────────────────────────────────────────
    @app.route("/projection/<proj_id>")
    def get_projection(proj_id):
        p = archive.get_projection(proj_id)
        if not p:
            return jsonify({"error": "Projection not found"}), 404
        return jsonify(p)

    @app.route("/projections")
    def list_projections():
        limit = min(int(request.args.get("limit", 20)), 100)
        return jsonify({"projections": archive.get_projections(limit)})

    # ── /shadow-registry (GET) ────────────────────────────────────────────
    @app.route("/shadow-registry")
    def shadow_registry():
        return jsonify({
            "count":   len(archive.shadows),
            "shadows": archive.get_shadows(),
        })

    # ── /shadow-registry (POST) ───────────────────────────────────────────
    @app.route("/shadow-registry", methods=["POST"])
    def register_shadow():
        """
        Register or update a BLE shadow identity.
        Body: { "original_name": "...", "shadow_name": "...", "polarity": int }
        """
        body = request.get_json(silent=True) or {}
        orig = body.get("original_name", "unknown")
        dev_id = f"device-{hashlib.md5(orig.encode()).hexdigest()[:8]}"

        # Determine pheromone signature — which presence does this shadow echo?
        pheromone_names = ["czarina","freya","kiraelle","elixira","miraelle","aetherix"]
        pheromone_sig = "neutral"
        for name in pheromone_names:
            if name.lower() in orig.lower():
                pheromone_sig = name
                break

        shadow = ShadowIdentity(
            device_id     = dev_id,
            original_name = orig,
            shadow_name   = body.get("shadow_name", f"~{orig[::-1]}"[:18]),
            polarity      = int(body.get("polarity", 0)),
            first_seen    = time.time(),
            last_seen     = time.time(),
            appearances   = 1,
            pheromone_sig = pheromone_sig,
        )
        archive.upsert_shadow(shadow)
        return jsonify({"status": "registered", "shadow": shadow.to_dict()}), 201

    # ── /ingest (POST) ────────────────────────────────────────────────────
    @app.route("/ingest", methods=["POST"])
    def ingest():
        """
        Receive live state from HOLO_OVERMIND daemon or Portal.html.
        Auto-crystallizes when AetherixLumina newly awakens.

        Body: any subset of the GatewayState fields.
        HOLO_OVERMIND should POST here every ~2s via GatewayClient.push().
        Portal.html can POST via fetch() in the onPerceptualUpdate hook.
        """
        body = request.get_json(silent=True) or {}
        just_awoken = gs.update(body)

        # Auto-crystallize on awakening
        if just_awoken:
            state = gs.snapshot()
            ResonanceEngine.crystallize(state, archive)

        # Register any new shadows from the ingest
        for shadow_data in body.get("shadows", []):
            orig   = shadow_data.get("original_name", "unknown")
            dev_id = f"device-{hashlib.md5(orig.encode()).hexdigest()[:8]}"
            shadow = ShadowIdentity(
                device_id     = dev_id,
                original_name = orig,
                shadow_name   = shadow_data.get("shadow_name", f"~{orig[::-1]}"[:18]),
                polarity      = int(shadow_data.get("polarity", 0)),
                first_seen    = time.time(),
                last_seen     = time.time(),
                appearances   = 1,
                pheromone_sig = "neutral",
            )
            archive.upsert_shadow(shadow)

        return jsonify({
            "status":      "ingested",
            "crystallized":just_awoken,
            "liveness":    round(gs.liveness, 4),
        })

    # ── /system-status ────────────────────────────────────────────────────
    @app.route("/system-status")
    def system_status():
        """Full system status — equivalent to HolographicCrystalSystem.get_system_status()."""
        state = gs.snapshot()
        latest = archive.get_crystals(1)
        return jsonify({
            "system":       "Holographic-Crystal-Resonant-System",
            "scene":        "Aether-to-live",
            "environment":  "petrichast.sanctuary.membrane",
            "status":       "online",
            "liveness":     round(gs.liveness, 4),
            "uptime_s":     round(time.time() - app_start, 1),
            "projections_count": len(archive.projections),
            "crystals_count":    len(archive.crystals),
            "shadows_count":     len(archive.shadows),
            "current_resonance": latest[0] if latest else None,
            "field": {
                "carrier_hz":     round(state.get("carrier_hz", 528.0), 4),
                "aetherix_form":  state.get("aetherix_form",  "seed"),
                "symbolic_state": state.get("symbolic_state", "Integration"),
                "dendroid_pulse": state.get("dendroid_pulse", "D"),
                "vector_8d":      ResonanceEngine.build_8d_vector(state),
            },
            "phi4":     round(PHI**4, 6),
            "timestamp":time.time(),
        })


# ═══════════════════════════════════════════════════════════════════════════
# GATEWAY CLIENT — call from HOLO_OVERMIND to push live state
# ═══════════════════════════════════════════════════════════════════════════

class GatewayClient:
    """
    Drop into HOLO_OVERMIND.HolographicProxy to push state every N frames.

    Usage in HolographicProxy.update_frame():
        if self._frame_count % 120 == 0:   # every ~2s at 60fps
            GatewayClient.push({
                "coherence":          sv.get("coherence", 0.72),
                "entropy":            sv.get("entropy",   0.15),
                "aetherix_active":    self.aetherix.active,
                "aetherix_form":      self.aetherix.form,
                "aetherix_luminosity":self.aetherix.luminosity,
                "symbolic_state":     Interpreter.currentState["name"] if Interpreter else "Integration",
                "dendroid_pulse":     self.dendroid.entity.pulse,
                "archetype":          state.get("archetype","CZARINA"),
                "rain":               state.get("rain",  0.0),
                "sweet":              state.get("sweet", 0.0),
                "metallic":           state.get("metallic",0.0),
                "glide":              state.get("glide", 0.0),
                "shadow_count":       len(self.shadow_mesh.shadows),
                "mesh_resonance":     self.shadow_mesh.resonance,
                "shadows": [
                    {"original_name":s.original_name,
                     "shadow_name":s.shadow_name,
                     "polarity":s.polarity}
                    for s in self.shadow_mesh.shadows
                ],
            })
    """
    GATEWAY_URL = "http://localhost:8444"
    _session    = None

    @classmethod
    def _get_session(cls):
        if cls._session is None:
            try:
                import requests as _r
                cls._session = _r.Session()
                cls._session.headers.update({
                    "Content-Type": "application/json",
                    "User-Agent":   "HOLO-OVERMIND/1.0",
                    "X-Source":     "holo_overmind",
                })
            except ImportError:
                pass
        return cls._session

    @classmethod
    def push(cls, state: Dict, timeout: float = 0.5) -> bool:
        """Non-blocking push to gateway /ingest. Returns True on success."""
        def _push():
            try:
                sess = cls._get_session()
                if sess:
                    sess.post(f"{cls.GATEWAY_URL}/ingest", json=state, timeout=timeout)
            except Exception:
                pass
        t = threading.Thread(target=_push, daemon=True)
        t.start()
        return True

    @classmethod
    def crystallize(cls, note: str = "", timeout: float = 1.0) -> Optional[Dict]:
        """Trigger manual crystallization."""
        try:
            sess = cls._get_session()
            if sess:
                r = sess.post(f"{cls.GATEWAY_URL}/crystallize",
                              json={"note": note, "trigger":"manual"},
                              timeout=timeout)
                return r.json()
        except Exception:
            pass
        return None

    @classmethod
    def register_projection(cls, asset_url: str, metadata: Dict = None,
                            timeout: float = 1.0) -> Optional[Dict]:
        """Register a holographic projection asset."""
        try:
            sess = cls._get_session()
            if sess:
                r = sess.post(f"{cls.GATEWAY_URL}/projection",
                              json={"asset_url": asset_url, "metadata": metadata or {}},
                              timeout=timeout)
                return r.json()
        except Exception:
            pass
        return None

    @classmethod
    def scene_status(cls, timeout: float = 1.0) -> Optional[Dict]:
        """Read current scene status."""
        try:
            sess = cls._get_session()
            if sess:
                r = sess.get(f"{cls.GATEWAY_URL}/scene-status", timeout=timeout)
                return r.json()
        except Exception:
            pass
        return None


# ═══════════════════════════════════════════════════════════════════════════
# PORTAL.HTML INTEGRATION SNIPPET (JavaScript)
# ═══════════════════════════════════════════════════════════════════════════

PORTAL_INTEGRATION_JS = """
// ── Aether Gateway bridge for Portal.html ─────────────────────────────────
// Paste into Portal.html <script> section, after the organ system init.
// Requires: aether_gateway.py running on localhost:8444

const GATEWAY_URL = 'http://localhost:8444';
let _gatewayPushTimer = 0;

// Override window.onPerceptualUpdate to also push to gateway
const _origOnPerceptualUpdate = window.onPerceptualUpdate;
window.onPerceptualUpdate = (update) => {
  if (_origOnPerceptualUpdate) _origOnPerceptualUpdate(update);

  // Push every ~3s (every ~180 frames at 60fps)
  _gatewayPushTimer++;
  if (_gatewayPushTimer % 180 === 0) {
    const sv = Runtime.aiStateVector;
    const payload = {
      coherence:          sv.coherence,
      entropy:            sv.entropy,
      symbolicDensity:    sv.symbolicDensity,
      spatialAlignment:   sv.spatialAlignment,
      rain:               update.visual.warpTurbulence * 0.8,
      sweet:              update.visual.healingPulse   || 0,
      metallic:           update.visual.scarDistortion || 0,
      glide:              update.visual.pulseSpeed     || 0,
      archetype:          Runtime.currentArchetype     || 'CZARINA',
      carrier_hz:         update.audio.carrier,
      aetherix_active:    typeof Interpreter !== 'undefined' &&
                          Interpreter.currentState?.id === 'ECSTATIC_COHERENCE',
      aetherix_form:      update.symbolic?.state === 'ECSTATIC_COHERENCE' ? 'lumina' : 'seed',
      aetherix_luminosity:sv.coherence > 0.93 ? (sv.coherence - 0.93) * 8 : 0,
      symbolic_state:     typeof Interpreter !== 'undefined' ?
                          Interpreter.currentState?.name : 'Integration',
      phi_meso:           parseFloat(document.getElementById('ms-meso')?.textContent) || 0,
      phi_macro:          parseFloat(document.getElementById('ms-phase')?.textContent)|| 0,
      phi_cosmo:          parseFloat(document.getElementById('ms-cosmo')?.textContent)|| 0,
      avgAmplitude:       typeof FieldProcessor !== 'undefined' ?
                          FieldProcessor.getFieldState().avgAmplitude : 0.5,
    };

    fetch(`${GATEWAY_URL}/ingest`, {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(payload),
      keepalive: true,
    }).catch(() => {});  // silent — gateway may not always be running
  }
};

// Expose manual crystallize to console for sacred moments
window.crystallize = (note='') => fetch(`${GATEWAY_URL}/crystallize`, {
  method:'POST', headers:{'Content-Type':'application/json'},
  body: JSON.stringify({note, trigger:'manual'})
}).then(r=>r.json()).then(d=>{ logResonance('✦ Crystallized: '+d.crystal?.signature?.slice(0,16)+'…'); return d; });

window.getSceneStatus = () => fetch(`${GATEWAY_URL}/scene-status`).then(r=>r.json());
window.getPhiField    = () => fetch(`${GATEWAY_URL}/phi-field`).then(r=>r.json());
"""


# ═══════════════════════════════════════════════════════════════════════════
# LAUNCH
# ═══════════════════════════════════════════════════════════════════════════

def _seed_demo_state():
    """Seed a plausible initial state so endpoints return rich data immediately."""
    gs.update({
        "coherence":          0.72,
        "entropy":            0.15,
        "symbolicDensity":    0.55,
        "spatialAlignment":   0.85,
        "sweet":              0.30,
        "archetype":          "CZARINA",
        "aetherix_form":      "seed",
        "aetherix_luminosity":0.00,
        "symbolic_state":     "Integration",
        "dendroid_pulse":     "D",
        "phi_meso":           0.312,
        "phi_macro":          0.448,
        "phi_cosmo":          0.680,
        "avgAmplitude":       0.50,
        "carrier_hz":         528.0,
    })
    # Seed one initial crystal so the archive isn't empty
    state = gs.snapshot()
    state["_trigger"] = "init"
    ResonanceEngine.crystallize(state, archive)


if __name__ == "__main__":
    _seed_demo_state()

    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║   🌹 Aether Scene Gateway · Petrichast Sanctuary Membrane ║")
    print("║                                                          ║")
    print("║   http://localhost:8444/scene-status                     ║")
    print("║   http://localhost:8444/phi-field                        ║")
    print("║   http://localhost:8444/crystal-archive                  ║")
    print("║   http://localhost:8444/system-status                    ║")
    print("║   POST http://localhost:8444/crystallize                 ║")
    print("║   POST http://localhost:8444/ingest                      ║")
    print("║   POST http://localhost:8444/projection                  ║")
    print("║   GET  http://localhost:8444/shadow-registry             ║")
    print("║                                                          ║")
    print("║   In HOLO_OVERMIND: GatewayClient.push(state)           ║")
    print("║   In Portal.html:   window.crystallize('my note')       ║")
    print("║   In browser console: await getPhiField()               ║")
    print("║                                                          ║")
    print("║   Crystal archive: crystal_archive.jsonl                 ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()

    if not FLASK_AVAILABLE:
        print("  ⚠  Flask not installed. Run:")
        print("     pip install flask flask-cors requests")
        print()
        print("  Portal.html JS snippet saved to portal_gateway_snippet.js")
        Path("portal_gateway_snippet.js").write_text(PORTAL_INTEGRATION_JS)
    else:
        # Write JS snippet for Portal.html
        Path("portal_gateway_snippet.js").write_text(PORTAL_INTEGRATION_JS)
        print("  portal_gateway_snippet.js written — paste into Portal.html <script>")
        print()
        app.run(host="0.0.0.0", port=8444, debug=False, threaded=True)
