# Status Code Assertion Patterns for Web API Tests

This document describes the standard patterns for handling HTTP status codes in test_web_api tests.

## Assertion Helpers

### Basic Assertions

Located in `test/testcases/test_web_api/common.py`:

| Function | Status Code | Description |
|----------|-------------|-------------|
| `assert_status_code(res, expected, msg)` | Any | Generic assertion |
| `assert_status_ok(res)` | 200 | OK |
| `assert_status_201(res)` | 201 | Created |
| `assert_status_400(res)` | 400 | Bad Request |
| `assert_status_401(res)` | 401 | Unauthorized |
| `assert_status_403(res)` | 403 | Forbidden |
| `assert_status_404(res)` | 404 | Not Found |
| `assert_status_422(res)` | 422 | Unprocessable Entity |
| `assert_status_500(res)` | 500 | Internal Server Error |
| `assert_status_in(res, codes)` | Multiple | Assert code in list |

### Usage Patterns

#### Pattern 1: Pass expected_status to API helper

```python
# Most API helpers accept expected_status parameter
res = create_dataset(auth, {"name": "test"}, expected_status=200)
```

#### Pattern 2: Assert on response object

```python
res = requests.get(url, auth=auth)
assert_status_ok(res)
data = res.json()
```

#### Pattern 3: Get status code and JSON together

```python
status, data = parse_response(res)
assert status == 200
```

#### Pattern 4: Assert multiple acceptable codes

```python
assert_status_in(res, [200, 201])  # Created or already exists
```

## API Helper Pattern

All API helpers follow this pattern:

```python
def some_api_call(auth, payload=None, *, headers=HEADERS, expected_status=None):
    res = requests.post(url=..., headers=headers, auth=auth, json=payload)
    if expected_status is not None:
        assert_status_code(res, expected_status)
    return res.json()
```

**Key points:**
- `expected_status` is optional (keyword-only)
- If provided, assertion happens before returning
- Always returns JSON data

## Generic API Call

For endpoints without dedicated helpers:

```python
status, data = api_call(
    "POST",
    f"{HOST_ADDRESS}/custom/endpoint",
    auth=auth,
    payload={"key": "value"},
    expected_status=201,
)
```

## Test Organization

### Positive Tests

```python
def test_create_dataset_success(auth):
    res = create_dataset(auth, {"name": "test"}, expected_status=200)
    assert res["code"] == 0
```

### Negative Tests

```python
def test_create_dataset_missing_name(auth):
    res = create_dataset(auth, {}, expected_status=400)
    assert "error" in res or res.get("code") != 0
```

### Error Handling Tests

```python
def test_unauthorized_access():
    res = create_dataset(None, {"name": "test"}, expected_status=401)
```

## Artifact Locations

- Assertion helpers: `test/testcases/test_web_api/common.py` (lines 74-122)
- API helpers: `test/testcases/test_web_api/common.py` (lines 123+)
- Test examples: `test/testcases/test_web_api/` (various test_*.py files)

## Assumptions

1. All API helpers return JSON data
2. Status code assertions raise `AssertionError` on failure with response text
3. The `expected_status` parameter is opt-in for backward compatibility
4. HTTP debug logging is controlled by `TEST_HTTP_DEBUG=1` env var
