"""Tests for iaf_core.spaces — Intent(P, N, A) triple.

TDD: Define expected API first, then implement.
"""

import pytest
from iaf_core.atoms import Exists, Assoc, Reachable, Avoid, Autonomy, TraceState
from iaf_core.spaces import Intent


# ─── Basic Construction ────────────────────────────────────────

class TestIntentConstruction:
    def test_empty(self):
        i = Intent(P=set(), N=set(), A=set())
        assert len(i.P) == 0
        assert len(i.N) == 0
        assert len(i.A) == 0

    def test_auto_convert_sets(self):
        i = Intent(P={Exists(x='u')}, N={Avoid(x='c')}, A={Autonomy(x='l')})
        assert isinstance(i.P, frozenset)
        assert isinstance(i.N, frozenset)
        assert isinstance(i.A, frozenset)

    def test_with_label(self):
        i = Intent(P=set(), N=set(), A=set(), label='test')
        assert i.label == 'test'

    def test_hashable(self):
        i = Intent(P=set(), N=set(), A=set())
        assert hash(i) is not None


# ─── Well-formedness ───────────────────────────────────────────

class TestWellFormed:
    def test_valid_intent(self):
        i = Intent(
            P={Exists(x='user')},
            N={Avoid(x='complex')},
            A={Autonomy(x='layout')},
        )
        ok, errors = i.well_formed()
        assert ok is True
        assert errors == []

    def test_p_n_overlap(self):
        a = Exists(x='user')
        i = Intent(P={a}, N={a}, A=set())
        ok, errors = i.well_formed()
        assert ok is False
        assert len(errors) > 0

    def test_empty_intent_is_valid(self):
        i = Intent.empty()
        ok, errors = i.well_formed()
        assert ok is True


# ─── Combine ───────────────────────────────────────────────────

class TestCombine:
    @pytest.fixture
    def intent_a(self):
        return Intent(P={Exists(x='user')}, N=set(), A={Autonomy(x='layout')})

    @pytest.fixture
    def intent_b(self):
        return Intent(P={Exists(x='order')}, N={Avoid(x='slow')}, A=set())

    def test_parallel_union(self, intent_a, intent_b):
        combined = intent_a.combine(intent_b, op='parallel')
        assert Exists(x='user') in combined.P
        assert Exists(x='order') in combined.P
        assert Avoid(x='slow') in combined.N

    def test_priority_keeps_first(self, intent_a, intent_b):
        combined = intent_a.combine(intent_b, op='priority')
        assert Exists(x='user') in combined.P

    def test_merge(self, intent_a, intent_b):
        combined = intent_a.combine(intent_b, op='merge')
        assert isinstance(combined, Intent)


# ─── Satisfaction ──────────────────────────────────────────────

class TestSatisfaction:
    def test_satisfaction_score(self):
        i = Intent(P={Exists(x='user')}, N=set(), A=set())
        trace = [TraceState(entities={'user': frozenset()})]
        score = i.satisfaction(trace)
        assert 0.0 <= score <= 1.0

    def test_minimax_scoring(self):
        """Hard constraint failure → total score = 0."""
        i = Intent(P={Exists(x='user')}, N=set(), A=set())
        trace = [TraceState(entities={'product': frozenset()})]  # user missing
        score = i.satisfaction(trace)
        assert score == 0.0


# ─── Helper Methods ────────────────────────────────────────────

class TestHelpers:
    def test_is_empty(self):
        assert Intent.empty().is_empty() is True
        assert Intent(P={Exists(x='u')}, N=set(), A=set()).is_empty() is False

    def test_size(self):
        i = Intent(P={Exists(x='a'), Exists(x='b')}, N={Avoid(x='c')}, A=set())
        assert i.size() == (2, 1, 0)

    def test_add_p(self):
        i = Intent.empty().add_p(Exists(x='user'))
        assert Exists(x='user') in i.P

    def test_remove_p(self):
        i = Intent(P={Exists(x='user')}, N=set(), A=set())
        i2 = i.remove_p(Exists(x='user'))
        assert Exists(x='user') not in i2.P

    def test_repr(self):
        i = Intent(P={Exists(x='user')}, N=set(), A=set(), label='test')
        s = repr(i)
        assert 'test' in s or 'Intent' in s
