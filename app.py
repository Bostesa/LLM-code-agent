"""
streamlit web UI for the formal verification system
"""
import streamlit as st
import os
from dotenv import load_dotenv

from src.agents.orchestrator import VerificationOrchestrator

# load environment variables
load_dotenv()

# page setup
st.set_page_config(
    page_title="LLM Formal Verifier",
    page_icon="✓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# custom styling
st.markdown("""
<style>
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        margin: 1rem 0;
    }
    .verified-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        background-color: #28a745;
        color: white;
        border-radius: 0.25rem;
        font-weight: bold;
        font-size: 0.875rem;
    }
</style>
""", unsafe_allow_html=True)

# set up session state
if 'orchestrator' not in st.session_state:
    st.session_state.orchestrator = None
if 'result' not in st.session_state:
    st.session_state.result = None
if 'setup_validated' not in st.session_state:
    st.session_state.setup_validated = False

# title
st.title("🔍 LLM-Powered Formal Verification")
st.markdown("Generate **mathematically proven** correct code from natural language")

# sidebar config
with st.sidebar:
    st.header("⚙️ Configuration")

    # API key input
    api_key = st.text_input(
        "Claude API Key",
        type="password",
        value=os.getenv("CLAUDE_API_KEY", ""),
        help="Enter your Anthropic Claude API key"
    )

    # dafny path
    dafny_path = st.text_input(
        "Dafny Path",
        value="dafny",
        help="Path to Dafny executable (or 'dafny' if in PATH)"
    )

    # max iterations slider
    max_iterations = st.slider(
        "Max Refinement Iterations",
        min_value=1,
        max_value=10,
        value=5,
        help="Maximum attempts to refine code if verification fails"
    )

    st.divider()

    # button to validate setup
    if st.button("🔍 Validate Setup"):
        with st.spinner("Validating setup..."):
            try:
                orchestrator = VerificationOrchestrator(
                    api_key=api_key,
                    dafny_path=dafny_path,
                    max_iterations=max_iterations
                )
                status = orchestrator.validate_setup()

                st.session_state.orchestrator = orchestrator
                st.session_state.setup_validated = True

                # show status
                st.success("Setup validated!")
                if status['dafny']['ok']:
                    st.info(f"✓ Dafny: {status['dafny'].get('version', 'OK')}")
                else:
                    st.error(f"✗ Dafny: {status['dafny']['error']}")

                if status.get('claude_api', {}).get('ok'):
                    st.info("✓ Claude API: Connected")
                elif status.get('gemini_api', {}).get('ok'):
                    st.info("✓ API: Connected")
                else:
                    error = status.get('claude_api', {}).get('error') or status.get('gemini_api', {}).get('error', 'Unknown error')
                    st.error(f"✗ API: {error}")

            except Exception as e:
                st.error(f"Setup validation failed: {e}")
                st.session_state.setup_validated = False

    st.divider()

    # some example prompts
    st.header("📝 Example Prompts")
    if st.button("Find Maximum", use_container_width=True):
        st.session_state.example_prompt = "Write a function that finds the maximum element in a non-empty array"
    if st.button("Binary Search", use_container_width=True):
        st.session_state.example_prompt = "Write a binary search that finds an element in a sorted array"
    if st.button("Linear Search", use_container_width=True):
        st.session_state.example_prompt = "Write a function that searches for a target value in an array and returns its index"

# main content area
tab1, tab2, tab3 = st.tabs(["🚀 Generate", "📊 Results", "ℹ️ About"])

with tab1:
    st.header("Generate Verified Code")

    # text input area
    user_input = st.text_area(
        "Describe the function you want to create:",
        value=st.session_state.get('example_prompt', ''),
        height=150,
        placeholder="Example: Write a function that finds the maximum element in a non-empty array",
        key="user_input"
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        generate_button = st.button("🚀 Generate & Verify", type="primary", use_container_width=True)

    if generate_button:
        if not api_key:
            st.error("Please enter your Claude API key in the sidebar")
        elif not user_input.strip():
            st.error("Please enter a function description")
        else:
            try:
                # set up orchestrator if needed
                if not st.session_state.orchestrator:
                    # get model name
                    import os
                    model_name = os.getenv("CLAUDE_MODEL")

                    st.session_state.orchestrator = VerificationOrchestrator(
                        api_key=api_key,
                        model_name=model_name,
                        dafny_path=dafny_path,
                        max_iterations=max_iterations
                    )

                # generate code
                with st.spinner("Generating and verifying code... This may take a minute."):
                    result = st.session_state.orchestrator.generate_verified_code(
                        user_input,
                        verbose=False
                    )

                    st.session_state.result = result

                # show result
                if result.verified:
                    st.markdown('<div class="success-box">✅ <strong>Verification Successful!</strong> Code is mathematically proven correct.</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="error-box">❌ <strong>Verification Failed</strong><br>{result.error_message}</div>', unsafe_allow_html=True)

                st.info(f"Completed in {result.total_iterations} iteration(s)")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                import traceback
                with st.expander("Show full error details"):
                    st.code(traceback.format_exc())

with tab2:
    st.header("Verification Results")

    if st.session_state.result:
        result = st.session_state.result

        # show the specification
        st.subheader("📋 Extracted Specification")
        if result.specification:
            spec = result.specification
            st.write(f"**Function:** `{spec.function_name}`")
            st.write(f"**Returns:** `{spec.return_type}`")

            col1, col2 = st.columns(2)
            with col1:
                st.write("**Parameters:**")
                for param in spec.parameters:
                    st.write(f"- `{param.name}: {param.type}`")

                st.write("**Preconditions:**")
                for pre in spec.preconditions:
                    st.write(f"- {pre}")

            with col2:
                st.write("**Postconditions:**")
                for post in spec.postconditions:
                    st.write(f"- {post}")
        else:
            st.warning("⚠️ Specification could not be extracted. Check error message below.")

        st.divider()

        # show the code
        if result.python_code:
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("🐍 Python Code")
                if result.verified:
                    st.markdown('<span class="verified-badge">✓ VERIFIED</span>', unsafe_allow_html=True)
                st.code(result.python_code, language="python")

            with col2:
                st.subheader("🔷 Dafny Code")
                st.code(result.dafny_code, language="dafny")

        st.divider()

        # show what happened in each iteration
        st.subheader("🔄 Iteration History")
        for attempt in result.attempts:
            status = '✅ Success' if (attempt.result and attempt.result.success) else '❌ Failed'
            with st.expander(f"Attempt {attempt.attempt_number} - {status}"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    if attempt.result and not attempt.result.success:
                        st.write("**Errors:**")
                        for error in attempt.result.errors:
                            st.error(f"Line {error.line_number}: {error.message}")

                        if attempt.feedback:
                            st.write("**Feedback:**")
                            st.info(attempt.feedback)
                    elif not attempt.result:
                        st.error("❌ Attempt failed before verification")
                        if attempt.feedback:
                            st.write("**Feedback:**")
                            st.info(attempt.feedback)

                with col2:
                    if attempt.result:
                        st.metric("Errors", len(attempt.result.errors))
                        if attempt.result.execution_time:
                            st.metric("Time", f"{attempt.result.execution_time:.2f}s")
                    else:
                        st.metric("Status", "Error")

    else:
        st.info("👈 Generate code in the 'Generate' tab to see results here")

with tab3:
    st.header("About This System")

    st.markdown("""
    ## 🎯 What is Formal Verification?

    Formal verification uses mathematical proofs to guarantee that code is correct.
    Unlike testing, which can only show the presence of bugs, formal verification
    provides absolute certainty that your code meets its specification.

    ## 🚀 How It Works

    1. **Specification Parsing**: AI extracts formal requirements from natural language
    2. **Code Generation**: AI generates Python implementation
    3. **Translation**: Python code is converted to Dafny (verification language)
    4. **Verification**: Dafny mathematically proves correctness
    5. **Refinement**: If verification fails, AI analyzes errors and improves code

    ## 🔧 Key Components

    - **LLM (Claude)**: Parses specs, generates code, analyzes errors
    - **Dafny**: Industry-standard formal verification tool
    - **Iterative Refinement**: Automatically fixes verification failures

    ## 🎓 Example Use Cases

    - **Critical Algorithms**: Binary search, sorting, data structures
    - **Security Functions**: Cryptographic operations, access control
    - **Financial Calculations**: Precise arithmetic, transaction logic
    - **Safety-Critical Systems**: Medical devices, aerospace, automotive

    ## 📚 Learn More

    - [Dafny Documentation](https://dafny.org/)
    - [Formal Methods Overview](https://en.wikipedia.org/wiki/Formal_methods)
    - [GitHub Repository](https://github.com/yourusername/llm-formal-verifier)

    ## ⚖️ Limitations

    - Currently supports simple Python functions
    - Best for algorithms with clear specifications
    - Complex data structures may require manual refinement
    - Verification time increases with code complexity
    """)

    st.divider()

    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
    Built with ❤️ using Streamlit, Claude AI, and Dafny<br>
    Making formal methods accessible to everyone
    </div>
    """, unsafe_allow_html=True)
