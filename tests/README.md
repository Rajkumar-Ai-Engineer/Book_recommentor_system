# Test Suite Documentation

## Overview
Production-grade test suite for the Book Recommendation System with comprehensive unit and integration tests using fixtures and monkey patching.

## Test Structure
```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── fixtures/
│   └── test_utils.py        # Test utilities and helpers
├── unit/                    # Unit tests
│   ├── test_data_ingestion.py
│   ├── test_data_validation.py
│   └── test_data_transformation.py
└── integration/             # Integration tests
    ├── test_data_pipeline.py
    └── test_model_training.py
```

## Key Features

### Fixtures
- **Sample Data Fixtures**: Pre-configured test data for ratings and books
- **Configuration Fixtures**: Mock configuration objects for all components
- **Temporary Directory Fixtures**: Isolated file system for each test
- **Mock Artifacts**: Reusable artifact objects for pipeline testing

### Monkey Patching
- **Logger Mocking**: Isolated logging for test verification
- **File System Mocking**: Mock file operations without actual I/O
- **External Dependencies**: Mock pandas, numpy, and sklearn operations
- **Exception Handling**: Test error propagation and handling

### Test Categories
- **Unit Tests**: Individual component testing with full isolation
- **Integration Tests**: End-to-end pipeline testing
- **Smoke Tests**: Quick validation of core functionality
- **Performance Tests**: Benchmark critical operations

## Running Tests

### Install Dependencies
```bash
pip install -r test-requirements.txt
```

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test Types
```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Using Makefile
```bash
# Install test dependencies
make install-test-deps

# Run all tests
make test

# Run with coverage
make test-coverage

# Run in parallel
make test-parallel
```

## Test Configuration

### pytest.ini
- Configured test discovery patterns
- Custom markers for test categorization
- Warning filters and output formatting

### Fixtures in conftest.py
- `sample_ratings_data`: Mock ratings DataFrame
- `sample_books_data`: Mock books DataFrame  
- `temp_dir`: Temporary directory for file operations
- `data_ingestion_config`: Mock configuration objects
- `mock_logger`: Isolated logger for testing

## Best Practices

### Unit Testing
- Each test is isolated and independent
- Mock all external dependencies
- Test both success and failure scenarios
- Verify method calls and return values

### Integration Testing
- Test complete workflows end-to-end
- Use realistic data volumes
- Verify file creation and data persistence
- Test error propagation through pipeline

### Fixtures Usage
- Reuse fixtures across multiple tests
- Keep fixtures focused and single-purpose
- Use parametrized fixtures for variations
- Clean up resources in fixture teardown

### Monkey Patching
- Patch at the appropriate level (module vs class)
- Use context managers for temporary patches
- Verify patch targets are called correctly
- Reset patches between tests

## CI/CD Integration

### GitHub Actions
- Automated testing on push/PR
- Multi-Python version testing
- Coverage reporting
- Test result artifacts

### Coverage Requirements
- Minimum 80% code coverage
- Critical paths must have 100% coverage
- Coverage reports in HTML and XML formats

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure PYTHONPATH includes src directory
2. **File Permissions**: Use temp_dir fixture for file operations
3. **Mock Conflicts**: Check patch targets and scope
4. **Fixture Scope**: Use appropriate fixture scope (function/class/session)

### Debug Mode
```bash
# Run with verbose output and no capture
pytest tests/ -v -s

# Run specific test with debugging
pytest tests/unit/test_data_ingestion.py::TestDataIngestion::test_init -v -s
```