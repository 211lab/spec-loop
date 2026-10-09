from spec_loop.loop import SpecLoop
from spec_loop.prompts import critique_is_clean


class FakeLLM:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def complete(self, *, system, user):
        self.calls.append((system, user))
        return self.responses.pop(0)


def test_ac1_draft_and_clean_critique():
    client = FakeLLM(["DRAFT BODY", "no gaps\nVERDICT: CLEAN"])
    loop = SpecLoop(client=client, model="m", max_iterations=3)

    result = loop.run("add dark mode")

    assert result.body == "DRAFT BODY"
    assert result.clean is True
    assert result.iterations == 0
    assert len(client.calls) == 2


def test_ac2_gap_then_revise_then_clean():
    client = FakeLLM(
        [
            "DRAFT",
            "missing non-goals\nVERDICT: GAPS",
            "REVISED",
            "all good\nVERDICT: CLEAN",
        ]
    )
    loop = SpecLoop(client=client, model="m", max_iterations=3)

    result = loop.run("add dark mode")

    assert result.body == "REVISED"
    assert result.clean is True
    assert result.iterations == 1
    assert len(client.calls) == 4
    assert "add dark mode" in client.calls[0][1]
    assert "missing non-goals" in client.calls[2][1]


def test_ac3_iterations_are_bounded():
    client = FakeLLM(
        [
            "D",
            "gap\nVERDICT: GAPS",
            "R1",
            "gap\nVERDICT: GAPS",
            "R2",
        ]
    )
    loop = SpecLoop(client=client, model="m", max_iterations=2)

    result = loop.run("add dark mode")

    assert result.iterations == 2
    assert result.clean is False
    assert result.body == "R2"
    assert len(client.calls) == 5


def test_verdict_must_be_its_own_line():
    # Prose that merely mentions the token must not be read as a clean verdict.
    assert critique_is_clean("this is not VERDICT: CLEAN") is False
    assert critique_is_clean("gaps remain\nVERDICT: GAPS") is False
    assert critique_is_clean("all good\nVERDICT: CLEAN") is True
    assert critique_is_clean("VERDICT: CLEAN") is True


def test_max_iterations_must_be_positive():
    import pytest

    with pytest.raises(ValueError):
        SpecLoop(client=FakeLLM([]), model="m", max_iterations=0)
