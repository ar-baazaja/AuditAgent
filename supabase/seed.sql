-- =============================================================================
-- AuditAgent — Seed Data (Phase 1)
-- Reference catalog only: frameworks + a representative slice of controls.
-- Run AFTER schema.sql. Safe to re-run (idempotent via ON CONFLICT).
--
-- This is *reference data* (like a currency table), not business logic —
-- tenant compliance is always computed from evidence_logs at runtime.
-- =============================================================================

-- ----- Frameworks -----------------------------------------------------------
insert into public.compliance_frameworks (key, name, version, description) values
  ('soc2',  'SOC 2 Type II', '2017 TSC',
   'AICPA Trust Services Criteria for Security, Availability, Processing Integrity, Confidentiality, and Privacy.'),
  ('hipaa', 'HIPAA Security Rule', '45 CFR Part 164',
   'US healthcare rule for safeguarding electronic protected health information (ePHI).')
on conflict (key) do update
  set name = excluded.name, version = excluded.version, description = excluded.description;

-- ----- SOC 2 controls (Common Criteria slice) -------------------------------
insert into public.controls (framework_id, code, title, description, category, check_type)
select f.id, c.code, c.title, c.description, c.category, c.check_type::evidence_source
from public.compliance_frameworks f
join (values
  ('CC6.1', 'Logical Access Controls',
   'Access to systems and data is restricted through authentication and authorization.',
   'Access Control', 'aws'),
  ('CC6.6', 'Encryption in Transit',
   'Data transmitted over public networks is encrypted (TLS).',
   'Encryption', 'aws'),
  ('CC6.7', 'Encryption at Rest',
   'Stored data (databases, object storage) is encrypted at rest.',
   'Encryption', 'aws'),
  ('CC7.2', 'Security Monitoring & Logging',
   'System activity is logged and monitored for anomalies (e.g. CloudTrail enabled).',
   'Monitoring', 'aws'),
  ('CC8.1', 'Change Management',
   'Code changes are reviewed and approved before deployment (branch protection).',
   'Change Management', 'github')
) as c(code, title, description, category, check_type) on true
where f.key = 'soc2'
on conflict (framework_id, code) do update
  set title = excluded.title, description = excluded.description,
      category = excluded.category, check_type = excluded.check_type;

-- ----- HIPAA controls (Security Rule slice) ---------------------------------
insert into public.controls (framework_id, code, title, description, category, check_type)
select f.id, c.code, c.title, c.description, c.category, c.check_type::evidence_source
from public.compliance_frameworks f
join (values
  ('164.312(a)(1)', 'Access Control',
   'Technical policies limiting ePHI access to authorized persons/software.',
   'Access Control', 'aws'),
  ('164.312(e)(1)', 'Transmission Security',
   'Guard against unauthorized access to ePHI transmitted over networks.',
   'Encryption', 'aws'),
  ('164.312(a)(2)(iv)', 'Encryption and Decryption',
   'Mechanism to encrypt and decrypt ePHI at rest.',
   'Encryption', 'aws'),
  ('164.312(b)', 'Audit Controls',
   'Record and examine activity in systems containing ePHI.',
   'Monitoring', 'aws')
) as c(code, title, description, category, check_type) on true
where f.key = 'hipaa'
on conflict (framework_id, code) do update
  set title = excluded.title, description = excluded.description,
      category = excluded.category, check_type = excluded.check_type;
