# general import 
import spacy
import os
import re
import json
from collections import defaultdict
from tqdm import tqdm

# Load SpaCy's NER model
nlp = spacy.load("en_core_web_sm")

def read_text_files_from_folder(input_folder):
    texts = {}
    for filename in os.listdir(input_folder):
        if filename.endswith(".txt"):
            filepath = os.path.join(input_folder, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                texts[filename] = f.read()
    return texts

def detect_headers(text):
    header_pattern = re.compile(
        r'^(?:\d+[\.\s]*)?'                     # Optional numbers
        r'([A-Z][A-Z0-9\s\-]*[A-Z])$'           # UPPERCASE headers
        r'|^([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)$'   # Title Case
        r'|^(\b[A-Z][a-z]+\b)$'                 # Single capitalized word
    )
    headers = []
    for line in text.split("\n"):
        match = header_pattern.match(line.strip())
        if match:
            header = next(group for group in match.groups() if group)
            headers.append(header)
    return headers

def normalize_header(header):
    header = re.sub(r'^\d+[\.\s]*', '', header)
    return header.strip().upper()

def paragraph_chunking(text):
    paragraphs = re.split(r"\n\s*\n", text)
    return [p.strip() for p in paragraphs if p.strip()]

def chunk_text(text):
    headers = detect_headers(text)
    headers = [normalize_header(h) for h in headers]

    sections = []
    current_section = ""
    for line in text.split("\n"):
        normalized_line = normalize_header(line)
        if normalized_line in headers:
            if current_section:
                sections.append(current_section.strip())
            current_section = line + "\n"
        else:
            current_section += line + "\n"

    if current_section:
        sections.append(current_section.strip())

    if len(sections) <= 1:
        return paragraph_chunking(text)
    return sections

def contains_date_and_location(text):
    # Process the text with SpaCy NER model
    doc = nlp(text)

    # Check if there are date or location entities
    dates = [ent for ent in doc.ents if ent.label_ == "DATE"]
    locations = [ent for ent in doc.ents if ent.label_ == "GPE" or ent.label_ == "LOC"]

    return len(dates) > 0 or len(locations) > 0


def process_text_files(input_folder):
    texts = read_text_files_from_folder(input_folder)
    structured_data = []

    for filename, content in texts.items():
        doc_id = os.path.splitext(filename)[0]
        segments = chunk_text(content)
        for segment in segments:
            structured_data.append({"source_type": doc_id, "text": segment})

    return structured_data

def filter_species(data):
    keywords = ["albopictus", "aegypti"]
    regex_pattern = '|'.join([''.join([f'{char}[\\W_]*' for char in word]) for word in keywords])
    filtered_data = [item for item in data if re.search(regex_pattern, item.get("text", "").lower())]
    return filtered_data

def filter_date_loc(chunks):
    filtered_chunks = []
    for chunk in tqdm(chunks):
        if contains_date_and_location(chunk['text']):
            filtered_chunks.append(chunk)
    return filtered_chunks

def combine_chunks(chunks):
    combined = defaultdict(str)   
    for item in chunks:
        combined[item['source_type']] += item['text']
    result = [{'source_type': doc_id, 'text': text} for doc_id, text in combined.items()]
    return result

