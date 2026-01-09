"""Tests for adventure moment utilities."""

from src.agents.keeper import KeeperResponse
from src.engine.moments import build_moment_from_keeper, format_moments_for_context
from src.state.models import AdventureMoment


class TestFormatMomentsForContext:
    """Tests for format_moments_for_context function."""

    def test_returns_empty_string_for_empty_list(self) -> None:
        """Should return empty string when no moments provided."""
        result = format_moments_for_context([])

        assert result == ""

    def test_formats_single_moment(self) -> None:
        """Should format a single moment correctly."""
        moments = [
            AdventureMoment(
                turn=5,
                type="combat_victory",
                summary="Defeated the cave goblin",
                significance=0.8,
            )
        ]

        result = format_moments_for_context(moments)

        assert "[STORY SO FAR]" in result
        assert "Turn 5 (combat_victory): Defeated the cave goblin" in result

    def test_respects_max_count(self) -> None:
        """Should only include up to max_count moments."""
        moments = [
            AdventureMoment(
                turn=i, type="discovery", summary=f"Moment {i}", significance=0.5
            )
            for i in range(10)
        ]

        result = format_moments_for_context(moments, max_count=3)

        # Should have header + 3 moments
        lines = result.strip().split("\n")
        assert len(lines) == 4  # 1 header + 3 moments

    def test_selects_most_significant_moments(self) -> None:
        """Should select moments with highest significance."""
        moments = [
            AdventureMoment(
                turn=1, type="discovery", summary="Low significance", significance=0.3
            ),
            AdventureMoment(
                turn=2,
                type="combat_victory",
                summary="High significance",
                significance=0.9,
            ),
            AdventureMoment(
                turn=3,
                type="achievement",
                summary="Medium significance",
                significance=0.6,
            ),
        ]

        result = format_moments_for_context(moments, max_count=2)

        assert "High significance" in result
        assert "Medium significance" in result
        assert "Low significance" not in result

    def test_sorts_selected_moments_chronologically(self) -> None:
        """Should sort selected moments by turn number."""
        moments = [
            AdventureMoment(
                turn=10, type="combat_victory", summary="Late battle", significance=0.9
            ),
            AdventureMoment(
                turn=3, type="discovery", summary="Early discovery", significance=0.8
            ),
        ]

        result = format_moments_for_context(moments, max_count=5)

        # Early discovery (turn 3) should appear before Late battle (turn 10)
        early_pos = result.find("Early discovery")
        late_pos = result.find("Late battle")
        assert early_pos < late_pos

    def test_default_max_count_is_five(self) -> None:
        """Should default to including 5 moments."""
        moments = [
            AdventureMoment(
                turn=i, type="discovery", summary=f"Moment {i}", significance=0.5
            )
            for i in range(10)
        ]

        result = format_moments_for_context(moments)

        # Should have header + 5 moments
        lines = result.strip().split("\n")
        assert len(lines) == 6  # 1 header + 5 moments


class TestBuildMomentFromKeeper:
    """Tests for build_moment_from_keeper function."""

    def test_creates_moment_with_all_fields(self) -> None:
        """Should create AdventureMoment from complete KeeperResponse."""
        keeper_response = KeeperResponse(
            resolution="14. Hits. 6 damage.",
            moment_type="combat_victory",
            moment_summary="Defeated the goblin chief",
            moment_significance=0.85,
        )

        result = build_moment_from_keeper(keeper_response, turn=12)

        assert result is not None
        assert result.turn == 12
        assert result.type == "combat_victory"
        assert result.summary == "Defeated the goblin chief"
        assert result.significance == 0.85

    def test_returns_none_when_no_moment_type(self) -> None:
        """Should return None when moment_type is None."""
        keeper_response = KeeperResponse(
            resolution="DC 12. Rolled 15. Succeeds.",
            moment_type=None,
            moment_summary="Some summary",
            moment_significance=0.5,
        )

        result = build_moment_from_keeper(keeper_response, turn=5)

        assert result is None

    def test_returns_none_when_no_moment_summary(self) -> None:
        """Should return None when moment_summary is None."""
        keeper_response = KeeperResponse(
            resolution="DC 12. Rolled 15. Succeeds.",
            moment_type="discovery",
            moment_summary=None,
            moment_significance=0.7,
        )

        result = build_moment_from_keeper(keeper_response, turn=5)

        assert result is None

    def test_returns_none_for_routine_action(self) -> None:
        """Should return None for routine actions without moment data."""
        keeper_response = KeeperResponse(
            resolution="DC 10. Rolled 12. Succeeds.",
            moment_type=None,
            moment_summary=None,
            moment_significance=0.5,
        )

        result = build_moment_from_keeper(keeper_response, turn=3)

        assert result is None

    def test_uses_default_significance_when_not_specified(self) -> None:
        """Should use the significance from keeper response."""
        keeper_response = KeeperResponse(
            resolution="Natural 20!",
            moment_type="critical_success",
            moment_summary="Perfect strike",
            # moment_significance defaults to 0.5
        )

        result = build_moment_from_keeper(keeper_response, turn=7)

        assert result is not None
        assert result.significance == 0.5  # Default value
