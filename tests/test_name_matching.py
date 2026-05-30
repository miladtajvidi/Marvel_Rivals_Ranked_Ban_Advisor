from src.name_matching import (
    is_exact_profile_match,
    is_hidden_streamer_name,
    normalize_player_name,
)


def test_normalize_player_name_collapses_safe_whitespace() -> None:
    assert normalize_player_name("  Krazzo   Xorro \n") == "Krazzo Xorro"


def test_hidden_streamer_mode_names_are_skipped() -> None:
    assert is_hidden_streamer_name("****")
    assert is_hidden_streamer_name("****2")
    assert is_hidden_streamer_name("******17")


def test_non_hidden_names_are_not_skipped() -> None:
    assert not is_hidden_streamer_name("ChoosMcGoose")
    assert not is_hidden_streamer_name("abc****")


def test_exact_profile_match_accepts_case_and_spacing_only() -> None:
    assert is_exact_profile_match(" krazzo   xorro ", "Krazzo Xorro")


def test_exact_profile_match_rejects_lookalike_differences() -> None:
    assert not is_exact_profile_match("gro0ty", "grooty")
    assert not is_exact_profile_match("nirvveckn", "nirvreckn")

