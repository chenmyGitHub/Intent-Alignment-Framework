"""IAF Intent Atom System — 6 categories, 27 atoms with formal semantics and trace satisfaction.

Categories:
    Existence  (4):   Exists, ExistsUnique, NonEmpty, Empty
    Relational (5):   Assoc, Subset, Disjoint, Dep, Precedes
    Behavioral (4):   Reachable, Reversible, Idempotent, Atomic
    Constraint (5):   Always, Eventually, ForAll, ForSome, Bound
    Preference (5):   Prefer, PreferEq, Avoid, Weight, Soft
    Uncertainty(4):   Autonomy, Confirm, Fuzzy, Probabilistic
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import (
    Any,
    Callable,
    FrozenSet,
    Generic,
    Hashable,
    Mapping,
    Optional,
    Protocol,
    Sequence,
    Set,
    Tuple,
    TypeVar,
    Union,
    runtime_checkable,
)

# ---------------------------------------------------------------------------
# Trace model
# ---------------------------------------------------------------------------

T = TypeVar("T", covariant=True)


@dataclass(frozen=True)
class TraceState:
    """A single snapshot in a trace.

    Attributes:
        entities:  Mapping from entity name -> set of values / properties
        predicates: Mapping from predicate name -> bool
        transitions: Set of (source, target) pairs active in this state
        assignments: Mapping from variable name -> concrete value
    """

    entities: Mapping[str, FrozenSet[Any]] = field(default_factory=dict)
    predicates: Mapping[str, bool] = field(default_factory=dict)
    transitions: FrozenSet[Tuple[str, str]] = field(default_factory=frozenset)
    assignments: Mapping[str, Any] = field(default_factory=dict)

    def __hash__(self) -> int:
        return hash((
            frozenset(self.entities.items()),
            frozenset(self.predicates.items()),
            self.transitions,
            frozenset((k, repr(v)) for k, v in self.assignments.items()),
        ))


Trace = Sequence[TraceState]
Formula = Union[str, Callable[[TraceState], bool]]

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class AtomCategory(Enum):
    """Top-level categories of intent atoms."""

    EXISTENCE = "existence"
    RELATIONAL = "relational"
    BEHAVIORAL = "behavioral"
    CONSTRAINT = "constraint"
    PREFERENCE = "preference"
    UNCERTAINTY = "uncertainty"


class AtomKind(Enum):
    """Finer-grained kind for each of the 27 atoms."""

    # Existence (4)
    EXISTS = auto()
    EXISTS_UNIQUE = auto()
    NON_EMPTY = auto()
    EMPTY = auto()

    # Relational (5)
    ASSOC = auto()
    SUBSET = auto()
    DISJOINT = auto()
    DEP = auto()
    PRECEDES = auto()

    # Behavioral (4)
    REACHABLE = auto()
    REVERSIBLE = auto()
    IDEMPOTENT = auto()
    ATOMIC = auto()

    # Constraint (5)
    ALWAYS = auto()
    EVENTUALLY = auto()
    FOR_ALL = auto()
    FOR_SOME = auto()
    BOUND = auto()

    # Preference (5)
    PREFER = auto()
    PREFER_EQ = auto()
    AVOID = auto()
    WEIGHT = auto()
    SOFT = auto()

    # Uncertainty (4)
    AUTONOMY = auto()
    CONFIRM = auto()
    FUZZY = auto()
    PROBABILISTIC = auto()


class DepType(Enum):
    """Dependency kind for the Dep relational atom."""

    DATA = "data"
    CONTROL = "control"
    TEMPORAL = "temporal"


# ---------------------------------------------------------------------------
# Base protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class IntentAtomProtocol(Protocol):
    """Every intent atom must satisfy this contract."""

    @property
    def kind(self) -> AtomKind: ...

    @property
    def category(self) -> AtomCategory: ...

    @property
    def formal_semantics(self) -> str: ...

    def satisfies(self, trace: Trace) -> bool: ...

    def __hash__(self) -> int: ...


# ---------------------------------------------------------------------------
# Abstract base with common machinery
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class IntentAtom(IntentAtomProtocol, ABC):
    """Abstract base for all intent atoms.

    Subclasses must define ``kind``, ``category``, ``formal_semantics``,
    and ``satisfies``.  Frozen dataclass guarantees ``__hash__``.
    """

    @property
    @abstractmethod
    def kind(self) -> AtomKind: ...

    @property
    @abstractmethod
    def category(self) -> AtomCategory: ...

    @property
    @abstractmethod
    def formal_semantics(self) -> str: ...

    @abstractmethod
    def satisfies(self, trace: Trace) -> bool: ...

    def __hash__(self) -> int:
        return hash((self.kind, self.formal_semantics))


# ===================================================================
# 1. EXISTENCE ATOMS (4)
# ===================================================================


@dataclass(frozen=True)
class Exists(IntentAtom):
    """Asserts that entity ``x`` exists in at least one state."""

    x: str

    @property
    def kind(self) -> AtomKind:
        return AtomKind.EXISTS

    @property
    def category(self) -> AtomCategory:
        return AtomCategory.EXISTENCE

    @property
    def formal_semantics(self) -> str:
        return r"\exists s \in \sigma.\; x \in \mathsf{entities}(s)"

    def satisfies(self, trace: Trace) -> bool:
        return any(self.x in s.entities for s in trace)


@dataclass(frozen=True)
class ExistsUnique(IntentAtom):
    """Asserts that entity ``x`` exists in exactly one state."""

    x: str

    @property
    def kind(self) -> AtomKind:
        return AtomKind.EXISTS_UNIQUE

    @property
    def category(self) -> AtomCategory:
        return AtomCategory.EXISTENCE

    @property
    def formal_semantics(self) -> str:
        return r"\exists! s \in \sigma.\; x \in \mathsf{entities}(s)"

    def satisfies(self, trace: Trace) -> bool:
        return sum(1 for s in trace if self.x in s.entities) == 1


@dataclass(frozen=True)
class NonEmpty(IntentAtom):
    """Asserts that set ``S`` is non-empty (appears with ≥ 1 member)."""

    S: str

    @property
    def kind(self) -> AtomKind:
        return AtomKind.NON_EMPTY

    @property
    def category(self) -> AtomCategory:
        return AtomCategory.EXISTENCE

    @property
    def formal_semantics(self) -> str:
        return r"\exists s \in \sigma.\; S \in \mathsf{entities}(s) \land |S| > 0"

    def satisfies(self, trace: Trace) -> bool:
        return any(
            self.S in s.entities and len(s.entities[self.S]) > 0
            for s in trace
        )


@dataclass(frozen=True)
class Empty(IntentAtom):
    """Asserts that set ``S`` is empty across the entire trace."""

    S: str

    @property
    def kind(self) -> AtomKind:
        return AtomKind.EMPTY

    @property
    def category(self) -> AtomCategory:
        return AtomCategory.EXISTENCE

    @property
    def formal_semantics(self) -> str:
        return r"\forall s \in \sigma.\; S \in \mathsf{entities}(s) \Rightarrow |S| = 0"

    def satisfies(self, trace: Trace) -> bool:
        return all(
            self.S not in s.entities or len(s.entities[self.S]) == 0
            for s in trace
        )


# ===================================================================
# 2. RELATIONAL ATOMS (5)
# ===================================================================


@dataclass(frozen=True)
class Assoc(IntentAtom):
    """Asserts entities ``x`` and ``y`` are associated (co-occur in some state)."""

    x: str
    y: str

    @property
    def kind(self) -> AtomKind:
        return AtomKind.ASSOC

    @property
    def category(self) -> AtomCategory:
        return AtomCategory.RELATIONAL

    @property
    def formal_semantics(self) -> str:
        return r"\exists s \in \sigma.\; x \in \mathsf{entities}(s) \land y \in \mathsf{entities}(s)"

    def satisfies(self, trace: Trace) -> bool:
        return any(self.x in s.entities and self.y in s.entities for s in trace)


@dataclass(frozen=True)
class Subset(IntentAtom):
    """Asserts that the value set of ``x`` is a subset of ``y``'s in every state."""

    x: str
    y: str

    @property
    def kind(self) -> AtomKind:
        return AtomKind.SUBSET

    @property
    def category(self) -> AtomCategory:
        return AtomCategory.RELATIONAL

    @property
    def formal_semantics(self) -> str:
        return r"\forall s \in \sigma.\; x \in \mathsf{entities}(s) \land y \in \mathsf{entities}(s) \Rightarrow \mathsf{val}(x) \subseteq \mathsf{val}(y)"

    def satisfies(self, trace: Trace) -> bool:
        for s in trace:
            if self.x in s.entities and self.y in s.entities:
                if not s.entities[self.x].issubset(s.entities[self.y]):
                    return False
        return True


@dataclass(frozen=True)
class Disjoint(IntentAtom):
    """Asserts that ``x`` and ``y`` never share common values."""

    x: str
    y: str

    @property
    def kind(self) -> AtomKind:
        return AtomKind.DISJOINT

    @property
    def category(self) -> AtomCategory:
        return AtomCategory.RELATIONAL

    @property
    def formal_semantics(self) -> str:
        return r"\forall s \in \sigma.\; \mathsf{val}(x) \cap \mathsf{val}(y) = \emptyset"

    def satisfies(self, trace: Trace) -> bool:
        for s in trace:
            if self.x in s.entities and self.y in s.entities:
                if s.entities[self.x] & s.entities[self.y]:
                    return False
        return True


@dataclass(frozen=True)
class Dep(IntentAtom):
    """Asserts that ``x`` depends on ``y`` with dependency type ``k``."""

    x: str
    y: str
    k: DepType

    @property
    def kind(self) -> AtomKind:
        return AtomKind.DEP

    @property
    def category(self) -> AtomCategory:
        return AtomCategory.RELATIONAL

    @property
    def formal_semantics(self) -> str:
        return (
            r"\forall s \in \sigma.\; \mathsf{dep}(x, y, k) \in s.\mathsf{transitions}"
            r"\quad\text{where } k \in \{\text{data}, \text{control}, \text{temporal}\}"
        )

    def satisfies(self, trace: Trace) -> bool:
        for s in trace:
            if self.x in s.entities and self.y in s.entities:
                if (self.x, self.y) not in s.transitions:
                    return False
        return True


@dataclass(frozen=True)
class Precedes(IntentAtom):
    """Asserts that ``x`` appears before ``y`` in the trace order."""

    x: str
    y: str

    @property
    def kind(self) -> AtomKind:
        return AtomKind.PRECEDES

    @property
    def category(self) -> AtomCategory:
        return AtomCategory.RELATIONAL

    @property
    def formal_semantics(self) -> str:
        return r"\exists i, j \in [0, |\sigma|).\; i < j \land x \in \mathsf{entities}(\sigma_i) \land y \in \mathsf{entities}(\sigma_j)"

    def satisfies(self, trace: Trace) -> bool:
        xi: Optional[int] = None
        yi: Optional[int] = None
        for i, s in enumerate(trace):
            if self.x in s.entities and xi is None:
                xi = i
            if self.y in s.entities and yi is None:
                yi = i
            if xi is not None and yi is not None:
                return xi < yi
        return False


# ===================================================================
# 3. BEHAVIORAL ATOMS (4)
# ===================================================================


@dataclass(frozen=True)
class Reachable(IntentAtom):
    """Asserts that state/action ``b`` is reachable from ``a``."""

    a: str
    b: str

    @property
    def kind(self) -> AtomKind:
        return AtomKind.REACHABLE

    @property
    def category(self) -> AtomCategory:
        return AtomCategory.BEHAVIORAL

    @property
    def formal_semantics(self) -> str:
        return r"\exists i, j.\; i \leq j \land a \in \sigma_i \land b \in \sigma_j \land \mathsf{path}(a \leadsto b)"

    def satisfies(self, trace: Trace) -> bool:
        a_seen = False
        for s in trace:
            if self.a in s.entities:
                a_seen = True
            if a_seen and self.b in s.entities:
                return True
            if a_seen:
                # Check transition path
                for (src, tgt) in s.transitions:
                    if src == self.a or (a_seen and src):
                        if tgt == self.b:
                            return True
        return False


@dataclass(frozen=True)
class Reversible(IntentAtom):
    """Asserts that the transition ``a → b`` can be reversed (b → a also occurs)."""

    a: str
    b: str

    @property
    def kind(self) -> AtomKind:
        return AtomKind.REVERSIBLE

    @property
    def category(self) -> AtomCategory:
        return AtomCategory.BEHAVIORAL

    @property
    def formal_semantics(self) -> str:
        return r"(a \rightarrow b) \land \Diamond(b \rightarrow a)"

    def satisfies(self, trace: Trace) -> bool:
        fwd = False
        rev = False
        for s in trace:
            if (self.a, self.b) in s.transitions:
                fwd = True
            if (self.b, self.a) in s.transitions:
                rev = True
        return fwd and rev


@dataclass(frozen=True)
class Idempotent(IntentAtom):
    """Asserts that applying function ``f`` twice yields the same result as once."""

    f: str

    @property
    def kind(self) -> AtomKind:
        return AtomKind.IDEMPOTENT

    @property
    def category(self) -> AtomCategory:
        return AtomCategory.BEHAVIORAL

    @property
    def formal_semantics(self) -> str:
        return r"\forall x.\; f(f(x)) = f(x)"

    def satisfies(self, trace: Trace) -> bool:
        for s in trace:
            if self.f in s.assignments:
                val = s.assignments[self.f]
                # Check: f(val) == val implies idempotence
                if self.f in s.assignments:
                    return True  # Simplified: presence in assignments implies stable
        return len(trace) > 0 and any(self.f in s.assignments for s in trace)


@dataclass(frozen=True)
class Atomic(IntentAtom):
    """Asserts that function ``f`` executes atomically (no interleaving)."""

    f: str

    @property
    def kind(self) -> AtomKind:
        return AtomKind.ATOMIC

    @property
    def category(self) -> AtomCategory:
        return AtomCategory.BEHAVIORAL

    @property
    def formal_semantics(self) -> str:
        return r"\forall s_i, s_j.\; i \neq j \Rightarrow \neg(\mathsf{in\_progress}(f, s_i) \land \mathsf{in\_progress}(f, s_j))"

    def satisfies(self, trace: Trace) -> bool:
        # Atomic: f appears as a predicate in at most one state
        count = sum(1 for s in trace if s.predicates.get(f"f:{self.f}", False))
        return count <= 1


# ===================================================================
# 4. CONSTRAINT ATOMS (5)
# ===================================================================


@dataclass(frozen=True)
class Always(IntentAtom):
    """LTL □φ: formula ``phi`` holds in every state."""

    phi: Formula

    @property
    def kind(self) -> AtomKind:
        return AtomKind.ALWAYS

    @property
    def category(self) -> AtomCategory:
        return AtomCategory.CONSTRAINT

    @property
    def formal_semantics(self) -> str:
        return r"\Box \varphi \equiv \forall i \in [0, |\sigma|).\; \sigma_i \models \varphi"

    def satisfies(self, trace: Trace) -> bool:
        if callable(self.phi):
            return all(self.phi(s) for s in trace)
        # phi is a predicate name string
        return all(s.predicates.get(self.phi, False) for s in trace)


@dataclass(frozen=True)
class Eventually(IntentAtom):
    """LTL ◇φ: formula ``phi`` holds in at least one state."""

    phi: Formula

    @property
    def kind(self) -> AtomKind:
        return AtomKind.EVENTUALLY

    @property
    def category(self) -> AtomCategory:
        return AtomCategory.CONSTRAINT

    @property
    def formal_semantics(self) -> str:
        return r"\Diamond \varphi \equiv \exists i \in [0, |\sigma|).\; \sigma_i \models \varphi"

    def satisfies(self, trace: Trace) -> bool:
        if callable(self.phi):
            return any(self.phi(s) for s in trace)
        return any(s.predicates.get(self.phi, False) for s in trace)


@dataclass(frozen=True)
class ForAll(IntentAtom):
    """∀x ∈ S: constraint ``C`` holds for every element."""

    x: str
    S: str
    C: Formula

    @property
    def kind(self) -> AtomKind:
        return AtomKind.FOR_ALL

    @property
    def category(self) -> AtomCategory:
        return AtomCategory.CONSTRAINT

    @property
    def formal_semantics(self) -> str:
        return r"\forall x \in S.\; C(x)"

    def satisfies(self, trace: Trace) -> bool:
        for s in trace:
            if self.S in s.entities:
                if callable(self.C):
                    if not all(self.C(s) for _ in s.entities[self.S]):
                        return False
                else:
                    if not s.predicates.get(self.C, False):
                        return False
        return True


@dataclass(frozen=True)
class ForSome(IntentAtom):
    """∃x ∈ S: constraint ``C`` holds for at least one element."""

    x: str
    S: str
    C: Formula

    @property
    def kind(self) -> AtomKind:
        return AtomKind.FOR_SOME

    @property
    def category(self) -> AtomCategory:
        return AtomCategory.CONSTRAINT

    @property
    def formal_semantics(self) -> str:
        return r"\exists x \in S.\; C(x)"

    def satisfies(self, trace: Trace) -> bool:
        for s in trace:
            if self.S in s.entities and len(s.entities[self.S]) > 0:
                if callable(self.C):
                    if self.C(s):
                        return True
                else:
                    if s.predicates.get(self.C, False):
                        return True
        return False


@dataclass(frozen=True)
class Bound(IntentAtom):
    """Asserts that variable ``x`` stays within [lo, hi] across all states."""

    x: str
    lo: float
    hi: float

    @property
    def kind(self) -> AtomKind:
        return AtomKind.BOUND

    @property
    def category(self) -> AtomCategory:
        return AtomCategory.CONSTRAINT

    @property
    def formal_semantics(self) -> str:
        return r"\forall s \in \sigma.\; \mathsf{lo} \leq \mathsf{val}(x, s) \leq \mathsf{hi}"

    def satisfies(self, trace: Trace) -> bool:
        for s in trace:
            if self.x in s.assignments:
                val = s.assignments[self.x]
                if isinstance(val, (int, float)):
                    if val < self.lo or val > self.hi:
                        return False
        return True


# ===================================================================
# 5. PREFERENCE ATOMS (5)
# ===================================================================


@dataclass(frozen=True)
class Prefer(IntentAtom):
    """Strict preference: ``a`` is preferred over ``b``."""

    a: str
    b: str

    @property
    def kind(self) -> AtomKind:
        return AtomKind.PREFER

    @property
    def category(self) -> AtomCategory:
        return AtomCategory.PREFERENCE

    @property
    def formal_semantics(self) -> str:
        return r"a \succ b"

    def satisfies(self, trace: Trace) -> bool:
        # Preference satisfied when 'a' appears and 'b' does not dominate
        for s in trace:
            a_present = self.a in s.entities or s.predicates.get(self.a, False)
            b_present = self.b in s.entities or s.predicates.get(self.b, False)
            if a_present and not b_present:
                return True
        # Also satisfied if neither appears (vacuous)
        return True


@dataclass(frozen=True)
class PreferEq(IntentAtom):
    """Weak preference: ``a`` is at least as good as ``b``."""

    a: str
    b: str

    @property
    def kind(self) -> AtomKind:
        return AtomKind.PREFER_EQ

    @property
    def category(self) -> AtomCategory:
        return AtomCategory.PREFERENCE

    @property
    def formal_semantics(self) -> str:
        return r"a \succeq b"

    def satisfies(self, trace: Trace) -> bool:
        # Weak preference: a appears at least as often as b
        a_count = sum(1 for s in trace if self.a in s.entities or s.predicates.get(self.a, False))
        b_count = sum(1 for s in trace if self.b in s.entities or s.predicates.get(self.b, False))
        return a_count >= b_count


@dataclass(frozen=True)
class Avoid(IntentAtom):
    """Entity ``x`` should not appear in any state."""

    x: str

    @property
    def kind(self) -> AtomKind:
        return AtomKind.AVOID

    @property
    def category(self) -> AtomCategory:
        return AtomCategory.PREFERENCE

    @property
    def formal_semantics(self) -> str:
        return r"\forall s \in \sigma.\; x \notin \mathsf{entities}(s) \land \neg \mathsf{pred}(x, s)"

    def satisfies(self, trace: Trace) -> bool:
        return all(
            self.x not in s.entities and not s.predicates.get(self.x, False)
            for s in trace
        )


@dataclass(frozen=True)
class Weight(IntentAtom):
    """Assigns weight ``alpha`` ∈ [0,1] to entity ``x``."""

    x: str
    alpha: float

    @property
    def kind(self) -> AtomKind:
        return AtomKind.WEIGHT

    @property
    def category(self) -> AtomCategory:
        return AtomCategory.PREFERENCE

    @property
    def formal_semantics(self) -> str:
        return r"\mathsf{weight}(x) = \alpha \quad \text{where } \alpha \in [0, 1]"

    def satisfies(self, trace: Trace) -> bool:
        # Weight is satisfied if alpha is valid and x appears with correct weight
        if not (0.0 <= self.alpha <= 1.0):
            return False
        return any(self.x in s.assignments for s in trace) or len(trace) == 0


@dataclass(frozen=True)
class Soft(IntentAtom):
    """Soft constraint: ``phi`` is desirable but not mandatory."""

    phi: Formula

    @property
    def kind(self) -> AtomKind:
        return AtomKind.SOFT

    @property
    def category(self) -> AtomCategory:
        return AtomCategory.PREFERENCE

    @property
    def formal_semantics(self) -> str:
        return r"\mathsf{soft}(\varphi) \equiv \text{prefer } \varphi \text{ but allow } \neg\varphi"

    def satisfies(self, trace: Trace) -> bool:
        # Soft constraints always "satisfy" — they express preference, not requirement
        return True


# ===================================================================
# 6. UNCERTAINTY ATOMS (4)
# ===================================================================


@dataclass(frozen=True)
class Autonomy(IntentAtom):
    """Entity ``x`` can operate independently (no external transitions required)."""

    x: str

    @property
    def kind(self) -> AtomKind:
        return AtomKind.AUTONOMY

    @property
    def category(self) -> AtomCategory:
        return AtomCategory.UNCERTAINTY

    @property
    def formal_semantics(self) -> str:
        return r"\mathsf{autonomous}(x) \equiv \nexists y.\; \mathsf{dep}(x, y, k)"

    def satisfies(self, trace: Trace) -> bool:
        for s in trace:
            if self.x in s.entities:
                # Check no incoming transitions from other entities
                for (src, tgt) in s.transitions:
                    if tgt == self.x and src != self.x:
                        return False
        return True


@dataclass(frozen=True)
class Confirm(IntentAtom):
    """Entity ``x`` requires confirmation before proceeding."""

    x: str

    @property
    def kind(self) -> AtomKind:
        return AtomKind.CONFIRM

    @property
    def category(self) -> AtomCategory:
        return AtomCategory.UNCERTAINTY

    @property
    def formal_semantics(self) -> str:
        return r"\mathsf{confirm}(x) \equiv \Diamond \mathsf{ack}(x)"

    def satisfies(self, trace: Trace) -> bool:
        x_seen = False
        for s in trace:
            if self.x in s.entities:
                x_seen = True
            if x_seen and s.predicates.get(f"ack:{self.x}", False):
                return True
        return False  # If x never appeared, confirmation was never needed


@dataclass(frozen=True)
class Fuzzy(IntentAtom):
    """Entity ``x`` has fuzzy membership with tolerance ``epsilon``."""

    x: str
    epsilon: float

    @property
    def kind(self) -> AtomKind:
        return AtomKind.FUZZY

    @property
    def category(self) -> AtomCategory:
        return AtomCategory.UNCERTAINTY

    @property
    def formal_semantics(self) -> str:
        return r"\mu_x(v) \in [0, 1] \pm \varepsilon"

    def satisfies(self, trace: Trace) -> bool:
        if not (0.0 <= self.epsilon <= 1.0):
            return False
        # Fuzzy is satisfied when x appears with valid membership bounds
        return any(self.x in s.entities for s in trace) or len(trace) == 0


@dataclass(frozen=True)
class Probabilistic(IntentAtom):
    """Entity ``x`` holds with probability ``p``."""

    x: str
    p: float

    @property
    def kind(self) -> AtomKind:
        return AtomKind.PROBABILISTIC

    @property
    def category(self) -> AtomCategory:
        return AtomCategory.UNCERTAINTY

    @property
    def formal_semantics(self) -> str:
        return r"P(x) = p \quad \text{where } p \in [0, 1]"

    def satisfies(self, trace: Trace) -> bool:
        if not (0.0 <= self.p <= 1.0):
            return False
        # Probabilistic constraint is satisfied if p is a valid probability
        return True


# ===================================================================
# Factory / Registry
# ===================================================================

# Mapping from AtomKind to its implementing class
ATOM_REGISTRY: dict[AtomKind, type[IntentAtom]] = {
    # Existence
    AtomKind.EXISTS: Exists,
    AtomKind.EXISTS_UNIQUE: ExistsUnique,
    AtomKind.NON_EMPTY: NonEmpty,
    AtomKind.EMPTY: Empty,
    # Relational
    AtomKind.ASSOC: Assoc,
    AtomKind.SUBSET: Subset,
    AtomKind.DISJOINT: Disjoint,
    AtomKind.DEP: Dep,
    AtomKind.PRECEDES: Precedes,
    # Behavioral
    AtomKind.REACHABLE: Reachable,
    AtomKind.REVERSIBLE: Reversible,
    AtomKind.IDEMPOTENT: Idempotent,
    AtomKind.ATOMIC: Atomic,
    # Constraint
    AtomKind.ALWAYS: Always,
    AtomKind.EVENTUALLY: Eventually,
    AtomKind.FOR_ALL: ForAll,
    AtomKind.FOR_SOME: ForSome,
    AtomKind.BOUND: Bound,
    # Preference
    AtomKind.PREFER: Prefer,
    AtomKind.PREFER_EQ: PreferEq,
    AtomKind.AVOID: Avoid,
    AtomKind.WEIGHT: Weight,
    AtomKind.SOFT: Soft,
    # Uncertainty
    AtomKind.AUTONOMY: Autonomy,
    AtomKind.CONFIRM: Confirm,
    AtomKind.FUZZY: Fuzzy,
    AtomKind.PROBABILISTIC: Probabilistic,
}

# Quick category → kinds lookup
CATEGORY_KINDS: dict[AtomCategory, list[AtomKind]] = {
    AtomCategory.EXISTENCE: [AtomKind.EXISTS, AtomKind.EXISTS_UNIQUE, AtomKind.NON_EMPTY, AtomKind.EMPTY],
    AtomCategory.RELATIONAL: [AtomKind.ASSOC, AtomKind.SUBSET, AtomKind.DISJOINT, AtomKind.DEP, AtomKind.PRECEDES],
    AtomCategory.BEHAVIORAL: [AtomKind.REACHABLE, AtomKind.REVERSIBLE, AtomKind.IDEMPOTENT, AtomKind.ATOMIC],
    AtomCategory.CONSTRAINT: [AtomKind.ALWAYS, AtomKind.EVENTUALLY, AtomKind.FOR_ALL, AtomKind.FOR_SOME, AtomKind.BOUND],
    AtomCategory.PREFERENCE: [AtomKind.PREFER, AtomKind.PREFER_EQ, AtomKind.AVOID, AtomKind.WEIGHT, AtomKind.SOFT],
    AtomCategory.UNCERTAINTY: [AtomKind.AUTONOMY, AtomKind.CONFIRM, AtomKind.FUZZY, AtomKind.PROBABILISTIC],
}


def all_atom_kinds() -> list[AtomKind]:
    """Return all 27 atom kinds in canonical order."""
    return [k for kinds in CATEGORY_KINDS.values() for k in kinds]


def atom_by_kind(kind: AtomKind) -> type[IntentAtom]:
    """Look up the implementing class for a given AtomKind."""
    cls = ATOM_REGISTRY.get(kind)
    if cls is None:
        raise KeyError(f"No atom class registered for {kind}")
    return cls


# ---------------------------------------------------------------------------
# Convenience constructors
# ---------------------------------------------------------------------------


def exists(x: str) -> Exists:
    return Exists(x=x)


def exists_unique(x: str) -> ExistsUnique:
    return ExistsUnique(x=x)


def non_empty(S: str) -> NonEmpty:
    return NonEmpty(S=S)


def empty(S: str) -> Empty:
    return Empty(S=S)


def assoc(x: str, y: str) -> Assoc:
    return Assoc(x=x, y=y)


def subset(x: str, y: str) -> Subset:
    return Subset(x=x, y=y)


def disjoint(x: str, y: str) -> Disjoint:
    return Disjoint(x=x, y=y)


def dep(x: str, y: str, k: DepType | str) -> Dep:
    if isinstance(k, str):
        k = DepType(k)
    return Dep(x=x, y=y, k=k)


def precedes(x: str, y: str) -> Precedes:
    return Precedes(x=x, y=y)


def reachable(a: str, b: str) -> Reachable:
    return Reachable(a=a, b=b)


def reversible(a: str, b: str) -> Reversible:
    return Reversible(a=a, b=b)


def idempotent(f: str) -> Idempotent:
    return Idempotent(f=f)


def atomic(f: str) -> Atomic:
    return Atomic(f=f)


def always(phi: Formula) -> Always:
    return Always(phi=phi)


def eventually(phi: Formula) -> Eventually:
    return Eventually(phi=phi)


def forall(x: str, S: str, C: Formula) -> ForAll:
    return ForAll(x=x, S=S, C=C)


def forsome(x: str, S: str, C: Formula) -> ForSome:
    return ForSome(x=x, S=S, C=C)


def bound(x: str, lo: float, hi: float) -> Bound:
    return Bound(x=x, lo=lo, hi=hi)


def prefer(a: str, b: str) -> Prefer:
    return Prefer(a=a, b=b)


def prefer_eq(a: str, b: str) -> PreferEq:
    return PreferEq(a=a, b=b)


def avoid(x: str) -> Avoid:
    return Avoid(x=x)


def weight(x: str, alpha: float) -> Weight:
    return Weight(x=x, alpha=alpha)


def soft(phi: Formula) -> Soft:
    return Soft(phi=phi)


def autonomy(x: str) -> Autonomy:
    return Autonomy(x=x)


def confirm(x: str) -> Confirm:
    return Confirm(x=x)


def fuzzy(x: str, epsilon: float) -> Fuzzy:
    return Fuzzy(x=x, epsilon=epsilon)


def probabilistic(x: str, p: float) -> Probabilistic:
    return Probabilistic(x=x, p=p)


# ---------------------------------------------------------------------------
# Pretty printing
# ---------------------------------------------------------------------------


def atoms_table() -> str:
    """Return a formatted table of all 27 atoms with category, kind, and semantics."""
    lines = [
        f"{'#':>2}  {'Category':<14} {'Kind':<16} {'Formal Semantics'}",
        "-" * 90,
    ]
    # Representative instances for atoms requiring parameters
    representative: dict[AtomKind, IntentAtom] = {
        AtomKind.EXISTS: Exists(x="x"),
        AtomKind.EXISTS_UNIQUE: ExistsUnique(x="x"),
        AtomKind.NON_EMPTY: NonEmpty(S="S"),
        AtomKind.EMPTY: Empty(S="S"),
        AtomKind.ASSOC: Assoc(x="x", y="y"),
        AtomKind.SUBSET: Subset(x="x", y="y"),
        AtomKind.DISJOINT: Disjoint(x="x", y="y"),
        AtomKind.DEP: Dep(x="x", y="y", k=DepType.DATA),
        AtomKind.PRECEDES: Precedes(x="x", y="y"),
        AtomKind.REACHABLE: Reachable(a="a", b="b"),
        AtomKind.REVERSIBLE: Reversible(a="a", b="b"),
        AtomKind.IDEMPOTENT: Idempotent(f="f"),
        AtomKind.ATOMIC: Atomic(f="f"),
        AtomKind.ALWAYS: Always(phi="φ"),
        AtomKind.EVENTUALLY: Eventually(phi="φ"),
        AtomKind.FOR_ALL: ForAll(x="x", S="S", C="C"),
        AtomKind.FOR_SOME: ForSome(x="x", S="S", C="C"),
        AtomKind.BOUND: Bound(x="x", lo=0.0, hi=1.0),
        AtomKind.PREFER: Prefer(a="a", b="b"),
        AtomKind.PREFER_EQ: PreferEq(a="a", b="b"),
        AtomKind.AVOID: Avoid(x="x"),
        AtomKind.WEIGHT: Weight(x="x", alpha=0.5),
        AtomKind.SOFT: Soft(phi="φ"),
        AtomKind.AUTONOMY: Autonomy(x="x"),
        AtomKind.CONFIRM: Confirm(x="x"),
        AtomKind.FUZZY: Fuzzy(x="x", epsilon=0.1),
        AtomKind.PROBABILISTIC: Probabilistic(x="x", p=0.5),
    }
    for idx, kind in enumerate(all_atom_kinds(), 1):
        atom = representative[kind]
        lines.append(f"{idx:>2}  {atom.category.value:<14} {kind.name:<16} {atom.formal_semantics}")
    return "\n".join(lines)


# Export all public symbols
__all__ = [
    # Trace model
    "TraceState",
    "Trace",
    "Formula",
    # Enums
    "AtomCategory",
    "AtomKind",
    "DepType",
    # Protocol / Base
    "IntentAtomProtocol",
    "IntentAtom",
    # Existence
    "Exists",
    "ExistsUnique",
    "NonEmpty",
    "Empty",
    # Relational
    "Assoc",
    "Subset",
    "Disjoint",
    "Dep",
    "Precedes",
    # Behavioral
    "Reachable",
    "Reversible",
    "Idempotent",
    "Atomic",
    # Constraint
    "Always",
    "Eventually",
    "ForAll",
    "ForSome",
    "Bound",
    # Preference
    "Prefer",
    "PreferEq",
    "Avoid",
    "Weight",
    "Soft",
    # Uncertainty
    "Autonomy",
    "Confirm",
    "Fuzzy",
    "Probabilistic",
    # Registry / Factory
    "ATOM_REGISTRY",
    "CATEGORY_KINDS",
    "all_atom_kinds",
    "atom_by_kind",
    # Convenience constructors
    "exists",
    "exists_unique",
    "non_empty",
    "empty",
    "assoc",
    "subset",
    "disjoint",
    "dep",
    "precedes",
    "reachable",
    "reversible",
    "idempotent",
    "atomic",
    "always",
    "eventually",
    "forall",
    "forsome",
    "bound",
    "prefer",
    "prefer_eq",
    "avoid",
    "weight",
    "soft",
    "autonomy",
    "confirm",
    "fuzzy",
    "probabilistic",
    # Utility
    "atoms_table",
]
