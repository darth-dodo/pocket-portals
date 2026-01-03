"""Tests for rate limiting module."""

import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, Request

from src.api.rate_limiting import (
    RateLimitBucket,
    RateLimiter,
    rate_limiter,
    require_rate_limit,
)

# ============================================================================
# RateLimitBucket Tests
# ============================================================================


class TestRateLimitBucket:
    """Tests for RateLimitBucket dataclass."""

    def test_bucket_starts_empty(self) -> None:
        """Test that a new bucket has no calls."""
        bucket = RateLimitBucket()
        assert bucket.count() == 0

    def test_add_call_increments_count(self) -> None:
        """Test that add_call increases the call count."""
        bucket = RateLimitBucket()
        bucket.add_call()
        assert bucket.count() == 1

        bucket.add_call()
        bucket.add_call()
        assert bucket.count() == 3

    def test_count_within_window(self) -> None:
        """Test that count returns calls within the time window."""
        bucket = RateLimitBucket()

        # Add 5 calls
        for _ in range(5):
            bucket.add_call()

        # All calls should be within the default 60-second window
        assert bucket.count(window_seconds=60) == 5

    def test_clean_old_calls_removes_expired(self) -> None:
        """Test that clean_old_calls removes calls outside the window."""
        bucket = RateLimitBucket()

        # Add calls with timestamps in the past
        old_time = time.time() - 120  # 2 minutes ago
        bucket.calls = [old_time, old_time + 1, old_time + 2]

        # Clean with 60-second window should remove all old calls
        bucket.clean_old_calls(window_seconds=60)
        assert len(bucket.calls) == 0

    def test_clean_old_calls_keeps_recent(self) -> None:
        """Test that clean_old_calls keeps calls within the window."""
        bucket = RateLimitBucket()

        # Add some recent calls
        bucket.add_call()
        bucket.add_call()

        # Clean should keep recent calls
        bucket.clean_old_calls(window_seconds=60)
        assert len(bucket.calls) == 2

    def test_count_cleans_and_counts(self) -> None:
        """Test that count method cleans old calls before counting."""
        bucket = RateLimitBucket()

        # Add old call (outside window)
        old_time = time.time() - 120
        bucket.calls.append(old_time)

        # Add recent calls
        bucket.add_call()
        bucket.add_call()

        # Count should only return recent calls (old one is cleaned)
        assert bucket.count(window_seconds=60) == 2

    def test_mixed_old_and_new_calls(self) -> None:
        """Test bucket with mix of old and new calls."""
        bucket = RateLimitBucket()

        # Add 3 old calls (outside 60-second window)
        old_time = time.time() - 90
        bucket.calls = [old_time, old_time + 1, old_time + 2]

        # Add 2 new calls
        bucket.add_call()
        bucket.add_call()

        # Count should only return the 2 new calls
        assert bucket.count(window_seconds=60) == 2

    def test_custom_window_seconds(self) -> None:
        """Test bucket with custom time window."""
        bucket = RateLimitBucket()

        # Add call 15 seconds ago
        bucket.calls = [time.time() - 15]

        # Add current calls
        bucket.add_call()

        # 10-second window should only include the most recent call
        assert bucket.count(window_seconds=10) == 1

        # 30-second window should include both calls
        bucket.calls = [time.time() - 15]
        bucket.add_call()
        assert bucket.count(window_seconds=30) == 2


# ============================================================================
# RateLimiter Tests
# ============================================================================


def create_mock_request(
    headers: dict[str, str] | None = None,
    query_params: dict[str, str] | None = None,
) -> MagicMock:
    """Create a mock FastAPI Request object."""
    request = MagicMock(spec=Request)
    request.headers = headers or {}
    request.query_params = query_params or {}
    return request


class TestRateLimiterSessionExtraction:
    """Tests for session_id extraction from requests."""

    def test_extracts_session_id_from_header(self) -> None:
        """Test that session_id is extracted from X-Session-ID header."""
        request = create_mock_request(headers={"X-Session-ID": "test-session-123"})

        limiter = RateLimiter()
        session_id = limiter._get_session_id(request)

        assert session_id == "test-session-123"

    def test_extracts_session_id_from_query_params(self) -> None:
        """Test that session_id is extracted from query params."""
        request = create_mock_request(query_params={"session_id": "query-session-456"})

        limiter = RateLimiter()
        session_id = limiter._get_session_id(request)

        assert session_id == "query-session-456"

    def test_header_takes_precedence_over_query(self) -> None:
        """Test that header session_id takes precedence over query param."""
        request = create_mock_request(
            headers={"X-Session-ID": "header-session"},
            query_params={"session_id": "query-session"},
        )

        limiter = RateLimiter()
        session_id = limiter._get_session_id(request)

        assert session_id == "header-session"

    def test_returns_anonymous_when_no_session_id(self) -> None:
        """Test that 'anonymous' is returned when no session_id found."""
        request = create_mock_request()

        limiter = RateLimiter()
        session_id = limiter._get_session_id(request)

        assert session_id == "anonymous"

    def test_empty_string_session_id_uses_anonymous(self) -> None:
        """Test that empty string session_id falls through to anonymous."""
        request = create_mock_request(headers={"X-Session-ID": ""})

        limiter = RateLimiter()
        session_id = limiter._get_session_id(request)

        # Empty string is falsy, so should fall through to anonymous
        assert session_id == "anonymous"


class TestRateLimiterCheckRateLimit:
    """Tests for check_rate_limit method."""

    @patch("src.api.rate_limiting.get_settings")
    def test_passes_when_under_limit(self, mock_get_settings: MagicMock) -> None:
        """Test that rate limit check passes when under the limit."""
        mock_settings = MagicMock()
        mock_settings.rate_limit_enabled = True
        mock_settings.environment = "production"
        mock_get_settings.return_value = mock_settings

        limiter = RateLimiter()
        request = create_mock_request(headers={"X-Session-ID": "test-session"})

        # Should not raise for first few calls
        for _ in range(5):
            limiter.check_rate_limit(request, limit=10)

    @patch("src.api.rate_limiting.get_settings")
    def test_raises_429_when_limit_exceeded(self, mock_get_settings: MagicMock) -> None:
        """Test that HTTPException 429 is raised when limit exceeded."""
        mock_settings = MagicMock()
        mock_settings.rate_limit_enabled = True
        mock_settings.environment = "production"
        mock_get_settings.return_value = mock_settings

        limiter = RateLimiter()
        request = create_mock_request(headers={"X-Session-ID": "test-exceed"})

        # Fill up to the limit
        for _ in range(5):
            limiter.check_rate_limit(request, limit=5)

        # Next call should raise 429
        with pytest.raises(HTTPException) as exc_info:
            limiter.check_rate_limit(request, limit=5)

        assert exc_info.value.status_code == 429
        assert exc_info.value.detail["error"] == "rate_limit_exceeded"
        assert "5 requests per minute" in exc_info.value.detail["message"]
        assert exc_info.value.detail["retry_after"] == 60
        assert exc_info.value.headers["Retry-After"] == "60"

    @patch("src.api.rate_limiting.get_settings")
    def test_disabled_rate_limiting_skips_check(
        self, mock_get_settings: MagicMock
    ) -> None:
        """Test that disabled rate limiting always passes."""
        mock_settings = MagicMock()
        mock_settings.rate_limit_enabled = False
        mock_settings.environment = "production"
        mock_get_settings.return_value = mock_settings

        limiter = RateLimiter()
        request = create_mock_request(headers={"X-Session-ID": "test-disabled"})

        # Should not raise even with many calls
        for _ in range(100):
            limiter.check_rate_limit(request, limit=5)

    @patch("src.api.rate_limiting.get_settings")
    def test_test_environment_skips_rate_limiting(
        self, mock_get_settings: MagicMock
    ) -> None:
        """Test that test environment bypasses rate limiting."""
        mock_settings = MagicMock()
        mock_settings.rate_limit_enabled = True
        mock_settings.environment = "test"
        mock_get_settings.return_value = mock_settings

        limiter = RateLimiter()
        request = create_mock_request(headers={"X-Session-ID": "test-env-skip"})

        # Should not raise even with many calls in test environment
        for _ in range(100):
            limiter.check_rate_limit(request, limit=5)

    @patch("src.api.rate_limiting.get_settings")
    def test_separate_buckets_per_session(self, mock_get_settings: MagicMock) -> None:
        """Test that different sessions have separate rate limit buckets."""
        mock_settings = MagicMock()
        mock_settings.rate_limit_enabled = True
        mock_settings.environment = "production"
        mock_get_settings.return_value = mock_settings

        limiter = RateLimiter()
        request1 = create_mock_request(headers={"X-Session-ID": "session-1"})
        request2 = create_mock_request(headers={"X-Session-ID": "session-2"})

        # Fill up session 1's bucket
        for _ in range(5):
            limiter.check_rate_limit(request1, limit=5)

        # Session 1 should be rate limited
        with pytest.raises(HTTPException) as exc_info:
            limiter.check_rate_limit(request1, limit=5)
        assert exc_info.value.status_code == 429

        # Session 2 should still be able to make calls
        for _ in range(5):
            limiter.check_rate_limit(request2, limit=5)

    @patch("src.api.rate_limiting.get_settings")
    def test_separate_buckets_per_limit_tier(
        self, mock_get_settings: MagicMock
    ) -> None:
        """Test that different limit tiers have separate buckets."""
        mock_settings = MagicMock()
        mock_settings.rate_limit_enabled = True
        mock_settings.environment = "production"
        mock_get_settings.return_value = mock_settings

        limiter = RateLimiter()
        request = create_mock_request(headers={"X-Session-ID": "test-tiers"})

        # Fill up the limit=5 bucket
        for _ in range(5):
            limiter.check_rate_limit(request, limit=5)

        # limit=5 bucket should be full
        with pytest.raises(HTTPException):
            limiter.check_rate_limit(request, limit=5)

        # limit=10 bucket should still have room
        for _ in range(10):
            limiter.check_rate_limit(request, limit=10)

    @patch("src.api.rate_limiting.get_settings")
    def test_custom_window_seconds(self, mock_get_settings: MagicMock) -> None:
        """Test rate limiting with custom window size."""
        mock_settings = MagicMock()
        mock_settings.rate_limit_enabled = True
        mock_settings.environment = "production"
        mock_get_settings.return_value = mock_settings

        limiter = RateLimiter()
        request = create_mock_request(headers={"X-Session-ID": "test-window"})

        # Fill up bucket with 120-second window
        for _ in range(3):
            limiter.check_rate_limit(request, limit=3, window_seconds=120)

        # Should raise with retry_after=120
        with pytest.raises(HTTPException) as exc_info:
            limiter.check_rate_limit(request, limit=3, window_seconds=120)

        assert exc_info.value.detail["retry_after"] == 120
        assert exc_info.value.headers["Retry-After"] == "120"


class TestRateLimiterConvenienceMethods:
    """Tests for check_llm_rate_limit, check_combat_rate_limit, check_default_rate_limit."""

    @patch("src.api.rate_limiting.get_settings")
    def test_check_llm_rate_limit_uses_llm_setting(
        self, mock_get_settings: MagicMock
    ) -> None:
        """Test that check_llm_rate_limit uses rate_limit_llm_calls setting."""
        mock_settings = MagicMock()
        mock_settings.rate_limit_enabled = True
        mock_settings.environment = "production"
        mock_settings.rate_limit_llm_calls = 3
        mock_get_settings.return_value = mock_settings

        limiter = RateLimiter()
        request = create_mock_request(headers={"X-Session-ID": "test-llm"})

        # Fill up LLM bucket (limit=3)
        for _ in range(3):
            limiter.check_llm_rate_limit(request)

        # Should raise at limit=3
        with pytest.raises(HTTPException) as exc_info:
            limiter.check_llm_rate_limit(request)

        assert exc_info.value.status_code == 429
        assert "3 requests per minute" in exc_info.value.detail["message"]

    @patch("src.api.rate_limiting.get_settings")
    def test_check_combat_rate_limit_uses_combat_setting(
        self, mock_get_settings: MagicMock
    ) -> None:
        """Test that check_combat_rate_limit uses rate_limit_combat_calls setting."""
        mock_settings = MagicMock()
        mock_settings.rate_limit_enabled = True
        mock_settings.environment = "production"
        mock_settings.rate_limit_combat_calls = 5
        mock_get_settings.return_value = mock_settings

        limiter = RateLimiter()
        request = create_mock_request(headers={"X-Session-ID": "test-combat"})

        # Fill up combat bucket (limit=5)
        for _ in range(5):
            limiter.check_combat_rate_limit(request)

        # Should raise at limit=5
        with pytest.raises(HTTPException) as exc_info:
            limiter.check_combat_rate_limit(request)

        assert exc_info.value.status_code == 429
        assert "5 requests per minute" in exc_info.value.detail["message"]

    @patch("src.api.rate_limiting.get_settings")
    def test_check_default_rate_limit_uses_default_setting(
        self, mock_get_settings: MagicMock
    ) -> None:
        """Test that check_default_rate_limit uses rate_limit_default_calls setting."""
        mock_settings = MagicMock()
        mock_settings.rate_limit_enabled = True
        mock_settings.environment = "production"
        mock_settings.rate_limit_default_calls = 7
        mock_get_settings.return_value = mock_settings

        limiter = RateLimiter()
        request = create_mock_request(headers={"X-Session-ID": "test-default"})

        # Fill up default bucket (limit=7)
        for _ in range(7):
            limiter.check_default_rate_limit(request)

        # Should raise at limit=7
        with pytest.raises(HTTPException) as exc_info:
            limiter.check_default_rate_limit(request)

        assert exc_info.value.status_code == 429
        assert "7 requests per minute" in exc_info.value.detail["message"]


# ============================================================================
# Global rate_limiter Instance Tests
# ============================================================================


class TestGlobalRateLimiter:
    """Tests for the global rate_limiter instance."""

    def test_global_rate_limiter_exists(self) -> None:
        """Test that global rate_limiter instance is available."""
        assert rate_limiter is not None
        assert isinstance(rate_limiter, RateLimiter)


# ============================================================================
# require_rate_limit Dependency Factory Tests
# ============================================================================


class TestRequireRateLimitDependency:
    """Tests for require_rate_limit dependency factory."""

    @patch("src.api.rate_limiting.rate_limiter")
    def test_llm_limit_type_calls_check_llm_rate_limit(
        self, mock_rate_limiter: MagicMock
    ) -> None:
        """Test that limit_type='llm' calls check_llm_rate_limit."""
        dependency = require_rate_limit("llm")
        request = create_mock_request()

        dependency(request)

        mock_rate_limiter.check_llm_rate_limit.assert_called_once_with(request)
        mock_rate_limiter.check_combat_rate_limit.assert_not_called()
        mock_rate_limiter.check_default_rate_limit.assert_not_called()

    @patch("src.api.rate_limiting.rate_limiter")
    def test_combat_limit_type_calls_check_combat_rate_limit(
        self, mock_rate_limiter: MagicMock
    ) -> None:
        """Test that limit_type='combat' calls check_combat_rate_limit."""
        dependency = require_rate_limit("combat")
        request = create_mock_request()

        dependency(request)

        mock_rate_limiter.check_combat_rate_limit.assert_called_once_with(request)
        mock_rate_limiter.check_llm_rate_limit.assert_not_called()
        mock_rate_limiter.check_default_rate_limit.assert_not_called()

    @patch("src.api.rate_limiting.rate_limiter")
    def test_default_limit_type_calls_check_default_rate_limit(
        self, mock_rate_limiter: MagicMock
    ) -> None:
        """Test that limit_type='default' calls check_default_rate_limit."""
        dependency = require_rate_limit("default")
        request = create_mock_request()

        dependency(request)

        mock_rate_limiter.check_default_rate_limit.assert_called_once_with(request)
        mock_rate_limiter.check_llm_rate_limit.assert_not_called()
        mock_rate_limiter.check_combat_rate_limit.assert_not_called()

    @patch("src.api.rate_limiting.rate_limiter")
    def test_unknown_limit_type_defaults_to_default(
        self, mock_rate_limiter: MagicMock
    ) -> None:
        """Test that unknown limit_type falls back to default rate limit."""
        dependency = require_rate_limit("unknown_type")
        request = create_mock_request()

        dependency(request)

        mock_rate_limiter.check_default_rate_limit.assert_called_once_with(request)

    @patch("src.api.rate_limiting.rate_limiter")
    def test_no_limit_type_uses_default(self, mock_rate_limiter: MagicMock) -> None:
        """Test that no limit_type argument uses default rate limit."""
        dependency = require_rate_limit()
        request = create_mock_request()

        dependency(request)

        mock_rate_limiter.check_default_rate_limit.assert_called_once_with(request)

    def test_dependency_returns_callable(self) -> None:
        """Test that require_rate_limit returns a callable function."""
        dependency = require_rate_limit("llm")
        assert callable(dependency)

    def test_dependency_function_accepts_request(self) -> None:
        """Test that returned dependency accepts Request parameter."""
        dependency = require_rate_limit("llm")
        request = create_mock_request()

        # Should not raise, even if rate limiting is disabled/test env
        result = dependency(request)
        assert result is None  # Dependency returns None


# ============================================================================
# Integration Tests
# ============================================================================


class TestRateLimitingIntegration:
    """Integration tests for rate limiting behavior."""

    @patch("src.api.rate_limiting.get_settings")
    def test_anonymous_requests_share_bucket(
        self, mock_get_settings: MagicMock
    ) -> None:
        """Test that anonymous requests share the same bucket."""
        mock_settings = MagicMock()
        mock_settings.rate_limit_enabled = True
        mock_settings.environment = "production"
        mock_get_settings.return_value = mock_settings

        limiter = RateLimiter()

        # Two requests without session_id both become "anonymous"
        request1 = create_mock_request()
        request2 = create_mock_request()

        # Fill up the anonymous bucket
        for _ in range(3):
            limiter.check_rate_limit(request1, limit=5)
        for _ in range(2):
            limiter.check_rate_limit(request2, limit=5)

        # Both should now be limited (shared 5 calls)
        with pytest.raises(HTTPException):
            limiter.check_rate_limit(request1, limit=5)

        with pytest.raises(HTTPException):
            limiter.check_rate_limit(request2, limit=5)

    @patch("src.api.rate_limiting.get_settings")
    def test_development_environment_applies_rate_limits(
        self, mock_get_settings: MagicMock
    ) -> None:
        """Test that development environment still applies rate limits."""
        mock_settings = MagicMock()
        mock_settings.rate_limit_enabled = True
        mock_settings.environment = "development"
        mock_get_settings.return_value = mock_settings

        limiter = RateLimiter()
        request = create_mock_request(headers={"X-Session-ID": "dev-test"})

        # Fill up bucket
        for _ in range(3):
            limiter.check_rate_limit(request, limit=3)

        # Should raise in development
        with pytest.raises(HTTPException):
            limiter.check_rate_limit(request, limit=3)

    @patch("src.api.rate_limiting.get_settings")
    def test_production_environment_applies_rate_limits(
        self, mock_get_settings: MagicMock
    ) -> None:
        """Test that production environment applies rate limits."""
        mock_settings = MagicMock()
        mock_settings.rate_limit_enabled = True
        mock_settings.environment = "production"
        mock_get_settings.return_value = mock_settings

        limiter = RateLimiter()
        request = create_mock_request(headers={"X-Session-ID": "prod-test"})

        # Fill up bucket
        for _ in range(3):
            limiter.check_rate_limit(request, limit=3)

        # Should raise in production
        with pytest.raises(HTTPException):
            limiter.check_rate_limit(request, limit=3)

    @patch("src.api.rate_limiting.get_settings")
    def test_exception_contains_proper_structure(
        self, mock_get_settings: MagicMock
    ) -> None:
        """Test that 429 exception has all required fields."""
        mock_settings = MagicMock()
        mock_settings.rate_limit_enabled = True
        mock_settings.environment = "production"
        mock_get_settings.return_value = mock_settings

        limiter = RateLimiter()
        request = create_mock_request(headers={"X-Session-ID": "error-test"})

        # Exceed limit
        limiter.check_rate_limit(request, limit=1)

        with pytest.raises(HTTPException) as exc_info:
            limiter.check_rate_limit(request, limit=1)

        exc = exc_info.value

        # Check status code
        assert exc.status_code == 429

        # Check detail structure
        assert isinstance(exc.detail, dict)
        assert "error" in exc.detail
        assert "message" in exc.detail
        assert "retry_after" in exc.detail

        # Check detail values
        assert exc.detail["error"] == "rate_limit_exceeded"
        assert "Rate limit exceeded" in exc.detail["message"]
        assert isinstance(exc.detail["retry_after"], int)

        # Check headers
        assert exc.headers is not None
        assert "Retry-After" in exc.headers
        assert exc.headers["Retry-After"] == str(exc.detail["retry_after"])
