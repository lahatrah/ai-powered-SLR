from Bio import Entrez
import requests
import lxml.etree as ET
import re
import json
import os
import time


with open("authentification.json","r") as f:
    AUTH_KEYS = json.load(f)

with open("prompts.json","r") as f:
    PROMPTS = json.load(f)

Entrez.email = AUTH_KEYS["email"]
Entrez.api_key = AUTH_KEYS["ncbi_api_key"]
query = PROMPTS["pubmed_search"]

def search_pmc_open_access(query, paper_results):
    """
    Search PMC for open-access articles and return PMCIDs.
    """
    handle = Entrez.esearch(
        db="pmc",
        term=f"{query} AND open access[filter]",
        retmax=paper_results,
        sort="relevance",
        usehistory="y"
    )
    results = Entrez.read(handle)
    handle.close()
    return results["IdList"]

def fetch_article_xml(pmcid):
    """
    Fetch XML for a given PMCID from PMC.
    """
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id={pmcid}&retmode=xml"
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    return None

def extract_metadata_and_paragraphs(xml_content, id_counter):
    """
    Extract metadata, paragraphs, and tables from PMC XML.
    """
    try:
        root = ET.fromstring(xml_content.encode('utf-8'))
        
        # Extract metadata
        title = root.find(".//article-title")
        title_text = "".join(title.itertext()).strip() if title is not None else "No title available"
        
        authors = []
        for contrib in root.findall(".//contrib[@contrib-type='author']//name"):
            surname = contrib.find("surname")
            given_names = contrib.find("given-names")
            if surname is not None and given_names is not None:
                authors.append(f"{given_names.text} {surname.text}")
        author_text = ", ".join(authors) if authors else "No authors available"
        
        pmcid = root.find(".//article-id[@pub-id-type='pmcid']")
        pmcid_text = pmcid.text if pmcid is not None else "Unknown"
        url_text = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmcid_text}/"
        
        journal = root.find(".//journal-title")
        journal_text = "".join(journal.itertext()).strip() if journal is not None else "No journal available"
        
        doi = root.find(".//article-id[@pub-id-type='doi']")
        doi_text = doi.text if doi is not None else "No DOI available"
        
        # Extract paragraphs and tables from <body>
        body = root.find(".//body")
        content_objects = []
        if body is not None:
            # Extract paragraphs from <p> tags
            for elem in body.iter("p"):
                if elem.text:
                    text = "".join(elem.itertext()).strip()
                    text = re.sub(r'\[\d+(,\d+)*\]', '', text)
                    text = re.sub(r'\s+', ' ', text)
                    if text:
                        content_objects.append({"type": "paragraph", "text": text})
            
            # Extract tables from <table-wrap> tags
            for table_wrap in body.iter("table-wrap"):
                table_text_parts = []
                # Get caption if available
                caption = table_wrap.find(".//caption")
                if caption is not None:
                    caption_text = "".join(caption.itertext()).strip()
                    if caption_text:
                        table_text_parts.append(caption_text)
                
                # Get table content
                table = table_wrap.find(".//table")
                if table is not None:
                    for row in table.iter("tr"):
                        row_cells = []
                        for cell in row.iter("td", "th"):
                            cell_text = "".join(cell.itertext()).strip()
                            if cell_text:
                                row_cells.append(cell_text)
                        if row_cells:
                            row_text = ", ".join(row_cells)
                            table_text_parts.append(f"Row: {row_text}")
                
                if table_text_parts:
                    table_text = "; ".join(table_text_parts)
                    table_text = re.sub(r'\[\d+(,\d+)*\]', '', table_text)
                    table_text = re.sub(r'\s+', ' ', table_text)
                    content_objects.append({"type": "table", "text": table_text})
        
        if not content_objects:  
            return None
        
        article_objects = []
        for content in content_objects:
            article_objects.append({
                "source_type": str(id_counter),
                "Author": author_text,
                "Title": title_text,
                "URL": url_text,
                "Journal": journal_text,
                "DOI": doi_text,
                "text": content["text"]
            })
        
        return article_objects
    except ET.ParseError:
        return None

def save_articles_json(articles, output_file="input.json"):
    """
    Save list of articles to a JSON file.
    """
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

def main():
    paper_results = 1000 
    delay = 0.34 if Entrez.api_key is None else 0.1
    
    try:
        pmc_ids = search_pmc_open_access(query, paper_results)
    except Exception as e:
        print(f"Search failed: {e}")
        return
    
    if not pmc_ids:
        print("No open-access articles found.")
        return
    
    articles = []
    id_counter = 1
    
    for i, pmcid in enumerate(pmc_ids, 1):
        print(f"Processing article {i}/{len(pmc_ids)}: PMCID {pmcid}")
        xml_content = fetch_article_xml(pmcid)
        if xml_content:
            article_objects = extract_metadata_and_paragraphs(xml_content, id_counter)
            if article_objects: 
                articles.extend(article_objects)
                id_counter += 1
                print(f"Successfully processed PMCID {pmcid} with {len(article_objects)} objects")
            else:
                print(f"Failed to extract content for PMCID {pmcid}")
        else:
            print(f"Failed to fetch XML for PMCID {pmcid}")
        time.sleep(delay)  
    
    if articles:
        save_articles_json(articles)
    else:
        print("No articles were successfully processed.")

if __name__ == "__main__":
    main()