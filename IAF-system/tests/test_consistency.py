"""Tests for iaf_core.consistency — Three-step consistency checking.

TDD: Define expected API first, then implement.
"""

import pytest
from iaf_core.atoms import Exists, Avoid, Always, Autonomy
from iaf_core.spaces import Intent
from iaf_core.consistency import ConsistencyLevel, check_consistency, check_all


# ─── ConsistencyLevel Enum ─────────────────────────────────────

class TestConsistencyLevel:
    def test_three_levels(self):
        assert len(ConsistencyLevel) == 3

    def test_syntactic(self):
        assert ConsistencyLevel.SYNTACTIC.value == 'syntactic'

    def test_semantic(self):
        assert ConsistencyLevel.SEMANTIC.value == 'semantic'

    def test_autonomy(self):
        assert ConsistencyLevel.AUTONOMY.value == 'autonomy'


# ─── check_consistency() ──────────────────────────────────────

class TestCheckConsistency:
    def test_syntactic_passes(self):
        i = Intent(P={Exists(x='user')}, N={Avoid(x='complex')}, A=set())
        result = check_consistency(i, ConsistencyLevel.SYNTACTIC)
        assert result.passed is True

    def test_syntactic_fails_on_overlap(self):
        a = Exists(x='user')
        i = Intent(P={a}, N={a}, A=set())
        result = check_consistency(i, ConsistencyLevel.SYNTACTIC)
        assert result.passed is False

    def test_semantic_passes(self):
        i = Intent(P={Exists(x='user')}, N={Avoid(x='complex')}, A=set())
        result = check_consistency(i, ConsistencyLevel.SEMANTIC)
        assert result.passed is True

    def test_autonomy_passes(self):
        i = Intent(
            P={Exists(x='user')},
            N={Avoid(x='complex')},
            A={Autonomy(x='layout')},
        )
        result = check_consistency(i, ConsistencyLevel.AUTONOMY)
        assert result.passed is True


# ─── check_all() ──────────────────────────────────────────────

class TestCheckAll:
    def test_returns_dict(self):
        i = Intent(P={Exists(x='user')}, N=set(), A=set())
        results = check_all(i)
        assert isinstance(results, dict)

    def test_three_levels(self):
        i = Intent(P={Exists(x='user')}, N=set(), A=set())
        results = check_all(i)
        assert 'syntactic' in results
        assert 'semantic' in results
        assert 'autonomy' in results
