"""error analyzer using claude"""
import os
from typing import Optional
from ..models.specifications import VerificationResult
from ..utils.claude_utils import call_claude

class ErrorAnalyzer:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or os.getenv("CLAUDE_API_KEY")
        self.model_name = model_name or os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")

    def analyze(self, dafny_code: str, result: VerificationResult) -> str:
        if result.success:
            return "Verification succeeded!"
        errors_str = "\n".join([f"{e.error_type}: {e.message}" for e in result.errors])
        prompt = f"""You are a Dafny verification expert. Analyze these errors and provide SPECIFIC, ACTIONABLE fixes.

**Dafny Code:**
```dafny
{dafny_code}
```

**Verification Errors:**
{errors_str}

**Common Error Patterns & Fixes:**

1. **"This invariant might not hold on entry"**
   - Fix: Check if invariant is true BEFORE the loop starts
   - Example: If invariant says `i > 0` but `i := 0`, change invariant to `i >= 0`

2. **"This invariant might not be maintained"**
   - Fix: Check if invariant stays true AFTER each loop iteration
   - Example: Add missing invariant that connects loop variable to result

3. **"This postcondition might not hold"**
   - Fix: Add loop invariant that directly implies the postcondition
   - Example: If postcondition needs `result == sum(arr)`, add invariant `result == sum(arr[0..i])`

4. **"This precondition might not hold"**
   - Fix: Add `requires` clause or ensure the condition before calling

5. **Syntax errors ("symbol not expected")**
   - Use `seq<T>` not `array<T>`
   - Use `|s|` not `len(s)` or `s.Length`
   - Use `:=` not `=`
   - Use `method` not `def`

6. **"Assertion might not hold"**
   - Fix: Add helper function to make property provable
   - Or: Add intermediate assertions to guide the verifier

**Your Analysis:**

1. **Root Cause:** [What's the actual problem - be specific about which line/invariant]

2. **Specific Fix:** [Exact code change needed - show the corrected invariant/postcondition]

3. **Why This Works:** [Brief explanation of why this fix will make verification pass]

Be concise and actionable. Focus on the EXACT change needed."""
        return call_claude(prompt, self.api_key, self.model_name, temperature=0.2, max_tokens=2048)
