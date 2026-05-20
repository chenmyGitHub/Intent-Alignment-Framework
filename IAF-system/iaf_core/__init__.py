"""IAF Core — Intent Alignment Framework core engine."""

from iaf_core.atoms import (
    IntentAtom, AtomCategory, AtomKind, DepType, TraceState,
    Exists, ExistsUnique, NonEmpty, Empty,
    Assoc, Subset, Disjoint, Dep, Precedes,
    Reachable, Reversible, Idempotent, Atomic,
    Always, Eventually, ForAll, ForSome, Bound,
    Prefer, PreferEq, Avoid, Weight, Soft,
    Autonomy, Confirm, Fuzzy, Probabilistic,
    exists, exists_unique, non_empty, empty,
    assoc, subset, disjoint, dep, precedes,
    reachable, reversible, idempotent, atomic,
    always, eventually, forall, forsome, bound,
    prefer, prefer_eq, avoid, weight, soft,
    autonomy, confirm, fuzzy, probabilistic,
)
from iaf_core.spaces import Intent
from iaf_core.operators import CombineOp, combine, detect_conflict, verify_properties
from iaf_core.consistency import ConsistencyLevel, check_consistency, check_all, encode_to_z3, ConsistencyResult
from iaf_core.verification import VerifyLevel, layered_verify, full_verification_report, ValidationResult
from iaf_core.evolution import (
    TransformType, Delta, VersionedIntent,
    apply_transform, invert_transform, evolve, diff, verify_weak_invertibility,
)

__all__ = [
    "IntentAtom", "AtomCategory", "AtomKind", "DepType", "TraceState",
    "Exists", "ExistsUnique", "NonEmpty", "Empty",
    "Assoc", "Subset", "Disjoint", "Dep", "Precedes",
    "Reachable", "Reversible", "Idempotent", "Atomic",
    "Always", "Eventually", "ForAll", "ForSome", "Bound",
    "Prefer", "PreferEq", "Avoid", "Weight", "Soft",
    "Autonomy", "Confirm", "Fuzzy", "Probabilistic",
    "exists", "exists_unique", "non_empty", "empty",
    "assoc", "subset", "disjoint", "dep", "precedes",
    "reachable", "reversible", "idempotent", "atomic",
    "always", "eventually", "forall", "forsome", "bound",
    "prefer", "prefer_eq", "avoid", "weight", "soft",
    "autonomy", "confirm", "fuzzy", "probabilistic",
    "Intent",
    "CombineOp", "combine", "detect_conflict", "verify_properties",
    "ConsistencyLevel", "check_consistency", "check_all", "encode_to_z3", "ConsistencyResult",
    "VerifyLevel", "layered_verify", "full_verification_report", "ValidationResult",
    "TransformType", "Delta", "VersionedIntent",
    "apply_transform", "invert_transform", "evolve", "diff", "verify_weak_invertibility",
]
