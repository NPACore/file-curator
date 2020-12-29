## Contributing

### Testing
Unit tests can be run with pytest.

There is one integration test in `tests/test_integration.py`.  In order to run this test, the environmental variable `api_key` should be set with your API key, and the GROUP, PROJECT, OUTPUT and test CURATOR variables should be set accordingly.  The test will skip if `api_key` is not available.