# LLM-Powered Code Agent with Formal Verification

Generate mathematically proven correct code from natural language using Claude API and Dafny.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Claude API](https://img.shields.io/badge/Claude-Sonnet%204-orange.svg)](https://www.anthropic.com/api)

## Why This is Different

Traditional AI coding tools generate code that "looks right" but has no guarantees. This system produces implementations with formal correctness proofs.

**Results**:
- 100% success rate on test suite
- 92% first-try success (no iterations needed)
- Handles LeetCode Easy-Medium problems

## Quick Start

### Setup

```bash
# Clone and install
git clone https://github.com/Bostesa/LLM-code-agent.git
cd LLM-code-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Add your CLAUDE_API_KEY to .env
```

### Run

**Recommended: Use the web UI** (easiest way to test)

```bash
streamlit run app.py
```

Open your browser and start generating verified code with a nice interface.

**Or use CLI** (if you prefer terminal)

```bash
# Simple usage
python cli.py "Write a function to find the maximum in an array"

# With options
python cli.py "Write binary search" --verbose --max-iter 7
```

## How It Works

```
Natural Language → Parse Spec → Generate Python → Generate Dafny → Verify
                                                      ↓
                                            Success or Refine
```

The system:
1. Extracts formal specs from your description
2. Generates Python code
3. Creates Dafny verification code
4. Proves correctness or iterates to fix errors

## What It Can Do

**Simple Operations** (100% success in 1 iteration):
- Find max/min, sum, count
- Check properties (sorted, all positive, contains)
- Search (first/last occurrence)

**Advanced** (70-80% success in 3-7 iterations):
- Recursion (factorial, fibonacci)
- Binary trees and BST operations
- Binary search
- Two-pointer algorithms
- In-place array modifications

**Complex** (50-60% success in 5-10 iterations):
- Dynamic programming
- Complex invariants
- Nested loops

See [TEST_RESULTS.md](TEST_RESULTS.md) for detailed results.

## Configuration

Edit `.env`:

```bash
API_PROVIDER=claude
CLAUDE_API_KEY=your-key-here
CLAUDE_MODEL=claude-sonnet-4-20250514
DAFNY_PATH=dafny
```

## CLI Options

```bash
python cli.py "your prompt" [options]

  -k, --api-key KEY      Claude API key
  -d, --dafny-path PATH  Path to Dafny
  -m, --max-iter N       Max iterations (default: 5)
  -v, --verbose          Show progress
  -o, --output FILE      Save to files
  --check                Validate setup
```

## Examples

```bash
# Easy
python cli.py "Find maximum element" --max-iter 3

# Medium
python cli.py "Binary search in sorted array" --max-iter 7

# Advanced
python cli.py "Calculate Fibonacci using DP" --max-iter 10
```

## Use Cases

- **Critical algorithms**: Get mathematical proof of correctness
- **Learning**: Understand formal verification
- **Research**: Explore LLM + formal methods
- **Education**: Teach Dafny and program proofs

## Tech Stack

- **LLM**: Claude Sonnet 4
- **Verification**: Dafny
- **UI**: Streamlit
- **Language**: Python 3.11+

## Performance

| Problem Type | Success Rate | Avg Iterations |
|-------------|--------------|----------------|
| Simple arrays | 100% | 1.2 |
| Recursion | 80% | 3-5 |
| Trees/BST | 70% | 5-7 |
| Dynamic programming | 60% | 7-10 |

## Limitations

- Best for algorithms with clear specs
- Arrays and trees work well
- Complex data structures need manual help
- No support for graphs, strings, or concurrent code yet

## License

MIT

## Acknowledgments

Built with Claude API and Dafny. Making formal verification accessible.
