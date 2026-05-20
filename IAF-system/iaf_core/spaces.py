"""IAF Intent Space — Intent(P, N, A) triple.

Represents a formal intent specification:
  P : positive constraints (must hold)
  N : negative constraints (must NOT hold)
  A : autonomy space (AI decides freely)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .atoms import IntentAtom, Trace


@dataclass(frozen=True)
class Intent:
    """IAF intent as (P, N, A) triple."""

    P: frozenset = frozenset()
    N: frozenset = frozenset()
    A: frozenset = frozenset()
    label: str = ""

    def __post_init__(self):
        # Auto-convert set to frozenset
        if isinstance(self.P, set):
            object.__setattr__(self, "P", frozenset(self.P))
        if isinstance(self.N, set):
            object.__setattr__(self, "N", frozenset(self.N))
        if isinstance(self.A, set):
            object.__setattr__(self, "A", frozenset(self.A))

    # ── Static factory ─────────────────────────────────────────
    @staticmethod
    def empty(label: str = "") -> Intent:
        return Intent(P=frozenset(), N=frozenset(), A=frozenset(), label=label)

    # ── Well-formedness ────────────────────────────────────────
    def well_formed(self) -> tuple[bool, list[str]]:
        errors = []
        # 1. Syntactic: P ∩ N = ∅
        overlap = self.P & self.N
        if overlap:
            errors.append(f"P ∩ N overlap: {overlap}")
        # 2. Autonomy disjoint: A ∩ P = ∅ and A ∩ N = ∅
        if self.A & self.P:
            errors.append(f"Autonomy overlaps P: {self.A & self.P}")
        if self.A & self.N:
            errors.append(f"Autonomy overlaps N: {self.A & self.N}")
        return (len(errors) == 0, errors)

    # ── Combine ────────────────────────────────────────────────
    def combine(self, other: Intent, op: str = "parallel") -> Intent:
        from .operators import combine
        return combine(self, other, op)

    # ── Satisfaction ───────────────────────────────────────────
    def satisfaction(self, trace: list) -> float:
        """Minimax satisfaction score [0, 1]."""
        if not self.P and not self.N:
            return 1.0
        p_satisfied = []
        for atom in self.P:
            for state in trace:
                try:
                    p_satisfied.append(atom.satisfies(state))
                except Exception:
                    p_satisfied.append(False)
                break  # check first state only

        if not p_satisfied:
            return 1.0

        # Minimax: any hard constraint failure → 0
        min_hard = min(p_satisfied) if p_satisfied else 1
        avg = sum(p_satisfied) / len(p_satisfied)
        return min_hard * avg

    # ── Helpers ────────────────────────────────────────────────
    def is_empty(self) -> bool:
        return len(self.P) == 0 and len(self.N) == 0 and len(self.A) == 0

    def size(self) -> tuple[int, int, int]:
        return (len(self.P), len(self.N), len(self.A))

    def add_p(self, atom: IntentAtom) -> Intent:
        return Intent(P=self.P | {atom}, N=self.N, A=self.A, label=self.label)

    def add_n(self, atom: IntentAtom) -> Intent:
        return Intent(P=self.P, N=self.N | {atom}, A=self.A, label=self.label)

    def add_a(self, atom: IntentAtom) -> Intent:
        return Intent(P=self.P, N=self.N, A=self.A | {atom}, label=self.label)

    def remove_p(self, atom: IntentAtom) -> Intent:
        return Intent(P=self.P - {atom}, N=self.N, A=self.A, label=self.label)

    def remove_n(self, atom: IntentAtom) -> Intent:
        return Intent(P=self.P, N=self.N - {atom}, A=self.A, label=self.label)

    def remove_a(self, atom: IntentAtom) -> Intent:
        return Intent(P=self.P, N=self.N, A=self.A - {atom}, label=self.label)

    def __repr__(self) -> str:
        label_part = f"{self.label}: " if self.label else ""
        return f"Intent({label_part}P={len(self.P)}, N={len(self.N)}, A={len(self.A)})"

    def __str__(self) -> str:
        return self.__repr__()

    def __hash__(self) -> int:
        return hash((self.P, self.N, self.A, self.label))
