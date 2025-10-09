# Test Suite

This directory contains the test suite for the invoice automation system.

## Structure

```
tests/
├── artifacts/                 # Test artifacts (screenshots, HTML files, etc.)
├── fixtures/                  # Test data and fixtures
├── integration/               # Integration tests
│   ├── adapters/             # Adapter integration tests
│   │   └── costs_sources/    # Costs source adapter tests
│   └── end_to_end/           # End-to-end tests
│       └── exploration/      # Website exploration tests
├── mocks/                    # Mock objects and test doubles
├── unit/                     # Unit tests
│   ├── adapters/            # Adapter unit tests
│   ├── core/                # Core domain unit tests
│   └── infrastructure/      # Infrastructure unit tests
├── conftest.py              # Pytest configuration and fixtures
└── run_repsol_exploration.py # Test runner for Repsol exploration
```

## Running Tests

### Unit Tests
```bash
pytest tests/unit/
```

### Integration Tests
```bash
pytest tests/integration/
```

### Specific Test
```bash
pytest tests/integration/adapters/costs_sources/test_repsol_explore.py
```

## Test Artifacts

Test artifacts (screenshots, HTML files, downloaded PDFs) are stored in `tests/artifacts/` and are automatically ignored by git.

## Environment Variables

Tests require the following environment variables to be set:

- `REPSOL_USERNAME` - Repsol customer portal username
- `REPSOL_PASSWORD` - Repsol customer portal password
- `DIGI_USERNAME` - Digi customer portal username
- `DIGI_PASSWORD` - Digi customer portal password
- `EMIVASA_USERNAME` - Emivasa customer portal username
- `EMIVASA_PASSWORD` - Emivasa customer portal password

## Test Categories

### Unit Tests
- Test individual components in isolation
- Use mocks for external dependencies
- Fast execution, no network calls

### Integration Tests
- Test component interactions
- May use real external services
- Slower execution, may require network access

### End-to-End Tests
- Test complete workflows
- Use real websites and services
- Slowest execution, requires full environment setup
