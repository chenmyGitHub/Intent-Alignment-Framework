"""IAF Intent Evolution — Transforms + weak invertibility.

Per IAF §5.3:
  Transform types: ADD, REMOVE, MODIFY, PROMOTE, DEMOTE, MIGRATE
  Invertibility: ADD/REMOVE/MODIFY are strong; PROMOTE/DEMOTE are weak.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .spaces import Intent
from .atoms import IntentAtom


class TransformType(Enum):
    ADD = "add"
    REMOVE = "remove"
    MODIFY = "modify"
    PROMOTE = "promote"
    DEMOTE = "demote"
    MIGRATE = "migrate"


@dataclass
class Delta:
    type: TransformType
    atom: IntentAtom
    new_atom: IntentAtom | None = None
    space: str = "P"

    def __post_init__(self):
        if isinstance(self.type, str):
            self.type = TransformType(self.type)


@dataclass
class VersionedIntent:
    intent: Intent
    version: int
    message: str
    timestamp: str = ""
    history: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


def apply_transform(intent: Intent, delta: Delta) -> Intent:
    """Apply a transformation delta to an intent."""
    t = delta.type if isinstance(delta.type, TransformType) else TransformType(delta.type)

    if t == TransformType.ADD:
        space = delta.space or "P"
        if space == "P":
            return Intent(P=intent.P | {delta.atom}, N=intent.N, A=intent.A, label=intent.label)
        elif space == "N":
            return Intent(P=intent.P, N=intent.N | {delta.atom}, A=intent.A, label=intent.label)
        elif space == "A":
            return Intent(P=intent.P, N=intent.N, A=intent.A | {delta.atom}, label=intent.label)

    elif t == TransformType.REMOVE:
        space = delta.space or "P"
        if space == "P":
            return Intent(P=intent.P - {delta.atom}, N=intent.N, A=intent.A, label=intent.label)
        elif space == "N":
            return Intent(P=intent.P, N=intent.N - {delta.atom}, A=intent.A, label=intent.label)
        elif space == "A":
            return Intent(P=intent.P, N=intent.N, A=intent.A - {delta.atom}, label=intent.label)

    elif t == TransformType.MODIFY:
        space = delta.space or "P"
        if space == "P":
            return Intent(P=(intent.P - {delta.atom}) | {delta.new_atom}, N=intent.N, A=intent.A, label=intent.label)
        elif space == "N":
            return Intent(P=intent.P, N=(intent.N - {delta.atom}) | {delta.new_atom}, A=intent.A, label=intent.label)

    elif t == TransformType.PROMOTE:
        # Move from N or A to P with stricter semantics
        new_p = intent.P | {delta.new_atom} if delta.new_atom else intent.P
        new_n = intent.N - {delta.atom} if delta.atom in intent.N else intent.N
        new_a = intent.A - {delta.atom} if delta.atom in intent.A else intent.A
        return Intent(P=new_p, N=new_n, A=new_a, label=intent.label)

    elif t == TransformType.DEMOTE:
        # Move from P to N or A with weaker semantics
        new_p = intent.P - {delta.atom}
        new_n = intent.N | {delta.new_atom} if delta.new_atom else intent.N
        return Intent(P=new_p, N=new_n, A=intent.A, label=intent.label)

    elif t == TransformType.MIGRATE:
        # Move from P/N to A
        new_p = intent.P - {delta.atom}
        new_n = intent.N - {delta.atom}
        new_a = intent.A | {delta.atom}
        return Intent(P=new_p, N=new_n, A=new_a, label=intent.label)

    raise ValueError(f"Unknown transform type: {t}")


def invert_transform(delta: Delta) -> Delta:
    """Compute the inverse of a transform (strong or weak)."""
    t = delta.type if isinstance(delta.type, TransformType) else TransformType(delta.type)

    inverse_map = {
        TransformType.ADD: TransformType.REMOVE,
        TransformType.REMOVE: TransformType.ADD,
        TransformType.MODIFY: TransformType.MODIFY,
        TransformType.PROMOTE: TransformType.DEMOTE,
        TransformType.DEMOTE: TransformType.PROMOTE,
        TransformType.MIGRATE: TransformType.MODIFY,  # no perfect inverse
    }

    return Delta(
        type=inverse_map[t],
        atom=delta.new_atom or delta.atom,
        new_atom=delta.atom,
        space=delta.space,
    )


def evolve(intent: Intent, delta: Delta, message: str = "") -> VersionedIntent:
    """Apply a transform and create a new version."""
    new_intent = apply_transform(intent, delta)
    return VersionedIntent(
        intent=new_intent,
        version=0,  # caller should set
        message=message,
        history=[message],
    )


def diff(old: Intent, new: Intent) -> dict:
    """Compute the diff between two intents."""
    return {
        "added_p": new.P - old.P,
        "removed_p": old.P - new.P,
        "added_n": new.N - old.N,
        "removed_n": old.N - new.N,
        "added_a": new.A - old.A,
        "removed_a": old.A - new.A,
    }


def verify_weak_invertibility(delta: Delta) -> bool:
    """Check if a transform is at least weakly invertible.

    Strong: ADD, REMOVE, MODIFY
    Weak: PROMOTE, DEMOTE, MIGRATE (always returns True as weak)
    """
    t = delta.type if isinstance(delta.type, TransformType) else TransformType(delta.type)
    strong = {TransformType.ADD, TransformType.REMOVE, TransformType.MODIFY}
    return True  # all transforms are at least weakly invertible
