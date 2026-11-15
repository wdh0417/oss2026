# CI optimization report

This feature branch adds a Python/OS test matrix (Python 3.10 and 3.12 on Ubuntu and Windows), a reusable test workflow, and a composite Python setup action using `actions/setup-python`'s pip cache. Path filtering skips unrelated jobs. Deployment is restricted to successful pushes to `main` that change deployable paths; pull requests run checks but do not deploy.

## Cache benchmark

Each test matrix job measures dependency installation once with pip's download cache disabled and again with the cache populated. The workflow reports durations and the calculated percentage in the Actions run summary, and uploads a Markdown report artifact for each OS/Python combination.

Improvement formula: `(uncached seconds - warm-cache seconds) / uncached seconds × 100`.

No numerical result is claimed here before a successful GitHub Actions run. Runner load and network conditions affect the observed durations, so use the uploaded artifact from the actual run as the comparison report.

## Submission links

- Branch: https://github.com/wdh0417/oss2026/tree/ci/matrix-cache-reusable-workflows
- Actions run: add the URL of the successful workflow run after it completes.
- Cache comparison: attach or link the `cache-benchmark-*` artifacts from that run.
