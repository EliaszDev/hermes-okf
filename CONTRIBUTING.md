# Contributing

Thank you for your interest in contributing to Hermes OKF! This is an early-stage
open-source project and every contribution helps shape the future of agent memory
systems.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/hermes-okf.git`
3. Install in development mode: `pip install -e ".[dev]"`
4. Run tests: `pytest`

## Development Workflow

- **Main branch**: `main` — always deployable
- **Feature branches**: `feature/your-feature-name`
- **Bug fixes**: `fix/issue-description`

## Code Quality

We use the following tools (all run in CI):

- **black** — code formatting (`black src tests`)
- **ruff** — linting (`ruff check src tests`)
- **mypy** — static type checking (`mypy src`)
- **pytest** — unit tests (`pytest`)

Pre-commit hooks are encouraged:

```bash
pip install pre-commit
pre-commit install
```

## Writing Tests

- Add tests to the `tests/` directory
- Name files `test_<module>.py`
- Use `pytest` fixtures and `tempfile.TemporaryDirectory` for filesystem tests
- Aim for >80% coverage on new code

## Documentation

- Update `README.md` for user-facing changes
- Update `docs/ARCHITECTURE.md` for design changes
- Add examples to `examples/` for new features

## Submitting a PR

1. Ensure all tests pass: `pytest`
2. Ensure linting passes: `ruff check src tests && black --check src tests`
3. Write a clear PR description explaining the *why* and *what*
4. Link any related issues

## Community

- Open an issue for bugs, feature requests, or questions
- Start a discussion for architectural proposals
- Be respectful and constructive

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
