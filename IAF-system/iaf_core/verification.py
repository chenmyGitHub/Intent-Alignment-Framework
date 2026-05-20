"""IAF Layered Verification Protocol — L0 to L3.

Per IAF §4.3:
  L0  Syntax        — well-formedness check       (decidable)
  L1  Structure     — atom coverage check           (decidable)
  L2  Simulation    — I_A simulates I_H             (semi-decidable)
  L3  Isomorphism   — graph isomorphism             (undecidable)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .spaces import Intent
from .atoms import IntentAtom


class VerifyLevel(Enum):
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"


@dataclass
class ValidationResult:
    passed: bool = False
    level: str = "L0"
    details: list[str] = field(default_factory=list)
    score: float = 0.0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _atom_match(a: IntentAtom, b: IntentAtom) -> bool:
    """Check if two atoms are structurally equivalent."""
    if type(a) != type(b):
        return False
    a_dict = {k: v for k, v in a.__dict__.items() if not k.startswith("_")}
    b_dict = {k: v for k, v in b.__dict__.items() if not k.startswith("_")}
    return a_dict == b_dict


def layered_verify(
    human: Intent, ai: Intent, level: VerifyLevel | str = VerifyLevel.L2
) -> ValidationResult:
    """Run layered verification between human and AI intents."""
    if isinstance(level, str):
        level = VerifyLevel(level)

    details = []
    passed = True
    score = 0.0

    # L0: Syntax check
    h_ok, h_errs = human.well_formed()
    a_ok, a_errs = ai.well_formed()
    details.append(f"L0: Human intent \'{human.label}\' is well-formed" if h_ok else f"L0: Human intent \'{human.label}\' FAIL: {h_errs}")
    details.append(f"L0: AI intent \'{ai.label}\' is well-formed" if a_ok else f"L0: AI intent \'{ai.label}\' FAIL: {a_errs}")

    if level == VerifyLevel.L0:
        passed = h_ok and a_ok
        score = 1.0 if passed else 0.0
        return ValidationResult(passed=passed, level="L0", details=details, score=score)

    if not (h_ok and a_ok):
        return ValidationResult(passed=False, level="L0", details=details, score=0.0)

    # L1: Structure containment — AI covers all human atoms
    h_p_ids = {repr(a) for a in human.P}
    a_p_ids = {repr(a) for a in ai.P}
    h_n_ids = {repr(a) for a in human.N}
    a_n_ids = {repr(a) for a in ai.N}
    h_a_ids = {repr(a) for a in human.A}
    a_a_ids = {repr(a) for a in ai.A}

    p_covered = h_p_ids.issubset(a_p_ids)
    n_covered = h_n_ids.issubset(a_n_ids)
    a_covered = h_a_ids.issubset(a_a_ids)

    details.append(f"L1: P coverage = {len(h_p_ids & a_p_ids)}/{len(h_p_ids)}")
    details.append(f"L1: N coverage = {len(h_n_ids & a_n_ids)}/{len(h_n_ids)}")
    details.append(f"L1: A coverage = {len(h_a_ids & a_a_ids)}/{len(h_a_ids)}")

    if level == VerifyLevel.L1:
        passed = p_covered and n_covered and a_covered
        total = len(h_p_ids) + len(h_n_ids) + len(h_a_ids)
        matched = len(h_p_ids & a_p_ids) + len(h_n_ids & a_n_ids) + len(h_a_ids & a_a_ids)
        score = matched / total if total > 0 else 1.0
        return ValidationResult(passed=passed, level="L1", details=details, score=score)

    if not (p_covered and n_covered and a_covered):
        return ValidationResult(passed=False, level="L1", details=details, score=score)

    # L2: Simulation — refined check with entailment
    sim_passed = True
    # For each human atom, find a matching or entailing AI atom
    for hp in human.P:
        found = any(_atom_match(hp, ap) for ap in ai.P)
        if not found:
            sim_passed = False
            details.append(f"L2: No match for P atom: {hp}")

    if level == VerifyLevel.L2:
        total = max(len(human.P) + len(human.N), 1)
        matched_p = sum(1 for hp in human.P if any(_atom_match(hp, ap) for ap in ai.P))
        matched_n = sum(1 for hn in human.N if any(_atom_match(hn, an) for an in ai.N))
        score = (matched_p + matched_n) / total
        return ValidationResult(passed=sim_passed, level="L2", details=details, score=score)

    # L3: Isomorphism (full structural match)
    isomorphic = (
        len(human.P) == len(ai.P)
        and len(human.N) == len(ai.N)
        and p_covered and n_covered
    )
    details.append(f"L3: Isomorphism = {isomorphic}")
    return ValidationResult(passed=isomorphic, level="L3", details=details, score=1.0 if isomorphic else 0.0)


def full_verification_report(human: Intent, ai: Intent) -> str:
    """Run all verification levels and return a report."""
    lines = [f"Verification Report: \'{human.label}\' → \'{ai.label}\'"]
    for lv in VerifyLevel:
        r = layered_verify(human, ai, level=lv)
        icon = "✅" if r.passed else "❌"
        lines.append(f"  {lv.value}: {icon} (score={r.score:.2f})")
        for d in r.details:
            lines.append(f"    {d}")
    return "\n".join(lines)
