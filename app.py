import streamlit as st
import subprocess
import PyPDF2
import tempfile

# ----------------------------
# Function to summarize text
# ----------------------------
def get_local_ollama_models():
    """Return a list of local Ollama model names (e.g. 'gemma3:1b')."""
    try:
        res = subprocess.run(["ollama", "list"], capture_output=True, check=False)
        out = res.stdout.decode("utf-8", errors="ignore")
        models = []
        for line in out.splitlines():
            line = line.strip()
            # skip header or empty lines
            if not line or line.startswith("NAME"):
                continue
            parts = line.split()
            if parts:
                models.append(parts[0])
        return models
    except Exception:
        return []


def summarize_text(text, model="gemma3:1b", length="short"):
    if not text or not text.strip():
        return "⚠️ No text provided for summarization."

    prompt = f"Summarize the following content in a {length} way:\n\n{text}"
    try:
        result = subprocess.run(
            ["ollama", "run", model],
            input=prompt.encode("utf-8"),
            capture_output=True,
            check=False,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        return "❌ Ollama run timed out."
    except FileNotFoundError:
        return "❌ 'ollama' executable not found. Make sure Ollama is installed and on your PATH."

    stdout = result.stdout.decode("utf-8", errors="ignore").strip()
    stderr = result.stderr.decode("utf-8", errors="ignore").strip()
    if result.returncode != 0:
        return f"❌ Ollama returned an error:\n{stderr or stdout}"
    return stdout or "(no output)"

# ----------------------------
# Function to read PDF
# ----------------------------
def extract_text_from_pdf(uploaded_file):
    reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="🧠 Content Summarization", layout="wide")
st.title("🧠 Content Summarization System (Gemma 3:b)")
st.markdown("Summarize text or upload documents locally using **Ollama + Gemma 3:b**.")

# Sidebar options
st.sidebar.header("⚙️ Settings")
summary_length = st.sidebar.radio("Summary length:", ["short", "medium", "detailed"])
input_mode = st.sidebar.radio("Input mode:", ["✏️ Type or Paste Text", "📄 Upload File"])
# Show available local Ollama models and allow the user to pick one
local_models = get_local_ollama_models()
if local_models:
    selected_model = st.sidebar.selectbox("Select Ollama model:", local_models, index=0)
else:
    selected_model = st.sidebar.text_input("Ollama model (e.g. gemma3:1b)", value="gemma3:1b")

# Main input area
input_text = ""

if input_mode == "✏️ Type or Paste Text":
    input_text = st.text_area("Enter or paste your text here:", height=250)
else:
    uploaded_file = st.file_uploader("Upload a .txt or .pdf file", type=["txt", "pdf"])
    if uploaded_file:
        if uploaded_file.name.endswith(".txt"):
            input_text = uploaded_file.read().decode("utf-8")
        elif uploaded_file.name.endswith(".pdf"):
            input_text = extract_text_from_pdf(uploaded_file)

# Summarize button
if st.button("🚀 Generate Summary"):
    with st.spinner("Generating summary with Gemma 3:b..."):
        summary = summarize_text(input_text, model=selected_model, length=summary_length)
        st.success("✅ Summary generated!")
        st.subheader("🧾 Summary Output:")
        st.write(summary)
