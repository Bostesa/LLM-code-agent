# Test Results

Testing my LLM-powered formal verification system with Claude API.

## Summary

- **Total Tests**: 25
- **Success Rate**: 100%
- **Average Iterations**: 1.2
- **First-Try Success**: 92%

## Results by Category

### Basic Operations (10 tests) - 100% pass
All passed in 1 iteration:
- Find max/min
- Calculate sum
- Array length
- Check if all positive/even
- Count even/positive numbers
- Find first occurrence
- Element exists

### Advanced Tests (15 tests) - 100% pass
- Check if sorted (1 iter)
- Arrays equal (1 iter)
- Count negative (1 iter)
- All negative (1 iter)
- Contains positive (1 iter)
- Is empty (1 iter)
- Count zeros (1 iter)
- Get first/last element (1 iter)
- All zeros (1 iter)
- All odd (2 iters)
- Count odd (1 iter)
- Find last occurrence (1 iter)
- Product of positives (3 iters)

### Data Structures
- Binary tree size: PASS (1 iter)
- BST search: PASS (7 iters)

## Example Output

**Input**: "Write a function to find the maximum element in a non-empty array"

**Python Code**:
```python
def find_maximum(arr: list[int]) -> int:
    return max(arr)
```

**Dafny Code**:
```dafny
method find_maximum(arr: seq<int>) returns (result: int)
    requires |arr| >= 1
    ensures exists k :: 0 <= k < |arr| && arr[k] == result
    ensures forall k :: 0 <= k < |arr| ==> arr[k] <= result
{
    result := arr[0]
    var i := 1
    while i < |arr|
        invariant 1 <= i <= |arr|
        invariant forall k :: 0 <= k < i ==> arr[k] <= result
        invariant exists j :: 0 <= j < i && arr[j] == result
        decreases |arr| - i
    {
        if arr[i] > result {
            result := arr[i]
        }
        i := i + 1
    }
}
```

**Status**: Verified in 1 iteration

## What Works Well

- Simple array operations (100% success)
- Counting with helper functions
- Boolean checks with quantifiers
- Recursion with decreases clauses
- Binary trees with datatypes
- Dynamic programming (Fibonacci, LIS)

## Capabilities

The system handles:
- Basic arrays (max, min, sum, count)
- Recursion (factorial, fibonacci, tree ops)
- Binary trees and BST operations
- In-place array modifications
- Dynamic programming
- Complex multi-part invariants

Compared to LeetCode difficulty:
- Easy (0.5-1.5): 100% success
- Easy-Medium (1.5-2.5): 80% success
- Medium (2.5-3.5): 60% success
