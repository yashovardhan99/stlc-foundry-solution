"""Unit tests for the static pytest/Playwright validator."""

import json

import tools

_validate = tools._validate_pytest_script


def _run(content: str) -> dict:
    return json.loads(_validate(content))


def test_valid_script_passes():
    result = _run("def test_ok():\n    assert True\n")
    assert result["valid"] is True
    assert result["errors"] == []


def test_syntax_error_is_reported():
    result = _run("def test_bad(:\n    pass\n")
    assert result["valid"] is False
    assert any("Syntax error" in e for e in result["errors"])


def test_missing_test_function_is_reported():
    result = _run("def helper():\n    return 1\n")
    assert result["valid"] is False
    assert any("test_" in e for e in result["errors"])


def test_to_have_url_lambda_is_rejected():
    content = "def test_url(page):\n    expect(page).to_have_url(lambda u: True)\n"
    result = _run(content)
    assert result["valid"] is False
    assert any("to_have_url" in e for e in result["errors"])


def test_to_have_utl_typo_is_detected():
    result = _run("def test_typo(page):\n    expect(page).to_have_utl('x')\n")
    assert result["valid"] is False
    assert any("to_have_utl" in e for e in result["errors"])


def test_time_sleep_emits_warning_but_stays_valid():
    content = "import time\n\n\ndef test_sleep():\n    time.sleep(1)\n    assert True\n"
    result = _run(content)
    assert result["valid"] is True
    assert any("time.sleep" in w for w in result["warnings"])
