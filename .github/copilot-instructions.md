# Repository Custom Instructions for GitHub Copilot

* **Preserve core functionality**: Never remove or change public APIs or critical business logic unless replacement code with equivalent (or improved) behaviour and passing tests is provided.

* **Static analysis excellence**: All Python code **must** pass `pylint` with no errors and conform to `black` formatting (`black --check` in CI).

* **Production‑safety guardrails**: When `TEST_MODE` is `False` (production), Copilot must not generate or modify code that writes to the database (INSERT/UPDATE/DELETE/DDL). Reads are allowed; writes must be behind feature flags or test harnesses.

* **Comprehensive testing mandate**: Every change requires unit, integration, security, and performance tests. Maintain ≥90 % coverage and ensure the full suite runs in CI before merge.

* **Config consistency**: Store all configuration artefacts under the `config/` directory. Place a config outside this folder only when absolutely indispensable and clearly document the reason.

* **Design for reuse & scale**: Apply SOLID principles, dependency injection, and type hints to keep code modular, extensible, and easy to refactor.

* **Readability & maintainability**: Follow PEP 8, write descriptive docstrings and comments, and use expressive naming conventions.

* **User experience first**: Prioritise clarity, accessibility, and performance in any UI/UX‑related code. Provide rationale for UX decisions and add UI tests where relevant.

* **Enterprise & OSS best practices**: Ensure security hardening, performance optimisation, semantic versioning, detailed CHANGELOG, and CONTRIBUTING guidelines. Use permissive licences and transparent governance.

* **Documentation discipline**: Keep code-level docstrings, architectural diagrams, ADRs, CHANGELOG, and user-facing guides current. Each pull request must update relevant documentation or explicitly justify why not. CI must include a documentation check step that fails if docs are stale.

* **No regressions**: Run the full pre-commit checks (linting, formatting, tests, security scans) before proposing a merge. If any check fails, fix or revert.
