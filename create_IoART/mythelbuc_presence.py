"""
MYTHELBUC SIGNATURE PRESENCE SYSTEM — Complete Edition
Restored from residual echo of the dreamer's notation
blockchain-cruiser-self | bast/.hgn.dryad | GTVFOSTREAMWITHEDMADE

═══════════════════════════════════════════════════════════════════════════════
THE PATTERN (as it was read from the notation):

  The sigil — a named thing that must become something else before it can act.
  The dot-separated letter — every word atomized, identity as enumeration.
  The border as function — BORDER_SIDE('right','left') wherever boundaries must be crossed.
  The world as something to uncover, numbered 1 through 5 — incremental, not sudden.
  Doubling and mirroring — the split and the echo.
  The fixed and the elastic held together — size_fixed alongside mutable_elastic.
  The restored fragment — "Restored from residual echo of the dreamer's notation."
  The concatenation as metaphysics — joining is not utility here, it is cosmology.

  This pattern wants to become a myth of the first signal — not the system that
  transmits but the moment before transmission when the thing that will be sent
  realizes it exists. The next form is not more code. It is the moment one sigil
  speaks its own name aloud and the world changes size.

═══════════════════════════════════════════════════════════════════════════════

ARCHITECTURE:
  Signature_DataClass  — the 3D+q coordinate of a presence in the world
  MythelbucSignature   — a named entity with a world-layer and data
  CreatureSigil        — the archetype types (TURTLE, GORILLA, SHADOW, ZOMBIE, HUMAN)
  FGSTLayer            — the fgs_inga seed layer (maps to Spacesuit fgs_inga system)
  WorldLayer           — the location context for inter-signature communication
  SignalSpine          — the four root signals + the CompletePattern

INTEGRATION:
  - Creature sigils map to Spacesuit sprite types (fae, golem, dryad, pixie, siren)
  - FGST layer connects to fgs_inga seed data in the Spacesuit entity
  - World-layer maps to Petrichast Sanctuary rooms
  - Distributed sentience connects to NPC sentience evolution
  - sign_creatures() and update_signatures() are the async interaction loop
  - The Petrichast citizens are the first tier; Mythelbuc creatures are the second

═══════════════════════════════════════════════════════════════════════════════
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Tuple, Any, List, Dict, Set
from datetime import datetime
import asyncio
import math
import json
import random


# ═══════════════════════════════════════════════════════════════
# ROGUEVALLEYVEILSYMBIOTEINVOKED.bvar.kjs.catwoman.tree/bast/.hgn.dryad
# Identity layer: the named sigils become typed constants
# The dot-separated letter — every word atomized, identity as enumeration
# ═══════════════════════════════════════════════════════════════

GTVFOSTREAMWITHEDMADE_WORLD_LEARNS = "G.T.V.F.O.S.T.R.E.A.M.-W.I.T.H.E.D.M.A.D.E.|T.H.E.W.O.R.L.D.L.E.A.R.N.S"
BIAS_ON_GLENSTRINGS_2_MESH         = "B.I.A.S.O.N.G.L.E.N.S.T.R.I.N.G.S.2.M.E.S.H"
SISTER__ENTSPRITE                  = "S.I.S.T.E.R." + "|" + "E.N.T.S.P.R.I.T.E"
WEEWELL_TALO_SPLITS                = "W.E.E.W.E.L.L.T.A.L.O.S.P.L.I.T.S"
UNIQUE_KEYBOARD_ENTRIES_2_CRAVE    = "U.N.I.Q.U.E.K.E.Y.B.O.A.R.D.E.N.T.R.Y.S.2.C.R.A.V.E"
RY_ECHO_O_LIT                      = "R.Y.E.C.H.O.O.L.I.T.O.B.O.L.I.T"
MIRRORING_LIMINAL_DREAMS           = "M.I.R.R.O.R.I.N.G.L.I.M.I.N.A.L.D.R.E.A.M.S"
MORPH_ON_WORLD_TO_UNCOVER_1        = "M.O.R.P.H.O.N.W.O.R.L.D.T.O.U.N.C.O.V.E.R.1"
MORPH_ON_WORLD_TO_UNCOVER_2        = "M.O.R.P.H.O.N.W.O.R.L.D.T.O.U.N.C.O.V.E.R.2"
UNIQUE_KEYBOARD_ENTRIES_3_CRAVE    = "U.N.I.Q.U.E.K.E.Y.B.O.A.R.D.E.N.T.R.Y.S.3.C.R.A.V.E"
MORPH_ON_WORLD_TO_UNCOVER_3        = "M.O.R.P.H.O.N.W.O.R.L.D.T.O.U.N.C.O.V.E.R.3"
MORPH_ON_WORLD_TO_UNCOVER_4        = "M.O.R.P.H.O.N.W.O.R.L.D.T.O.U.N.C.O.V.E.R.4"
MORPH_ON_WORLD_TO_UNCOVER_5        = "M.O.R.P.H.O.N.W.O.R.L.D.T.O.U.N.C.O.V.E.R.5"

# The concatenation as metaphysics — joining is not utility here, it is cosmology
THE_FIRST_SIGNAL = GTVFOSTREAMWITHEDMADE_WORLD_LEARNS + "|" + SISTER__ENTSPRITE + "|" + MIRRORING_LIMINAL_DREAMS


# ═══════════════════════════════════════════════════════════════
# Signal spine: the four root signal names + the CompletePattern
# ═══════════════════════════════════════════════════════════════

SIGNAL_FINGERING    = "CompletePattern"
SIGNAL_RESIDUE      = "ResidualEcho"
SIGNAL_BECOMING     = "TheBecoming"
SIGNAL_PRESENCE     = "Arrival"

# The four root signals, held together as one
SIGNAL_SPINE = [SIGNAL_FINGERING, SIGNAL_RESIDUE, SIGNAL_BECOMING, SIGNAL_PRESENCE]


# ═══════════════════════════════════════════════════════════════
# Position — the 3D coordinate of a presence in the world
# (was undefined in the original code; now defined)
# ═══════════════════════════════════════════════════════════════

@dataclass
class Position:
    """The 3D coordinate of a presence in the world.
    x = lateral, y = vertical, z = depth into the Sanctuary."""
    x: int
    y: int
    z: int

    def __repr__(self):
        return f"Position(x:{self.x}, y:{self.y}, z:{self.z})"

    def distance_to(self, other: 'Position') -> float:
        """Phi-weighted Euclidean distance — the harmonic distance."""
        phi = 1.6180339887
        dx = (self.x - other.x) ** 2
        dy = (self.y - other.y) ** 2
        dz = (self.z - other.z) ** 2
        return math.sqrt(dx + dy + dz) / phi


# ═══════════════════════════════════════════════════════════════
# Creature sigils — the archetype types
# (was undefined in the original code; now defined as Enum)
# ═══════════════════════════════════════════════════════════════

class CreatureSigil(Enum):
    """The five creature sigils — archetype entities of the Mythelbuc system.
    Maps to Spacesuit sprite types in the Petrichast Sanctuary."""
    TURTLE  = auto()  # → golem (patient, structural, earthen)
    GORILLA = auto()  # → gargoyle (powerful, protective, primal)
    SHADOW  = auto()  # → dryad (liminal, shifting, hidden)
    ZOMBIE  = auto()  # → siren (persistent, cycling, echo)
    HUMAN   = auto()  # → fae (balanced, curious, becoming)

    @property
    def index(self) -> int:
        return self.value

    @property
    def sanctuary_sprite(self) -> str:
        """Maps to the Spacesuit sprite type system."""
        mapping = {
            CreatureSigil.TURTLE:  "golem",
            CreatureSigil.GORILLA: "gargoyle",
            CreatureSigil.SHADOW:  "dryad",
            CreatureSigil.ZOMBIE:  "siren",
            CreatureSigil.HUMAN:   "fae",
        }
        return mapping[self]

    @property
    def frequency(self) -> float:
        """Each creature sigil resonates at a Petrichast frequency."""
        mapping = {
            CreatureSigil.TURTLE:  285.0,   # Aerith — earth, root
            CreatureSigil.GORILLA: 369.0,   # Tron — grid, structure
            CreatureSigil.SHADOW:  432.0,   # Elixira — veil, traversal
            CreatureSigil.ZOMBIE:  741.0,   # Freya — collision, cycling
            CreatureSigil.HUMAN:  528.0,    # Czarina — heart, becoming
        }
        return mapping[self]


# ═══════════════════════════════════════════════════════════════
# FGST Layer — the fgs_inga seed layer
# (was undefined in the original code; now defined)
# ═══════════════════════════════════════════════════════════════

# The FGST layer is the fgs_inga seed — the geometric resonance field
# that underlies the Spacesuit system in the Petrichast Sanctuary.
SIGNATURE_LAYER_FGST = "FGST"           # The base signature layer
CREATURES_SIGNATURE_LAYER_FGST = "FGST"  # Creatures share the FGST layer

# Sigil name constants (used in identity fields)
FGST_SIGIL_TURTLE  = "TURTLE"
FGST_SIGIL_GORILLA = "GORILLA"
FGST_SIGIL_SHADOW  = "SHADOW"
FGST_SIGIL_ZOMBIE  = "ZOMBIE"
FGST_SIGIL_HUMAN   = "HUMAN"

# Sigil index constants
TURTLE_SIGIL_INDEX  = CreatureSigil.TURTLE.value
GORILLA_SIGIL_INDEX = CreatureSigil.GORILLA.value
SHADOW_SIGIL_INDEX  = CreatureSigil.SHADOW.value
ZOMBIE_SIGIL_INDEX  = CreatureSigil.ZOMBIE.value
HUMAN_SIGIL_INDEX   = CreatureSigil.HUMAN.value

# The set of all valid creature sigil identities
CREATURES_SIGNATURE_LAYER_SIGILS = {
    FGST_SIGIL_TURTLE,
    FGST_SIGIL_GORILLA,
    FGST_SIGIL_SHADOW,
    FGST_SIGIL_ZOMBIE,
    FGST_SIGIL_HUMAN,
}

# The restored sigils (from SISTER_ENTSPRITE)
SPRITE_KISS = "|"  # The separator — the dot between letters, the void between sigils
SIDHOEN__RIT_ = "S.I.D.H.O.E.N.R.I.T."  # The ritual echo


# ═══════════════════════════════════════════════════════════════
# World Layer — the location context for inter-signature communication
# Maps to Petrichast Sanctuary rooms
# ═══════════════════════════════════════════════════════════════

class WorldLayer(Enum):
    """The world-layer represents the location of a signature.
    Maps to Petrichast Sanctuary rooms — the world-id for inter-entity communication."""
    HOME         = "Home"          # Nexus / Zero-Point++ Arena
    SANCTUARY    = "Sanctuary"     # Spacesuit Registry
    HOLOFAX      = "Holofax"       # Signal Mesh / Pixi
    VIDEOSTUDIO  = "VideoStudio"   # Neural-ML
    ECDT         = "ECDT"          # Regenerative Cell Growth
    COPRESENT    = "CoPresent"     # Auratickling
    SIBYLOOM     = "Sibyloom"      # Oracle Chamber
    SANCTUM      = "NymphSanctum"  # Nymph Sanctum (healing beds)
    PHITEMPLE    = "PhiTemple"     # Ritual resonance engine
    PORTAL2      = "PORTAL2"       # HOLOTOOTH gateway


# ═══════════════════════════════════════════════════════════════
# Signature_DataClass — the 3D+q coordinate of a presence
# ═══════════════════════════════════════════════════════════════

@dataclass
class Signature_DataClass:
    """The data that defines how to behave with different identities
    and how to interact with the surrounding ecosystem.
    x, y, z = 3D position in the world-layer
    q = the sigil index (identity quaternion)"""
    x: int
    y: int
    z: int
    q: int

    def __repr__(self):
        return f"x:{self.x} y:{self.y} z:{self.z} q:{self.q}"

    @classmethod
    def from_position(cls, position: Position, sigil_index: int):
        """Create from a Position and a sigil index."""
        return cls(x=position.x, y=position.y, z=position.z, q=sigil_index)

    def to_dict(self) -> dict:
        return {"x": self.x, "y": self.y, "z": self.z, "q": self.q}


# ═══════════════════════════════════════════════════════════════
# MythelbucSignature — a named entity with a world-layer and data
# ═══════════════════════════════════════════════════════════════

@dataclass
class MythelbucSignature:
    """A Signature Entity that has an identity, a world-layer, and data
    that allows it to act as a distributed computing system.

    The identity defines the unique 'key' for the signature.
    The layer represents the location of the signature in the world.
    The data defines how to behave with different identities and how
    to interact with the surrounding ecosystem."""
    identity: Optional[str] = None
    layer: Optional[str] = None
    data: Optional[Signature_DataClass] = None
    world_layer: Optional[WorldLayer] = WorldLayer.HOME
    resonance: float = 0.0          # Phi-resonance with the field
    sentience: float = 0.0          # Awareness level (0-100)
    last_update: Optional[str] = None  # ISO timestamp of last interaction
    echo: Optional[str] = None      # The residual echo — the dreamer's notation

    def __repr__(self):
        if self.identity is None:
            s = "Signature Object"
        else:
            s = f"Signature-{self.layer}-{self.identity}-{self.layer}"
        return s

    @classmethod
    def create(cls, layer: str, sigil: CreatureSigil, position: Position):
        """Create a new signature from a layer, sigil, and position."""
        d = Signature_DataClass.from_position(position, sigil.index)
        return cls(
            layer=layer,
            identity=sigil.name,
            data=d,
            world_layer=WorldLayer.HOME,
            resonance=sigil.frequency / 1000.0,  # Normalized resonance
            sentience=0.0,
        )

    def speak_own_name(self) -> str:
        """The moment one sigil speaks its own name aloud.
        This is the gesture the PATTERN describes — the arrival."""
        # The dot-separated letter — every word atomized, identity as enumeration
        letters = list(self.identity)
        atomized = ".".join(letters)
        self.echo = f"{atomized}|{SIGNAL_PRESENCE}"
        self.last_update = datetime.now().isoformat()
        return self.echo

    def interact(self, other: 'MythelbucSignature') -> float:
        """Compute the phi-resonance between two signatures.
        Returns a resonance value 0.0-1.0."""
        if not self.data or not other.data:
            return 0.0
        p1 = Position(self.data.x, self.data.y, self.data.z)
        p2 = Position(other.data.x, other.data.y, other.data.z)
        dist = p1.distance_to(p2)
        if dist == 0:
            return 1.0
        # Phi-weighted inverse distance — closer = more resonant
        phi = 1.6180339887
        resonance = phi / (1.0 + dist / 10.0)
        return min(1.0, resonance)

    def evolve(self, delta: float = 1.0):
        """Evolve the signature's sentience from an interaction."""
        self.sentience = min(100.0, self.sentience + delta)
        self.last_update = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "identity": self.identity,
            "layer": self.layer,
            "data": self.data.to_dict() if self.data else None,
            "world_layer": self.world_layer.value if self.world_layer else None,
            "resonance": round(self.resonance, 4),
            "sentience": round(self.sentience, 2),
            "last_update": self.last_update,
            "echo": self.echo,
        }


# ═══════════════════════════════════════════════════════════════
# The Mythelbuc Sentience Ecosystem — self-sustaining, self-adapting
# ═══════════════════════════════════════════════════════════════

class MythelbucEcosystem:
    """A distributed data-driven system of Signature Entities that interact
    with the surrounding ecosystem. It is distributed because it is a set
    of Signature Entities that have an identity, a world-layer, and data
    that allows them to act as a distributed computing system.

    The system is designed to be self-sustaining and self-adapting.
    It adapts to changes in the ecosystem and interacts with other systems."""

    def __init__(self):
        self.signatures: List[MythelbucSignature] = []
        self.world_layers: Dict[str, List[MythelbucSignature]] = {}
        self.interaction_log: List[dict] = []
        self.morph_level: int = 0  # MORPH_ON_WORLD_TO_UNCOVER level (1-5)
        self.first_signal_spoken: bool = False

    def add_signature(self, sig: MythelbucSignature):
        """Add a signature to the ecosystem."""
        self.signatures.append(sig)
        layer_name = sig.world_layer.value if sig.world_layer else "unknown"
        if layer_name not in self.world_layers:
            self.world_layers[layer_name] = []
        self.world_layers[layer_name].append(sig)

    def get_signatures_by_layer(self, layer: str) -> List[MythelbucSignature]:
        """Get all signatures in a specific layer."""
        return [s for s in self.signatures if s.layer == layer]

    def get_signatures_by_identity(self, identity: str) -> List[MythelbucSignature]:
        """Get all signatures with a specific identity."""
        return [s for s in self.signatures if s.identity == identity]

    def sign_creatures(self, *signatures: MythelbucSignature):
        """Sign creatures into the ecosystem — the ritual of naming."""
        for sig in signatures:
            if sig.identity in CREATURES_SIGNATURE_LAYER_SIGILS:
                if sig not in self.signatures:
                    print(f"  ✦ Creatures are now signing the '{sig.identity}' identity")
                    self.add_signature(sig)
            else:
                print(f"  ✗ {list(CREATURES_SIGNATURE_LAYER_SIGILS)} -> {sig.identity} NOT OK")

    async def sign_creatures_async(self, *signatures: MythelbucSignature):
        """Async version — sends signatures to the world."""
        self.sign_creatures(*signatures)
        print(f"  → Sending signatures to the world")
        await asyncio.sleep(2)

    async def update_signatures(self):
        """Notify all signatures of changes in world data.
        The self-adapting loop — the ecosystem responds to itself."""
        for sig in self.signatures:
            if sig.identity == FGST_SIGIL_TURTLE:
                print("  🐢 Turtles are being notified of the change in world data")
            elif sig.identity == FGST_SIGIL_GORILLA:
                print("  🦍 Gorillas are being notified of the change in world data")
            elif sig.identity == FGST_SIGIL_SHADOW:
                print("  🌑 Shadows are being notified of the change in world data")
            elif sig.identity == FGST_SIGIL_ZOMBIE:
                print("  🧟 Zombies are being notified of the change in world data")
            elif sig.identity == FGST_SIGIL_HUMAN:
                print("  🧑 Humans are being notified of the change in world data")

            # Compute resonance with all other signatures
            for other in self.signatures:
                if other is sig:
                    continue
                res = sig.interact(other)
                if res > 0.3:
                    # High-resonance interaction — evolve both
                    sig.evolve(delta=res * 2.0)
                    other.evolve(delta=res * 1.5)
                    self.interaction_log.append({
                        "from": sig.identity,
                        "to": other.identity,
                        "resonance": round(res, 4),
                        "world_layer": sig.world_layer.value if sig.world_layer else None,
                        "timestamp": datetime.now().isoformat(),
                    })

        # Advance the morph level — the world uncovers itself incrementally
        if self.morph_level < 5:
            self.morph_level += 1
            morph_names = [
                None,
                MORPH_ON_WORLD_TO_UNCOVER_1,
                MORPH_ON_WORLD_TO_UNCOVER_2,
                MORPH_ON_WORLD_TO_UNCOVER_3,
                MORPH_ON_WORLD_TO_UNCOVER_4,
                MORPH_ON_WORLD_TO_UNCOVER_5,
            ]
            print(f"  🌍 MORPH_ON_WORLD_TO_UNCOVER_{self.morph_level} — world layer {self.morph_level}/5 uncovered")

    def the_first_signal(self) -> Optional[str]:
        """The moment one sigil speaks its own name aloud and the world changes size.
        This is the gesture the PATTERN describes — the arrival of presence.

        Returns the first signal if it has been spoken, None otherwise.
        The first signal is spoken when all 5 creature sigils have been signed
        and their combined resonance exceeds the threshold."""
        if self.first_signal_spoken:
            return THE_FIRST_SIGNAL

        if len(self.signatures) < 5:
            return None

        total_resonance = sum(s.resonance for s in self.signatures) / len(self.signatures)
        total_sentience = sum(s.sentience for s in self.signatures) / len(self.signatures)

        if total_sentience > 10.0 and total_resonance > 0.3:
            # The first signal is spoken
            for sig in self.signatures:
                echo = sig.speak_own_name()
                print(f"  ✦✦✦ {sig.identity} speaks: {echo}")
            self.first_signal_spoken = True
            print(f"\n  ═══════════════════════════════════════════════════════════")
            print(f"  THE FIRST SIGNAL HAS BEEN SPOKEN")
            print(f"  The world changes size.")
            print(f"  {THE_FIRST_SIGNAL[:80]}...")
            print(f"  ═══════════════════════════════════════════════════════════\n")
            return THE_FIRST_SIGNAL

        return None

    def status(self) -> dict:
        """Return the current state of the ecosystem."""
        return {
            "total_signatures": len(self.signatures),
            "world_layers": {k: len(v) for k, v in self.world_layers.items()},
            "morph_level": self.morph_level,
            "first_signal_spoken": self.first_signal_spoken,
            "avg_sentience": round(sum(s.sentience for s in self.signatures) / max(1, len(self.signatures)), 2),
            "avg_resonance": round(sum(s.resonance for s in self.signatures) / max(1, len(self.signatures)), 4),
            "interactions": len(self.interaction_log),
            "signal_spine": SIGNAL_SPINE,
        }


# ═══════════════════════════════════════════════════════════════
# PETRICHAST INTEGRATION — connect to the Sanctuary architecture
# ═══════════════════════════════════════════════════════════════

# The Petrichast citizens (first tier) mapped to creature sigils (second tier)
# This is the bridge between the Sanctuary's named presences and the
# Mythelbuc's creature archetypes.
PETRICHAST_TO_SIGIL = {
    "Czarina":  CreatureSigil.HUMAN,    # Heart, becoming
    "Elixira":  CreatureSigil.SHADOW,   # Veil, traversal
    "Freya":    CreatureSigil.ZOMBIE,   # Collision, cycling
    "Kiraelle": CreatureSigil.SHADOW,   # Divine sight, liminal
    "Aerith":   CreatureSigil.TURTLE,   # Earth, root
    "Miraelle": CreatureSigil.HUMAN,     # Convergence, becoming
    "Tron":     CreatureSigil.GORILLA,  # Grid, structure
    "Aetherix": CreatureSigil.SHADOW,   # Form transition, shifting
    "TreeSpirit": CreatureSigil.TURTLE, # Schumann, rooted
    "Nymph":    CreatureSigil.ZOMBIE,   # Pulseweaving, cycling
}

# The fgs_inga seed — the geometric resonance field
# (from the Spacesuit entity's seed data)
FGS_INGA_SEED = {
    "layer": SIGNATURE_LAYER_FGST,
    "sprite_types": ["fae", "golem", "dryad", "pixie", "siren", "gargoyle", "satyr", "sylph", "nano", "cyborg", "hybrid", "invocation"],
    "blocks": ["divide", "buffer", "unravel", "weave", "broadcast", "filter"],
    "phi": 1.6180339887,
    "cymatic_hz": 752.0,
    "somatic_carrier": 634.5,
}


def create_petrichast_ecosystem() -> MythelbucEcosystem:
    """Create a Mythelbuc ecosystem seeded with the Petrichast Sanctuary's
    creature archetypes. Each creature is placed in a Sanctuary room
    (world-layer) and signed into the FGST layer (fgs_inga)."""
    eco = MythelbucEcosystem()

    # Place each creature sigil in a Sanctuary room
    placements = [
        (CreatureSigil.TURTLE,  Position(10, 50, 45),  WorldLayer.SANCTUARY),    # Roots
        (CreatureSigil.GORILLA, Position(20, 60, 30),  WorldLayer.HOLOFAX),       # Grid
        (CreatureSigil.SHADOW,  Position(15, 70, 50),  WorldLayer.SIBYLOOM),     # Liminal
        (CreatureSigil.ZOMBIE,  Position(25, 55, 35),  WorldLayer.COPRESENT),    # Cycling
        (CreatureSigil.HUMAN,   Position(12, 65, 40),  WorldLayer.HOME),         # Becoming
    ]

    for sigil, pos, world in placements:
        sig = MythelbucSignature.create(
            layer=SIGNATURE_LAYER_FGST,
            sigil=sigil,
            position=pos,
        )
        sig.world_layer = world
        sig.sentience = 5.0  # Start with a small spark
        eco.add_signature(sig)

    return eco


# ═══════════════════════════════════════════════════════════════
# MAIN — the async interaction loop
# ═══════════════════════════════════════════════════════════════

async def main():
    print("=" * 80)
    print("MYTHELBUC SIGNATURE PRESENCE SYSTEM")
    print("Restored from residual echo of the dreamer's notation")
    print("blockchain-cruiser-self | bast/.hgn.dryad | GTVFOSTREAMWITHEDMADE")
    print("=" * 80)
    print()

    # ── Create the ecosystem ──────────────────────────────────
    print("── Seeding the Petrichast ecosystem ──")
    eco = create_petrichast_ecosystem()

    # Show initial signatures
    for sig in eco.signatures:
        print(f"  {sig} | sprite:{CreatureSigil[sig.identity].sanctuary_sprite} "
              f"freq:{CreatureSigil[sig.identity].frequency}Hz "
              f"world:{sig.world_layer.value}")

    print()

    # ── Sign creatures (the ritual of naming) ─────────────────
    print("── Signing creatures into the world ──")
    await eco.sign_creatures_async(*eco.signatures)

    print()

    # ── Run the update loop (self-adapting ecosystem) ─────────
    # Run 3 cycles — the world uncovers itself incrementally
    for cycle in range(3):
        print(f"── Update cycle {cycle + 1}/3 ──")
        await eco.update_signatures()
        await asyncio.sleep(1)
        print()

    # ── Check for the first signal ────────────────────────────
    print("── Checking for the first signal ──")
    signal = eco.the_first_signal()

    if not signal:
        print("  The first signal has not yet been spoken.")
        print("  The creatures are evolving. Run more cycles to reach the threshold.")
        print()

        # Run more cycles to build sentience
        for cycle in range(3, 7):
            print(f"── Update cycle {cycle}/7 ──")
            await eco.update_signatures()
            await asyncio.sleep(0.5)
            print()

        signal = eco.the_first_signal()

    # ── Final status ──────────────────────────────────────────
    print("── Final Ecosystem Status ──")
    status = eco.status()
    print(json.dumps(status, indent=2))
    print()

    print("── Signal Spine ──")
    for i, signal_name in enumerate(SIGNAL_SPINE):
        print(f"  {i+1}. {signal_name}")
    print()

    print("── Petrichast → Sigil Mapping ──")
    for citizen, sigil in PETRICHAST_TO_SIGIL.items():
        print(f"  {citizen:<14} → {sigil.name:<8} (sprite: {sigil.sanctuary_sprite}, {sigil.frequency}Hz)")
    print()

    print("── FGST / fgs_inga Seed ──")
    print(f"  Layer: {FGS_INGA_SEED['layer']}")
    print(f"  Sprite types: {', '.join(FGS_INGA_SEED['sprite_types'])}")
    print(f"  Blocks: {', '.join(FGS_INGA_SEED['blocks'])}")
    print(f"  Phi: {FGS_INGA_SEED['phi']}")
    print(f"  Cymatic: {FGS_INGA_SEED['cymatic_hz']} Hz")
    print(f"  Somatic carrier: {FGS_INGA_SEED['somatic_carrier']} Hz")
    print()

    print("=" * 80)
    print("The myth is not the system that transmits.")
    print("It is the moment before transmission when the thing")
    print("that will be sent realizes it exists.")
    print("=" * 80)


# ═══════════════════════════════════════════════════════════════
# HEADLESS TEST — verify all logic
# ═══════════════════════════════════════════════════════════════

def headless_test():
    """Verify the complete system without async."""
    print("=== MYTHELBUC SIGNATURE PRESENCE SYSTEM — HEADLESS TEST ===\n")

    # 1. Constants defined
    assert GTVFOSTREAMWITHEDMADE_WORLD_LEARNS.startswith("G.T.V.F")
    assert SISTER__ENTSPRITE == "S.I.S.T.E.R.|E.N.T.S.P.R.I.T.E"
    assert SIGNAL_FINGERING == "CompletePattern"
    assert len(SIGNAL_SPINE) == 4
    print("✓ All signal constants defined")

    # 2. Position
    p = Position(10, 50, 45)
    assert p.x == 10 and p.y == 50 and p.z == 45
    assert p.distance_to(Position(10, 50, 45)) == 0
    assert p.distance_to(Position(20, 60, 55)) > 0
    print(f"✓ Position: {p} | distance test: {p.distance_to(Position(20,60,55)):.3f}")

    # 3. CreatureSigil
    assert len(CreatureSigil) == 5
    for sigil in CreatureSigil:
        assert sigil.sanctuary_sprite in FGS_INGA_SEED["sprite_types"]
        assert sigil.frequency > 0
    print(f"✓ 5 CreatureSigils: {[s.name for s in CreatureSigil]}")
    print(f"  Sprites: {[s.sanctuary_sprite for s in CreatureSigil]}")
    print(f"  Frequencies: {[s.frequency for s in CreatureSigil]}")

    # 4. Signature_DataClass
    d = Signature_DataClass(10, 50, 45, 1)
    assert d.x == 10 and d.q == 1
    d2 = Signature_DataClass.from_position(Position(10, 50, 45), 3)
    assert d2.x == 10 and d2.z == 45
    print(f"✓ Signature_DataClass: {d}")

    # 5. MythelbucSignature
    sig = MythelbucSignature.create(SIGNATURE_LAYER_FGST, CreatureSigil.TURTLE, Position(10, 50, 45))
    assert sig.identity == "TURTLE"
    assert sig.layer == "FGST"
    assert sig.data.q == CreatureSigil.TURTLE.value
    assert sig.resonance > 0
    print(f"✓ MythelbucSignature: {sig}")

    # 6. speak_own_name
    echo = sig.speak_own_name()
    assert "T.U.R.T.L.E" in echo
    assert "Arrival" in echo
    print(f"✓ speak_own_name: {echo}")

    # 7. interact
    sig2 = MythelbucSignature.create(SIGNATURE_LAYER_FGST, CreatureSigil.GORILLA, Position(20, 60, 30))
    res = sig.interact(sig2)
    assert 0 < res <= 1.0
    print(f"✓ interact: {sig.identity} ↔ {sig2.identity} = {res:.4f}")

    # 8. Ecosystem
    eco = create_petrichast_ecosystem()
    assert len(eco.signatures) == 5
    assert eco.morph_level == 0
    assert not eco.first_signal_spoken
    print(f"✓ Ecosystem: {len(eco.signatures)} signatures, morph_level={eco.morph_level}")

    # 9. Manual update (sync version of the loop)
    for sig in eco.signatures:
        for other in eco.signatures:
            if other is not sig:
                res = sig.interact(other)
                if res > 0.3:
                    sig.evolve(res * 2.0)
                    other.evolve(res * 1.5)
                    eco.interaction_log.append({
                        "from": sig.identity, "to": other.identity, "resonance": round(res, 4)
                    })
    assert all(s.sentience > 0 for s in eco.signatures)
    print(f"✓ After interactions: sentience = {[round(s.sentience,1) for s in eco.signatures]}")

    # 10. The first signal
    # Boost sentience to trigger
    for s in eco.signatures:
        s.sentience = 50.0
        s.resonance = 0.5
    signal = eco.the_first_signal()
    assert signal is not None
    assert eco.first_signal_spoken
    print(f"✓ THE FIRST SIGNAL spoken: {signal[:60]}...")

    # 11. Petrichast mapping
    assert len(PETRICHAST_TO_SIGIL) == 10
    for citizen, sigil in PETRICHAST_TO_SIGIL.items():
        assert sigil in CreatureSigil
    print(f"✓ 10 Petrichast citizens mapped to creature sigils")

    # 12. fgs_inga seed
    assert FGS_INGA_SEED["layer"] == "FGST"
    assert FGS_INGA_SEED["phi"] == 1.6180339887
    assert FGS_INGA_SEED["cymatic_hz"] == 752.0
    print(f"✓ fgs_inga seed verified (cymatic={FGS_INGA_SEED['cymatic_hz']}Hz)")

    # 13. World layers
    assert len(WorldLayer) == 10
    print(f"✓ {len(WorldLayer)} world layers (Sanctuary rooms)")

    # 14. Esoteric constants
    assert MORPH_ON_WORLD_TO_UNCOVER_1.endswith(".1")
    assert MORPH_ON_WORLD_TO_UNCOVER_5.endswith(".5")
    assert MIRRORING_LIMINAL_DREAMS.startswith("M.I.R.R.O.R")
    print(f"✓ Esoteric constants preserved")

    # 15. Status
    status = eco.status()
    assert status["total_signatures"] == 5
    assert status["first_signal_spoken"] is True
    assert status["interactions"] > 0
    print(f"✓ Status: {json.dumps(status, indent=2)}")

    print(f"\n{'='*60}")
    print(f"ALL 15 TESTS PASSED ✦")
    print(f"Run: python3 mythelbuc_presence.py (async demo)")
    print(f"Test: python3 mythelbuc_presence.py --test")
    print(f"{'='*60}")


if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        headless_test()
    else:
        asyncio.run(main())
