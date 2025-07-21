import json
from difflib import SequenceMatcher
from config import SAMPLE_DOC, PROCESS_STEP1_JSON, PROCESS_STEP2_JSON, OPENAI_MODEL_MISSING, MODEL_NAME, OPENAI_MODEL_DEVIATING, OPENAI_MODEL_ADDITIONAL, MODEL_PRICING, BASEDIR
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Flowable
import json
import re
from reportlab.platypus import Paragraph, Spacer

SHORT_MODEL_NAME = MODEL_NAME.split("/")[1]  # Extract the first part of the model name
#SHORT_MODEL_NAME = MODEL_NAME

# --- Step 1: Load the JSON data ---
deviating_file = f'V3_Frontend/{PROCESS_STEP2_JSON}'
with open(deviating_file, "r", encoding="utf-8") as file:
    deviating_data = json.load(file)


missing_file = f'V3_Frontend/{PROCESS_STEP1_JSON}'
with open(missing_file, "r", encoding="utf-8") as file:
    missing_data = json.load(file)


def get_best_retrieved_clause(retrieved_clauses):
    return max(retrieved_clauses, key=lambda x: x["confidence"])

def filter_missing_answers(input_file: str, output_file=False):
    """
    Filters JSON objects where the 'answer' attribute equals 'missing' (case-insensitive)
    and counts the total number of objects in the JSON file.

    """
    with open(input_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    # Filter objects where "answer" is "missing" (case-insensitive, stripping spaces)
    missing_objects = [obj for obj in data if obj.get("answer", "").strip().lower() == "missing"]

    return missing_objects

# --- Utility: Function to mark overlapping text ---
# This function uses difflib's SequenceMatcher to find overlapping sequences between the modified text and the retrieved clause.
# It wraps overlapping segments in a font tag to change the color (red in this case) so they are “highlighted” in the PDF.
def OLD_mark_overlapping_text(modified, retrieved):
    s = SequenceMatcher(None, modified, retrieved)
    opcodes = s.get_opcodes()
    marked_text = ""
    for tag, i1, i2, j1, j2 in opcodes:
        segment = modified[i1:i2]
        if tag == 'equal' and segment.strip():  # an overlapping segment found
            # Wrap overlapping text in a <font> tag with a red color
            marked_text += f"<font color='red'>{segment}</font>"
        else:
            marked_text += segment
    return marked_text

def mark_overlapping_text(modified, retrieved):
    from difflib import SequenceMatcher
    s = SequenceMatcher(None, modified, retrieved)
    opcodes = s.get_opcodes()
    marked_text = ""
    for tag, i1, i2, j1, j2 in opcodes:
        segment = modified[i1:i2]
        # Highlight segments that do not match the retrieved clause
        if tag != 'equal' and segment.strip():
            marked_text += f"<font color='red'>{segment}</font>"
        else:
            marked_text += segment
    return marked_text


def append_deviating_clauses(clauses_data, styles, story):
    """
    Append Flowable objects (Paragraphs and Spacers) for clause content to the existing story list.

    Args:
        clauses_data (list): List of dictionaries with clause details.
        styles (dict): A dictionary of ReportLab ParagraphStyle objects; it should contain
                       'ClauseHeading' and 'ClauseBody' styles.
        story (list): The existing list of Flowable objects that will be appended to.

    Returns:
        None
    """

    story.append(Paragraph("Deviating Clauses", styles["ClauseHeading"]))
    for clause_obj in clauses_data:
        clause_name = clause_obj.get("clause_name", "Unnamed Clause")
        input_clause = clause_obj.get("input_clause", "")
        modified_clause = clause_obj.get("modified_clause", "")

        # Get the retrieved clause with the highest confidence
        best_retrieved = get_best_retrieved_clause(clause_obj.get("retrieved_clauses", []))
        retrieved_clause = best_retrieved.get("clause", "")

        # Mark overlapping text in the modified clause based on the retrieved clause
        marked_modified_clause = mark_overlapping_text(modified_clause, retrieved_clause)

        # Append the various sections as Paragraphs to the provided story list
        story.append(Paragraph(f"<b>Clause:</b> {clause_name}", styles['ClauseHeading']))
        story.append(Paragraph("<b>Input Clause:</b>", styles['ClauseBody']))
        story.append(Paragraph(input_clause, styles['ClauseBody']))
        story.append(Spacer(1, 6))

        story.append(Paragraph("<b>Retrieved Clause (Highest Confidence):</b>", styles['ClauseBody']))
        story.append(Paragraph(retrieved_clause, styles['ClauseBody']))
        story.append(Spacer(1, 6))

        story.append(Paragraph("<b>Modified Clause (Overlapping text highlighted in red):</b>", styles['ClauseBody']))
        story.append(Paragraph(marked_modified_clause, styles['ClauseBody']))
        story.append(Spacer(1, 20))


# Append Additional Clauses content from temp/3_V3_additional_clauses.txt to the story

def OLD_append_additional_clauses(additional_file_path, styles, story):
    """
    Reads the additional clauses content from the provided file path
    and appends it to the story list as a heading and a paragraph.

    Parameters:
    - additional_file_path: path to the 3_V3_additional_clauses.txt file.
    - styles: a dictionary of ReportLab ParagraphStyle objects.
    - story: the list to which the content will be appended.
    """
    with open(additional_file_path, "r", encoding="utf-8") as file:
        content = file.read()

    # Append heading for additional clauses section
    story.append(Paragraph("Additional Clauses", styles["ClauseHeading"]))

    # Append the file content as a paragraph
    story.append(Paragraph(content, styles["ClauseBody"]))
    story.append(Spacer(1, 20))




def append_additional_clauses_TXT(additional_file_path, styles, story):
    """
    Reads the additional clauses content from the provided file path,
    splits it into individual clauses, and appends each clause and its
    legal impact as separate styled paragraphs to the story list.

    Expects the file to use this structure, repeated:

    - **Clause from External NDA:**
      "…clause text…"

    - **Legal Impact:**
      impact text

    Clauses are separated by lines of --- (three or more hyphens).
    """
    with open(additional_file_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Add the main section heading
    story.append(Paragraph("Additional Clauses", styles["ClauseHeading"]))
    story.append(Spacer(1, 12))

    # Split into clause blocks on lines of --- (three or more hyphens)
    blocks = re.split(r'\n-{3,}\s*\n', text)

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # Extract the clause text (inside quotes)
        clause_match = re.search(
            r'\*\*Clause from External NDA:\*\*\s*"([\s\S]*?)"',
            block
        )
        clause_text = clause_match.group(1).strip() if clause_match else ""

        # Extract the legal impact text
        impact_match = re.search(
            r'\*\*Legal Impact:\*\*\s*([\s\S]+)$',
            block
        )
        impact_text = impact_match.group(1).strip() if impact_match else ""

        # Append Clause label + text
        story.append(Paragraph("Clause from External NDA:", styles["ClauseSubHeading"]))
        story.append(Paragraph(clause_text, styles["ClauseBody"]))
        story.append(Spacer(1, 6))

        # Append Impact label + text
        story.append(Paragraph("Legal Impact:", styles["ClauseSubHeading"]))
        story.append(Paragraph(impact_text, styles["ClauseBody"]))
        story.append(Spacer(1, 12))

    # a little extra space at the end
    story.append(Spacer(1, 20))

def append_additional_clauses_MD(additional_file_path, styles, story):
    """
    Reads the additional clauses content from the provided file path
    and appends it as a single styled paragraph to the story list.

    The content is taken directly from the Markdown file, preserving all spacing.
    """
    with open(additional_file_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Add the main section heading
    story.append(Paragraph("Additional Clauses", styles["ClauseHeading"]))
    story.append(Spacer(1, 12))

    # Append the entire text as a single paragraph
    story.append(Paragraph(text, styles["ClauseBody"]))
    story.append(Spacer(1, 20))


def append_additional_clauses_JSON(json_path, styles, story):
    """
    Reads the JSON file at json_path containing:
      {
        "entries": [
          {
            "additional_clause_name": "...",
            "additional_clause": "...",
            "legal_impact": "..."
          },
          …
        ]
      }
    and appends them to the story flowables. Each entry will be laid out as:
      1. <bold clause name>
         clause text
         legal impact
    """
    # 1) Load the data
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    entries = data.get("entries", [])
    if not entries:
        return  # nothing to add

    # 2) Section heading
    story.append(Paragraph("Additional Clauses", styles["ClauseHeading"]))
    story.append(Spacer(1, 12))

    # 3) Iterate entries
    for i, entry in enumerate(entries, start=1):
        name   = entry.get("additional_clause_name", "").strip()
        clause = entry.get("additional_clause", "").strip()
        impact = entry.get("legal_impact", "").strip()

        # a) Clause name, bolded and numbered
        story.append(
            Paragraph(f"{i}. <b>{name}</b>", styles["ClauseSubHeading"])
        )
        story.append(Spacer(1, 4))

        # b) Clause text
        if clause:
            story.append(Paragraph(f"<i>{clause}</i>", styles["ClauseBody"]))
            story.append(Spacer(1, 4))

        # c) Legal impact
        if impact:
            story.append(Paragraph(f'Legal Impact: {impact}', styles["ClauseBody"]))
            story.append(Spacer(1, 12))


def append_missing_paragraphs(missing_data, styles, story):
    """
    Append Flowable objects (Paragraphs and Spacers) for missing clause content to the existing story list.

    Each missing entry is expected to have:
      - "clause_name": the main name of the clause.
      - "clause_subname": the subname or further information.
      - "input_clause": the input text for that clause.
      - "retrieved_clauses": a list of dictionaries, each with a "clause" (text) and "confidence" value.

    The function will add the clause name (with its subname), input clause, and all retrieved clauses to the story.

    Args:
        missing_data (list): List of missing clause objects.
        styles (dict): A dictionary of ReportLab ParagraphStyle objects; expected keys include:
                       'ClauseHeading' and 'ClauseBody'.
        story (list): The existing list of Flowable objects that this function appends to.

    Returns:
        None
    """

    story.append(Paragraph("Missing Clauses", styles["Heading2"]))
    for missing_obj in missing_data:
        clause_name = missing_obj.get("clause_name", "Unnamed Clause")
        clause_subname = missing_obj.get("clause_subname", "")
        input_clause = missing_obj.get("input_clause", "")
        retrieved_clauses = missing_obj.get("retrieved_clauses", [])

        # Append the heading for the missing clause entry
        story.append(Paragraph(
            f"<b>Missing Clause:</b> {clause_name} ({clause_subname})",
            styles['ClauseBody']
        ))

        # Append the input clause
        story.append(Paragraph("<b>Input Clause:</b>", styles['ClauseBody']))
        story.append(Paragraph(input_clause, styles['ClauseBody']))
        story.append(Spacer(1, 6))

        # Append all retrieved clauses
        story.append(Paragraph("<b>Retrieved Clauses:</b>", styles['ClauseBody']))
        for idx, clause in enumerate(retrieved_clauses, start=1):
            retrieved_text = f"{idx}. {clause.get('clause', '')} (Confidence: {clause.get('confidence', 0):.3f})"
            story.append(Paragraph(retrieved_text, styles["NumberedClause"]))
            story.append(Spacer(1, 3))

        # Add extra space between missing entries.
        story.append(Spacer(1, 20))


def calculate_api_usage_price(input_tokens, output_tokens):
    """
    Calculate the price of API usage based on token counts and model pricing.

    Args:
        input_tokens (int): The number of input tokens used.
        output_tokens (int): The number of output tokens generated.

    Returns:
        float: The total price of the API usage.
    """
    model = OPENAI_MODEL_ADDITIONAL
    if model not in MODEL_PRICING:
        raise ValueError(f"Pricing information for model '{model}' is not available.")

    input_price = MODEL_PRICING[model]["input"]
    output_price = MODEL_PRICING[model]["output"]

    total_price = (input_tokens * input_price) + (output_tokens * output_price)
    return total_price


# --- Step 2: Set up ReportLab PDF generation ---
pdf_filename = f"Findings Overview - {OPENAI_MODEL_MISSING}.pdf"
doc = SimpleDocTemplate(pdf_filename, pagesize=letter,
                        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='ClauseHeading', fontSize=14, leading=16, spaceAfter=10, spaceBefore=10))
styles.add(ParagraphStyle(name='ClauseBody', fontSize=10, leading=14))
styles.add(ParagraphStyle(
    "NumberedClause",
    parent=styles["ClauseBody"],
    leftIndent=20  # Adjust the indent as desired
))
styles.add(ParagraphStyle(
    "ClauseSubHeading",
    parent=styles["ClauseHeading"],
    fontSize=10,
    leading=12,
    spaceAfter=4,
))


with open('V3_Frontend/temp/execuation_details.json', 'r', encoding='utf-8') as file:
    execution_details = json.load(file)

# Totals : Time
time_seconds_1 = execution_details['steps'][0]['time_seconds']
time_seconds_2 = execution_details['steps'][1]['time_seconds']
time_seconds_3 = execution_details['steps'][2]['time_seconds']
total_time = time_seconds_1 + time_seconds_2 + time_seconds_3

# Totals: Tokens
total_input_tokens = sum(step["input_tokens"] for step in execution_details["steps"])
total_output_tokens = sum(step["output_tokens"] for step in execution_details["steps"])

# Totals: Cost
price = calculate_api_usage_price(total_input_tokens, total_output_tokens)

story = []

story.append(Paragraph(f"Findings Overview in {SAMPLE_DOC}",styles["Heading1"]))
story.append(Spacer(1, 6))
story.append(Paragraph(f'Embedding Model: {MODEL_NAME}', styles["Normal"]))
story.append(Paragraph(f'Missing Model: {OPENAI_MODEL_MISSING}', styles["Normal"]))
story.append(Paragraph(f'Deviating Model: {OPENAI_MODEL_DEVIATING}', styles["Normal"]))
story.append(Paragraph(f'Additional Model: {OPENAI_MODEL_ADDITIONAL}', styles["Normal"]))
story.append(Paragraph(f'Total Input tokens: {total_input_tokens}', styles["Normal"]))
story.append(Paragraph(f'Total Output tokens: {total_output_tokens}', styles["Normal"]))
story.append(Paragraph(f'Total Cost: {round(price, 3)} $', styles["Normal"]))

story.append(Paragraph(f'Duration Total : {round(total_time, 1)}', styles["Normal"]))
story.append(Paragraph(f'Duration Step 1 (Missing): {time_seconds_1}', styles["Normal"]))
story.append(Paragraph(f'Duration Step 2 (Deviation): {time_seconds_2}', styles["Normal"]))
story.append(Paragraph(f'Duration Step 3 (Additional): {time_seconds_3}', styles["Normal"]))


# --- Step 3: Append the data to the PDF story ---
# Append the missing clauses to the story
missing_data = filter_missing_answers(missing_file)
append_missing_paragraphs(missing_data, styles, story)

# Append the deviating clauses to the story
append_deviating_clauses(deviating_data, styles, story)

# Append the additional clauses to the story
additional_file_path = "V3_Frontend/temp/3_V3_additional_clauses.json"
append_additional_clauses_JSON(additional_file_path, styles, story)

story.append(Spacer(1, 20))
story.append(Paragraph(f"{SAMPLE_DOC} is finished", styles["Heading1"]))




# --- Step 4: Build the PDF ---
doc.build(story)

print(f"PDF generated and saved as '{pdf_filename}'.")
