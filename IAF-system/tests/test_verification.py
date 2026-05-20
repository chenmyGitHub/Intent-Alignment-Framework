"""Tests for iaf_core.verification — Layered verification L0–L3.

TDD: Define expected API first, then implement.
"""

import pytest
from iaf_core.atoms import Exists, Avoid, Reachable, Autonomy
from iaf_core.spaces import Intent
from iaf_core.verification import VerifyLevel, layered_verify, full_verification_report


# ─── VerifyLevel Enum ──────────────────────────────────────────

class TestVerifyLevel:
    def test_four_levels(self):
        assert len(VerifyLevel) == 4

    def test_values(self):
        assert VerifyLevel.L0.value == 'L0'
        assert VerifyLevel.L3.value == 'L3'


# ─── layered_verify() ──────────────────────────────────────────

class TestLayeredVerify:
    @pytest.fixture
    def human(self):
        return Intent(
            P={Exists(x='user'), Reachable(a='home', b='browse')},
            N={Avoid(x='complex')},
            A={Autonomy(x='layout')},
            label='Human',
        )

    @pytest.fixture
    def ai(self):
        """AI refines human intent (adds detail, same core)."""
        return Intent(
            P={
                Exists(x='user'),
                Exists(x='cart'),
                Reachable(a='home', b='browse'),
                Reachable(a='browse', b='cart'),
            },
            N={Avoid(x='complex')},
            A={Autonomy(x='layout')},
            label='AI',
        )

    def test_l0_syntax(self, human, ai):
        result = layered_verify(human, ai, level=VerifyLevel.L0)
        assert result.passed is True

    def test_l1_structure(self, human, ai):
        result = layered_verify(human, ai, level=VerifyLevel.L1)
        assert result.passed is True

    def test_l2_simulation(self, human, ai):
        result = layered_verify(human, ai, level=VerifyLevel.L2)
        assert result.passed is True

    def test_score_in_range(self, human, ai):
        result = layered_verify(human, ai, level=VerifyLevel.L2)
        assert 0.0 <= result.score <= 1.0

    def test_details_populated(self, human, ai):
        result = layered_verify(human, ai, level=VerifyLevel.L2)
        assert isinstance(result.details, list)


# ─── full_verification_report() ────────────────────────────────

class TestFullReport:
    def test_returns_string(self):
        human = Intent(P={Exists(x='u')}, N=set(), A=set(), label='H')
        ai = Intent(P={Exists(x='u'), Exists(x='o')}, N=set(), A=set(), label='A')
        report = full_verification_report(human, ai)
        assert isinstance(report, str)
        assert 'L0' in report
