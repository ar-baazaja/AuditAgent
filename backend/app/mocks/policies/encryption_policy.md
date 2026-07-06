# Encryption Policy

**Owner:** Security Team · **Applies to:** SOC 2, HIPAA

## Data in Transit
- All data crossing public networks MUST use TLS 1.2 or higher.
- Plaintext (HTTP, TLS 1.0/1.1) listeners are prohibited.

## Data at Rest
- All object storage (S3) and databases (RDS) MUST be encrypted at rest.
- Encryption keys are managed in KMS with automatic key rotation enabled.

## Enforcement
- Unencrypted storage or downgraded TLS is a violation requiring immediate fix.
