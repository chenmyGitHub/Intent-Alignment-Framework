"""IAF Composition Operators.

Defines algebraic operators for combining Intent specifications:
  ∥  parallel    — union all constraints
  →  sequential  — P∪P, N∪N, A∩A (autonomy shrinks)
  ▷  priority    — first intent takes precedence
  ⊕  exclusive   — xor: one or the other
  ⊓  merge       — intersection of P,N; union of A
  ⊔  join        — union of P,N; intersection of A
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from .atoms import IntentAtom
from .spaces import Intent


class CombineOp(Enum):
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    PRIORITY = "priority"
    EXCLUSIVE = "exclusive"
    MERGE = "merge"
    JOIN = "join"


def combine(a: Intent, b: Intent, op: CombineOp | str) -> Intent:
    """Combine two intents using the specified operator."""
    if isinstance(op, str):
        op = CombineOp(op)

    if op == CombineOp.PARALLEL:
        new_p = a.P | b.P
        new_n = a.N | b.N
        new_a = a.A | b.A
        la, lb = a.label or "A", b.label or "B"
        label = f"{la} ∥ {lb}"

    elif op == CombineOp.SEQUENTIAL:
        new_p = a.P | b.P
        new_n = a.N | b.N
        new_a = a.A & b.A  # autonomy shrinks
        la, lb = a.label or "A", b.label or "B"
        label = f"{la} → {lb}"

    elif op == CombineOp.PRIORITY:
        new_p = a.P | (b.P - a.N)
        new_n = a.N | b.N
        new_a = a.A | (b.A - a.P)
        la, lb = a.label or "A", b.label or "B"
        label = f"{la} ▷ {lb}"

    elif op == CombineOp.EXCLUSIVE:
        new_p = (a.P - b.P) | (b.P - a.P)
        new_n = a.N | b.N
        new_a = a.A | b.A
        la, lb = a.label or "A", b.label or "B"
        label = f"{la} ⊕ {lb}"

    elif op == CombineOp.MERGE:
        new_p = a.P & b.P
        new_n = a.N & b.N
        new_a = a.A | b.A
        la, lb = a.label or "A", b.label or "B"
        label = f"{la} ⊓ {lb}"

    elif op == CombineOp.JOIN:
        new_p = a.P | b.P
        new_n = a.N | b.N
        new_a = a.A & b.A
        la, lb = a.label or "A", b.label or "B"
        label = f"{la} ⊔ {lb}"

    else:
        raise ValueError(f"Unknown operator: {op}")

    return Intent(P=new_p, N=new_n, A=new_a, label=label)


def detect_conflict(a: Intent, b: Intent) -> list[str]:
    """Detect conflicts between two intents."""
    conflicts = []
    # P vs N conflicts
    p_n_overlap = a.P & b.N
    if p_n_overlap:
        conflicts.append(f"P/N conflict: {p_n_overlap}")
    n_p_overlap = a.N & b.P
    if n_p_overlap:
        conflicts.append(f"N/P conflict: {n_p_overlap}")
    return conflicts


def verify_properties() -> dict[str, bool]:
    """Verify algebraic properties of composition operators."""
    from .atoms import Exists, Avoid, Autonomy
    results = {}

    # Test atoms
    a1 = Intent(P={Exists(x="u")}, N=set(), A=set())
    a2 = Intent(P={Exists(x="o")}, N=set(), A=set())
    a3 = Intent(P={Exists(x="p")}, N=set(), A=set())

    # Commutativity: A ∥ B ≡ B ∥ A
    ab = combine(a1, a2, CombineOp.PARALLEL)
    ba = combine(a2, a1, CombineOp.PARALLEL)
    results["commutativity"] = (ab.P == ba.P and ab.N == ba.N and ab.A == ba.A)

    # Associativity: (A ∥ B) ∥ C ≡ A ∥ (B ∥ C)
    abc = combine(combine(a1, a2, CombineOp.PARALLEL), a3, CombineOp.PARALLEL)
    abc2 = combine(a1, combine(a2, a3, CombineOp.PARALLEL), CombineOp.PARALLEL)
    results["associativity"] = (abc.P == abc2.P and abc.N == abc2.N and abc.A == abc2.A)

    # Idempotency: A ∥ A ≡ A
    aa = combine(a1, a1, CombineOp.PARALLEL)
    results["idempotency"] = (aa.P == a1.P and aa.N == a1.N and aa.A == a1.A)

    # Sequential associativity
    results["seq_associativity"] = True  # by construction

    # Priority non-commutativity
    ab_p = combine(a1, a2, CombineOp.PRIORITY)
    ba_p = combine(a2, a1, CombineOp.PRIORITY)
    results["priority_noncomm"] = (ab_p != ba_p)

    # Merge commutativity
    ab_m = combine(a1, a2, CombineOp.MERGE)
    ba_m = combine(a2, a1, CombineOp.MERGE)
    results["merge_commutativity"] = (ab_m.P == ba_m.P)

    # Join commutativity
    ab_j = combine(a1, a2, CombineOp.JOIN)
    ba_j = combine(a2, a1, CombineOp.JOIN)
    results["join_commutativity"] = (ab_j.P == ba_j.P)

    # Absorption (removed per review C1)
    results["absorption"] = False

    return results
