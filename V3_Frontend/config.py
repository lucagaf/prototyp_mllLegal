import os
from pathlib import Path
# os.environ["PROCESS_STEP1_JSON"] = "V3-missing-o1-2024-12-17-Sample 10-K3.json"
# os.environ["PROCESS_STEP2_JSON"] = "TEST - V3-missing-o1-2024-12-17-Sample 10-K3.json"
# os.environ["OPENAI_MODEL_DEVIATING"] = "gpt-4o-2024-08-06" #"o1-2024-12-17"

# Read configuration variables from environment variables, with defaults if not set.
SAMPLE_DOC = os.environ.get("SAMPLE_DOC")
MODEL_NAME = os.environ.get("MODEL_NAME")
DOC_PATH = os.environ.get("DOC_PATH")
OPENAI_MODEL_MISSING = os.environ.get("OPENAI_MODEL_MISSING")
OPENAI_MODEL_DEVIATING = os.environ.get("OPENAI_MODEL_DEVIATING")
OPENAI_MODEL_ADDITIONAL = os.environ.get("OPENAI_MODEL_ADDITIONAL")
# Convert RETRIEVED_K to an integer since environment variables are strings.
RETRIEVED_K = int(os.environ.get("RETRIEVED_K", 3))
PROCESS_STEP1_JSON = os.environ.get("PROCESS_STEP1_JSON")
PROCESS_STEP2_JSON = os.environ.get("PROCESS_STEP2_JSON")
BASEDIR = Path(os.environ.get("BASEDIR"))

# PRICE PER TOKEN
MODEL_PRICING = {
    "gpt-4o-2024-08-06": {"input": 0.0000025, "output": 0.00001},
    "gpt-4.1-2025-04-14": {"input": 0.000002, "output": 0.000008},

    # Reasoning model (from OpenAI Assistants API)
    "o1-2024-12-17": {"input": 0.000015, "output": 0.00006},
    "o3-2025-04-16": {"input": 0.00001, "output": 0.00004},
    "o4-mini-2025-04-16": {"input": 0.0000011, "output": 0.0000044},
    "o3-mini-2025-01-31": {"input": 0.0000011, "output": 0.0000044},
    "gpt-4.1-mini-2025-04-14": {"input": 0.0000011, "output": 0.0000044}
}
"""

SAMPLE_DOC = "Sample 10"
MODEL_NAME = "lucagafner/NDA_finetuned_V1"
SHORT_MODEL_NAME = "NDA_finetuned_V1"
DOC_PATH = f"/Users/luca/Documents/HSLU/Bachelor Thesis/thesis_luca_gafner/data/raw/{SAMPLE_DOC}.docx"
OPENAI_MODEL_MISSING = "gpt-4o-2024-08-06" #"o1-2024-12-17"
OPENAI_MODEL_DEVIATING = "o1-2024-12-17"
RETRIEVED_K = 3

PROCESS_STEP1_JSON= f"V3-missing-{OPENAI_MODEL_MISSING}-{SAMPLE_DOC}-K{RETRIEVED_K}.json"
PROCESS_STEP2_JSON = f"V3-deviating-{OPENAI_MODEL_DEVIATING}-{SAMPLE_DOC}.json"

"""