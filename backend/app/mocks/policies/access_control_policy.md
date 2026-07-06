# Access Control Policy

**Owner:** Security Team · **Applies to:** SOC 2, HIPAA

## Authentication
- All user and administrative access to production systems MUST require
  multi-factor authentication (MFA).
- The root/owner account MUST have MFA enabled and hardware-key protected.
- Passwords MUST be at least 14 characters and rotate at most every 90 days.

## Authorization
- Access follows least privilege; service accounts are reviewed quarterly.
- No production human access without an approved, time-bound request.

## Enforcement
- Any account without MFA is a violation and must be remediated within 24 hours.
