"""Dafny Generator using Claude"""
import os
from typing import Optional
from ..models.specifications import FormalSpecification
from ..utils.claude_utils import call_claude

class DafnyCodeGenerator:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or os.getenv("CLAUDE_API_KEY")
        self.model_name = model_name or os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")

    def generate(self, spec: FormalSpecification, python_code: str) -> str:
        prompt = f"""You are a Dafny expert. Generate verified Dafny code for this specification.

**Target Function:** {spec.function_name}

**Python Implementation:**
```python
{python_code}
```

**Preconditions:** {spec.preconditions}
**Postconditions:** {spec.postconditions}

**CRITICAL Dafny Guidelines:**

1. **Use `seq<T>` not `array<T>`** - Sequences are easier to verify
2. **Use `|s|` for length** - Not `s.Length` or `len(s)`
3. **Loop invariants must:**
   - Bound all variables: `0 <= i <= |arr|`
   - State what's proven so far: `forall k :: 0 <= k < i ==> ...`
   - Connect to postconditions
   - Include a `decreases` clause: `decreases |arr| - i`

4. **Use helper functions for complex postconditions:**
   ```dafny
   function sum(s: seq<int>, n: int): int
       requires 0 <= n <= |s|
   {{
       if n == 0 then 0 else sum(s, n-1) + s[n-1]
   }}
   ```

5. **Common patterns:**
   - **Find max:** `forall k :: 0 <= k < |arr| ==> arr[k] <= result`
   - **Element exists:** `exists k :: 0 <= k < |arr| && arr[k] == result`
   - **All elements satisfy:** `forall k :: 0 <= k < |arr| ==> P(arr[k])`

6. **For early returns:** Just use `return;` (Dafny will verify postconditions)

7. **No Python syntax!** Use:
   - `method` not `def`
   - `returns (result: T)` not `-> T`
   - `:=` not `=`
   - `==` for equality, `!=` for inequality
   - `&&` for and, `||` for or
   - `==>` for implies
   - `<==>`for if and only if

**Example 1 - Find Maximum:**
```dafny
method FindMax(arr: seq<int>) returns (result: int)
    requires |arr| >= 1
    ensures exists k :: 0 <= k < |arr| && arr[k] == result
    ensures forall k :: 0 <= k < |arr| ==> arr[k] <= result
{{
    result := arr[0];
    var i := 1;
    while i < |arr|
        invariant 1 <= i <= |arr|
        invariant forall k :: 0 <= k < i ==> arr[k] <= result
        invariant exists j :: 0 <= j < i && arr[j] == result
        decreases |arr| - i
    {{
        if arr[i] > result {{
            result := arr[i];
        }}
        i := i + 1;
    }}
}}
```

**Example 2 - Count Elements (Simple Version):**
```dafny
function CountPositive(s: seq<int>, n: int): int
    requires 0 <= n <= |s|
{{
    if n == 0 then 0
    else if s[n-1] > 0 then CountPositive(s, n-1) + 1
    else CountPositive(s, n-1)
}}

method CountPositiveNumbers(arr: seq<int>) returns (count: int)
    ensures count >= 0 && count <= |arr|
    ensures count == CountPositive(arr, |arr|)
{{
    count := 0;
    var i := 0;
    while i < |arr|
        invariant 0 <= i <= |arr|
        invariant 0 <= count <= i
        invariant count == CountPositive(arr, i)
        decreases |arr| - i
    {{
        if arr[i] > 0 {{
            count := count + 1;
        }}
        i := i + 1;
    }}
}}
```

**Example 3 - Product (Multiplication):**
```dafny
function ProductOfPositive(s: seq<int>, n: int): int
    requires 0 <= n <= |s|
{{
    if n == 0 then 1
    else if s[n-1] > 0 then ProductOfPositive(s, n-1) * s[n-1]
    else ProductOfPositive(s, n-1)
}}

method product_of_positive_numbers(arr: seq<int>) returns (result: int)
    ensures result == ProductOfPositive(arr, |arr|)
    ensures result >= 1
{{
    result := 1;
    var i := 0;
    while i < |arr|
        invariant 0 <= i <= |arr|
        invariant result >= 1
        invariant result == ProductOfPositive(arr, i)
        decreases |arr| - i
    {{
        if arr[i] > 0 {{
            result := result * arr[i];
        }}
        i := i + 1;
    }}
}}
```

**Example 4 - Recursion with Decreases:**
```dafny
function Factorial(n: nat): nat
    decreases n
{{
    if n == 0 then 1 else n * Factorial(n-1)
}}

method FactorialIterative(n: nat) returns (result: nat)
    ensures result == Factorial(n)
{{
    result := 1;
    var i := 0;
    while i < n
        invariant 0 <= i <= n
        invariant result == Factorial(i)
        decreases n - i
    {{
        i := i + 1;
        result := result * i;
    }}
}}
```

**Example 5 - Binary Search (Recursive):**
```dafny
function method BinarySearch(arr: seq<int>, target: int, low: int, high: int): int
    requires 0 <= low <= high <= |arr|
    requires forall i,j :: 0 <= i < j < |arr| ==> arr[i] <= arr[j]  // sorted
    decreases high - low
{{
    if low >= high then -1
    else
        var mid := (low + high) / 2;
        if arr[mid] == target then mid
        else if arr[mid] < target then BinarySearch(arr, target, mid+1, high)
        else BinarySearch(arr, target, low, mid)
}}
```

**Example 6 - Two Pointers (Partition):**
```dafny
method Partition(arr: seq<int>, pivot: int) returns (left: seq<int>, right: seq<int>)
    ensures forall x :: x in left ==> x <= pivot
    ensures forall x :: x in right ==> x > pivot
    ensures |left| + |right| == |arr|
    ensures multiset(left) + multiset(right) == multiset(arr)
{{
    left := [];
    right := [];
    var i := 0;
    while i < |arr|
        invariant 0 <= i <= |arr|
        invariant forall x :: x in left ==> x <= pivot
        invariant forall x :: x in right ==> x > pivot
        invariant |left| + |right| == i
        invariant multiset(left) + multiset(right) == multiset(arr[..i])
        decreases |arr| - i
    {{
        if arr[i] <= pivot {{
            left := left + [arr[i]];
        }} else {{
            right := right + [arr[i]];
        }}
        i := i + 1;
    }}
}}
```

**Example 7 - Remove Duplicates (Two Pointers):**
```dafny
method RemoveDuplicates(arr: seq<int>) returns (result: seq<int>)
    requires forall i,j :: 0 <= i < j < |arr| ==> arr[i] <= arr[j]  // sorted
    ensures forall i,j :: 0 <= i < j < |result| ==> result[i] < result[j]  // strictly increasing
    ensures forall x :: x in result ==> x in arr
    ensures forall x :: x in arr ==> x in result
{{
    if |arr| == 0 {{
        return [];
    }}

    result := [arr[0]];
    var i := 1;
    while i < |arr|
        invariant 1 <= i <= |arr|
        invariant |result| >= 1
        invariant result[|result|-1] == arr[i-1] || result[|result|-1] < arr[i-1]
        invariant forall j,k :: 0 <= j < k < |result| ==> result[j] < result[k]
        invariant forall x :: x in result ==> x in arr[..i]
        decreases |arr| - i
    {{
        if arr[i] != arr[i-1] {{
            result := result + [arr[i]];
        }}
        i := i + 1;
    }}
}}
```

**CRITICAL Advanced Patterns:**

**For Recursion:**
- ALWAYS include `decreases` clause showing what gets smaller
- Base case first: `if n == 0 then ...`
- Recursive case: function calls itself with smaller input

**For Two Pointers:**
- Maintain invariants for BOTH pointers
- Show relationship between pointers: `0 <= left <= right <= |arr|`
- Prove partitioning property: elements before/after pointers satisfy different conditions

**For Multiset (permutations):**
- Use `multiset(arr)` to prove rearrangement preserves elements
- `multiset(left) + multiset(right) == multiset(arr)` proves partition is valid

**For Sorted Arrays:**
- `forall i,j :: 0 <= i < j < |arr| ==> arr[i] <= arr[j]` means sorted
- `forall i,j :: 0 <= i < j < |arr| ==> arr[i] < arr[j]` means strictly increasing

**Example 8 - In-Place Modification (Reverse Array):**
```dafny
method ReverseArray(arr: array<int>)
    requires arr.Length > 0
    modifies arr
    ensures forall i :: 0 <= i < arr.Length ==> arr[i] == old(arr[arr.Length - 1 - i])
{{
    var left := 0;
    var right := arr.Length - 1;

    while left < right
        invariant 0 <= left <= right + 1 <= arr.Length
        invariant forall i :: 0 <= i < left ==> arr[i] == old(arr[arr.Length - 1 - i])
        invariant forall i :: right < i < arr.Length ==> arr[i] == old(arr[arr.Length - 1 - i])
        invariant forall i :: left <= i <= right ==> arr[i] == old(arr[i])
        decreases right - left
    {{
        var temp := arr[left];
        arr[left] := arr[right];
        arr[right] := temp;
        left := left + 1;
        right := right - 1;
    }}
}}
```

**Example 9 - Binary Tree (Data Structure):**
```dafny
datatype Tree = Leaf | Node(value: int, left: Tree, right: Tree)

function TreeSize(t: Tree): nat
{{
    match t
    case Leaf => 0
    case Node(_, left, right) => 1 + TreeSize(left) + TreeSize(right)
}}

function TreeContains(t: Tree, x: int): bool
{{
    match t
    case Leaf => false
    case Node(v, left, right) => v == x || TreeContains(left, x) || TreeContains(right, x)
}}

predicate IsBST(t: Tree)
{{
    match t
    case Leaf => true
    case Node(v, left, right) =>
        IsBST(left) && IsBST(right) &&
        (forall x :: TreeContains(left, x) ==> x < v) &&
        (forall x :: TreeContains(right, x) ==> x > v)
}}

method FindInBST(t: Tree, target: int) returns (found: bool)
    requires IsBST(t)
    ensures found <==> TreeContains(t, target)
    decreases TreeSize(t)
{{
    match t
    case Leaf => found := false;
    case Node(v, left, right) =>
        if v == target {{
            found := true;
        }} else if target < v {{
            found := FindInBST(left, target);
        }} else {{
            found := FindInBST(right, target);
        }}
}}
```

**Example 10 - Linked List (Class-based):**
```dafny
class Node {{
    var data: int
    var next: Node?

    constructor(d: int)
        ensures data == d
        ensures next == null
    {{
        data := d;
        next := null;
    }}
}}

method FindInList(head: Node?, target: int) returns (found: bool)
    decreases *
{{
    var current := head;
    found := false;

    while current != null
        decreases *
    {{
        if current.data == target {{
            found := true;
            return;
        }}
        current := current.next;
    }}
}}
```

**CRITICAL for In-Place Modifications:**
- Use `array<T>` not `seq<T>` for mutable arrays
- Add `modifies arr` to declare mutation
- Use `old(arr[i])` to refer to original values
- Invariants must relate current state to `old()` state
- Use two-pointer technique with swap for reversals/partitions

**CRITICAL for Data Structures:**

**For Trees:**
- Use `datatype Tree = Leaf | Node(...)` for immutable trees
- Use `match` expressions to handle cases
- Define helper functions: `TreeSize`, `TreeContains`, `TreeHeight`
- For BST: predicate `IsBST` checks ordering property recursively
- `decreases TreeSize(t)` for termination

**For Linked Lists:**
- Use `class Node` with nullable references (`Node?`)
- Add `decreases *` for unknown termination (when cycles possible)
- Be careful with null checks before accessing fields
- For length/contains: simple while loop with null check

**For Graphs:**
- Model as `seq<seq<int>>` (adjacency matrix)
- Or as `seq<set<int>>` (adjacency list)
- Invariants track visited nodes and connectivity

**Example 11 - Dynamic Programming (Fibonacci with Memoization):**
```dafny
function Fib(n: nat): nat
    decreases n
{{
    if n <= 1 then n
    else Fib(n-1) + Fib(n-2)
}}

method FibonacciDP(n: nat) returns (result: nat)
    ensures result == Fib(n)
{{
    if n <= 1 {{
        return n;
    }}

    var dp := new nat[n+1];
    dp[0] := 0;
    dp[1] := 1;

    var i := 2;
    while i <= n
        invariant 2 <= i <= n + 1
        invariant forall j :: 0 <= j < i ==> dp[j] == Fib(j)
        decreases n - i
    {{
        dp[i] := dp[i-1] + dp[i-2];
        i := i + 1;
    }}

    result := dp[n];
}}
```

**Example 12 - Dynamic Programming (Longest Increasing Subsequence):**
```dafny
method LongestIncreasingSubsequence(arr: seq<int>) returns (length: nat)
    ensures length >= 0
    ensures length <= |arr|
{{
    if |arr| == 0 {{
        return 0;
    }}

    var dp := new nat[|arr|];
    var i := 0;

    while i < |arr|
        invariant 0 <= i <= |arr|
        invariant forall k :: 0 <= k < i ==> dp[k] >= 1
        decreases |arr| - i
    {{
        dp[i] := 1;
        var j := 0;

        while j < i
            invariant 0 <= j <= i
            invariant dp[i] >= 1
            decreases i - j
        {{
            if arr[j] < arr[i] && dp[j] + 1 > dp[i] {{
                dp[i] := dp[j] + 1;
            }}
            j := j + 1;
        }}

        i := i + 1;
    }}

    length := 0;
    i := 0;
    while i < |arr|
        invariant 0 <= i <= |arr|
        invariant forall k :: 0 <= k < |arr| ==> length >= dp[k] || length >= 0
        decreases |arr| - i
    {{
        if dp[i] > length {{
            length := dp[i];
        }}
        i := i + 1;
    }}
}}
```

**Example 13 - Complex Multi-Part Invariants (Partition with Counters):**
```dafny
method PartitionCounting(arr: seq<int>, pivot: int) returns (lessCount: nat, equalCount: nat, greaterCount: nat)
    ensures lessCount + equalCount + greaterCount == |arr|
    ensures lessCount == |seq i | 0 <= i < |arr| && arr[i] < pivot|
    ensures equalCount == |seq i | 0 <= i < |arr| && arr[i] == pivot|
    ensures greaterCount == |seq i | 0 <= i < |arr| && arr[i] > pivot|
{{
    lessCount := 0;
    equalCount := 0;
    greaterCount := 0;
    var i := 0;

    while i < |arr|
        invariant 0 <= i <= |arr|
        invariant lessCount + equalCount + greaterCount == i
        invariant lessCount == |seq j | 0 <= j < i && arr[j] < pivot|
        invariant equalCount == |seq j | 0 <= j < i && arr[j] == pivot|
        invariant greaterCount == |seq j | 0 <= j < i && arr[j] > pivot|
        decreases |arr| - i
    {{
        if arr[i] < pivot {{
            lessCount := lessCount + 1;
        }} else if arr[i] == pivot {{
            equalCount := equalCount + 1;
        }} else {{
            greaterCount := greaterCount + 1;
        }}
        i := i + 1;
    }}
}}
```

**CRITICAL for Dynamic Programming:**

**DP Table as Array:**
- Use `var dp := new T[n+1]` for mutable DP table
- Index represents subproblem size
- `modifies dp` in method signature if needed

**Key DP Invariant Pattern:**
```dafny
invariant forall j :: 0 <= j < i ==> dp[j] == OptimalSolution(j)
```
This says: "All DP entries computed so far are correct"

**Optimal Substructure:**
- Define recursive function for optimal solution
- Prove iterative DP matches recursive definition
- `ensures result == OptimalFunction(n)`

**Common DP Patterns:**
1. **Fibonacci-style**: `dp[i] = dp[i-1] + dp[i-2]`
2. **Nested loops**: Outer loop for position, inner for choices
3. **Max/Min tracking**: Update `maxVal` alongside DP table
4. **Backtracking**: Store choices in separate array

**For Memoization:**
- Arrays naturally memoize (store computed values)
- Invariant proves values only computed once
- Access `dp[j]` for `j < i` is safe (already computed)

**CRITICAL for Very Complex Invariants:**

**Multi-Part Invariants:**
Break into multiple `invariant` lines:
```dafny
invariant 0 <= i <= n              // bounds
invariant sum == Sum(arr, i)       // accumulator correctness
invariant count <= i               // derived property
invariant forall j :: 0 <= j < i ==> P(j)  // universal property
```

**Relating Multiple Variables:**
```dafny
invariant left + right == i                    // partition
invariant 0 <= left <= i && 0 <= right <= i   // bounds
invariant sum == leftSum + rightSum            // conservation
```

**Using Helper Predicates:**
```dafny
predicate Valid(arr: seq<int>, i: int)
{{
    0 <= i < |arr| && arr[i] > 0
}}

// In loop:
invariant forall j :: 0 <= j < i ==> Valid(arr, j)
```

**Quantifier Tips:**
- `forall j :: 0 <= j < i ==> ...` for "all elements before i"
- `exists j :: 0 <= j < i && ...` for "some element before i"
- Use `==>` (implies) after quantifier bounds
- Use `&&` for additional conditions

**If Verification Fails After Many Iterations:**
1. Add intermediate assertions: `assert P;` to guide verifier
2. Split complex invariant into multiple simpler ones
3. Add helper functions to abstract complex properties
4. Use `calc` for multi-step reasoning
5. Consider simplifying the algorithm

Now generate the Dafny code. Return ONLY the Dafny code, no explanations."""
        code = call_claude(prompt, self.api_key, self.model_name, temperature=0.2, max_tokens=4096)
        return code.strip().replace("```dafny","").replace("```","").strip()
