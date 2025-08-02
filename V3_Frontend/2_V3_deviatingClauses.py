from Class_RetrievedClause import RetrievedClause
import json
import os
import sys
import opik
from opik import opik_context
from dotenv import load_dotenv
load_dotenv()

current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from utils import initialize_openai_client, initialize_opik_client

from config import OPENAI_MODEL_DEVIATING, SAMPLE_DOC, PROCESS_STEP1_JSON, PROCESS_STEP2_JSON, BASEDIR

SAMPLE = SAMPLE_DOC.split(".")[0]

def filter_missing_answers(input_file: str, output_file=False):
    """
    Filters JSON objects where the 'answer' attribute equals 'missing' (case-insensitive)
    and counts the total number of objects in the JSON file.

    :param input_file: Path to the input JSON file.
    :param output_file: Boolean flag.
                        - True: Saves the filtered JSON to "models/V3/temp/missing_filtered.json".
                        - False (or None): Does not output any file.
    :return: Tuple (total_objects, filtered_objects)
    """

    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Build a path to "temp" within the same folder as the script
    temp_folder = os.path.join(script_dir, "temp")

    # Load JSON file
    with open(input_file, "r", encoding="utf-8") as file:
        data = json.load(file)  # Assuming it's a list of dictionaries

    # Filter objects where "answer" is "missing" (case-insensitive, stripping spaces)
    missing_objects = [obj for obj in data if obj.get("answer", "").strip().lower() == "missing"]

    if output_file:
        os.makedirs(temp_folder, exist_ok=True)
        output_path = os.path.join(temp_folder, f"{SAMPLE}-missing_filtered.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(missing_objects, f, indent=4)

    return len(data), len(missing_objects)


def filter_entailment_answers(input_file: str, output_file=False):
    """
    Filters JSON objects where the 'answer' attribute equals 'entailment' (case-insensitive)
    and counts the total number of objects in the JSON file.

    :param input_file: Path to the input JSON file.
    :param output_file: Boolean flag.
                        - True: Saves the filtered JSON to "temp/entailment_filtered.json".
                        - False (or None): Does not output any file.
    :return: Tuple (total_objects, filtered_objects)
    """
    # Get the directory where this script is located
    print(input_file)
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Build a path to "temp" within the same folder as the script
    temp_folder = os.path.join(script_dir, "temp")

    # Load JSON file
    with open(input_file, "r", encoding="utf-8") as file:
        data = json.load(file)  # Assuming it's a list of dictionaries

    # Filter objects where "answer" is "entailment" (case-insensitive, stripping spaces)
    entailment_objects = [
        obj for obj in data if obj.get("answer", "").strip().lower() == "entailment"
    ]

    if output_file:
        os.makedirs(temp_folder, exist_ok=True)
        output_path = os.path.join(temp_folder, f"{SAMPLE}-entailment_filtered.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(entailment_objects, f, indent=4)

    return len(data), len(entailment_objects)

@opik.track(name="Check Deviating Clauses")
def get_openai_response(clause:RetrievedClause, openai_client, OPENAI_MODEL="gpt-4o-2024-08-06"):
    """
    Gets a response from OpenAI using the input clause and retrieved clauses with confidence scores.

    Parameters:
    - input_clause (str): The queried clause.
    - retrieved_clauses (list of tuples): List of (clause, confidence) tuples.

    Returns:
    - str: The response from OpenAI.
    """
    thread_id = f"V3 - 2_V3_deviatingClauses - {SAMPLE_DOC}"
    client = initialize_opik_client()
    prompt = client.get_prompt(name="V3 - Deviating Clauses - Zero-shot")
    formatted_prompt = prompt.format(name=obj.clause_name, subname=obj.clause_subname, template_clause=obj.input_clause,
                                     counterparty_clause=obj.get_best_clause())

    opik_context.update_current_trace(
        thread_id=thread_id
    )

    response = openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": client.get_prompt(name="V1 - System Prompt").format()},
            {"role": "user", "content": formatted_prompt}
        ],
        seed=42
    )

    content = response.choices[0].message.content  #.strip()
    # Extract token usage
    input_tokens = response.usage.prompt_tokens
    output_tokens = response.usage.completion_tokens
    total_tokens = response.usage.total_tokens

    print(f"Input Tokens: {input_tokens}")
    print(f"Output Tokens: {output_tokens}")
    print(f"Total Tokens: {total_tokens}")

    # Optionally, return the token usage along with the content
    return content, input_tokens, output_tokens, total_tokens


def write_retrieved_clauses_to_file(retrieved_clauses, file_path):
    """
    Writes a list of RetrievedClause objects to a JSON file.

    Parameters:
    - retrieved_clauses (list): List of RetrievedClause objects.
    - file_path (str): Path to the output JSON file.
    """
    # Convert each RetrievedClause object into a dictionary
    data_to_write = []
    for clause in retrieved_clauses:
        clause_dict = {
            "clause_name": clause.clause_name,
            "clause_subname": clause.clause_subname,
            "input_clause": clause.input_clause,
            "retrieved_clauses": clause.retrieved_clauses,
            "answer": clause.answer,
            "modified_clause": clause.modified_clause,
        }
        data_to_write.append(clause_dict)

    # Write the list of dictionaries to the JSON file
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data_to_write, file, indent=4, ensure_ascii=False)

    return True


# When you want to output the file to the default location.
total_entailment, filtered_entailment = filter_entailment_answers(f'V3_Frontend/{PROCESS_STEP1_JSON}', True)
#print(f"Total objects: {total_entailment}, Filtered objects (entailment): {filtered_entailment}")

total_missing, filtered_missing = filter_missing_answers(f'V3_Frontend/{PROCESS_STEP1_JSON}', True)
#print(f"Total objects: {total_missing}, Filtered objects: {filtered_missing}")



assert total_missing == total_entailment, "Total has to be equal for both values"
assert filtered_entailment + filtered_missing == total_entailment, "Both filtered has to be equal to total"



with open(f'V3_Frontend/temp/{SAMPLE}-entailment_filtered.json', 'r', encoding='utf-8') as file:
    clauses_data = json.load(file)

retrieved_clause_objects = []
for entry in clauses_data:
    # Initialize the object with only the accepted parameters
    obj = RetrievedClause(
        clause_name=entry["clause_name"],
        clause_subname=entry["clause_subname"],
        input_clause=entry["input_clause"],
    )


    obj.set_clauses(entry["retrieved_clauses"])
    #print(entry["answer"])
    obj.answer = entry["answer"]
    retrieved_clause_objects.append(obj)


OPENAI_CLIENT = initialize_openai_client()

output_tokens = 0
input_tokens = 0
total_tokens = 0

for obj in retrieved_clause_objects:
    content, input_tokens, output_tokens, total_tokens = get_openai_response(obj, OPENAI_CLIENT, OPENAI_MODEL_DEVIATING)
    obj.modified_clause = content
    output_tokens += output_tokens
    input_tokens += input_tokens
    total_tokens += total_tokens
    print(f"Modified Clause: {obj.modified_clause}")

status = write_retrieved_clauses_to_file(retrieved_clause_objects, f'V3_Frontend/{PROCESS_STEP2_JSON}')

execution_details_path = 'V3_Frontend/temp/execuation_details.json'
with open(execution_details_path, 'r+', encoding='utf-8') as file:
    execution_details = json.load(file)
    execution_details['steps'][1]['input_tokens'] = input_tokens
    execution_details['steps'][1]['output_tokens'] = output_tokens
    execution_details['steps'][1]['total_tokens'] = total_tokens # TODO: Change to correct path
    file.seek(0)
    json.dump(execution_details, file, indent=4)
    file.truncate()

assert status == True, "File not written successfully"
