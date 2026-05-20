"""Tests for iaf_core.operators — Composition operators.

TDD: Define expected API first, then implement.
"""

import pytest
from iaf_core.atoms import Exists, Avoid, Autonomy, Reachable
from iaf_core.spaces import Intent
from iaf_core.operators import CombineOp, combine, detect_conflict, verify_properties


# ─── CombineOp Enum ───────────────────────────────────────────

class TestCombineOp:
    def test_has_parallel(self):
        assert CombineOp.PARALLEL.value == 'parallel'

    def test_has_sequential(self):
        assert CombineOp.SEQUENTIAL.value == 'sequential'

    def test_has_priority(self):
        assert CombineOp.PRIORITY.value == 'priority'

    def test_has_exclusive(self):
        assert CombineOp.EXCLUSIVE.value == 'exclusive'


# ─── combine() ─────────────────────────────────────────────────

class TestCombine:
    @pytest.fixture
    def auth(self):
        return Intent(
            P={Exists(x='user'), Exists(x='session')},
            N={Avoid(x='insecure')},
            A={Autonomy(x='method')},
            label='Auth',
        )

    @pytest.fixture
    def crud(self):
        return Intent(
            P={Exists(x='entity'), Reachable(a='list', b='detail')},
            N=set(),
            A={Autonomy(x='ui')},
            label='CRUD',
        )

    def test_parallel_combines_all(self, auth, crud):
        result = combine(auth, crud, CombineOp.PARALLEL)
        assert isinstance(result, Intent)
        # Parallel = union of all
        assert Exists(x='user') in result.P
        assert Exists(x='entity') in result.P
        assert Avoid(x='insecure') in result.N
        assert Autonomy(x='method') in result.A or Autonomy(x='ui') in result.A

    def test_sequential_shrinks_autonomy(self, auth, crud):
        result = combine(auth, crud, CombineOp.SEQUENTIAL)
        assert isinstance(result, Intent)
        # Sequential: autonomy intersection
        assert len(result.A) <= len(auth.A)
        assert len(result.A) <= len(crud.A)

    def test_priority_keeps_first_constraints(self, auth, crud):
        result = combine(auth, crud, CombineOp.PRIORITY)
        assert isinstance(result, Intent)
        assert Avoid(x='insecure') in result.N  # auth's N preserved

    def test_result_has_label(self, auth, crud):
        result = combine(auth, crud, CombineOp.PARALLEL)
        assert result.label is not None


# ─── detect_conflict() ────────────────────────────────────────

class TestDetectConflict:
    def test_no_conflict(self):
        a = Intent(P={Exists(x='user')}, N=set(), A=set())
        b = Intent(P={Exists(x='order')}, N=set(), A=set())
        conflicts = detect_conflict(a, b)
        assert len(conflicts) == 0

    def test_p_n_conflict(self):
        atom = Exists(x='user')
        a = Intent(P={atom}, N=set(), A=set())
        b = Intent(P=set(), N={atom}, A=set())
        conflicts = detect_conflict(a, b)
        assert len(conflicts) > 0

    def test_conflict_detail(self):
        atom = Avoid(x='complex')
        a = Intent(P=set(), N={atom}, A=set())
        b = Intent(P=set(), N={atom}, A=set())
        conflicts = detect_conflict(a, b)
        assert isinstance(conflicts, list)


# ─── verify_properties() ──────────────────────────────────────

class TestVerifyProperties:
    def test_returns_dict(self):
        props = verify_properties()
        assert isinstance(props, dict)

    def test_commutativity(self):
        props = verify_properties()
        assert 'commutativity' in props

    def test_associativity(self):
        props = verify_properties()
        assert 'associativity' in props

    def test_idempotency(self):
        props = verify_properties()
        assert 'idempotency' in props
