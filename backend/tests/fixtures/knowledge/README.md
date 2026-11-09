# Structured knowledge development fixtures

Project-authored synthetic notes refer to real CWE identifiers but are not captured
MITRE documents or independently reviewed gold knowledge. Source revisions and
freshness windows are fixture values. No external request or feed ingestion produced
these files. Source content hashes cover the exact fixture UTF-8 bytes.

The retrieval labels cover one exact query, three lexical queries and one no-match
query. They check deterministic retrieval mechanics, not version applicability,
remediation correctness, general retrieval quality or model improvement. Native
source ingestion and corpus licensing/provenance review are separate work.

Actual PostgreSQL tests execute fixed parameter-bound SQL inside read-only
transactions. For small snapshots (max 128 documents), FTS projects bounded JSONB
values without runtime DDL or migration graph changes. Persistent indexing, feed
synchronization and provider knowledge transmission are not implemented by this slice.
