---
name: test-conventions
description: Explains the test conventions used in this project. Use when writing new tests or converting existing tests.
allowed-tools: Read Grep
user-invocable: true
disable-model-invocation: false
---

# Test Conventions for yaque

When writing or modifying tests in this project, follow these conventions strictly.

## Framework

- Use `unittest.TestCase` as the base class for all test classes.
- Import `unittest` — do NOT use bare `assert` statements or `pytest`-specific features.
- Files run with `pytest` as the test runner, but all assertions use `unittest.TestCase` methods.

## Assertion Style

Always use `self.assertEqual` and friends with a descriptive message as the last argument:

```python
self.assertEqual(actual, expected, 'description of what is being checked')
self.assertIsNone(value, 'should return None when not found')
self.assertTrue(condition, 'description')
self.assertFalse(condition, 'description')
self.assertIn(item, collection, 'item should be in collection')
self.assertNotIn(item, collection, 'item should not be in collection')
self.assertGreater(a, b, 'a should be greater than b')
self.assertGreaterEqual(a, b, 'a should be >= b')
self.assertLess(a, b, 'a should be less than b')
self.assertLessEqual(a, b, 'a should be <= b')
self.assertNotEqual(a, b, 'values should differ')
self.assertRaises(ExceptionType, msg='should raise on invalid input')
```

**NEVER** use bare `assert` like `assert x == y`. Always use `self.assertXxx(...)`.

The descriptive message should be short and explain the intent, not restate the code:
- Good: `'best time should be 45000'`
- Bad: `'assertEqual failed for best time'`

## Parametrized Tests

Do NOT use `@pytest.mark.parametrize`. Instead, use `self.subTest`:

```python
def test_something_for_all_sizes(self):
    for size in [6, 7, 8]:
        with self.subTest(size=size):
            game = Game(size, max_solutions=10)
            self.assertEqual(len(game.queens), size, f'{size}x{size} queen count')
```

## Test Structure

- Group related tests in a `class` inheriting from `unittest.TestCase`.
- Use `setUp` and `tearDown` for shared setup/cleanup (not `@pytest.fixture`).
- Each test method starts with `test_` and has a docstring.
- Use helper methods on the class for shared logic (e.g., `make_marks`, `find_conflicts`).

```python
class TestSomething(unittest.TestCase):
    """Test group description."""

    def setUp(self):
        self.resource = create_resource()

    def tearDown(self):
        cleanup(self.resource)

    def test_behavior(self):
        """Should do the expected thing."""
        result = do_thing()
        self.assertEqual(result, expected, 'description')
```

## File Layout

```python
"""Module docstring describing what is tested."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from module_under_test import thing_to_test


class TestGroupName(unittest.TestCase):
    """Description of test group."""
    ...


if __name__ == "__main__":
    unittest.main()
```

## Keeping Tests Compact

- **Combine tests with the same setup.** If multiple test methods create the same object or state before asserting, merge them into one test with multiple assertions. One test function can verify several properties of the same result.

```python
# Bad: two tests that both create the same game
def test_queens_count(self):
    game = Game(7, max_solutions=10)
    self.assertEqual(len(game.queens), 7, 'queen count')

def test_queens_one_per_row(self):
    game = Game(7, max_solutions=10)
    rows = [r for r, c in game.queens]
    self.assertEqual(sorted(rows), list(range(7)), 'one per row')

# Good: one test, same setup, multiple assertions
def test_queen_placement(self):
    game = Game(7, max_solutions=10)
    self.assertEqual(len(game.queens), 7, 'queen count')
    rows = [r for r, c in game.queens]
    self.assertEqual(sorted(rows), list(range(7)), 'one per row')
```

- **Avoid overlapping tests.** Don't test the same behavior in multiple places. If `test_encode_decode_roundtrip` already covers all sizes via `subTest`, don't also have individual `test_encode_6x6`, `test_encode_7x7` etc. Each behavior should be tested exactly once.

- **Use `subTest` to compress parametric cases** rather than writing separate methods per input value.

## Mocking

Use `unittest.mock.patch` for mocking. Prefer `@patch` decorator on individual test methods when the mock is needed during method execution (e.g., `date.today()`). Use `with patch(...)` context manager in helpers when the mock is only needed during setup.

## What NOT to Do

- Do NOT use `pytest.raises` — use `self.assertRaises`
- Do NOT use `pytest.fixture` — use `setUp`/`tearDown`
- Do NOT use `pytest.mark.parametrize` — use `self.subTest`
- Do NOT use bare `assert` — use `self.assertXxx`
- Do NOT import `pytest` at all
- Do NOT skip the descriptive message argument on assertions
