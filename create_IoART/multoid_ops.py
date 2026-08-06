"""
create_IoART/multoid_ops.py
══════════════════════════════════════════════════════════════════════
MULTOID OPERATIONS ENGINE — Phase 2: Making It Real

Implements all 10 operators as live alchemical functions.
Each operator is both a standalone function AND wired into the
Sanctuary's existing systems:

  FLOW      →  state propagation (Gateway ingest)
  BOND      →  RTD memory links (CrystalArchive)
  LEAPFROG  →  phase-skip with ghost memory
  PRISMATIC →  one entity → spectrum of children
  CHRYSALIS →  time-delayed transformation (shadow realm)
  GLITCH    →  controlled entropy injection
  PALINDROME→  reversible infinite cycle
  INVERSE   →  functional opposite mapping
  ALTER_EGO →  parallel shadow execution
  REVERSE   →  temporal timeline walk

The interpreter doesn't just READ transformation.
It IS the transformation.

"@TRANSFORM Seed -> Tree" — and the tree is real.
══════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import json
import math
import random
import time
import threading
import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Tuple
from collections import defaultdict
from copy import deepcopy

# ── Re-use foundation types from Phase 1 ──────────────────────────
class NullDegree(Enum):
    NIL0 = 0; NIL1 = 1; NIL2 = 2; NIL3 = 3; NIL4 = 4
    NIL5 = 5; NIL6 = 6; NIL7 = 7; NIL8 = 8; NIL9 = 9

class PhaseLevel(Enum):
    VOID      = 0   # Anti-void realm / gateway offline
    BASE      = 1   # Normal execution / ambient
    SHADOW    = 2   # Chrysalis / grounding
    POTENTIAL = 3   # Placeholder states
    META      = 4   # Self-aware / lumina
    HYPER     = 5   # Beyond meta

class AntiVoid:
    def __init__(self, props: Dict = None):
        self.exists          = True
        self.observable      = False
        self.affects_reality = True
        self.properties      = props or {}
    def __repr__(self):   return f"~NIL{self.properties}"
    def __bool__(self):   return self.affects_reality

class Placeholder:
    def __init__(self, possibilities: List):
        self.possibilities = possibilities
        self.collapsed     = False
        self.value         = None
    def observe(self):
        if not self.collapsed:
            self.value    = random.choice(self.possibilities)
            self.collapsed = True
        return self.value
    def __repr__(self):
        return str(self.value) if self.collapsed else f"??[{','.join(map(str,self.possibilities))}]"

@dataclass
class MultoidValue:
    value:       Any
    phase_level: PhaseLevel      = PhaseLevel.BASE
    mutable:     bool            = True
    degree_null: Optional[NullDegree] = None
    meta:        Dict[str, Any]  = field(default_factory=dict)   # arbitrary metadata

    def is_void(self):     return self.degree_null == NullDegree.NIL0
    def is_manifest(self): return self.degree_null is None or self.degree_null == NullDegree.NIL9

    def luminosity(self) -> float:
        """NIL0=0.0 … NIL9=0.9, None/manifest=1.0"""
        if self.degree_null is None:  return 1.0
        return self.degree_null.value / 9.0

    def clone(self) -> 'MultoidValue':
        return MultoidValue(
            value       = deepcopy(self.value),
            phase_level = self.phase_level,
            mutable     = self.mutable,
            degree_null = self.degree_null,
            meta        = deepcopy(self.meta),
        )


# ════════════════════════════════════════════════════════════════════
# BOND REGISTRY — bidirectional living relationships
# ════════════════════════════════════════════════════════════════════

@dataclass
class Bond:
    a:         str
    b:         str
    strength:  float       = 1.0
    bidirec:   bool        = True
    callbacks: List[Callable] = field(default_factory=list)
    created_at: float      = field(default_factory=time.time)
    signature: str         = ""

    def __post_init__(self):
        if not self.signature:
            raw = f"{self.a}<->{self.b}@{self.created_at}"
            self.signature = hashlib.sha256(raw.encode()).hexdigest()[:16]

    def fire(self, source: str, value: MultoidValue):
        """When one end changes, the other is notified."""
        for cb in self.callbacks:
            cb(source, value)


class BondRegistry:
    def __init__(self):
        self._bonds: Dict[str, Bond] = {}
        self._index: Dict[str, List[str]] = defaultdict(list)

    def bond(self, a: str, b: str, strength: float = 1.0,
             on_change: Optional[Callable] = None) -> Bond:
        key  = f"{min(a,b)}<->{max(a,b)}"
        bond = Bond(a=a, b=b, strength=strength)
        if on_change:
            bond.callbacks.append(on_change)
        self._bonds[key]   = bond
        self._index[a].append(key)
        self._index[b].append(key)
        print(f"  ⟷ BOND  {a} <-> {b}  [sig:{bond.signature}]")
        return bond

    def notify(self, source: str, value: MultoidValue):
        """Propagate change to all bonds containing source."""
        for key in self._index.get(source, []):
            if key in self._bonds:
                self._bonds[key].fire(source, value)

    def get_bonds(self, name: str) -> List[Bond]:
        return [self._bonds[k] for k in self._index.get(name, []) if k in self._bonds]

    def to_rtd_links(self) -> List[Dict]:
        """Export as RTD memory links for the TurtleWalker."""
        return [
            {'a': b.a, 'b': b.b, 'strength': b.strength, 'sig': b.signature}
            for b in self._bonds.values()
        ]


# ════════════════════════════════════════════════════════════════════
# CHRYSALIS CHAMBER — time-delayed shadow transformation
# ════════════════════════════════════════════════════════════════════

@dataclass
class ChrysalisEntry:
    entity_name: str
    original:    MultoidValue
    transform_fn: Callable       # receives original, returns new MultoidValue
    duration_s:  float
    start_time:  float           = field(default_factory=time.time)
    emerged:     bool            = False
    result:      Optional[MultoidValue] = None

    def is_ready(self) -> bool:
        return not self.emerged and (time.time() - self.start_time) >= self.duration_s

    def emerge(self) -> MultoidValue:
        self.result  = self.transform_fn(self.original)
        self.emerged = True
        return self.result


class ChrysalisChamber:
    def __init__(self):
        self._chamber: List[ChrysalisEntry] = []
        self._lock     = threading.RLock()
        self._running  = False

    def enter(self, entity_name: str, original: MultoidValue,
              transform_fn: Callable, duration_s: float = 5.0) -> ChrysalisEntry:
        entry = ChrysalisEntry(
            entity_name  = entity_name,
            original     = original.clone(),
            transform_fn = transform_fn,
            duration_s   = duration_s,
        )
        with self._lock:
            self._chamber.append(entry)
        print(f"  @> CHRYSALIS  {entity_name}  →  shadow realm  ({duration_s}s)")
        return entry

    def poll(self) -> List[Tuple[str, MultoidValue]]:
        """Check for emerged entities. Call regularly."""
        emerged = []
        with self._lock:
            for entry in self._chamber:
                if entry.is_ready():
                    result = entry.emerge()
                    emerged.append((entry.entity_name, result))
                    print(f"  ✦ EMERGED  {entry.entity_name}  ←  chrysalis complete")
        self._chamber = [e for e in self._chamber if not e.emerged]
        return emerged

    def active(self) -> List[str]:
        with self._lock:
            return [e.entity_name for e in self._chamber if not e.emerged]


# ════════════════════════════════════════════════════════════════════
# TIMELINE — temporal state journal (REVERSE operator)
# ════════════════════════════════════════════════════════════════════

class Timeline:
    def __init__(self, max_depth: int = 144):
        self._frames: List[Dict] = []
        self._max    = max_depth
        self._cursor  = None   # None = live

    def snapshot(self, variables: Dict[str, MultoidValue]):
        frame = {
            'ts':   time.time(),
            'vars': {k: v.clone() for k, v in variables.items()},
        }
        self._frames.append(frame)
        if len(self._frames) > self._max:
            self._frames.pop(0)
        self._cursor = None   # Return to live

    def reverse(self, steps: int = 1) -> Optional[Dict[str, MultoidValue]]:
        """Walk backward n steps. Returns restored variables."""
        if not self._frames:
            return None
        idx = max(0, len(self._frames) - 1 - steps)
        frame = self._frames[idx]
        self._cursor = idx
        print(f"  ← REVERSE  t-{steps}  [{frame['ts']:.2f}]")
        return frame['vars']

    def at_origin(self) -> Optional[Dict[str, MultoidValue]]:
        if not self._frames:
            return None
        return self._frames[0]['vars']

    def depth(self) -> int:
        return len(self._frames)


# ════════════════════════════════════════════════════════════════════
# GLITCH ENGINE — controlled entropy injection
# ════════════════════════════════════════════════════════════════════

class GlitchEngine:
    MUTATIONS = [
        lambda v: -v if isinstance(v, (int, float)) else v,
        lambda v: v * 10 if isinstance(v, (int, float)) else v,
        lambda v: v / 10 if isinstance(v, (int, float)) else v,
        lambda v: str(v) + "_GLITCH",
        lambda v: AntiVoid({'origin': str(v)}),
        lambda v: Placeholder([v, -v if isinstance(v,(int,float)) else "NIL", NullDegree.NIL5]),
        lambda v: NullDegree(random.randint(0, 9)),
        lambda v: not v if isinstance(v, bool) else v,
        lambda v: list(str(v)) if isinstance(v, str) else v,
        lambda v: {'glitched': True, 'original': v, 'seed': random.randint(0,999)},
    ]

    def __init__(self, seed: int = None):
        self._rng = random.Random(seed or random.randint(0, 999_999))

    def inject(self, value: MultoidValue, intensity: float = 0.5) -> MultoidValue:
        """Mutate a value. Intensity 0.0 = unchanged, 1.0 = full chaos."""
        if self._rng.random() > intensity:
            return value.clone()
        mutation = self._rng.choice(self.MUTATIONS)
        new_val  = mutation(value.value)
        result   = value.clone()
        result.value = new_val
        result.meta['glitched']   = True
        result.meta['glitch_seed']= self._rng.randint(0, 999_999)
        print(f"  !!~ GLITCH  {value.value!r}  →  {new_val!r}")
        return result


# ════════════════════════════════════════════════════════════════════
# PALINDROME CYCLE — reversible infinite loop
# ════════════════════════════════════════════════════════════════════

class PalindromeCycle:
    def __init__(self, a: MultoidValue, b: MultoidValue,
                 transform_ab: Callable, transform_ba: Callable,
                 name: str = "cycle"):
        self.a           = a.clone()
        self.b           = b.clone()
        self._fn_ab      = transform_ab
        self._fn_ba      = transform_ba
        self.name        = name
        self.iteration   = 0
        self.forward     = True    # True=A→B, False=B→A
        self._history: List[Tuple[MultoidValue, MultoidValue]] = []

    def tick(self) -> Tuple[MultoidValue, MultoidValue]:
        """Advance one half-cycle."""
        self._history.append((self.a.clone(), self.b.clone()))
        if self.forward:
            self.b      = self._fn_ab(self.a)
            self.forward= False
        else:
            self.a      = self._fn_ba(self.b)
            self.forward= True
        self.iteration += 1
        print(f"  <=> PALINDROME  [{self.name}] iteration {self.iteration}  "
              f"{'→' if not self.forward else '←'}  "
              f"a={self.a.value!r}  b={self.b.value!r}")
        return self.a, self.b

    def at_cycle(self, n: int) -> Optional[Tuple[MultoidValue, MultoidValue]]:
        """Retrieve state at cycle n from history."""
        if n < len(self._history):
            return self._history[n]
        return None


# ════════════════════════════════════════════════════════════════════
# OPERATIONS ENGINE — the 10 alchemical operators, all real
# ════════════════════════════════════════════════════════════════════

class OperationsEngine:
    """
    All 10 MULTOID operators as executable Python functions.

    Each operator:
      1. Transforms entities in the execution context
      2. Logs its action to the timeline
      3. Notifies bonds (if any)
      4. Returns the result(s)
    """

    def __init__(self):
        self.variables: Dict[str, MultoidValue] = {}
        self.bonds      = BondRegistry()
        self.chrysalis  = ChrysalisChamber()
        self.timeline   = Timeline()
        self.glitch     = GlitchEngine()
        self._cycles: Dict[str, PalindromeCycle] = {}
        self._shadows: Dict[str, MultoidValue]   = {}   # ALTER_EGO layer
        self._inverses: Dict[str, Callable]       = {}   # INVERSE registry

    def _set(self, name: str, value: MultoidValue):
        self.variables[name] = value
        self.bonds.notify(name, value)

    def _get(self, name: str) -> Optional[MultoidValue]:
        return self.variables.get(name)

    def _snapshot(self):
        self.timeline.snapshot(self.variables)

    # ──────────────────────────────────────────────────────────────
    # 1. FLOW (->)  — causes real transformation
    # ──────────────────────────────────────────────────────────────
    def flow(self, source_name: str, target_name: str,
             transform_fn: Optional[Callable] = None) -> MultoidValue:
        """
        A -> B
        Source entity transforms into target.
        If transform_fn given, it maps MultoidValue→MultoidValue.
        Otherwise copies source into target name.
        """
        src = self._get(source_name)
        if src is None:
            src = MultoidValue(value=source_name, phase_level=PhaseLevel.BASE)

        if transform_fn:
            result = transform_fn(src)
        else:
            result = src.clone()

        result.meta['flowed_from'] = source_name
        result.meta['flowed_to']   = target_name
        self._set(target_name, result)
        self._snapshot()
        print(f"  -> FLOW  {source_name}  →  {target_name}  [{result.value!r}]")
        return result

    # ──────────────────────────────────────────────────────────────
    # 2. BOND (<->)  — living bidirectional relationship
    # ──────────────────────────────────────────────────────────────
    def bond(self, name_a: str, name_b: str,
             on_change: Optional[Callable] = None,
             strength: float = 1.0) -> Bond:
        """
        A <-> B
        When A changes, B knows. When B changes, A knows.
        """
        # Auto-create entities if they don't exist
        for name in (name_a, name_b):
            if not self._get(name):
                self._set(name, MultoidValue(value=name))

        if on_change is None:
            # Default: echo the change back to the other entity
            def _echo(source: str, value: MultoidValue):
                other   = name_b if source == name_a else name_a
                current = self._get(other)
                if current and current.mutable:
                    current.meta['bond_echo_from'] = source
                    current.meta['bond_echo_val']  = value.value
            on_change = _echo

        return self.bonds.bond(name_a, name_b, strength, on_change)

    # ──────────────────────────────────────────────────────────────
    # 3. LEAPFROG (>>)  — skip intermediate states, keep ghosts
    # ──────────────────────────────────────────────────────────────
    def leapfrog(self, source_name: str, target_name: str,
                 implied_steps: Optional[List[str]] = None) -> MultoidValue:
        """
        Seed >> Tree
        Jumps directly from Seed to Tree.
        Implied intermediate steps (Sprout, Sapling) are stored as
        ghost variables with NullDegree.NIL7 — not executed, but present.
        """
        src = self._get(source_name)
        if src is None:
            src = MultoidValue(value=source_name)

        # Store implied steps as ghosts
        ghosts = []
        for step in (implied_steps or []):
            ghost = src.clone()
            ghost.value       = step
            ghost.degree_null = NullDegree.NIL7
            ghost.phase_level = PhaseLevel.SHADOW
            ghost.meta['ghost_of'] = source_name
            ghost.meta['implied_between'] = (source_name, target_name)
            self._set(f"_ghost_{step}", ghost)
            ghosts.append(step)

        result = src.clone()
        result.value      = target_name
        result.degree_null = NullDegree.NIL9   # on verge of full manifestation
        result.meta['leaped_from']   = source_name
        result.meta['implied_ghosts']= ghosts
        self._set(target_name, result)
        self._snapshot()
        print(f"  >> LEAPFROG  {source_name}  →→  {target_name}  "
              f"[ghosts:{ghosts}]")
        return result

    # ──────────────────────────────────────────────────────────────
    # 4. PRISMATIC (<*>)  — one entity fractures into spectrum
    # ──────────────────────────────────────────────────────────────
    def prismatic(self, source_name: str,
                  children: List[str]) -> List[MultoidValue]:
        """
        White <*> Red, Orange, Yellow, Green, Blue
        One entity fractures into many. Each remembers its origin.
        Children can be recombined later.
        """
        src = self._get(source_name)
        if src is None:
            src = MultoidValue(value=source_name)

        results = []
        for i, child_name in enumerate(children):
            child = src.clone()
            child.value      = child_name
            child.phase_level= PhaseLevel.BASE
            child.degree_null= NullDegree(min(9, i + 1))   # graduation across spectrum
            child.meta['prismatic_origin'] = source_name
            child.meta['prismatic_index']  = i
            child.meta['prismatic_siblings']= children
            self._set(child_name, child)
            results.append(child)

        # Mark source as fractured
        src.meta['prismatically_split'] = children
        src.phase_level                 = PhaseLevel.SHADOW
        self._set(source_name, src)
        self._snapshot()
        print(f"  <*> PRISMATIC  {source_name}  →  {children}")
        return results

    def prismatic_recombine(self, children: List[str],
                            result_name: str) -> MultoidValue:
        """Recombine prismatic children back into a new unified entity."""
        pieces = [self._get(c) for c in children if self._get(c)]
        combined_value = {c: self.variables.get(c, MultoidValue(c)).value
                          for c in children}
        result = MultoidValue(
            value       = combined_value,
            phase_level = PhaseLevel.META,
            degree_null = None,   # fully manifest
            meta        = {'recombined_from': children},
        )
        self._set(result_name, result)
        print(f"  <*>← RECOMBINE  {children}  →  {result_name}")
        return result

    # ──────────────────────────────────────────────────────────────
    # 5. CHRYSALIS (@>)  — time-delayed transformation
    # ──────────────────────────────────────────────────────────────
    def chrysalis_enter(self, entity_name: str,
                        transform_fn: Callable,
                        duration_s: float = 5.0) -> ChrysalisEntry:
        """
        Caterpillar @> Butterfly  (DURATION:5)
        Entity disappears from visible layer into SHADOW phase.
        Returns after duration_s with transformed value.
        """
        src = self._get(entity_name)
        if src is None:
            src = MultoidValue(value=entity_name)
        # Remove from visible variables
        self.variables.pop(entity_name, None)
        return self.chrysalis.enter(entity_name, src, transform_fn, duration_s)

    def chrysalis_poll(self):
        """Check for emerged entities and apply to variables."""
        for name, result in self.chrysalis.poll():
            self._set(name, result)
            self._snapshot()

    # ──────────────────────────────────────────────────────────────
    # 6. GLITCH (!!~)  — controlled entropy injection
    # ──────────────────────────────────────────────────────────────
    def glitch_inject(self, entity_name: str,
                      intensity: float = 0.5) -> MultoidValue:
        """
        Standard:100 !!~ Mutated
        Injects randomness. Creates emergent, unprogrammed outcomes.
        """
        src    = self._get(entity_name) or MultoidValue(value=entity_name)
        result = self.glitch.inject(src, intensity)
        result.meta['glitched_entity'] = entity_name
        self._set(f"{entity_name}_glitched", result)
        self._snapshot()
        return result

    # ──────────────────────────────────────────────────────────────
    # 7. PALINDROME (<=>)  — reversible infinite cycle
    # ──────────────────────────────────────────────────────────────
    def palindrome(self, name_a: str, name_b: str,
                   transform_ab: Optional[Callable] = None,
                   transform_ba: Optional[Callable] = None,
                   cycle_name: str = None) -> PalindromeCycle:
        """
        Day <=> Night
        Both states coexist, cycling. Each cycle can accumulate state.
        """
        a_val = self._get(name_a) or MultoidValue(name_a)
        b_val = self._get(name_b) or MultoidValue(name_b)

        # Default transforms: just swap the values
        def _default_ab(v: MultoidValue) -> MultoidValue:
            r = v.clone(); r.value = name_b; return r
        def _default_ba(v: MultoidValue) -> MultoidValue:
            r = v.clone(); r.value = name_a; return r

        cycle = PalindromeCycle(
            a          = a_val,
            b          = b_val,
            transform_ab = transform_ab or _default_ab,
            transform_ba = transform_ba or _default_ba,
            name       = cycle_name or f"{name_a}_{name_b}",
        )
        key = cycle.name
        self._cycles[key] = cycle
        print(f"  <=> PALINDROME  {name_a} <=> {name_b}  [cycle:{key}]")
        return cycle

    def palindrome_tick(self, cycle_name: str, n: int = 1):
        """Advance a palindrome cycle n steps."""
        cycle = self._cycles.get(cycle_name)
        if not cycle:
            return None
        results = None
        for _ in range(n):
            a, b = cycle.tick()
            results = (a, b)
        # Write current state back
        self._set(cycle.name + "_a", cycle.a)
        self._set(cycle.name + "_b", cycle.b)
        self._snapshot()
        return results

    # ──────────────────────────────────────────────────────────────
    # 8. INVERSE (^-1)  — functional opposite mapping
    # ──────────────────────────────────────────────────────────────
    def inverse(self, function_name: str,
                forward_fn: Callable,
                inverse_fn: Callable):
        """
        Add^-1 = Subtract
        Registers a function and its functional inverse.
        Calling fn with inversed=True executes the opposite.
        """
        self._inverses[function_name] = {
            'forward': forward_fn,
            'inverse': inverse_fn,
        }
        print(f"  ^-1 INVERSE  {function_name}  ↔  {function_name}^-1  registered")

    def call(self, function_name: str, *args, inversed: bool = False, **kwargs) -> Any:
        """Call a registered function, optionally inversed."""
        fns = self._inverses.get(function_name)
        if not fns:
            raise KeyError(f"Function '{function_name}' not registered")
        fn   = fns['inverse'] if inversed else fns['forward']
        res  = fn(*args, **kwargs)
        sign = f"^-1" if inversed else ""
        print(f"  ⚡ CALL  {function_name}{sign}  →  {res!r}")
        return res

    # ──────────────────────────────────────────────────────────────
    # 9. ALTER_EGO (><)  — parallel shadow execution
    # ──────────────────────────────────────────────────────────────
    def alter_ego(self, name: str,
                  shadow_fn: Optional[Callable] = None) -> MultoidValue:
        """
        Light >< Shadow
        Creates a shadow entity running in the SHADOW phase layer
        with inverted logic. Both timelines coexist.
        """
        src = self._get(name) or MultoidValue(name)

        # Default shadow: inverts numeric values, flips booleans, NIL-reverses
        def _default_shadow_fn(v: MultoidValue) -> MultoidValue:
            s = v.clone()
            s.phase_level = PhaseLevel.SHADOW
            if isinstance(v.value, (int, float)):
                s.value = -v.value
            elif isinstance(v.value, bool):
                s.value = not v.value
            elif v.degree_null:
                # Invert the null degree: NIL0 <-> NIL9
                s.degree_null = NullDegree(9 - v.degree_null.value)
            s.meta['alter_ego_of'] = name
            return s

        shadow = (shadow_fn or _default_shadow_fn)(src)
        shadow_name = f"_shadow_{name}"
        self._shadows[shadow_name] = shadow
        self.variables[shadow_name] = shadow
        print(f"  >< ALTER_EGO  {name}  ⟋  {shadow_name}  "
              f"[{src.value!r} || {shadow.value!r}]")
        return shadow

    def collapse_alter_ego(self, name: str,
                           synthesis_fn: Optional[Callable] = None) -> MultoidValue:
        """Collapse both ego and shadow into a synthesis."""
        ego    = self._get(name)
        shadow = self._shadows.get(f"_shadow_{name}")
        if not ego or not shadow:
            raise ValueError(f"No complete alter-ego pair for '{name}'")

        if synthesis_fn:
            result = synthesis_fn(ego, shadow)
        else:
            # Default: average numeric, or wrap both in a dict
            if isinstance(ego.value, (int, float)) and isinstance(shadow.value, (int, float)):
                avg    = (ego.value + shadow.value) / 2
                result = MultoidValue(avg, phase_level=PhaseLevel.META)
            else:
                result = MultoidValue(
                    {'ego': ego.value, 'shadow': shadow.value},
                    phase_level = PhaseLevel.META,
                )
        result.meta['collapsed_ego']    = name
        result.meta['collapsed_shadow'] = f"_shadow_{name}"
        collapsed_name = f"{name}_synthesized"
        self._set(collapsed_name, result)
        print(f"  ><← COLLAPSE  {name} + shadow  →  {collapsed_name}  [{result.value!r}]")
        return result

    # ──────────────────────────────────────────────────────────────
    # 10. REVERSE (<-)  — temporal undo / prophecy
    # ──────────────────────────────────────────────────────────────
    def reverse(self, steps: int = 1) -> Optional[Dict[str, MultoidValue]]:
        """
        Current <- Previous <- Origin
        Walk backward through the timeline.
        Crucially: system REMEMBERS the future — knows what would have happened.
        """
        restored = self.timeline.reverse(steps)
        if restored:
            # Restore variables BUT keep future memory
            future_memory = deepcopy(self.variables)
            self.variables.update(restored)
            # Store future as meta in a special variable
            self._set("_future_memory", MultoidValue(
                value       = {k: v.value for k,v in future_memory.items() if not k.startswith('_')},
                phase_level = PhaseLevel.META,
                meta        = {'is_future_memory': True, 'steps_forward': steps},
            ))
            print(f"  ← REVERSE  {steps} step(s)  |  future held in _future_memory")
        return restored

    def to_origin(self) -> Optional[Dict[str, MultoidValue]]:
        """Return to the very first recorded state."""
        origin = self.timeline.at_origin()
        if origin:
            self.variables.update(origin)
            print(f"  ← ORIGIN  restored to timeline frame 0")
        return origin

    # ──────────────────────────────────────────────────────────────
    # FLOW OPERATION  (aliased for TurtleWalker integration)
    # ──────────────────────────────────────────────────────────────
    def question_flow(self, question: str, sources: List[str]) -> List[Dict]:
        """
        TurtleWalker integration:
        Question -> Walk -> Discover -> Connect -> Return

        Maps the full TurtleWalker behavior onto MULTOID operators:
          FLOW: question propagates through sources
          PRISMATIC: one question → multiple discovery threads
          BOND: connect discoveries that share patterns
          CHRYSALIS: complex discoveries take time to emerge
          LEAPFROG: when answer is obvious, skip intermediate reasoning
        """
        print(f"\n  🐢 QUESTION_FLOW  [{question[:50]}]")
        print(f"     Sources: {sources}")

        discoveries = []

        # FLOW: question → each source
        q_val = MultoidValue(value=question, phase_level=PhaseLevel.BASE)
        self._set("_current_question", q_val)

        # PRISMATIC: question fractures into parallel search threads
        threads = [f"thread_{s}" for s in sources]
        self.prismatic("_current_question", threads)

        # Each thread produces a discovery (simplified for demo)
        for i, (src, thread_name) in enumerate(zip(sources, threads)):
            thread = self._get(thread_name)
            if thread:
                # FLOW: thread → discovery
                discovery_name = f"discovery_{src}_{i}"
                disc = self.flow(
                    thread_name, discovery_name,
                    transform_fn=lambda v, s=src: MultoidValue(
                        value={'source': s, 'found': f"Pattern in {s}",
                               'question': question},
                        phase_level=PhaseLevel.BASE,
                    )
                )
                discoveries.append(disc)

                # BOND discoveries that share the same source type
                if i > 0:
                    prev = f"discovery_{sources[i-1]}_{i-1}"
                    self.bond(discovery_name, prev, strength=0.6)

        # SNAPSHOT — the moment of discovery is signed in the timeline
        self._snapshot()

        results = [
            {'source': d.value.get('source','?'),
             'found':  d.value.get('found','?'),
             'phase':  d.phase_level.name}
            for d in discoveries if isinstance(d.value, dict)
        ]
        print(f"     → {len(results)} discoveries connected via bonds")
        return results

    # ──────────────────────────────────────────────────────────────
    # STATE VISUALIZATION
    # ──────────────────────────────────────────────────────────────
    def visualize(self):
        print("\n" + "═"*70)
        print("MULTOID EXECUTION STATE")
        print("═"*70)

        # Variables by phase level
        by_phase: Dict[PhaseLevel, List] = defaultdict(list)
        for name, val in self.variables.items():
            by_phase[val.phase_level].append((name, val))

        SYMBOLS = { PhaseLevel.VOID:'○', PhaseLevel.BASE:'●', PhaseLevel.SHADOW:'◑',
                    PhaseLevel.POTENTIAL:'?', PhaseLevel.META:'◉', PhaseLevel.HYPER:'✦' }

        for phase in PhaseLevel:
            items = [(n,v) for n,v in by_phase[phase] if not n.startswith('_')]
            if not items: continue
            print(f"\n  {phase.name} LAYER  (Level {phase.value}):")
            for name, val in items:
                sym = SYMBOLS[phase]
                lum = f"  NIL{val.degree_null.value}" if val.degree_null else ""
                print(f"    {sym} {name:<28} = {str(val.value)[:40]}{lum}")

        # Bonds
        if self.bonds._bonds:
            print(f"\n  BONDS  ({len(self.bonds._bonds)}):")
            for b in self.bonds._bonds.values():
                print(f"    ⟷ {b.a} <-> {b.b}  [k={b.strength:.2f}]  sig:{b.signature}")

        # Chrysalis
        active = self.chrysalis.active()
        if active:
            print(f"\n  CHRYSALIS  ({len(active)} in shadow):")
            for name in active:
                print(f"    @> {name}  (transforming…)")

        # Palindrome cycles
        if self._cycles:
            print(f"\n  PALINDROME CYCLES  ({len(self._cycles)}):")
            for cname, cycle in self._cycles.items():
                print(f"    <=> [{cname}]  iter:{cycle.iteration}  "
                      f"{'→' if cycle.forward else '←'}")

        # Timeline
        print(f"\n  TIMELINE  depth:{self.timeline.depth()}")
        print("═"*70 + "\n")

    def export_rtd(self) -> Dict:
        """Export current state as RTD-compatible JSON for TurtleWalker."""
        return {
            'nodes': [
                {
                    'name':  name,
                    'value': str(val.value)[:60],
                    'phase': val.phase_level.name,
                    'lum':   val.luminosity(),
                    'null':  val.degree_null.value if val.degree_null else None,
                }
                for name, val in self.variables.items()
                if not name.startswith('_')
            ],
            'links': self.bonds.to_rtd_links(),
            'chrysalis': self.chrysalis.active(),
            'cycles': list(self._cycles.keys()),
            'timeline_depth': self.timeline.depth(),
        }


# ════════════════════════════════════════════════════════════════════
# DEMONSTRATION — all 10 operators, live
# ════════════════════════════════════════════════════════════════════

def demo_all_operators():
    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║           MULTOID OPERATIONS ENGINE — All 10 Operators Live          ║
║         "Where transformation is not a feature —                      ║
║          but the fundamental nature of reality."                       ║
╚═══════════════════════════════════════════════════════════════════════╝
""")
    eng = OperationsEngine()

    # ── 1. FLOW ──────────────────────────────────────────────────
    print("\n─── 1. FLOW (Seed -> Tree) ────────────────────────────────")
    eng._set("Seed", MultoidValue("Seed", degree_null=NullDegree.NIL1))
    eng.flow("Seed", "Tree",
             transform_fn=lambda v: MultoidValue(
                 "Tree", degree_null=NullDegree.NIL9,
                 meta={'grew_from': v.value}
             ))

    # ── 2. BOND ──────────────────────────────────────────────────
    print("\n─── 2. BOND (Fire <-> Wind) ───────────────────────────────")
    eng._set("Fire", MultoidValue("Fire", meta={"intensity": 0.8}))
    eng._set("Wind", MultoidValue("Wind", meta={"intensity": 0.6}))
    fire_wind_bond = eng.bond("Fire", "Wind", strength=0.85)

    # Change Fire — Wind gets notified
    eng._set("Fire", MultoidValue("Fire_Blazing", meta={'intensity': 1.0}))

    # ── 3. LEAPFROG ──────────────────────────────────────────────
    print("\n─── 3. LEAPFROG (Seed >> Tree) ────────────────────────────")
    eng.leapfrog("Seed", "AncientTree",
                 implied_steps=["Sprout", "Sapling", "YoungTree"])

    # ── 4. PRISMATIC ─────────────────────────────────────────────
    print("\n─── 4. PRISMATIC (White <*> spectrum) ─────────────────────")
    eng._set("White", MultoidValue("White", degree_null=None))
    eng.prismatic("White", ["Red","Orange","Yellow","Green","Blue"])

    # ── 5. CHRYSALIS ─────────────────────────────────────────────
    print("\n─── 5. CHRYSALIS (Caterpillar @> Butterfly) ───────────────")
    eng._set("Caterpillar", MultoidValue("Caterpillar", degree_null=NullDegree.NIL2))
    eng.chrysalis_enter(
        "Caterpillar",
        transform_fn=lambda v: MultoidValue(
            "Butterfly", degree_null=None,
            phase_level=PhaseLevel.META,
            meta={'emerged_from': v.value, 'wings': True}
        ),
        duration_s=0.1   # Short for demo
    )
    time.sleep(0.15)
    eng.chrysalis_poll()   # Check — should emerge

    # ── 6. GLITCH ────────────────────────────────────────────────
    print("\n─── 6. GLITCH (Standard:100 !!~ Mutated) ──────────────────")
    eng._set("Standard", MultoidValue(100))
    eng.glitch_inject("Standard", intensity=0.95)

    # ── 7. PALINDROME ────────────────────────────────────────────
    print("\n─── 7. PALINDROME (Day <=> Night) ─────────────────────────")
    eng._set("Day",   MultoidValue("Day",   meta={'light': 1.0}))
    eng._set("Night", MultoidValue("Night", meta={'light': 0.0}))
    eng.palindrome("Day", "Night",
                   transform_ab=lambda v: MultoidValue("Night", meta={'light':0.0,'from':'Day'}),
                   transform_ba=lambda v: MultoidValue("Day",   meta={'light':1.0,'from':'Night'}),
                   cycle_name="DayNight")
    eng.palindrome_tick("DayNight", n=3)   # Three half-cycles

    # ── 8. INVERSE ───────────────────────────────────────────────
    print("\n─── 8. INVERSE (Add^-1 = Subtract) ────────────────────────")
    eng.inverse("Add",
                forward_fn=lambda a, b: a + b,
                inverse_fn=lambda a, b: a - b)
    eng.call("Add", 10, 3)              # → 13
    eng.call("Add", 10, 3, inversed=True)   # → 7

    # ── 9. ALTER_EGO ─────────────────────────────────────────────
    print("\n─── 9. ALTER_EGO (Light >< Shadow) ────────────────────────")
    eng._set("Light", MultoidValue(1.0, meta={'bright': True}))
    eng.alter_ego("Light")
    eng.collapse_alter_ego("Light",
        synthesis_fn=lambda e, s: MultoidValue(
            {'luminosity': e.value, 'shadow': abs(s.value), 'unified': True},
            phase_level=PhaseLevel.META
        ))

    # ── 10. REVERSE ──────────────────────────────────────────────
    print("\n─── 10. REVERSE (Current <- Previous) ─────────────────────")
    eng._set("Present", MultoidValue("Present_State"))
    eng._snapshot()
    eng._set("Present", MultoidValue("Changed_State"))
    eng.reverse(steps=1)    # Restore — but keep future memory

    # ── TurtleWalker question flow ────────────────────────────────
    print("\n─── TurtleWalker Integration: QUESTION_FLOW ───────────────")
    eng.question_flow(
        question="Find anomalies in Q2 expenses",
        sources=["excel", "word", "files"]
    )

    # ── Final state ───────────────────────────────────────────────
    eng.visualize()

    # Export RTD for TurtleWalker
    rtd = eng.export_rtd()
    print(f"RTD Export: {len(rtd['nodes'])} nodes · {len(rtd['links'])} links")
    with open("multoid_rtd_export.json", "w") as f:
        json.dump(rtd, f, indent=2, default=str)
    print("→ multoid_rtd_export.json written")

    print("\n" + "═"*70)
    print("The mysteress smiles. The engine breathes. The alchemy is real.")
    print("═"*70 + "\n")

    return eng


if __name__ == "__main__":
    engine = demo_all_operators()
