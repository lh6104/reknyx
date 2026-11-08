# Offline Analyst harness fixtures

Project-authored synthetic development fixtures, without native captures or
independent gold-label review. This single service case tests the harness, not
model quality. The package-local case/manifest JSON schemas are the internal
schema authority; public OpenAPI and existing review evaluation stay unchanged.

From `backend/`, write to a new output path:

```bash
uv run --frozen python -m reknyx.security_analysis.benchmarks \
  --cases tests/fixtures/analyst_benchmark/development-sample.json \
  --manifest tests/fixtures/analyst_benchmark/offline-manifest.json \
  --output /tmp/reknyx-analyst-offline-report.json
```

The CLI never loads credentials or calls models/scanners. It validates the inputs
and records all cases as `not_run`. Exit 0 means coverage report creation, not model
success. Existing outputs are rejected. Python tests can inject an offline transport
with `generate(pack, options)`; it receives query and observation IDs/kinds only.
Deadline metadata is advisory, not process enforcement; this is not a live runner.

Scoring validates structured claim IDs against labelled supporting observations.
It cannot judge arbitrary prose entailment. Valid structured outputs are retained
for rescoring; invalid content and exception messages are omitted. Unknown monetary
cost remains null. Annotation coverage, response coverage and full scheduled success
are distinct. Error/not_run rows never pass. Comparison rechecks outputs and allows
only declared factor changes, reporting a descriptive paired delta without a winner
on incomplete coverage. There are no confidence intervals or significance claims.

Live adapters require a separate reviewed plan covering data use, durable attempt
reservations, hard timeouts and reconciliation. This fixture is not the proposed
120-case domain-reviewed dataset. Keep existing reserved holdout sealed.
