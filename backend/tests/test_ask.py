"""/ask safety logic, with no real LLM calls and no network: question filters, citation checking,
and the Gemini backup-key / timeout-budget rules."""
import httpx
import pytest
from google.genai import errors

import ask

# --- Question filters ---------------------------------------------------------------------


def test_late_night_online_shopping_filters():
    f = ask.detect_filters("Show me suspicious late-night online shopping purchases")
    assert f["time_of_day"] == "late night (22:00-04:00)"
    assert f["hours"] == [0, 1, 2, 3, 22, 23]
    assert f["categories"] == ["shopping_net"]  # not also in-store shopping


def test_plain_shopping_means_both_shopping_categories():
    assert ask.detect_categories("any big shopping purchases?") == ["shopping_net", "shopping_pos"]


def test_far_from_home_is_not_a_category():
    assert ask.detect_categories("payments far from home") is None


def test_risk_level_needs_exactly_one_level():
    assert ask.detect_risk_level("Why were the high-risk transactions flagged?") == "high"
    assert ask.detect_risk_level("compare high risk and low risk") is None


def test_two_times_of_day_apply_no_time_filter():
    assert ask.detect_time_of_day("late night and evening spending") == (None, None)


# --- Citation checking --------------------------------------------------------------------

EXAMPLES = [{"id": 660, "trans_num": "abc", "summary": "A $996 purchase"}]


def test_made_up_citations_are_removed_and_real_ones_kept():
    answer, citations, invalid = ask.check_citations("Flagged: [#660] and [#99999].", EXAMPLES)
    assert "[#660]" in answer and "[#99999]" not in answer
    assert [c["id"] for c in citations] == [660]
    assert invalid == [99999]


def test_repeated_citation_is_listed_once():
    _, citations, invalid = ask.check_citations("[#660] again [#660]", EXAMPLES)
    assert [c["id"] for c in citations] == [660] and invalid == []


# --- Gemini backup keys and time budget ---------------------------------------------------


def api_error(code, message=None):
    return errors.APIError(code, {"error": {"code": code, "message": message or f"fake {code}"}})


@pytest.fixture
def gemini(monkeypatch):
    """Fake Gemini: `gemini(keys, behaviour)` sets which key slots exist and what each returns
    (text, or an exception to raise). Returns the list of (slot, timeout_ms) calls made."""
    calls = []
    monkeypatch.setattr(ask, "_rate_limited_until", {})
    monkeypatch.setattr(ask, "GEMINI_THINKING", "low")

    def setup(keys, behaviour):
        for slot in range(1, ask.MAX_GEMINI_KEYS + 1):
            monkeypatch.delenv(ask.gemini_key_name(slot), raising=False)
        for slot in keys:
            monkeypatch.setenv(ask.gemini_key_name(slot), f"fake-key-{slot}")

        class Models:
            def __init__(self, slot):
                self.slot = slot

            def generate_content(self, model, contents, config):
                calls.append((self.slot, config.http_options.timeout))
                assert str(config.thinking_config.thinking_level).endswith("LOW")
                outcome = behaviour[self.slot]
                if isinstance(outcome, Exception):
                    raise outcome
                return type("Response", (), {"text": outcome})()

        monkeypatch.setattr(ask, "gemini_client", lambda slot, key: type("Client", (), {"models": Models(slot)})())
        return calls

    return setup


def test_first_key_answers(gemini):
    calls = gemini([1, 2], {1: "from 1", 2: "from 2"})
    assert ask.call_gemini("q")[0] == "from 1"
    assert calls == [(1, 40_000)]


def test_rate_limited_key_falls_back_to_next(gemini):
    calls = gemini([1, 2, 3], {1: api_error(429), 2: api_error(429), 3: "from 3"})
    assert ask.call_gemini("q")[0] == "from 3"
    assert [slot for slot, _ in calls] == [1, 2, 3]


def test_gaps_in_key_numbers_are_fine(gemini):
    gemini([1, 3], {1: api_error(429), 3: "from 3"})
    assert ask.call_gemini("q")[0] == "from 3"


def test_all_keys_rate_limited(gemini):
    gemini([1, 2], {1: api_error(429), 2: api_error(429)})
    with pytest.raises(ask.LLMRateLimited):
        ask.call_gemini("q")


@pytest.mark.parametrize("failure, message", [
    (api_error(504), "overloaded"),
    (api_error(503), "overloaded"),
    (httpx.ReadTimeout("slow"), "didn't respond"),
])
def test_overload_and_timeout_do_not_switch_keys(gemini, failure, message):
    # Another key would hit the same overloaded servers, so don't waste the time budget.
    calls = gemini([1, 2], {1: failure, 2: "from 2"})
    with pytest.raises(ask.LLMUnavailable, match=message):
        ask.call_gemini("q")
    assert [slot for slot, _ in calls] == [1]


def test_invalid_backup_key_is_named(gemini):
    gemini([1, 2], {1: api_error(429), 2: api_error(400, "API key not valid")})
    with pytest.raises(ask.LLMNotConfigured, match="GEMINI_API_KEY_2 is invalid"):
        ask.call_gemini("q")


def test_no_keys_configured(gemini):
    gemini([], {})
    with pytest.raises(ask.LLMNotConfigured, match="set GEMINI_API_KEY"):
        ask.call_gemini("q")


def test_rate_limited_key_is_skipped_on_the_next_question(gemini):
    calls = gemini([1, 2], {1: api_error(429), 2: "from 2"})
    ask.call_gemini("q")
    calls.clear()
    assert ask.call_gemini("q")[0] == "from 2"
    assert calls == [(2, 40_000)]


def test_no_backup_when_the_budget_is_nearly_spent(gemini, monkeypatch):
    calls = gemini([1, 2], {1: api_error(429), 2: "from 2"})
    start = 1000.0
    ticks = iter([start, start, start + 40, start + 40])  # key 1 took 40 of the 50 seconds
    monkeypatch.setattr(ask.time, "monotonic", lambda: next(ticks, start + 40))
    with pytest.raises(ask.LLMRateLimited):
        ask.call_gemini("q")
    assert [slot for slot, _ in calls] == [1]


def test_invalid_thinking_level_is_a_config_error(gemini, monkeypatch):
    gemini([1], {1: "x"})
    monkeypatch.setattr(ask, "GEMINI_THINKING", "turbo")
    with pytest.raises(ask.LLMNotConfigured, match="GEMINI_THINKING"):
        ask.call_gemini("q")
