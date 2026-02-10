"""
Tests for audit trail logging.

Verifies audit event creation, JSON file persistence,
and event type constants.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from auth.audit import AuditEvents, _persist_to_json, log_audit_event
from auth.schemas import CurrentUser


class TestAuditEvents:
    """Test audit event type constants."""

    def test_event_types_exist(self):
        assert AuditEvents.LOGIN == "LOGIN"
        assert AuditEvents.SLIDE_VIEWED == "SLIDE_VIEWED"
        assert AuditEvents.ANNOTATION_CREATED == "ANNOTATION_CREATED"
        assert AuditEvents.BREAK_GLASS_ACTIVATED == "BREAK_GLASS_ACTIVATED"

    def test_all_event_types_are_strings(self):
        for attr in dir(AuditEvents):
            if not attr.startswith("_"):
                value = getattr(AuditEvents, attr)
                assert isinstance(value, str)


class TestAuditJsonPersistence:
    """Test JSON file fallback persistence."""

    def test_persist_to_json(self, tmp_path):
        """Test writing audit event to JSON Lines file."""
        log_file = tmp_path / "audit.jsonl"

        event = {
            "id": "test-id",
            "timestamp": "2026-02-10T00:00:00Z",
            "level": "INFO",
            "event_type": "TEST_EVENT",
            "user_sub": "test-user",
            "action": "TEST",
        }

        with (
            patch("auth.audit._AUDIT_LOG_DIR", tmp_path),
            patch("auth.audit._AUDIT_LOG_FILE", log_file),
        ):
            _persist_to_json(event)

        assert log_file.exists()
        content = log_file.read_text()
        parsed = json.loads(content.strip())
        assert parsed["id"] == "test-id"
        assert parsed["event_type"] == "TEST_EVENT"


class TestLogAuditEvent:
    """Test the main log_audit_event function."""

    @pytest.mark.asyncio
    async def test_log_event_with_user(self, tmp_path):
        """Test logging with a user context."""
        log_file = tmp_path / "audit.jsonl"

        user = CurrentUser(
            sub="dr-martin",
            username="dr.martin",
            roles=["MEDECIN"],
        )

        request = MagicMock()
        request.headers = {"User-Agent": "TestBrowser/1.0"}
        request.client = MagicMock()
        request.client.host = "192.168.1.100"

        with (
            patch("auth.audit._AUDIT_LOG_DIR", tmp_path),
            patch("auth.audit._AUDIT_LOG_FILE", log_file),
            patch("auth.audit._persist_to_db", new_callable=AsyncMock),
        ):
            await log_audit_event(
                event_type=AuditEvents.SLIDE_VIEWED,
                action="READ",
                user=user,
                request=request,
                resource_type="slide",
                resource_id="abc123",
                level="INFO",
            )

        assert log_file.exists()
        content = log_file.read_text().strip()
        parsed = json.loads(content)
        assert parsed["event_type"] == "SLIDE_VIEWED"
        assert parsed["user_sub"] == "dr-martin"
        assert parsed["ip_address"] == "192.168.1.100"
        assert parsed["resource_type"] == "slide"

    @pytest.mark.asyncio
    async def test_log_event_without_user(self, tmp_path):
        """Test logging without user (failed auth)."""
        log_file = tmp_path / "audit.jsonl"

        with (
            patch("auth.audit._AUDIT_LOG_DIR", tmp_path),
            patch("auth.audit._AUDIT_LOG_FILE", log_file),
            patch("auth.audit._persist_to_db", new_callable=AsyncMock),
        ):
            await log_audit_event(
                event_type=AuditEvents.AUTH_FAILED,
                action="LOGIN",
                level="WARNING",
                details={"reason": "invalid token"},
            )

        content = log_file.read_text().strip()
        parsed = json.loads(content)
        assert parsed["event_type"] == "AUTH_FAILED"
        assert parsed["level"] == "WARNING"
        assert parsed["user_sub"] is None

    @pytest.mark.asyncio
    async def test_critical_event(self, tmp_path):
        """Test CRITICAL level for break-glass."""
        log_file = tmp_path / "audit.jsonl"

        user = CurrentUser(sub="dr-martin", username="dr.martin", roles=["MEDECIN"])

        with (
            patch("auth.audit._AUDIT_LOG_DIR", tmp_path),
            patch("auth.audit._AUDIT_LOG_FILE", log_file),
            patch("auth.audit._persist_to_db", new_callable=AsyncMock),
        ):
            await log_audit_event(
                event_type=AuditEvents.BREAK_GLASS_ACTIVATED,
                action="CREATE",
                user=user,
                level="CRITICAL",
                details={"reason": "Emergency patient access"},
            )

        content = log_file.read_text().strip()
        parsed = json.loads(content)
        assert parsed["level"] == "CRITICAL"
        assert parsed["event_type"] == "BREAK_GLASS_ACTIVATED"
