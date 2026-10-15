# Contributing

Thank you for helping build a useful and verifiable open-source engineering tool.

## Start here

1. Check existing issues and the [roadmap](ROADMAP.md).
2. Propose significant behavioral or security changes in an issue before investing substantial work.
3. Create a focused branch; keep work generic, independently licensed, and free of proprietary code.
4. Add regression tests and update README/architecture/security documentation when behavior changes.
5. Run checks locally:

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python -m compileall -q src tests
safeops --root . scan
```

6. Open a PR using the PR template. Explain the change, risks, tests, and whether the change involves network access or code execution. The `quality-gate` check aggregates the full CI matrix and should pass before merging.
7. For release or governance changes, follow [Maintainer guide](docs/MAINTAINER_GUIDE.md) and [Release procedure](docs/RELEASING.md).

## Project rules

- Never introduce credentials, tokens, PII, private source code or unlicensed assets.
- AI-generated patches must be reviewed and tested by a human contributor.
- New external network calls must be explicitly opt-in and must not transmit workspace files by default.
- Do not silently broaden check allowlists or bypass human approval gates.
- Avoid shell execution or interpolating prompts into commands.
- Prefer standard-library functionality; justify any runtime dependencies.
- Ensure docs and source use valid UTF-8, including PT-PT diacritics.
- Update package metadata and `__version__`, current EN/PT-PT document version markers, implementation status, roadmap and changelog together when behavior/version changes. Preserve dated audit and historical-version records.
- Changes to fixed checks or runner behavior must update the execution contract and document approval compatibility; never migrate approval intent automatically.
- Keep [provider test evidence](docs/PROVIDER_TESTING.md) explicit: transport doubles and loopback fixtures do not establish live authentication or inference. Never add real credentials or default billable API calls to tests.

## License

By submitting a contribution, you agree it may be distributed under Apache-2.0 and confirm you are entitled to contribute the material. A CLA is not currently required. All contributors retain the copyright to their contributions.
