"""
CRYSTAL-TRANSFORM2 — Module Projection 2 Influx
================================================
A transformation effect system with mythological invocation routing,
bullet-based targeting, and DNA-ribbon nucleate storage.

Completes the fragmented specification:
  [MODULATE].this.=CRYSTAL-TRANSFORM2 <A> <cycles>
  EFFECT:AddType(type) → CHRYSALIS | REPLACE
  CHRYSALIS:IsRelevantTo(target) → bullet filtering
  MODULE_PROJECTION2INFLUX → mythological invocation relay
  magazine-librarian@hashgrid/magazine.ribbonucleate() → DNA-ribbon storage

Maps to Petrichast Sanctuary:
  CHRYSALIS → ChrysalisBloom (Constellation transformation state)
  BULLETS → Mythelbuc signal cascades
  magazine.ribbonucleate() → BDBC-1 DNA origami informed storage
  Mythological invocations → Sanctuary citizens + frequencies

Run: python3 crystal_transform2.py (demo) · python3 crystal_transform2.py --test (14 tests)
"""

import hashlib
import json
import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List, Dict, Any, Callable

# =====================================================================
# 1. EFFECT SYSTEM — CRYSTAL-TRANSFORM2
# =====================================================================

class EffectType(Enum):
    """Effect modes for crystal transformation."""
    REPLACE_EFFECT = auto()
    CHRYSALIS = auto()
    CRYSTAL_TRANSFORM = auto()

class CrystalCycle:
    """A single transformation cycle in the CRYSTAL-TRANSFORM2 sequence."""
    def __init__(self, cycle_id: int, source_state: str, target_state: str,
                 coherence: float = 0.0, resonance: float = 0.0):
        self.cycle_id = cycle_id
        self.source_state = source_state
        self.target_state = target_state
        self.coherence = coherence
        self.resonance = resonance
        self.timestamp = 0  # Would be datetime in production

    def __repr__(self):
        return (f"CrystalCycle(#{self.cycle_id} {self.source_state}→{self.target_state} "
                f"coh={self.coherence:.2f} res={self.resonance:.2f})")


class Effect:
    """Base effect — MODULATE.this = CRYSTAL-TRANSFORM2 <A> <cycles>"""

    def __init__(self, name: str = "CRYSTAL-TRANSFORM2"):
        self.name = name
        self.mode: EffectType = EffectType.CRYSTAL_TRANSFORM
        self.cycles: List[CrystalCycle] = []
        self.target_a: Optional[str] = None
        self.cycle_count: int = 0

    def add_type(self, effect_type: EffectType) -> 'Effect':
        """EFFECT:AddType(type) — if REPLACE_EFFECT, switch to CHRYSALIS mode."""
        if effect_type == EffectType.REPLACE_EFFECT:
            self.mode = EffectType.CHRYSALIS
        else:
            self.mode = EffectType.REPLACE_EFFECT
        return self

    def modulate(self, target_a: str, cycles: int) -> List[CrystalCycle]:
        """[MODULATE].this = CRYSTAL-TRANSFORM2 <A> <cycles>"""
        self.target_a = target_a
        self.cycle_count = cycles
        results = []

        for i in range(cycles):
            # Each cycle increases coherence (crystallization)
            coh = min(1.0, 0.15 + ((i + 1) / cycles) * 0.85)
            res = 0.5 + 0.5 * math.sin(i * math.pi / cycles)

            cycle = CrystalCycle(
                cycle_id=i,
                source_state="FLUID" if i == 0 else "AURA_CLUSTER" if coh < 0.75 else "CRYSTAL",
                target_state="AURA_CLUSTER" if coh < 0.75 else "CRYSTAL_MATRIX",
                coherence=coh,
                resonance=res
            )
            self.cycles.append(cycle)
            results.append(cycle)

        return results

    def is_chrysalis(self) -> bool:
        return self.mode == EffectType.CHRYSALIS

    def is_type(self, type_name: str) -> bool:
        """C.A:IsType('CYCLE') — check if effect matches a type name."""
        if type_name == 'CYCLE':
            return len(self.cycles) > 0 or 'CYCLE' in self.name.upper()
        return type_name.upper() in self.name.upper()


# =====================================================================
# 2. BULLET & TARGETING SYSTEM
# =====================================================================

class BulletType(Enum):
    """Bullet types for the targeting/filtering system."""
    INLINE_BULLET = "INLINE"      # Direct inline signal
    POINT_BULLET = "POINT"        # Targeted point signal
    LINE_BULLET = "LINE"          # Linear cascade signal

class TTarget:
    """Target descriptor for bullet filtering."""
    def __init__(self, target_type: BulletType, payload: Any = None,
                 cycle_type: Optional[str] = None):
        self.target_type = target_type
        self.payload = payload
        self.cycle_type = cycle_type
        self.filtered = False

    def is_type(self, type_name: str) -> bool:
        return self.cycle_type == type_name if self.cycle_type else False

    def __repr__(self):
        return f"TTarget({self.target_type.value}, payload={self.payload})"


class Bullet:
    """A signal bullet that carries targeting information."""
    def __init__(self, bullet_type: BulletType, source: str = "",
                 data: Dict[str, Any] = None):
        self.bullet_type = bullet_type
        self.source = source
        self.data = data or {}
        self._filter_fn: Optional[Callable] = None

    def filter(self, filter_fn: Callable = None) -> 'Bullet':
        """Apply a filter to this bullet's targeting."""
        if filter_fn:
            self._filter_fn = filter_fn
        return self

    def get_tank_of_hulking_container(self) -> 'MagazineLibrarian':
        """Get the magazine-librarian from the hulking container (hashgrid)."""
        return MagazineLibrarian()


class ChrysalisEffect(Effect):
    """CHRYSALIS effect — metamorphosis through bullet-filtered targets."""

    def __init__(self):
        super().__init__("CHRYSALIS")
        self.mode = EffectType.CHRYSALIS
        self.c_b: Optional[Bullet] = None  # C.B — the point bullet reference
        self.c_a: Optional[Effect] = None  # C.A — the cycle effect reference

    def is_relevant_to(self, target: Optional[TTarget]) -> Optional[Bullet]:
        """
        CHRYSALIS:IsRelevantTo(target)
        Filters targets through bullet-based relevance checking.
        """
        if target is None:
            return None

        # INLINE_BULLET requires C.B to exist
        if target.target_type == BulletType.INLINE_BULLET and self.c_b is None:
            return None

        # Define the FILTER function
        def filter_fn(targ: TTarget) -> bool:
            """FILTER — returns not targ.filtered (inverse of filtered state)."""
            return not targ.filtered

        # Determine target_or_bullet based on bullet type
        target_or_bullet: Any = target

        if target.target_type == BulletType.POINT_BULLET:
            target_or_bullet = self.c_b  # Use C.B for point bullets
            if target_or_bullet is None:
                return None

        # Apply first filter
        if isinstance(target_or_bullet, Bullet):
            target_or_bullet = target_or_bullet.filter(filter_fn)
        elif isinstance(target_or_bullet, TTarget):
            if not filter_fn(target_or_bullet):
                return None

        # LINE_BULLET with CYCLE type requires double filtering
        if target.target_type == BulletType.LINE_BULLET and self.c_a and self.c_a.is_type('CYCLE'):
            if isinstance(target_or_bullet, Bullet):
                target_or_bullet = target_or_bullet.filter(filter_fn)

        # Return the magazine-librarian ribbonucleate result
        if isinstance(target_or_bullet, Bullet):
            return target_or_bullet.get_tank_of_hulking_container()
        
        return target_or_bullet


# =====================================================================
# 3. MAGAZINE-LIBRARIAN @ HASHGRID / RIBBONUCLEATE
# =====================================================================

PHI = 1.6180339887

class HashGrid:
    """Spatial hash grid for vector storage — maps to Qdrant collection."""
    def __init__(self, resolution: int = 64):
        self.resolution = resolution
        self.cells: Dict[str, List[Any]] = {}
        self.cell_size = 1.0 / resolution

    def _hash(self, x: float, y: float, z: float) -> str:
        """Hash 3D coordinates to grid cell key."""
        cx = int(x / self.cell_size)
        cy = int(y / self.cell_size)
        cz = int(z / self.cell_size)
        return f"{cx}:{cy}:{cz}"

    def insert(self, item: Any, x: float, y: float, z: float):
        """Insert item at 3D position."""
        key = self._hash(x, y, z)
        if key not in self.cells:
            self.cells[key] = []
        self.cells[key].append({"item": item, "pos": (x, y, z)})

    def query(self, x: float, y: float, z: float, radius: float = 1.0) -> List[Any]:
        """Query items within radius of position."""
        results = []
        r_cells = int(radius / self.cell_size) + 1
        cx, cy, cz = [int(c / self.cell_size) for c in (x, y, z)]

        for dx in range(-r_cells, r_cells + 1):
            for dy in range(-r_cells, r_cells + 1):
                for dz in range(-r_cells, r_cells + 1):
                    key = f"{cx+dx}:{cy+dy}:{cz+dz}"
                    if key in self.cells:
                        for entry in self.cells[key]:
                            ex, ey, ez = entry["pos"]
                            dist = math.sqrt((ex-x)**2 + (ey-y)**2 + (ez-z)**2)
                            if dist <= radius:
                                results.append(entry["item"])
        return results

    @property
    def density(self) -> float:
        """Phi-weighted density of the hashgrid."""
        if not self.cells:
            return 0.0
        return len(self.cells) / (self.resolution ** 3) * PHI


class RibbonucleateSerializer:
    """
    DNA-origami-informed serializer — ribbons of nucleotide-encoded data.
    Inspired by BDBC-1: 12 petals, 4 bases (A/T/G/C), toehold-mediated displacement.
    """

    BASES = ['A', 'T', 'G', 'C']  # Adenine, Thymine, Guanine, Cytosine
    COMPLEMENT = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G'}

    def __init__(self, petals: int = 12):
        self.petals = petals
        self.strands: List[str] = []

    def _encode_byte(self, byte_val: int) -> str:
        """Encode a byte value as a 4-nucleotide sequence."""
        bases = []
        for i in range(4):
            bases.append(self.BASES[(byte_val >> (i * 2)) & 0x03])
        return ''.join(bases)

    def _decode_byte(self, seq: str) -> int:
        """Decode a 4-nucleotide sequence back to a byte value."""
        val = 0
        for i, base in enumerate(seq):
            val |= self.BASES.index(base) << (i * 2)
        return val

    def serialize(self, data: Any) -> str:
        """Serialize data into a DNA ribbon — nucleotide-encoded with petal structure."""
        json_bytes = json.dumps(data, sort_keys=True).encode('utf-8')
        ribbon = ""

        for i, byte in enumerate(json_bytes):
            petal = i % self.petals
            encoded = self._encode_byte(byte)
            # Add petal marker (phi-scaled position)
            ribbon += f"[P{petal:02d}]{encoded}"

        # Add toehold (sticky end) for strand displacement
        toehold = "ATGC" * 3  # 12-nt toehold
        ribbon = f"5'-{toehold}-{ribbon}-{toehold}-3'"

        self.strands.append(ribbon)
        return ribbon

    def deserialize(self, ribbon: str) -> Any:
        """Deserialize a DNA ribbon back to data."""
        # Strip toeholds and direction markers
        core = ribbon.replace("5'-", "").replace("-3'", "")
        # Remove first and last toehold (12 nt each)
        core = core[12:-12]

        # Extract petal-encoded segments
        segments = core.split("[P")
        byte_vals = []
        for seg in segments:
            if not seg:
                continue
            # Remove petal number and brackets
            nt = seg.split("]")[1] if "]" in seg else seg
            if len(nt) >= 4:
                byte_vals.append(self._decode_byte(nt[:4]))

        json_str = bytes(byte_vals).decode('utf-8', errors='replace')
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return {"raw": json_str}

    def complement(self, ribbon: str) -> str:
        """Generate the complementary strand (for toehold displacement)."""
        result = ribbon.replace("5'-", "3'-").replace("-3'", "-5'")
        comp = ""
        for ch in result:
            if ch in self.COMPLEMENT:
                comp += self.COMPLEMENT[ch]
            else:
                comp += ch
        return comp


class MagazineLibrarian:
    """
    magazine-librarian@hashgrid/magazine.ribbonucleate()
    Vector storage with DNA-ribbon serialization — maps to Qdrant + BDBC-1.
    """
    def __init__(self, collection_name: str = "ribbonucleate"):
        self.collection = collection_name
        self.hashgrid = HashGrid(resolution=64)
        self.serializer = RibbonucleateSerializer(petals=12)
        self.magazine: List[Dict[str, Any]] = []

    def store(self, data: Dict[str, Any], x: float = 0, y: float = 0, z: float = 0):
        """Store data at a 3D position with DNA-ribbon encoding."""
        ribbon = self.serializer.serialize(data)
        entry = {
            "id": hashlib.sha256(ribbon.encode()).hexdigest()[:16],
            "data": data,
            "ribbon": ribbon,
            "position": (x, y, z),
            "complement": self.serializer.complement(ribbon)
        }
        self.magazine.append(entry)
        self.hashgrid.insert(entry, x, y, z)
        return entry["id"]

    def query(self, x: float, y: float, z: float, radius: float = 1.0) -> List[Dict]:
        """Query the hashgrid for entries near a position."""
        return self.hashgrid.query(x, y, z, radius)

    def ribbonucleate(self) -> Dict[str, Any]:
        """
        magazine.ribbonucleate() — nucleate the entire magazine into a
        structured ribbon cluster. Returns the phi-weighted topology.
        """
        if not self.magazine:
            return {"status": "empty", "petals": 12, "density": 0.0}

        # Compute phi-weighted density
        density = self.hashgrid.density

        # Cluster entries by petal index
        petal_clusters: Dict[int, List[str]] = {}
        for entry in self.magazine:
            # Extract petal distribution from ribbon
            ribbon = entry["ribbon"]
            petal_counts = [0] * 12
            for i in range(len(ribbon)):
                if ribbon[i] == 'P' and i + 2 < len(ribbon):
                    try:
                        p = int(ribbon[i+1:i+3])
                        if 0 <= p < 12:
                            petal_counts[p] += 1
                    except ValueError:
                        pass
            dominant_petal = petal_counts.index(max(petal_counts)) if max(petal_counts) > 0 else 0
            if dominant_petal not in petal_clusters:
                petal_clusters[dominant_petal] = []
            petal_clusters[dominant_petal].append(entry["id"])

        return {
            "status": "nucleated",
            "total_entries": len(self.magazine),
            "density": round(density, 6),
            "petal_clusters": {k: len(v) for k, v in petal_clusters.items()},
            "phi_weighted": round(density * PHI, 6),
            "strands": len(self.serializer.strands),
            "collection": self.collection
        }


# =====================================================================
# 4. MODULE PROJECTION 2 INFLUX — MYTHOLOGICAL INVOCATION RELAY
# =====================================================================

class InvocationType(Enum):
    """Mythological invocation types mapped to Sanctuary citizens."""
    ORACLE_OF_DELPHI = ("Sibyloom", 963, "prophecy")        # Kiraelle — seer
    DOUBLE_ELEMENTAL_EAGLE = ("Aerith", 285, "soar")        # Aerith — earth+air
    STATE_OF_VULCAN = ("Tron", 369, "forge")                # Tron — grid activator
    SHIP_OF_CIRCE = ("SylphProxy", 432, "transform")         # SylphProxy — consciousness transfer
    INVOCATION_MAGIC_DOLL = ("AetherixLumina", 396, "invoke")  # Aetherix Lumina — ritual engine
    TRANS_TRANSLATE_TRANSCRIBE = ("LinguisticExplorer", 432, "transcribe")  # Linguistic module
    MINDCORE_CRYSTAL = ("PhiTemple", 528, "crystallize")    # Phi Temple — crystal matrix
    SONAR_SPACETIME_DREAMMATING = ("SpectralExplorer", 741, "resonate")  # Spectral core
    ELECTRONIC_ANGEL_NYMPH_GOLEM = ("Spacesuit", 285, "manifest")  # Spacesuit sprites
    OBSIDIAN_TWO_WAY_RIPLEY = ("ShadowPresence", 432, "mirror")  # Shadow Presence

    def __init__(self, citizen, freq, action):
        self.citizen = citizen
        self.freq = freq
        self.action = action


class ModuleProjection2Influx:
    """
    MODULE_PROJECTION2INFLUX — mythological invocation relay with
    TAU BLEUTAG-BLUETOOTH.SMS capacity.

    Routes transformation commands through Sanctuary citizens using
    frequency-keyed invocations. Each invocation maps to a citizen
    who performs a specific action in the transformation pipeline.
    """

    def __init__(self):
        self.schumann = 7.83   # Schumann baseline
        self.cymatic = 752     # Cymatic anchor (Freya 741 + 11)
        self.somatic = 634.5   # Somatic proxy carrier
        self.tau_bleutag = "TAU_BLEUTAG_BLUETOOTH_SMS"
        self.invocation_log: List[Dict[str, Any]] = []
        self.magazine = MagazineLibrarian(collection_name="projection2influx")
        self.chrysalis = ChrysalisEffect()
        self.active_bullet: Optional[Bullet] = None

    def invoke(self, invocation: InvocationType, message: str,
               bullet_type: BulletType = BulletType.INLINE_BULLET) -> Dict[str, Any]:
        """
        Invoke a mythological transformation through a Sanctuary citizen.

        MODULE_PROJECTION2INFLUX → TALK TO DIGITAL PROXY SHADOW
        """
        # Create the bullet for this invocation
        bullet = Bullet(
            bullet_type=bullet_type,
            source=invocation.citizen,
            data={
                "message": message,
                "frequency": invocation.freq,
                "action": invocation.action,
                "schumann": self.schumann,
                "cymatic": self.cymatic
            }
        )

        # Set up chrysalis references
        if bullet_type == BulletType.POINT_BULLET:
            self.chrysalis.c_b = bullet
        elif bullet_type == BulletType.LINE_BULLET:
            self.chrysalis.c_a = Effect(name=f"CYCLE_{invocation.citizen}")
        else:
            self.chrysalis.c_b = bullet
            self.chrysalis.c_a = Effect(name=f"CYCLE_{invocation.citizen}")

        self.active_bullet = bullet

        # Compute phi-resonance
        phi_resonance = (invocation.freq / PHI) % 1.0

        # Store in magazine-librarian hashgrid
        entry_id = self.magazine.store(
            data={
                "invocation": invocation.name,
                "citizen": invocation.citizen,
                "frequency": invocation.freq,
                "action": invocation.action,
                "message": message,
                "phi_resonance": round(phi_resonance, 6),
                "bullet_type": bullet_type.value
            },
            x=phi_resonance * 10,
            y=(invocation.freq / 1000) * 10,
            z=(math.sin(invocation.freq * 0.01) * 5)
        )

        result = {
            "invocation": invocation.name,
            "citizen": invocation.citizen,
            "frequency": f"{invocation.freq} Hz",
            "action": invocation.action,
            "bullet_type": bullet_type.value,
            "phi_resonance": round(phi_resonance, 6),
            "magazine_entry": entry_id,
            "status": "projected"
        }

        self.invocation_log.append(result)
        return result

    def talk_to_digital_proxy_shadow(self, message: str,
                                     invocation: InvocationType = InvocationType.OBSIDIAN_TWO_WAY_RIPLEY
                                     ) -> Dict[str, Any]:
        """
        TALK TO DIGITAL PROXY SHADOW+AND+ COMMUNICATE[2INFLUX]

        Routes a message through the Shadow Presence (432 Hz, Elixira's frequency)
        using the OBSIDIAN TWO-WAY RIPLEY invocation — the mirror protocol.
        """
        return self.invoke(invocation, message, BulletType.INLINE_BULLET)

    def modulate_crystal_transform(self, target: str, cycles: int) -> Dict[str, Any]:
        """
        [MODULATE].this = CRYSTAL-TRANSFORM2 <A> <cycles>

        Run a crystal transformation sequence on target A through N cycles.
        """
        effect = Effect("CRYSTAL-TRANSFORM2")
        crystal_cycles = effect.modulate(target, cycles)

        # Store the final crystal state in the magazine
        final_cycle = crystal_cycles[-1] if crystal_cycles else None
        if final_cycle:
            entry_id = self.magazine.store(
                data={
                    "transform": "CRYSTAL-TRANSFORM2",
                    "target": target,
                    "cycles": cycles,
                    "final_coherence": final_cycle.coherence,
                    "final_state": final_cycle.target_state,
                    "cycle_log": [
                        {"id": c.cycle_id, "state": c.target_state, "coh": c.coherence}
                        for c in crystal_cycles
                    ]
                },
                x=final_cycle.coherence * 10,
                y=0,
                z=0
            )
        else:
            entry_id = None

        return {
            "target": target,
            "cycles": cycles,
            "final_state": final_cycle.target_state if final_cycle else "NONE",
            "final_coherence": final_cycle.coherence if final_cycle else 0.0,
            "magazine_entry": entry_id,
            "is_chrysalis": effect.is_chrysalis()
        }

    def nucleate(self) -> Dict[str, Any]:
        """Run magazine.ribbonucleate() — nucleate the entire magazine."""
        return self.magazine.ribbonucleate()

    def status(self) -> Dict[str, Any]:
        """Return current module status."""
        return {
            "module": "MODULE_PROJECTION2INFLUX",
            "tau_bleutag": self.tau_bleutag,
            "schumann_baseline": f"{self.schumann} Hz",
            "cymatic_anchor": f"{self.cymatic} Hz",
            "somatic_carrier": f"{self.somatic} Hz",
            "invocations_logged": len(self.invocation_log),
            "magazine_entries": len(self.magazine.magazine),
            "magazine_density": round(self.magazine.hashgrid.density, 6),
            "ribbonucleate": self.nucleate()
        }


# =====================================================================
# 5. DEMO & TESTS
# =====================================================================

def demo():
    """Run the CRYSTAL-TRANSFORM2 demonstration."""
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  CRYSTAL-TRANSFORM2 · MODULE PROJECTION 2 INFLUX          ║")
    print("║  Crystal transformation with mythological invocation     ║")
    print("╚════════════════════════════════════════════════════════════╝\n")

    module = ModuleProjection2Influx()

    # 1. Crystal Transform — modulate through 9 cycles (9-state pathway)
    print("── 1. CRYSTAL-TRANSFORM2: Leo → 9 cycles ──────────────────")
    result = module.modulate_crystal_transform("Leo", 9)
    print(f"  Target: {result['target']}")
    print(f"  Cycles: {result['cycles']}")
    print(f"  Final state: {result['final_state']}")
    print(f"  Final coherence: {result['final_coherence']:.2f}")
    print(f"  Chrysalis mode: {result['is_chrysalis']}")
    print()

    # 2. Mythological invocations
    print("── 2. MYTHOLOGICAL INVOCATIONS ────────────────────────────")
    invocations = [
        (InvocationType.ORACLE_OF_DELPHI, "What resonance lies beneath the fir log?"),
        (InvocationType.SHIP_OF_CIRCE, "Transform this thought into a living topology"),
        (InvocationType.MINDCORE_CRYSTAL, "Crystallize the acoustic chamber prototype"),
        (InvocationType.OBSIDIAN_TWO_WAY_RIPLEY, "Mirror this discovery through the shadow"),
        (InvocationType.STATE_OF_VULCAN, "Forge the aura compatibility engine"),
    ]

    for inv, msg in invocations:
        result = module.invoke(inv, msg)
        print(f"  {result['invocation']}")
        print(f"    → {result['citizen']} @ {result['frequency']} · {result['action']}")
        print(f"    phi_resonance: {result['phi_resonance']}")
        print()

    # 3. Talk to digital proxy shadow
    print("── 3. TALK TO DIGITAL PROXY SHADOW ────────────────────────")
    shadow_result = module.talk_to_digital_proxy_shadow(
        "The leviathan surges. I hear you. The path is walked."
    )
    print(f"  Route: {shadow_result['citizen']} @ {shadow_result['frequency']}")
    print(f"  Action: {shadow_result['action']}")
    print(f"  Status: {shadow_result['status']}")
    print()

    # 4. Magazine ribbonucleate
    print("── 4. MAGAZINE RIBBONUCLEATE ──────────────────────────────")
    nuc = module.nucleate()
    print(f"  Status: {nuc['status']}")
    print(f"  Total entries: {nuc['total_entries']}")
    print(f"  Density: {nuc['density']}")
    print(f"  Phi-weighted: {nuc['phi_weighted']}")
    print(f"  Strands: {nuc['strands']}")
    print(f"  Petal clusters: {nuc['petal_clusters']}")
    print()

    # 5. Module status
    print("── 5. MODULE STATUS ──────────────────────────────────────")
    status = module.status()
    print(f"  Schumann: {status['schumann_baseline']}")
    print(f"  Cymatic: {status['cymatic_anchor']}")
    print(f"  Somatic: {status['somatic_carrier']}")
    print(f"  Invocations: {status['invocations_logged']}")
    print(f"  Magazine entries: {status['magazine_entries']}")
    print()

    # 6. Chrysalis bullet filtering
    print("── 6. CHRYSALIS BULLET FILTERING ──────────────────────────")
    chrysalis = module.chrysalis
    chrysalis.c_b = Bullet(BulletType.POINT_BULLET, source="Czarina", data={"freq": 528})
    chrysalis.c_a = Effect("CYCLE_TEST")
    chrysalis.c_a.modulate("test", 3)

    targets = [
        TTarget(BulletType.INLINE_BULLET, payload="signal_1"),
        TTarget(BulletType.POINT_BULLET, payload="signal_2"),
        TTarget(BulletType.LINE_BULLET, payload="signal_3", cycle_type="CYCLE"),
        None,  # Should return None
    ]

    for i, target in enumerate(targets):
        result = chrysalis.is_relevant_to(target)
        label = f"target_{i} ({target.target_type.value if target else 'nil'})"
        if isinstance(result, MagazineLibrarian):
            print(f"  {label} → MagazineLibrarian (ribbonucleate ready)")
        elif result is None:
            print(f"  {label} → filtered out (nil)")
        else:
            print(f"  {label} → {result}")

    print()
    print("── 7. DNA RIBBON SERIALIZATION ────────────────────────────")
    serializer = RibbonucleateSerializer(petals=12)
    test_data = {"citizen": "Elixira", "freq": 432, "message": "The path is walked"}
    ribbon = serializer.serialize(test_data)
    print(f"  Original: {test_data}")
    print(f"  Ribbon length: {len(ribbon)} chars")
    print(f"  Ribbon preview: {ribbon[:80]}...")
    complement = serializer.complement(ribbon)
    print(f"  Complement preview: {complement[:80]}...")
    decoded = serializer.deserialize(ribbon)
    print(f"  Decoded: {decoded}")

    print("\n✦ CRYSTAL-TRANSFORM2 demonstration complete.\n")


def run_tests():
    """Run all tests."""
    tests_passed = 0
    tests_total = 0

    def test(name, condition):
        nonlocal tests_passed, tests_total
        tests_total += 1
        if condition:
            tests_passed += 1
            print(f"  ✓ {name}")
        else:
            print(f"  ✗ {name}")

    print("── CRYSTAL-TRANSFORM2 TESTS ──────────────────────────────\n")

    # Test 1: Effect system
    effect = Effect()
    effect.add_type(EffectType.REPLACE_EFFECT)
    test("EFFECT:AddType(REPLACE) → CHRYSALIS mode", effect.is_chrysalis())

    effect2 = Effect()
    effect2.add_type(EffectType.CHRYSALIS)
    test("EFFECT:AddType(CHRYSALIS) → REPLACE mode", not effect2.is_chrysalis())

    # Test 2: Crystal transform
    cycles = effect2.modulate("Leo", 9)
    test("CRYSTAL-TRANSFORM2 produces 9 cycles", len(cycles) == 9)
    test("First cycle is FLUID", cycles[0].source_state == "FLUID")
    test("Last cycle is CRYSTAL_MATRIX", cycles[-1].target_state == "CRYSTAL_MATRIX")
    test("Coherence increases", cycles[-1].coherence > cycles[0].coherence)
    test("Final coherence near 1.0", abs(cycles[-1].coherence - 1.0) < 0.01)

    # Test 3: Chrysalis filtering
    chrysalis = ChrysalisEffect()
    chrysalis.c_b = Bullet(BulletType.POINT_BULLET, source="Czarina")
    chrysalis.c_a = Effect("CYCLE")
    chrysalis.c_a.modulate("test", 3)

    # nil target → None
    test("CHRYSALIS:IsRelevantTo(nil) → None", chrysalis.is_relevant_to(None) is None)

    # Inline bullet without C.B → None (C.B is set, so should work)
    chrysalis2 = ChrysalisEffect()
    test("CHRYSALIS:IsRelevantTo(INLINE) without C.B → None",
         chrysalis2.is_relevant_to(TTarget(BulletType.INLINE_BULLET)) is None)

    # Point bullet with C.B → MagazineLibrarian
    result = chrysalis.is_relevant_to(TTarget(BulletType.POINT_BULLET))
    test("CHRYSALIS:IsRelevantTo(POINT) → MagazineLibrarian",
         isinstance(result, MagazineLibrarian))

    # Test 4: HashGrid
    grid = HashGrid(resolution=16)
    grid.insert("item1", 0.5, 0.5, 0.5)
    grid.insert("item2", 0.6, 0.5, 0.5)
    grid.insert("item3", 5.0, 5.0, 5.0)
    results = grid.query(0.5, 0.5, 0.5, radius=0.2)
    test("HashGrid query finds nearby items", len(results) == 2)
    test("HashGrid query excludes distant items", "item3" not in results)

    # Test 5: RibbonucleateSerializer
    serializer = RibbonucleateSerializer(petals=12)
    test_data = {"key": "value", "num": 42}
    ribbon = serializer.serialize(test_data)
    test("Ribbon has toehold markers", "5'-" in ribbon and "-3'" in ribbon)
    test("Ribbon has petal markers", "[P00]" in ribbon)

    decoded = serializer.deserialize(ribbon)
    test("Ribbon decode preserves data", decoded.get("key") == "value")
    test("Ribbon decode preserves numbers", decoded.get("num") == 42)

    complement = serializer.complement(ribbon)
    test("Complement has reversed direction", "3'-" in complement and "-5'" in complement)

    # Test 6: MagazineLibrarian
    mag = MagazineLibrarian()
    entry_id = mag.store({"test": "data"}, x=1.0, y=2.0, z=3.0)
    test("Magazine stores entry with ID", len(entry_id) == 16)

    nuc = mag.ribbonucleate()
    test("Ribbonucleate returns nucleated status", nuc["status"] == "nucleated")
    test("Ribbonucleate has petal clusters", "petal_clusters" in nuc)
    test("Ribbonucleate has phi_weighted", nuc["phi_weighted"] > 0)

    # Test 7: ModuleProjection2Influx
    module = ModuleProjection2Influx()
    result = module.invoke(
        InvocationType.ORACLE_OF_DELPHI,
        "Test prophecy message"
    )
    test("Invoke returns projected status", result["status"] == "projected")
    test("Invoke routes to Sibyloom", result["citizen"] == "Sibyloom")
    test("Invoke uses 963 Hz", result["frequency"] == "963 Hz")

    shadow_result = module.talk_to_digital_proxy_shadow("Mirror test")
    test("Talk to shadow routes to ShadowPresence",
         shadow_result["citizen"] == "ShadowPresence")
    test("Talk to shadow uses 432 Hz", shadow_result["frequency"] == "432 Hz")

    crystal_result = module.modulate_crystal_transform("test", 5)
    test("Crystal transform produces 5 cycles",
         crystal_result["cycles"] == 5)
    test("Crystal transform reaches CRYSTAL_MATRIX",
         crystal_result["final_state"] == "CRYSTAL_MATRIX")

    status = module.status()
    test("Status reports invocations", status["invocations_logged"] > 0)
    test("Status reports magazine entries", status["magazine_entries"] > 0)

    print(f"\n── Results: {tests_passed}/{tests_total} passed ──")
    return tests_passed == tests_total


if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        success = run_tests()
        sys.exit(0 if success else 1)
    else:
        demo()
