# Logging & Monitoring Policy

**Owner:** Security Team · **Applies to:** SOC 2, HIPAA

## Audit Logging
- CloudTrail MUST be enabled across all regions (multi-region trail).
- Log retention MUST be at least 365 days for systems handling ePHI.

## Change Management
- All production code changes MUST go through a reviewed pull request.
- Protected branches require at least 2 approving reviews and passing checks.

## Enforcement
- Disabled logging, short retention, or unreviewed changes are violations.
