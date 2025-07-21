from config import OPENAI_MODEL_ADDITIONAL, DOC_PATH
from dotenv import load_dotenv
load_dotenv()
import opik
import os
import sys
import openai
import json
import docx2txt

current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from utils.openAI_client import initialize_openai_client

# Function to load the template NDA from a JSON file.
def load_template_nda(json_path):
    with open(json_path, 'r') as file:
        data = json.load(file)
    return data


# Function to load the counterparty contract from a text file.
def load_counterparty_contract(txt_path):
    with open(txt_path, 'r', encoding='utf-8', errors="replace") as file:
        contract = file.read()
    print(contract)
    return contract

def read_docx(file_path: str) -> str:
    """
    Read a .docx file and return its textual content as a single string.
    Utilizes the docx2txt library for straightforward extraction.

    :param file_path: Path to the .docx file
    :return: The extracted text
    """
    return docx2txt.process(file_path)


@opik.track(name="Search Additional Clauses", flush=True)
def identify_additional_clauses(
    mll_template: str,
    external_contract: str,
) -> str:
    """
    Identify additional clauses in an external NDA contract using OpenAI.

    Parameters:
    - mll_template: The base MLL template text.
    - external_contract: The full text of the external NDA.

    Returns:
    The assistant's response with identified additional clauses.
    """
    # Initialize prompt from Opik
    client = opik.Opik()
    openai_client = initialize_openai_client()

    prompt = client.get_prompt(name="V1.2 - Additional")
    formatted_prompt = prompt.format(
        MLL_template=mll_template,
        external_contract=external_contract
    )

    print(formatted_prompt)
    print(OPENAI_MODEL_ADDITIONAL)
    # Call OpenAI ChatCompletion
    response = openai_client.chat.completions.create(
        model=OPENAI_MODEL_ADDITIONAL,
        messages=[
            {"role": "system", "content": client.get_prompt(name="V1 - System Prompt").format()},
            {"role": "user", "content": formatted_prompt},
        ],
        response_format={
            "type": "json_object"
        },
        seed=42
    )

    content = response.choices[0].message.content

    try:
        content_json = json.loads(content)
    except json.JSONDecodeError:
        raise ValueError(f"Failed to parse JSON from model:\n{content}")

    # Extract token usage
    input_tokens = response.usage.prompt_tokens
    output_tokens = response.usage.completion_tokens
    total_tokens = response.usage.total_tokens

    print(f"Input Tokens: {input_tokens}")
    print(f"Output Tokens: {output_tokens}")
    print(f"Total Tokens: {total_tokens}")

    # Optionally, return the token usage along with the content
    return content_json, input_tokens, output_tokens, total_tokens



MLL_NDA = load_template_nda("/Users/luca/Documents/HSLU/Bachelor Thesis/thesis_luca_gafner/src/datasets/V3 - Template Clause MLL.json")
EXTERNAL_NDA = read_docx(DOC_PATH)

print(f'Additional / Path: {DOC_PATH}')
print(EXTERNAL_NDA)

# Call the function to identify additional clauses
content, input_tokens, output_tokens, total_tokens = identify_additional_clauses(
    mll_template=MLL_NDA,
    external_contract=EXTERNAL_NDA
)

# Write the results to a text file in the "temp" folder, overwriting if it exists
base_dir = os.path.dirname(os.path.abspath(__file__))
temp_dir = os.path.join(base_dir, "temp")
print(f'TEMP DIR PATH: {temp_dir}')
os.makedirs(temp_dir, exist_ok=True)
output_path = os.path.join(temp_dir, "3_V3_additional_clauses.json")
#with open(output_path, 'w', encoding='utf-8') as out_file:
#    out_file.write(content)
with open(output_path, 'w', encoding='utf-8') as out_file:
    json.dump(content, out_file, indent=4)

execution_details_path = 'src/models/V3_Frontend/temp/execuation_details.json'
with open(execution_details_path, 'r+', encoding='utf-8') as file:
    execution_details = json.load(file)
    execution_details['steps'][2]['input_tokens'] = input_tokens
    execution_details['steps'][2]['output_tokens'] = output_tokens
    execution_details['steps'][2]['total_tokens'] = total_tokens
    file.seek(0)
    json.dump(execution_details, file, indent=4)
    file.truncate()

print(f"Results written to {output_path}")