"""Tests for iaf_core.atoms — 27 intent atoms with formal semantics.

TDD: Define expected API first, then implement.
"""

import pytest
from iaf_core.atoms import (
    AtomCategory, AtomKind, DepType,
    TraceState, IntentAtom,
    # Existence (4)
    Exists, ExistsUnique, NonEmpty, Empty,
    # Relational (5)
    Assoc, Subset, Disjoint, Dep, Precedes,
    # Behavioral (4)
    Reachable, Reversible, Idempotent, Atomic,
    # Constraint (5)
    Always, Eventually, ForAll, ForSome, Bound,
    # Preference (5)
    Prefer, PreferEq, Avoid, Weight, Soft,
    # Uncertainty (4)
    Autonomy, Confirm, Fuzzy, Probabilistic,
    # Registry
    ATOM_REGISTRY, CATEGORY_KINDS,
    # Constructors
    exists, exists_unique, non_empty, empty,
    assoc, dep, reachable, always, eventually,
    prefer, avoid, autonomy, prefer_eq,
)


# ─── AtomCategory ───────────────────────────────────────────────

class TestAtomCategory:
    def test_six_categories(self):
        assert len(AtomCategory) == 6

    def test_category_values(self):
        names = {c.name for c in AtomCategory}
        expected = {'EXISTENCE', 'RELATIONAL', 'BEHAVIORAL', 'CONSTRAINT', 'PREFERENCE', 'UNCERTAINTY'}
        assert names == expected


# ─── AtomKind ───────────────────────────────────────────────────

class TestAtomKind:
    def test_twenty_seven_kinds(self):
        assert len(AtomKind) == 27

    def test_registry_complete(self):
        assert len(ATOM_REGISTRY) == 27


# ─── TraceState ─────────────────────────────────────────────────

class TestTraceState:
    def test_create(self):
        s = TraceState(entities={'user', 'order'}, predicates={'active': True})
        assert 'user' in s.entities
        assert s.predicates['active'] is True

    def test_hashable(self):
        s = TraceState(entities={'a': frozenset()}, predicates={'b': True})
        assert hash(s) is not None  # must be hashable for use in sets

    def test_default_values(self):
        s = TraceState()
        assert s.entities == {}
        assert s.predicates == {}
        assert s.transitions == frozenset()
        assert s.assignments == {}


# ─── Base IntentAtom ────────────────────────────────────────────

class TestIntentAtomBase:
    def test_is_abc(self):
        with pytest.raises(TypeError):
            IntentAtom()  # cannot instantiate abstract

    def test_atom_is_hashable(self):
        a = Exists(x='user')
        assert hash(a) is not None

    def test_atom_has_formal_semantics(self):
        a = Exists(x='user')
        sem = a.formal_semantics  # property, not method
        assert isinstance(sem, str)
        assert len(sem) > 0

    def test_atom_satisfies_returns_bool(self):
        a = Exists(x='user')
        trace = [TraceState(entities={'user': frozenset()})]
        result = a.satisfies(trace)
        assert isinstance(result, bool)


# ─── Existence Atoms ────────────────────────────────────────────

class TestExistenceAtoms:
    def test_exists(self):
        a = Exists(x='user')
        assert a.kind == AtomKind.EXISTS
        assert a.category == AtomCategory.EXISTENCE
        assert a.satisfies([TraceState(entities={'user': frozenset()})]) is True
        assert a.satisfies([TraceState(entities={'order': frozenset()})]) is False

    def test_exists_unique(self):
        a = ExistsUnique(x='user')
        assert a.category == AtomCategory.EXISTENCE

    def test_non_empty(self):
        a = NonEmpty(S='products')
        assert a.category == AtomCategory.EXISTENCE

    def test_empty(self):
        a = Empty(S='temp')
        assert a.category == AtomCategory.EXISTENCE


# ─── Relational Atoms ───────────────────────────────────────────

class TestRelationalAtoms:
    def test_assoc(self):
        a = Assoc(x='user', y='order')
        assert a.category == AtomCategory.RELATIONAL

    def test_subset(self):
        a = Subset(x='admins', y='users')
        assert a.category == AtomCategory.RELATIONAL

    def test_disjoint(self):
        a = Disjoint(x='admins', y='guests')
        assert a.category == AtomCategory.RELATIONAL

    def test_dep(self):
        a = Dep(x='order', y='payment', k=DepType.DATA)
        assert a.category == AtomCategory.RELATIONAL
        assert a.k == DepType.DATA  # k parameter

    def test_precedes(self):
        a = Precedes(x='login', y='checkout')
        assert a.category == AtomCategory.RELATIONAL


# ─── Behavioral Atoms ──────────────────────────────────────────

class TestBehavioralAtoms:
    def test_reachable(self):
        a = Reachable(a='home', b='browse')
        assert a.category == AtomCategory.BEHAVIORAL

    def test_reversible(self):
        a = Reversible(a='checkout', b='cart')
        assert a.category == AtomCategory.BEHAVIORAL

    def test_idempotent(self):
        a = Idempotent(f='read')
        assert a.category == AtomCategory.BEHAVIORAL

    def test_atomic(self):
        a = Atomic(f='payment')
        assert a.category == AtomCategory.BEHAVIORAL


# ─── Constraint Atoms ──────────────────────────────────────────

class TestConstraintAtoms:
    def test_always(self):
        a = Always(phi='inventory >= 0')
        assert a.category == AtomCategory.CONSTRAINT

    def test_eventually(self):
        a = Eventually(phi='delivery_complete')
        assert a.category == AtomCategory.CONSTRAINT

    def test_forall(self):
        a = ForAll(x='p', S='products', C='has_image(p)')
        assert a.category == AtomCategory.CONSTRAINT

    def test_forsome(self):
        a = ForSome(x='p', S='plans', C='is_free(p)')
        assert a.category == AtomCategory.CONSTRAINT

    def test_bound(self):
        a = Bound(x='fee', lo=0, hi=0.03)
        assert a.category == AtomCategory.CONSTRAINT


# ─── Preference Atoms ──────────────────────────────────────────

class TestPreferenceAtoms:
    def test_prefer(self):
        a = Prefer(a='simple', b='complex')
        assert a.category == AtomCategory.PREFERENCE

    def test_prefer_eq(self):
        a = prefer_eq(a='fast', b='quick')
        assert a.category == AtomCategory.PREFERENCE

    def test_avoid(self):
        a = Avoid(x='complex')
        assert a.category == AtomCategory.PREFERENCE

    def test_weight(self):
        a = Weight(x='speed', alpha=0.8)
        assert a.category == AtomCategory.PREFERENCE

    def test_soft(self):
        a = Soft(phi='nice_to_have')
        assert a.category == AtomCategory.PREFERENCE


# ─── Uncertainty Atoms ─────────────────────────────────────────

class TestUncertaintyAtoms:
    def test_autonomy(self):
        a = Autonomy(x='layout')
        assert a.category == AtomCategory.UNCERTAINTY

    def test_confirm(self):
        a = Confirm(x='publish')
        assert a.category == AtomCategory.UNCERTAINTY

    def test_fuzzy(self):
        a = Fuzzy(x='price', epsilon=5)
        assert a.category == AtomCategory.UNCERTAINTY

    def test_probabilistic(self):
        a = Probabilistic(x='success', p=0.95)
        assert a.category == AtomCategory.UNCERTAINTY


# ─── Convenience Constructors ──────────────────────────────────

class TestConstructors:
    def test_exists_constructor(self):
        a = exists('user')
        assert isinstance(a, Exists)

    def test_assoc_constructor(self):
        a = assoc('user', 'order')
        assert isinstance(a, Assoc)

    def test_reachable_constructor(self):
        a = reachable('home', 'browse')
        assert isinstance(a, Reachable)

    def test_always_constructor(self):
        a = always('x >= 0')
        assert isinstance(a, Always)

    def test_prefer_constructor(self):
        a = prefer('a', 'b')
        assert isinstance(a, Prefer)

    def test_avoid_constructor(self):
        a = avoid('complex')
        assert isinstance(a, Avoid)

    def test_autonomy_constructor(self):
        a = autonomy('layout')
        assert isinstance(a, Autonomy)


# ─── Category-Kinds Mapping ────────────────────────────────────

class TestCategoryKinds:
    def test_existence_kinds(self):
        kinds = CATEGORY_KINDS[AtomCategory.EXISTENCE]
        assert len(kinds) == 4

    def test_relational_kinds(self):
        kinds = CATEGORY_KINDS[AtomCategory.RELATIONAL]
        assert len(kinds) == 5

    def test_behavioral_kinds(self):
        kinds = CATEGORY_KINDS[AtomCategory.BEHAVIORAL]
        assert len(kinds) == 4

    def test_constraint_kinds(self):
        kinds = CATEGORY_KINDS[AtomCategory.CONSTRAINT]
        assert len(kinds) == 5

    def test_preference_kinds(self):
        kinds = CATEGORY_KINDS[AtomCategory.PREFERENCE]
        assert len(kinds) == 5

    def test_uncertainty_kinds(self):
        kinds = CATEGORY_KINDS[AtomCategory.UNCERTAINTY]
        assert len(kinds) == 4
