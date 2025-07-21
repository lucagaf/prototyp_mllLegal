import time

import streamlit as st
import pandas as pd
import numpy as np
# import altair as alt
import os
import sys
import tempfile
import subprocess
import shutil
import json
from difflib import SequenceMatcher
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
#import src.models.V3_Frontend.run_pipeline
#from src.models.V3_Frontend.run_pipeline import main
# --------------  file processing --------------
from tempfile import NamedTemporaryFile



# --------------  main page --------------
st.set_page_config(page_title="Doc Analyzer", layout="wide")

st.title("Dependency Check")

st.write(f"Python executable: {sys.executable}")
st.write(f"Python version: {sys.version}")
st.write(f"sys.path: {sys.path}")

try:
    import docx
    st.write("docx package found!")
except ImportError:
    st.write("docx package NOT found in this environment.")

st.title("Legal Document Analyzer")
st.markdown("""
Welcome to the Legal Document Analyzer. This tool helps users analyze legal documents—specifically NDAs—based on selected criteria.
Developed as part of a Bachelor's thesis at HSLU by Luca Gafner.
""")

with st.expander("How does it work?"):
    st.markdown("""
    1. **Choose the Contract Type**: Currently, only NDAs are supported.
    2. **Select User Role**: Developer of this interface can choose the role "Developer" 
    3. **Set Parameters**: Choose whether the NDA is bilateral or unilateral, SIX listing and desired formulation.
    4. **Upload the NDA File**: Upload a `.doc` or `.docx` file for analysis.
    5. **Run Analysis**: The AI will process and highlight key insights.
    """)

# --------------  sidebar controls --------------
st.sidebar.header("Settings")

openai_api_key = st.sidebar.text_input('Key')
control_contractType = st.sidebar.selectbox(
    "Select Contract Type", ["NDA", "SPA (not implemented yet)", "SLA (not implemented yet)"],
    index=None,  #start empty
    placeholder="Select Contract Type"
    #default=["A", "B"]
)

# Add a selectbox for User and Developer
model_typ = st.sidebar.selectbox("Select openAI model Type", ["o1", "GPT-4.1", "gpt-4.1-mini"], index=0)
openai_model = "o1-2024-12-17"
if model_typ == "o1":
    openai_model = "o1-2024-12-17"
elif model_typ == "GPT-4.1":
    openai_model = "gpt-4.1-2025-04-14"
elif model_typ == "gpt-4.1-mini":
    openai_model = "gpt-4.1-mini-2025-04-14"



if control_contractType == "NDA":  # Check if a selection has been made
    with st.sidebar:
        st.write("---")
        st.info(
            "**Note:** This section is currently not implemented, "
            "but could be added in a future version if desired."
        )

        control_lcontract_type = st.sidebar.radio("Which contract type should be used?", ["Bilateral", "Unilateral"])

        control_llisting_six = st.sidebar.radio("Is the company listed on the SIX?", ["Yes", "No"])


        control_listing_six = st.sidebar.radio("Which formulation is necessary for this contract", ["Neutral", "Strong", "Mild"])
    with st.sidebar:
       st.sidebar.header("Anonymization Settings")
       # Initialize session state for name-abbreviation pairs
       st.write(
           "Enter full names and their desired abbreviations for anonymization. "
           "Full names will not be sent to OpenAI."
       )
       # Two simple fixed input pairs
       full_name_1 = st.text_input("Full Name 1", key="full_name_1")
       abbr_1 = st.text_input("Abbreviation 1", key="abbr_1")

       full_name_2 = st.text_input("Full Name 2", key="full_name_2")
       abbr_2 = st.text_input("Abbreviation 2", key="abbr_2")

       # Build a dictionary only for filled entries
       anonymization_dict = {}
       if full_name_1 and abbr_1:
           anonymization_dict[abbr_1] = full_name_1
       if full_name_2 and abbr_2:
           anonymization_dict[abbr_2] = full_name_2

    # Display a summary of the selected parameters
    st.markdown("### Summary of Selected Parameters")
    st.write(f"- **Contract Type**: {control_contractType}")
    st.write(f"- **Selected OpenAI Model**: {openai_model}")
    st.write("---")
    st.write(f"⚠️ Parameters that are currently not implemented and will not be used in the analysis:")
    st.write(f"- **Contract Usage**: {control_lcontract_type}")
    st.write(f"- **Listed on SIX**: {control_llisting_six}")
    st.write(f"- **Formulation**: {control_listing_six}")
    st.text(" ")
    st.write("**Current Anonymization Mapping**")
    if anonymization_dict:
        for abbr, fullname in anonymization_dict.items():
            st.write(f"- **{fullname}** → {abbr}")
    else:
        st.write("No anonymization pairs set yet.")
    st.write("---")
# --------------  file upload --------------

st.subheader("Upload the NDA document")
upload_placeholder = st.empty()

# -- Upload Section --
#st.subheader("Upload a Word file and run pipeline")

uploaded_doc = upload_placeholder.file_uploader("🔄 Upload the NDA that you wish to be analyzed by the AI model. The file has to be either a docx or doc file.", type=["docx", "doc"])


if uploaded_doc:
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_doc.name)[1]) as tmp:
        tmp.write(uploaded_doc.read())
        tmp_path = tmp.name
    #st.markdown(f"**Saved to**: `{tmp_path}`")

    # Copy into data/raw/
    filename = os.path.basename(tmp_path)
    raw_dir = os.path.join(os.getcwd(), "data", "raw")
    os.makedirs(raw_dir, exist_ok=True)
    dest = os.path.join(raw_dir, filename)
    shutil.copy(tmp_path, dest)
    #st.markdown(f"**Copied to**: `{dest}`")

    buttons_placeholder = st.empty()
    pipeline_steps = st.empty()
    with buttons_placeholder.container():
        run_sub = st.button("▶️ Run Analysis", key="subproc")
        #run_sub = None
        #run_direct = st.button("▶️ Run pipeline (direct import)", key="direct")
        #run_direct = False



    if run_sub:
        if not openai_api_key:
            st.error("❌ Please enter your OpenAI API key in the sidebar.")
            st.stop()

        if not control_contractType:
            st.error("❌ Please select a contract type in the sidebar.")
            st.stop()

        upload_placeholder.empty()
        buttons_placeholder.empty()

        step1_slot, step2_slot, step3_slot = st.empty(), st.empty(), st.empty()

        step1_slot.info("⚙️ Step 1 – Identify missing clauses …")
        time.sleep(0.5)

        step2_slot.info("⚙️ Step 2 – Identify deviating clauses …")
        time.sleep(0.5)

        step3_slot.info("⚙️ Step 3 – Identify additional clauses …")
        time.sleep(1.5)

        with st.spinner("Running AI Model in the background…"):
            try:
                if run_sub:
                    cmd = [
                        sys.executable,  # ensures same Python interpreter
                        "V3_Frontend/run_pipeline.py",  # your script
                        "-s", "UserDocument.docx",  # -s "Sample 2.docx"
                        "-d", dest,  # -s "Sample 2.docx"
                        "-a", openai_model,  # -a "gpt-4.1-2025-04-14"
                        "-b", openai_model,  # -b "gpt-4.1-2025-04-14"
                        "-c", openai_model,  # -c "gpt-4.1-2025-04-14"
                        "-K", openai_api_key,
                    ]
                    result = subprocess.run(cmd, capture_output=True, text=True)

                    if result.returncode != 0:
                        st.error("❌ Pipeline failed!")
                        st.write("**Error Output:**")
                        st.code(result.stderr if result.stderr else "No error message provided.")
                        # Optionally also show stdout for debugging
                        if result.stdout:
                            st.write("**Standard Output:**")
                            st.code(result.stdout)
                        st.stop()  # Stop further execution

                    output = result.stdout

                st.success("✅ Pipeline finished successfully!")
                BASE = Path("V3_Frontend")
                with open(BASE / "temp/3_V3_additional_clauses.json", encoding="utf‑8") as f:
                    additional_raw = json.load(f)["entries"]

                step1_slot.success("✅ Step 1 – Identify missing clauses: ")
                step2_slot.success("✅ Step 2 – Identify deviating clauses")
                step3_slot.success("✅ Step 3 – Identify additional clauses:")

                additional = [
                    f"**{e['additional_clause_name']}**\n\n{e['additional_clause']}\n\n"
                    f"<span style='background-color: yellow;'>*Legal impact:*</span> {e['legal_impact']}"
                    for e in additional_raw
                ]


                # MISSING CLAUSES
                MISSING_FILE = BASE / "temp/UserDocument-missing_filtered.json"
                with open(MISSING_FILE, encoding="utf-8") as f:
                    missing_raw = json.load(f)

                missing = [
                    f"**{e['clause_name']} – {e['clause_subname']}**\n\n{e['input_clause']}"
                    for e in missing_raw
                ]

                # DEVIATING CLAUSES
                DEV_FILE = BASE / f"V3-deviating-{openai_model}-UserDocument.json"
                with open(DEV_FILE, encoding="utf-8") as f:
                    dev_raw = json.load(f)


                def get_best_retrieved_clause(retrieved_clauses):
                    """Return the retrieved clause dict with the highest confidence."""
                    return max(retrieved_clauses, key=lambda x: x["confidence"])

                def mark_overlapping_text(modified, retrieved):
                    import re
                    from difflib import SequenceMatcher

                    # Tokenize the texts preserving whitespace
                    mod_tokens = re.findall(r'\S+\s*', modified)
                    ret_tokens = re.findall(r'\S+\s*', retrieved)

                    # Create a SequenceMatcher on token lists
                    s = SequenceMatcher(None, mod_tokens, ret_tokens)
                    marked_text = ""
                    for tag, i1, i2, j1, j2 in s.get_opcodes():
                        for token in mod_tokens[i1:i2]:
                            # For equal tokens, display as is.
                            if tag == 'equal':
                                marked_text += token
                            else:
                                # Check if this token (ignoring case and extra whitespace)
                                # exists anywhere in the corresponding retrieved tokens.
                                ret_segment = "".join(ret_tokens[j1:j2]).lower()
                                if token.strip().lower() and token.strip().lower() in ret_segment:
                                    marked_text += token
                                else:
                                    marked_text += f"<font color='red'>{token}</font>"
                    return marked_text

                deviating = []
                for e in dev_raw:
                    best = get_best_retrieved_clause(e["retrieved_clauses"])
                    highlighted_modified = mark_overlapping_text(e["modified_clause"], best["clause"])
                    deviating.append(
                        f"**{e['clause_name']} – {e['clause_subname']}**\n\n"
                        f"*Input clause:*\n{e['input_clause']}\n\n"
                        f"*Retrieved clause:  (confidence {best['confidence']:.1%})*\n{best['clause']}\n\n"
                        f"<span style='background-color: yellow;'>*Modified clause:*</span>\n{highlighted_modified}"
                    )

                # 2) erst jetzt die Tabs anzeigen
                tab1, tab2, tab3 = st.tabs([
                    "Additional Clauses",
                    "Deviating Clauses",
                    "Missing Clauses",
                ])

                with tab1:
                    st.write("### Additional Clauses")
                    for clause in additional:  # List
                        st.markdown(f"- {clause}", unsafe_allow_html=True)

                with tab2:
                    st.write("### Deviating Clauses")
                    for clause in deviating:
                        st.markdown(f"- {clause}", unsafe_allow_html=True)

                with tab3:
                    st.write("### Missing Clauses")
                    for clause in missing:
                        st.markdown(f"- {clause}", unsafe_allow_html=True)

                #st.code(output)
            except Exception as e:
                st.error(f"❌ Pipeline error: {e}")
                if hasattr(e, 'stdout'):
                    st.subheader("Stdout")
                    st.code(e.stdout or "— no stdout —")
                if hasattr(e, 'stderr'):
                    st.subheader("Stderr")
                    st.code(e.stderr or "— no stderr —")






