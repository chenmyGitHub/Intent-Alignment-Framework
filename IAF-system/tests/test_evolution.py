"""Tests for iaf_core.evolution — Intent transforms + weak invertibility.

TDD: Define expected API first, then implement.
"""

import pytest
from iaf_core.atoms import Exists, Avoid, Always, Autonomy
from iaf_core.spaces import Intent
from iaf_core.evolution import (
    TransformType, Delta, VersionedIntent,
    apply_transform, invert_transform, evolve, diff, verify_weak_invertibility,
)


# ─── TransformType Enum ────────────────────────────────────────

class TestTransformType:
    def test_six_types(self):
        assert len(TransformType) == 6

    def test_values(self):
        assert TransformType.ADD.value == 'add'
        assert TransformType.REMOVE.value == 'remove'
        assert TransformType.MODIFY.value == 'modify'
        assert TransformType.PROMOTE.value == 'promote'
        assert TransformType.DEMOTE.value == 'demote'
        assert TransformType.MIGRATE.value == 'migrate'


# ─── Delta ─────────────────────────────────────────────────────

class TestDelta:
    def test_add_delta(self):
        d = Delta(type=TransformType.ADD, atom=Exists(x='user'), space='P')
        assert d.type == TransformType.ADD
        assert d.space == 'P'

    def test_modify_delta(self):
        d = Delta(
            type=TransformType.MODIFY,
            atom=Exists(x='old'),
            new_atom=Exists(x='new'),
            space='P',
        )
        assert d.new_atom is not None


# ─── apply_transform() ────────────────────────────────────────

class TestApplyTransform:
    def test_add(self):
        i = Intent(P={Exists(x='user')}, N=set(), A=set())
        d = Delta(type=TransformType.ADD, atom=Exists(x='order'), space='P')
        result = apply_transform(i, d)
        assert Exists(x='order') in result.P
        assert len(result.P) == 2

    def test_remove(self):
        i = Intent(P={Exists(x='user'), Exists(x='order')}, N=set(), A=set())
        d = Delta(type=TransformType.REMOVE, atom=Exists(x='order'), space='P')
        result = apply_transform(i, d)
        assert Exists(x='user') in result.P
        assert Exists(x='order') not in result.P

    def test_promote(self):
        i = Intent(P={Avoid(x='slow')}, N=set(), A=set())
        d = Delta(type=TransformType.PROMOTE, atom=Avoid(x='slow'), space='P',
                  new_atom=Always(phi='response < 2s'))
        result = apply_transform(i, d)
        assert Always(phi='response < 2s') in result.P

    def test_migrate(self):
        i = Intent(P={Exists(x='color')}, N=set(), A=set())
        d = Delta(type=TransformType.MIGRATE, atom=Exists(x='color'), space='A')
        result = apply_transform(i, d)
        assert Exists(x='color') in result.A
        assert Exists(x='color') not in result.P


# ─── weak invertibility ───────────────────────────────────────

class TestWeakInvertibility:
    def test_add_is_strongly_invertible(self):
        d = Delta(type=TransformType.ADD, atom=Exists(x='r'), space='P')
        assert verify_weak_invertibility(d) is True

    def test_promote_is_weakly_invertible(self):
        d = Delta(
            type=TransformType.PROMOTE,
            atom=Avoid(x='slow'),
            new_atom=Always(phi='response < 2s'),
            space='P',
        )
        result = verify_weak_invertibility(d)
        # Promote is weakly (not strongly) invertible
        assert result is True  # at least weakly

    def test_invert_add(self):
        d = Delta(type=TransformType.ADD, atom=Exists(x='r'), space='P')
        inv = invert_transform(d)
        assert inv.type == TransformType.REMOVE


# ─── evolve() ──────────────────────────────────────────────────

class TestEvolve:
    def test_creates_versioned(self):
        i = Intent(P={Exists(x='user')}, N=set(), A=set(), label='v0')
        d = Delta(type=TransformType.ADD, atom=Exists(x='order'), space='P')
        v = evolve(i, d, 'Added order')
        assert isinstance(v, VersionedIntent)
        assert v.version >= 0

    def test_history(self):
        i = Intent.empty()
        d = Delta(type=TransformType.ADD, atom=Exists(x='u'), space='P')
        v = evolve(i, d, 'First change')
        assert len(v.history) == 1


# ─── diff() ────────────────────────────────────────────────────

class TestDiff:
    def test_detects_additions(self):
        old = Intent(P={Exists(x='user')}, N=set(), A=set())
        new = Intent(P={Exists(x='user'), Exists(x='order')}, N=set(), A=set())
        d = diff(old, new)
        assert 'added_p' in d
        assert len(d['added_p']) == 1

    def test_detects_removals(self):
        old = Intent(P={Exists(x='user'), Exists(x='order')}, N=set(), A=set())
        new = Intent(P={Exists(x='user')}, N=set(), A=set())
        d = diff(old, new)
        assert 'removed_p' in d
