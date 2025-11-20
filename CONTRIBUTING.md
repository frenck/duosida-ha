# Contributing to Duosida EV Charger Integration

Thank you for your interest in contributing to the Duosida EV Charger integration for Home Assistant!

## Development Setup

### Prerequisites

- Python 3.10 or newer
- Home Assistant 2023.1 or newer
- Duosida EV charger (for testing)
- Git

### Setting Up Development Environment

1. **Fork and clone the repository**

```bash
git clone https://github.com/YOUR_USERNAME/duosida-ha.git
cd duosida-ha
```

2. **Create a virtual environment using uv**

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows
```

3. **Install dependencies**

```bash
uv pip install -r requirements.txt
uv pip install -r requirements_dev.txt
```

4. **Install pre-commit hooks**

```bash
pre-commit install
```

This will automatically run code quality checks (ruff, black, isort, mypy) before each commit.

## Code Quality Standards

This project maintains high code quality standards:

- ✅ **100% type hints** - All functions must have type annotations
- ✅ **Black formatting** - 88 character line length
- ✅ **isort** - Sorted imports (black profile)
- ✅ **ruff** - Linting with no errors
- ✅ **mypy** - Type checking passes
- ✅ **100% test pass rate** - All tests must pass

### Running Quality Checks

```bash
# Format code
black custom_components/ tests/
isort custom_components/ tests/

# Lint
ruff check custom_components/ tests/

# Type check
mypy --ignore-missing-imports custom_components/

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_coordinator.py -v

# Run tests with coverage
pytest tests/ --cov=custom_components.duosida_ev
```

## Testing

### Test Requirements

- All new features must include tests
- Bug fixes should include regression tests
- Test coverage should remain at or above current levels (100%)
- All tests must pass before merging

### Running Tests

```bash
# Run all tests
.venv/bin/python -m pytest tests/ -v

# Run with coverage report
.venv/bin/python -m pytest tests/ --cov=custom_components.duosida_ev --cov-report=html

# Run specific test
.venv/bin/python -m pytest tests/test_coordinator.py::test_coordinator_update_success -v
```

### Writing Tests

Tests use `pytest` and `pytest-homeassistant-custom-component`. See existing tests in the `tests/` directory for examples.

**Test file structure:**
- `tests/conftest.py` - Shared fixtures and mocks
- `tests/test_*.py` - Test files (one per module)

**Key fixtures:**
- `hass` - Home Assistant instance
- `mock_charger` - MockDuosidaCharger instance
- `coordinator` - DuosidaDataUpdateCoordinator instance
- `setup_integration` - Full integration setup

## Making Changes

### Workflow

1. **Create a feature branch**

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

2. **Make your changes**

- Follow the existing code style
- Add type hints to all new functions
- Update tests as needed
- Update documentation if applicable

3. **Run quality checks**

```bash
# Pre-commit will run automatically, but you can run manually:
black custom_components/ tests/
isort custom_components/ tests/
ruff check custom_components/ tests/
mypy --ignore-missing-imports custom_components/
pytest tests/ -v
```

4. **Commit your changes**

```bash
git add .
git commit -m "Add feature: description of your change"
```

Pre-commit hooks will run automatically. If they fail, fix the issues and commit again.

5. **Push to your fork**

```bash
git push origin feature/your-feature-name
```

6. **Create a Pull Request**

- Go to the original repository on GitHub
- Click "New Pull Request"
- Select your branch
- Fill out the PR template
- Wait for review

### Commit Message Guidelines

Use clear, descriptive commit messages:

- Start with a verb (Add, Fix, Update, Remove, etc.)
- Be concise but descriptive
- Reference issues if applicable (#123)

**Good examples:**
```
Add solar-powered charging automation example
Fix entity unavailability after network disconnect
Update README with FAQ section
Remove deprecated stop_on_disconnect parameter
```

**Bad examples:**
```
Fixed stuff
Update
Changes
asdf
```

## Code Style

### Python Style

- Follow PEP 8
- Use type hints everywhere (`from __future__ import annotations`)
- Use async/await for all I/O operations
- Use `async_add_executor_job` for blocking code
- Avoid blocking calls in the event loop

### Naming Conventions

- Classes: `PascalCase`
- Functions/methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`
- Async functions: Always use `async def`, never blocking calls

### Documentation

- Add docstrings to all public functions/classes
- Use Google-style docstrings
- Keep comments concise and meaningful
- Update README.md for user-facing changes

## Adding New Features

### New Sensor

1. Add sensor definition to `sensor.py` in the `SENSORS` tuple
2. Ensure data is available in coordinator's `data` dictionary
3. Add test in `tests/test_sensor.py`
4. Update README.md sensor table

### New Control (Switch/Number/Button)

1. Create entity class in appropriate file (`switch.py`, `number.py`, `button.py`)
2. Add to platform setup function
3. Add coordinator method if needed
4. Add test in corresponding test file
5. Update README.md controls table

### New Stored Setting

1. Add to `coordinator._stored_settings` dictionary
2. Create getter/setter methods in coordinator
3. Add sync to charger in `_sync_settings_to_charger()`
4. Add tests for persistence
5. Document in README.md

## Project Structure

```
duosida-ha/
├── custom_components/duosida_ev/  # Integration code
│   ├── __init__.py                # Entry point
│   ├── config_flow.py             # Setup wizard
│   ├── coordinator.py             # Data fetching
│   ├── const.py                   # Constants
│   ├── entity.py                  # Base entity
│   ├── sensor.py                  # Sensors
│   ├── switch.py                  # Switches
│   ├── number.py                  # Number controls
│   ├── button.py                  # Buttons
│   ├── manifest.json              # Metadata
│   └── strings.json               # UI strings
├── tests/                         # Test suite
│   ├── conftest.py                # Test fixtures
│   ├── test_*.py                  # Test files
├── .github/workflows/             # CI/CD (future)
├── README.md                      # User documentation
├── CONTRIBUTING.md                # This file
├── INTEGRATION_CHECKLIST.md       # Quality tier tracking
├── pyproject.toml                 # Tool configuration
└── requirements.txt               # Dependencies
```

## Common Tasks

### Update Translations

Translations are in `custom_components/duosida_ev/translations/`:

1. Edit `strings.json` (English base)
2. Update corresponding language files in `translations/`
3. Test in Home Assistant UI

### Update Dependencies

1. Edit `manifest.json` to change `duosida-ev` version
2. Update `requirements.txt` if needed
3. Test thoroughly
4. Update INTEGRATION_CHECKLIST.md

### Fix a Bug

1. Write a test that reproduces the bug
2. Fix the bug
3. Ensure test now passes
4. Run full test suite
5. Update CHANGELOG if applicable

## Getting Help

- **Questions?** Open a [Discussion](https://github.com/americodias/duosida-ha/discussions)
- **Bug?** Open an [Issue](https://github.com/americodias/duosida-ha/issues)
- **Feature idea?** Open a [Discussion](https://github.com/americodias/duosida-ha/discussions) first

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Thank You!

Your contributions help make this integration better for everyone. Thank you for taking the time to contribute! 🎉
