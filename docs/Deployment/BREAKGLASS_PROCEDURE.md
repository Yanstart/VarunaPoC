# Break-Glass Emergency Access Procedure

## Overview

Break-glass access is an emergency mechanism that grants temporary elevated privileges when normal authentication is unavailable or insufficient. This is critical in hospital environments where patient care cannot be delayed by technical authentication failures.

## When to Use Break-Glass Access

Break-glass access should **only** be used in the following scenarios:

1. **Keycloak / IdP is down**: The OIDC provider is unreachable, and a physician needs immediate access to slides for patient care.
2. **Account locked out**: A physician's account is locked (e.g., password expiry, MFA issues) and there is an urgent clinical need.
3. **Role escalation needed**: A user needs temporary access to resources outside their normal scope for an emergency case.
4. **Disaster recovery**: During system recovery, when normal auth infrastructure is being restored.

Break-glass access must **never** be used for:

- Convenience (bypassing normal login procedures)
- Routine access to restricted data
- Testing or development purposes
- Circumventing access control policies

## How to Issue Emergency Tokens

### Prerequisites

- You must have the `ADMIN_TECHNIQUE` role.
- You must document the medical/operational reason for the emergency access.

### API Endpoint

```
POST /api/auth/breakglass
```

### Request Body

```json
{
  "target_user": "user-sub-identifier",
  "reason": "Patient #12345 requires urgent biopsy slide review, Keycloak unavailable",
  "duration_minutes": 30
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `target_user` | string | Yes | Subject identifier of the user needing access |
| `reason` | string | Yes | 10-500 characters, medical/operational justification |
| `duration_minutes` | integer | No | 5-60 minutes, default 30 |

### Response

```json
{
  "session_id": "uuid",
  "target_user": "user-sub-identifier",
  "issued_by": "admin-sub-identifier",
  "reason": "Patient #12345 requires urgent biopsy slide review, Keycloak unavailable",
  "duration_minutes": 30,
  "activated_at": "2026-03-11T10:00:00+00:00",
  "expires_at": "2026-03-11T10:30:00+00:00",
  "token": "bg_<session_id>_<random>_<expiry>"
}
```

The returned `token` should be provided to the target user. They include it as a `Bearer` token in the `Authorization` header for API requests.

### Using cURL

```bash
# Issue a break-glass token (admin only)
curl -X POST https://varuna.example.com/api/auth/breakglass \
  -H "Authorization: Bearer <admin-jwt>" \
  -H "Content-Type: application/json" \
  -d '{
    "target_user": "doctor-uuid-here",
    "reason": "Emergency slide access - Keycloak down, patient in OR",
    "duration_minutes": 30
  }'
```

## Review and Closure Workflow

Every break-glass session **must** be reviewed by an `ADMIN_TECHNIQUE` user after the emergency is resolved. This is a regulatory requirement for clinical compliance.

### 1. List Sessions

```
GET /api/auth/breakglass/sessions
```

Query parameters:
- `active_only=true` - Only show currently active sessions
- `pending_review=true` - Only show sessions not yet reviewed

```bash
# List sessions pending review
curl https://varuna.example.com/api/auth/breakglass/sessions?pending_review=true \
  -H "Authorization: Bearer <admin-jwt>"
```

### 2. Revoke Active Sessions

If a break-glass session is no longer needed (emergency resolved, user regained normal access), revoke it immediately:

```
DELETE /api/auth/breakglass/sessions/{session_id}
```

```bash
curl -X DELETE https://varuna.example.com/api/auth/breakglass/sessions/<session-id> \
  -H "Authorization: Bearer <admin-jwt>"
```

### 3. Review Completed Sessions

After a session expires or is revoked, review it to confirm the access was justified:

```
POST /api/auth/breakglass/sessions/{session_id}/review
```

```json
{
  "notes": "Confirmed: Keycloak was down 10:00-10:45. Dr. Dupont needed access for emergency biopsy review. Access was appropriate and limited to the required slides."
}
```

```bash
curl -X POST https://varuna.example.com/api/auth/breakglass/sessions/<session-id>/review \
  -H "Authorization: Bearer <admin-jwt>" \
  -H "Content-Type: application/json" \
  -d '{"notes": "Confirmed justified - Keycloak outage during emergency case."}'
```

### Review Checklist

When reviewing a break-glass session, verify:

- [ ] The stated reason was a genuine emergency
- [ ] The duration was appropriate (not longer than necessary)
- [ ] The target user was the correct person for the clinical scenario
- [ ] No unauthorized data access occurred during the session
- [ ] The root cause of the authentication failure has been addressed

## Audit Requirements

### What Gets Logged

Every break-glass action generates an audit event:

| Action | Level | Event Type |
|--------|-------|------------|
| Token issued | CRITICAL | `BREAK_GLASS_ACTIVATED` |
| Session revoked | WARNING | `BREAK_GLASS_REVIEWED` |
| Session reviewed | INFO | `BREAK_GLASS_REVIEWED` |

### Audit Fields

Each audit event includes:
- **Timestamp**: UTC ISO 8601
- **Issuer**: Admin who issued/revoked/reviewed the token
- **Target user**: User who received emergency access
- **Reason**: Documented justification
- **Duration**: Requested access duration
- **IP address**: Network address of the admin
- **Session ID**: Unique identifier linking all events for the session

### Data Retention

- Break-glass audit logs are retained for **minimum 6 years** per clinical compliance requirements (HIPAA, GDPR).
- In-memory sessions are lost on server restart (safety feature). The persistent audit trail in the database and JSONL fallback file is the authoritative record.

### Querying Audit Logs

Use the audit API to search break-glass events:

```bash
# All break-glass events
curl "https://varuna.example.com/api/audit/events?event_type=BREAK_GLASS_ACTIVATED" \
  -H "Authorization: Bearer <admin-jwt>"
```

## Architecture Notes

### Storage

- **In-memory**: Active sessions are stored in-memory for fast lookup. This means sessions are lost on server restart, which is intentional -- it limits the blast radius of any compromise.
- **PostgreSQL**: `break_glass_logs` table stores the persistent audit trail including review status.
- **JSONL fallback**: `backend/logs/audit.jsonl` provides disaster recovery if the database is unavailable.

### Session Lifecycle

```
ISSUED -> ACTIVE -> EXPIRED -> REVIEWED
                 \-> REVOKED -> REVIEWED
```

1. Admin issues token (session created, status: `active`)
2. Session expires naturally or is revoked by admin
3. Admin reviews the session (mandatory post-hoc audit)

### Security Considerations

- Tokens have a **hard maximum TTL of 60 minutes**.
- Only `ADMIN_TECHNIQUE` role can issue, list, revoke, and review tokens.
- All actions are logged at CRITICAL or WARNING level.
- In-memory storage means a server restart invalidates all active sessions.
- The `reason` field enforces a minimum length of 10 characters to prevent empty justifications.
