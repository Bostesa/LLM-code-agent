"""
demo script for the formal verification system

run this to test it out with some examples
"""
import os
from dotenv import load_dotenv
from src.agents.orchestrator import VerificationOrchestrator

# Load environment variables
load_dotenv()


def print_separator():
    """just prints a line to separate stuff"""
    print("\n" + "="*80 + "\n")


def print_result(result):
    """print the verification result nicely"""
    print(f"\n{'='*80}")
    print(f"VERIFICATION RESULT")
    print(f"{'='*80}")

    if result.verified:
        print("✅ STATUS: VERIFIED - Code is mathematically proven correct!")
    else:
        print("❌ STATUS: FAILED")
        if result.error_message:
            print(f"Error: {result.error_message}")

    print(f"\nIterations: {result.total_iterations}")

    if result.specification:
        spec = result.specification
        print(f"\nFunction: {spec.function_name}")
        print(f"Parameters: {', '.join([f'{p.name}: {p.type}' for p in spec.parameters])}")
        print(f"Returns: {spec.return_type}")

    if result.python_code:
        print(f"\n{'='*80}")
        print("PYTHON CODE:")
        print(f"{'='*80}")
        print(result.python_code)

    if result.dafny_code:
        print(f"\n{'='*80}")
        print("DAFNY CODE:")
        print(f"{'='*80}")
        print(result.dafny_code)

    # Show iteration history
    if result.attempts:
        print(f"\n{'='*80}")
        print("ITERATION HISTORY:")
        print(f"{'='*80}")
        for attempt in result.attempts:
            status = "✅ Success" if attempt.result.success else "❌ Failed"
            print(f"\nAttempt {attempt.attempt_number}: {status}")
            if not attempt.result.success:
                print(f"  Errors: {len(attempt.result.errors)}")
                for error in attempt.result.errors[:3]:  # just show first 3
                    print(f"    - {error.error_type}: {error.message[:80]}...")


def run_example(orchestrator, description, name):
    """run one example"""
    print(f"\n{'='*80}")
    print(f"EXAMPLE: {name}")
    print(f"{'='*80}")
    print(f"Description: {description}")
    print(f"{'='*80}")

    result = orchestrator.generate_verified_code(description, verbose=True)
    print_result(result)

    return result


def main():
    """runs the demo examples"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║           LLM-POWERED FORMAL VERIFICATION SYSTEM - DEMO                      ║
║                                                                              ║
║           Generate mathematically proven correct code                        ║
║                     from natural language                                    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    # Check for API key
    api_key = os.getenv("CLAUDE_API_KEY")
    if not api_key:
        print("❌ ERROR: CLAUDE_API_KEY not found in environment variables")
        print("\nPlease set your API key:")
        print("  1. Create a .env file in the project root")
        print("  2. Add: CLAUDE_API_KEY=your_api_key_here")
        print("\nOr set it directly:")
        print("  export CLAUDE_API_KEY=your_api_key_here")
        return

    print("✓ API Key found")

    # start up the orchestrator
    print("\n[Initializing system...]")
    model_name = os.getenv("CLAUDE_MODEL")
    try:
        orchestrator = VerificationOrchestrator(
            api_key=api_key,
            model_name=model_name,
            max_iterations=5
        )
        print("✓ Orchestrator initialized")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return

    # make sure everything works
    print("\n[Validating setup...]")
    status = orchestrator.validate_setup()

    if status['dafny']['ok']:
        print(f"✓ Dafny: {status['dafny'].get('version', 'OK')}")
    else:
        print(f"❌ Dafny: {status['dafny']['error']}")
        print("\nPlease install Dafny:")
        print("  Download from: https://github.com/dafny-lang/dafny/releases")
        return

    if status.get('claude_api', {}).get('ok'):
        print("✓ Claude API: Connected")
    else:
        error = status.get('claude_api', {}).get('error', 'Unknown error')
        print(f"❌ Claude API: {error}")
        return

    print_separator()

    # run example 1
    print("\n🚀 Starting Example 1: Find Maximum")
    result1 = run_example(
        orchestrator,
        "Write a function that finds the maximum element in a non-empty array",
        "Find Maximum Element"
    )

    input("\n\nPress Enter to continue to next example...")

    # run example 2
    print_separator()
    print("\n🚀 Starting Example 2: Linear Search")
    result2 = run_example(
        orchestrator,
        "Write a function that searches for a target value in an array and returns its index, or -1 if not found",
        "Linear Search"
    )

    input("\n\nPress Enter to continue to next example...")

    # run example 3
    print_separator()
    print("\n🚀 Starting Example 3: Binary Search")
    result3 = run_example(
        orchestrator,
        "Write a binary search function that finds an element in a sorted array",
        "Binary Search"
    )

    # show summary at the end
    print_separator()
    print("\n📊 DEMO SUMMARY")
    print("="*80)

    examples = [
        ("Find Maximum", result1),
        ("Linear Search", result2),
        ("Binary Search", result3),
    ]

    verified_count = sum(1 for _, r in examples if r.verified)
    total_iterations = sum(r.total_iterations for _, r in examples)

    print(f"\nExamples run: {len(examples)}")
    print(f"Successfully verified: {verified_count}/{len(examples)}")
    print(f"Total iterations: {total_iterations}")
    print(f"Average iterations: {total_iterations/len(examples):.1f}")

    print("\n" + "="*80)
    for name, result in examples:
        status = "✅ VERIFIED" if result.verified else "❌ FAILED"
        print(f"{name:20} {status:15} ({result.total_iterations} iterations)")

    print("\n" + "="*80)
    print("\n✨ Demo complete! The verified code has mathematical guarantees of correctness.")
    print("\n💡 Try the Streamlit UI for an interactive experience:")
    print("   streamlit run app.py")
    print("\n")


if __name__ == "__main__":
    main()
