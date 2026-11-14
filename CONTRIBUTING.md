# Contributing

1. Create a focused branch for your change.
2. Keep simulator-only behavior isolated from any future live model integration.
3. Add or update tests for changed behavior and scoring.
4. Run `pytest -q` and `python -m compileall -q app tests`.
5. Update documentation and the threat model when trust boundaries or capabilities change.
6. Do not add real credentials, personal data, external targets, or destructive tool integrations to test fixtures.
