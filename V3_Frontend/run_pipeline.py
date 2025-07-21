#!/usr/bin/env python3
"""
run_pipeline.py
This script executes a three-step Python pipeline.
It uses argparse to manage parameters with descriptive names.
"""

import argparse
import os
import subprocess
import time
import json
import openai
from path import Path
from opik.integrations.openai import track_openai
from opik import Opik

def main():
    parser = argparse.ArgumentParser(
        description="Run a three-step Python pipeline with customizable parameters."
    )

    # Define command-line arguments with both short and long options
    parser.add_argument(
        "--sample-doc", "-s",
        help="Name of the sample document (no default)",
        required=True
    )
    parser.add_argument(
        "--model-name", "-m",
        default="lucagafner/NDA_finetuned_V1",
        help="Name of the model to be used (default: 'lucagafner/NDA_finetuned_V1')"
    )
    parser.add_argument(
        "--doc-path", "-d",
        help="Path to the document (default: '/Users/luca/Documents/HSLU/Bachelor Thesis/thesis_luca_gafner/data/raw/Sample 10.docx')"
    )
    parser.add_argument(
        "--missing-model", "-a",
        default="o1-2024-12-17",
        help="OpenAI model name for missing clauses (default: 'o1-2024-12-17')"
    )
    parser.add_argument(
        "--deviating-model", "-b",
        default="o1-2024-12-17",
        help="OpenAI model name for deviating clauses (default: 'o1-2024-12-17')"
    )
    parser.add_argument(
        "--additional-model", "-c",
        default="o1-2024-12-17",
        help="OpenAI model name for deviating clauses (default: 'o1-2024-12-17')"
    )
    parser.add_argument(
        "--retrieved-k", "-k",
        type=int,
        default=3,
        help="Number of items to retrieve (default: 3)"
    )
    parser.add_argument(
        "--step1-json", "-1",
        default=None,
        help="Output JSON filename for step 1 (default: auto-generated)"
    )
    parser.add_argument(
        "--step2-json", "-2",
        default=None,
        help="Output JSON filename for step 2 (default: auto-generated)"
    )
    parser.add_argument(
        "--openai_key", "-K",
        default=None,
        help="OpenAI API key"
    )

    args = parser.parse_args()

    # Generate default filenames if not explicitly provided
    sample = args.sample_doc.split(".")[0]
    if not args.step1_json:
        args.step1_json = f"V3-missing-{args.missing_model}-{sample}-K{args.retrieved_k}.json"
    if not args.step2_json:
        args.step2_json = f"V3-deviating-{args.deviating_model}-{sample}.json"
    #if not args.doc_path:
    #    args.doc_path = f"/Users/luca/Documents/HSLU/Bachelor Thesis/thesis_luca_gafner/data/raw/{args.sample_doc}"

    # Print out the parameters for verification
    print("Using the following parameters:")
    print(f"  Sample Document    : {args.sample_doc}")
    print(f"  Model Name         : {args.model_name}")
    print(f"  Document Path      : {args.doc_path}")
    print(f"  Missing Model      : {args.missing_model}")
    print(f"  Deviating Model    : {args.deviating_model}")
    print(f"  Additional Model   : {args.additional_model}")
    print(f"  Retrieved K        : {args.retrieved_k}")
    print(f"  Step 1 JSON Output : {args.step1_json}")
    print(f"  Step 2 JSON Output : {args.step2_json}")
    print("")

    # Set the environment variables so they are available to the downstream Python modules
    os.environ["SAMPLE_DOC"] = args.sample_doc
    os.environ["MODEL_NAME"] = args.model_name
    os.environ["DOC_PATH"] = args.doc_path
    os.environ["OPENAI_MODEL_MISSING"] = args.missing_model
    os.environ["OPENAI_MODEL_DEVIATING"] = args.deviating_model
    os.environ["OPENAI_MODEL_ADDITIONAL"] = args.additional_model
    os.environ["RETRIEVED_K"] = str(args.retrieved_k)
    os.environ["PROCESS_STEP1_JSON"] = args.step1_json
    os.environ["PROCESS_STEP2_JSON"] = args.step2_json
    os.environ["OPENAI_API_KEY"] = args.openai_key

    # Define the pipeline steps and their corresponding Python scripts


    pipeline_steps = [
        ("Running Step 1: '1_V3_RAG for top-k missing.py'...", "V3_Frontend/1_V3_RAG for top-k missing.py"),
        ("Running Step 2: '2_V3_deviatingClauses.py'...", "V3_Frontend/2_V3_deviatingClauses.py"),
        ("Running Step 3: '3_V3_AdditionalClauses.py'...", "V3_Frontend/3_V3_AdditionalClauses.py")
    ]
    # 2) Prepare output JSON
    output_path = Path(
        "V3_Frontend/temp/execuation_details.json"
    )
    #output_path.parent.mkdir(parents=True, exist_ok=True)

    # Initialize file before running any steps
    # with output_path.open("w") as f:
    #     json.dump({"steps": []}, f, indent=4)

    results = {"steps": []}

    for message, script in pipeline_steps:
        step_record = {
            "script": script,
            "time_seconds": 0,
            "total_tokens": 0,
            "input_tokens": 0,
            "output_tokens": 0
        }
        results["steps"].append(step_record)

    # Write the prepopulated results to the JSON file
    with output_path.open("w") as f:
        json.dump(results, f, indent=4)

    # Execute each step and update the JSON file
    for index, (message, script) in enumerate(pipeline_steps):
        print(message)

        start_time = time.time()
        result = subprocess.run(
            ["python", script],
            capture_output=True,
            text=True
        )
        end_time = time.time()

        elapsed = round(end_time - start_time, 1)
        with output_path.open("r", encoding="utf-8") as f:
            results = json.load(f)

        # Update only the elapsed time for the current step
        elapsed = round(end_time - start_time, 1)
        results["steps"][index]["time_seconds"] = elapsed

        if result.returncode != 0:
            print(f"Error: {script} exited with code {result.returncode}")
            print(result.stderr)
            exit(result.returncode)

        # Write the updated JSON content back to the file
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(results, f, indent=4)


    print("Pipeline execution completed.")

    message, script = ("Running Step 4: '4_PDF Generator.py'...", "V3_Frontend/4_PDF Generator.py")

    print(message)
    result = subprocess.run(["python", script])
    if result.returncode != 0:
        print(f"Error: {script} exited with return code {result.returncode}")
        exit(result.returncode)



if __name__ == "__main__":
    main()

# python3 src/models/V3/run_pipeline.py -s "Sample 2.docx" -a "gpt-4o-2024-08-06" -b "gpt-4o-2024-08-06" -c "gpt-4o-2024-08-06"
# python3 src/models/V3/run_pipeline.py -s "Sample 2.docx" -a "o1-2024-12-17" -b "o1-2024-12-17" -c "o1-2024-12-17" --> Saved into Reports
# python3 src/models/V3/run_pipeline.py -s "Sample 2.docx" -a "gpt-4.1-2025-04-14" -b "gpt-4.1-2025-04-14" -c "gpt-4.1-2025-04-14" --> Saved into Reports
# python3 src/models/V3/run_pipeline.py -s "Sample 2.docx" -a "o4-mini-2025-04-16" -b "o4-mini-2025-04-16" -c "o4-mini-2025-04-16" --> Saved into Reports
# python3 src/models/V3/run_pipeline.py -s "Sample 2.docx" -a "o3-mini-2025-01-31" -b "o3-mini-2025-01-31" -c "o3-mini-2025-01-31"  --> Dismissed bc see file "adaptions.md"

# python3 src/models/V3/run_pipeline.py -s "Sample 2.docx" -a "o3-2025-04-16" -b "o3-2025-04-16" -c "o3-2025-04-16" --> Organization needs to be verified to use this model --> Government ID necessary

# Different Embeddings Model
# python3 src/models/V3/run_pipeline.py -s "Sample 2.docx" -a "o1-2024-12-17" -b "o1-2024-12-17" -c "o1-2024-12-17" -m "all-MiniLM-L6-v2" --> Saved into Reports/Embeddings Folder
# python3 src/models/V3/run_pipeline.py -s "Sample 2.docx" -a "o1-2024-12-17" -b "o1-2024-12-17" -c "o1-2024-12-17" -m "nlpaueb/legal-bert-base-uncased" --> Saved into Reports/Embeddings Folder
