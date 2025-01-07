# Test Support Files Migration

The test support files have been reorganized into the following structure:

- /tests/uncategorized/config/: Configuration files
  - backend_conftest.py (moved from backend/tests/conftest.py)

- /tests/uncategorized/data/: Test data files
  - sample_blueprint_full.json
  - sample_blueprint_partial.json
  - backend/ (contents from backend/tests/data/)

- /tests/uncategorized/requirements/: Test requirements
  - backend-requirements-test.txt

- /tests/uncategorized/logs/: Test logs
  - backend/ (contents from backend/tests/logs/)

Note: You may need to update import paths in your test files to reflect these new locations.
