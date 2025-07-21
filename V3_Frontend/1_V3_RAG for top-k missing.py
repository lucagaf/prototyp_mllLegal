import os
import sys
from docx import Document
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
import opik
from opik.integrations.openai import track_openai
from opik import Opik, opik_context
from openai import OpenAI
import openai
from dotenv import load_dotenv
import json
from Class_RetrievedClause import RetrievedClause
current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, "../../"))

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils import initialize_openai_client
from config import SAMPLE_DOC, MODEL_NAME, DOC_PATH, OPENAI_MODEL_MISSING, RETRIEVED_K, PROCESS_STEP1_JSON

EMBEDDING_MODEL = SentenceTransformer(MODEL_NAME)

load_dotenv()



def load_paragraphs(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    doc = Document(file_path)
    # Only keep paragraphs with non-empty text
    paragraphs = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
    return paragraphs


def extract_clauses_from_json(json_path) -> list[RetrievedClause]:
    """
    Extracts clauses from a JSON file and returns a list of RetrievedClause objects.

    Parameters:
    - json_path (str): Path to the JSON file.

    Returns:
    - List of RetrievedClause objects.
    """
    with open(json_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    retrieved_clauses = []
    for main_key, sub_dict in data.items():
        if isinstance(sub_dict, dict):
            for sub_key, value in sub_dict.items():
                retrieved_clauses.append(RetrievedClause(main_key, sub_key, value))

    return retrieved_clauses

def normalize_embeddings(embeddings):
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    return embeddings / norms

def retrieve(query, embedding_model, index, paragraphs, k=3):
    # Compute and normalize the query embedding
    query_embedding = embedding_model.encode([query])
    query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
    # Perform search on the FAISS index
    scores, indices = index.search(np.array(query_embedding, dtype=np.float32), k)
    retrieved = []

    # Return each retrieved paragraph along with its confidence (cosine similarity score)
    for score, idx in zip(scores[0], indices[0]):
        retrieved.append((paragraphs[idx], score))
    return retrieved



def save_retrieved_clauses_to_json(retrieved_clauses_list, filename="retrieved_clauses.json"):
    json_data = []

    for clause_obj in retrieved_clauses_list:
        json_data.append({
            "clause_name": clause_obj.clause_name,
            "clause_subname": clause_obj.clause_subname,
            "input_clause": clause_obj.input_clause,
            "retrieved_clauses": [{"clause": c, "confidence": float(conf)} for c, conf in clause_obj.retrieved_clauses],
            "answer": clause_obj.answer
        })

    if isinstance(filename, tuple):
        filename = filename[0]
    current_directory = os.path.dirname(__file__)
    file_path = os.path.join(current_directory, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=4, ensure_ascii=False)




def get_openai_response(clause:RetrievedClause, openai_client, thread_id, opik_client, OPENAI_MODEL):
    """
    Gets a response from OpenAI using the input clause and retrieved clauses with confidence scores.

    Parameters:
    - input_clause (str): The queried clause.
    - retrieved_clauses (list of tuples): List of (clause, confidence) tuples.

    Returns:
    - str: The response from OpenAI.
    """
    client = opik_client
    retrieved_clause = clause.return_retrievedClauses()
    prompt = client.get_prompt(name="V3 - Missing Clauses - Zero-shot")
    context = prompt.format(input_clause=clause.input_clause,
                            retrieved_clauses=retrieved_clause)


    response = openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": client.get_prompt(name="V1 - System Prompt").format()},
            {"role": "user", "content": context}
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

    trace = client.trace(
        name=f'{clause.clause_name} - {clause.clause_subname}',
        input=context,
        output=content,
        thread_id=thread_id
    )

    return content, input_tokens, output_tokens, total_tokens



def initialize_faiss_index(doc_path, embedding_model):
    paragraphs = load_paragraphs(doc_path)

    # Compute embeddings
    print("Computing embeddings for document paragraphs...")
    paragraph_embeddings = embedding_model.encode(paragraphs, show_progress_bar=True)
    normalized_paragraph_embeddings = normalize_embeddings(np.array(paragraph_embeddings))

    # Build FAISS index
    dimension = normalized_paragraph_embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # Inner product on normalized vectors equals cosine similarity
    index.add(np.array(normalized_paragraph_embeddings, dtype=np.float32))

    print(f"FAISS index built with {index.ntotal} vectors.")
    return index, paragraphs


# Example usage
if __name__ == "__main__":
    # INITIALIZE
    print(DOC_PATH)
    index, paragraphs = initialize_faiss_index(DOC_PATH, EMBEDDING_MODEL)
    openai_client = initialize_openai_client()
    current_directory = os.path.dirname(__file__)
    json_file_path = os.path.join(current_directory, "data/V3 - Template Clause MLL.json")
    json_file_path = "data/V3 - Template Clause MLL.json"
    retrieved_clauses_list = extract_clauses_from_json(json_file_path)

    for clause_query in retrieved_clauses_list:
        similar_clauses = retrieve(clause_query.input_clause, EMBEDDING_MODEL, index, paragraphs, k=RETRIEVED_K)
        clause_query.retrieved_clauses = similar_clauses

    thread_id = f"TEST Identify Missing / Entailment - 1_V3_RAG - {SAMPLE_DOC}"
    opik_client =client = opik.Opik()

    input_tokens = 0
    output_tokens = 0
    total_tokens = 0

    for retrieved_clause in retrieved_clauses_list:
        content, input_tokens, output_tokens, total_tokens = get_openai_response(retrieved_clause, openai_client, thread_id, opik_client,  OPENAI_MODEL_MISSING)
        retrieved_clause.answer = content
        output_tokens += output_tokens
        input_tokens += input_tokens
        total_tokens += total_tokens

    opik_client.end()
    save_retrieved_clauses_to_json(retrieved_clauses_list, PROCESS_STEP1_JSON)

    execution_details_path = 'V3_Frontend/temp/execuation_details.json'
    with open(execution_details_path, 'r+', encoding='utf-8') as file:
        execution_details = json.load(file)
        execution_details['steps'][0]['input_tokens'] = input_tokens
        execution_details['steps'][0]['output_tokens'] = output_tokens
        execution_details['steps'][0]['total_tokens'] = total_tokens
        file.seek(0)
        json.dump(execution_details, file, indent=4)
        file.truncate()


    print("JSON file saved successfully.")