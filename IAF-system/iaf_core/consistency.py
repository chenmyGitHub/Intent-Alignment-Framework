"""IAF Consistency Checking — Three-step verification.

Per IAF §5: consistency is checked in three levels:
  1. SYNTACTIC  — P ∩ N = ∅, no overlap
  2. SEMANTIC   — P ∪ ¬N is satisfiable (heuristic / SMT)
  3. AUTONOMY   — ∀a ∈ A, at least one choice doesn\'t violate P ∪ ¬N
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .spaces import Intent


class ConsistencyLevel(Enum):
    SYNTACTIC = "syntactic"
    SEMANTIC = "semantic"
    AUTONOMY = "autonomy"


@dataclass
class ConsistencyResult:
    level: str
    passed: bool
    details: list[str]
    errors: list[str]


def check_consistency(intent: Intent, level: ConsistencyLevel | str) -> ConsistencyResult:
    """Check intent consistency at the given level."""
    if isinstance(level, str):
        level = ConsistencyLevel(level)

    details = []
    errors = []

    if level == ConsistencyLevel.SYNTACTIC:
        passed, errs = intent.well_formed()
        errors = errs
        details.append(f"Syntactic check: {'PASS' if passed else 'FAIL'}")
        if not passed:
            for e in errs:
                details.append(f"  Error: {e}")

    elif level == ConsistencyLevel.SEMANTIC:
        # Heuristic: check for obvious semantic conflicts
        # (Full SMT integration would go here)
        passed = True
        # Check for Always vs Always negation patterns
        always_phis = set()
        for atom in intent.P:
            kind = getattr(atom, "kind", None)
            phi = getattr(atom, "phi", None)
            if phi:
                # Look for contradictory always constraints
                key = phi.split(">=")[0].split("<=")[0].split("<")[0].split(">")[0].strip()
                if key in always_phis:
                    passed = False
                    errors.append(f"Duplicate Always constraint: {phi}")
                always_phis.add(key)
        details.append(f"Semantic check (heuristic): {'PASS' if passed else 'FAIL'}")

    elif level == ConsistencyLevel.AUTONOMY:
        # Check autonomy completeness: A atoms don\'t contradict P or N
        passed = True
        a_p_conflict = intent.A & intent.P
        a_n_conflict = intent.A & intent.N
        if a_p_conflict:
            passed = False
            errors.append(f"Autonomy overlaps P: {a_p_conflict}")
        if a_n_conflict:
            passed = False
            errors.append(f"Autonomy overlaps N: {a_n_conflict}")
        # Also check syntactic first
        syn_ok, syn_errs = intent.well_formed()
        if not syn_ok:
            passed = False
            errors.extend(syn_errs)
        details.append(f"Autonomy completeness check: {'PASS' if passed else 'FAIL'}")

    else:
        raise ValueError(f"Unknown level: {level}")

    return ConsistencyResult(
        level=level.value,
        passed=passed,
        details=details,
        errors=errors,
    )


def check_all(intent: Intent) -> dict[str, ConsistencyResult]:
    """Check all three consistency levels."""
    results = {}
    for level in ConsistencyLevel:
        results[level.value] = check_consistency(intent, level)
    return results


def encode_to_z3(intent: Intent) -> str:
    """Encode intent as Z3 SMT-LIB constraints (stub)."""
    lines = [";; IAF Intent → Z3 encoding", f";; Label: {intent.label}"]
    for atom in intent.P:
        lines.append(f";; P: {atom}")
    for atom in intent.N:
        lines.append(f";; N: (not {atom})")
    for atom in intent.A:
        lines.append(f";; A: (free {atom})")
    return "\n".join(lines)
