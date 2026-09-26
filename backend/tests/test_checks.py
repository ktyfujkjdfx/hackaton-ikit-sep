"""13 эталонных проверок раздела 8. Таблица — та же, что у /api/checks."""
import pytest

from app.engine import run_checks
from app.engine.checks import CHECKS, run_check


def test_there_are_13_checks():
    assert [c.id for c in CHECKS] == list(range(1, 14))


@pytest.mark.parametrize("check", CHECKS, ids=[f"{c.id}-{c.title}" for c in CHECKS])
def test_reference_check(check):
    item = run_check(check)
    assert item.ok, f"{check.title}: ждали «{check.expected}», получили «{item.got}»"


def test_run_checks_13_of_13():
    result = run_checks()
    assert (result.passed, result.total) == (13, 13)
