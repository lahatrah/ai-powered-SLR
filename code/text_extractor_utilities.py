# general import
import os
import pandas as pd
from pdf2image import convert_from_path
from pytesseract import image_to_string
import PyPDF2
import re
import logging
from tqdm import tqdm
import camelot.io as camelot

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_text_with_pypdf2(pdf_path):
    """
    Extract text using PyPDF2 library
    
    @params:
        - pdf_path: path to the PDF file
        
    @returns:
        - extracted text as string
    """
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n\n"
        
        # If text extraction returned substantial content, return it
        if len(re.sub(r'\s+', '', text)) > 100:  
            return text
    except Exception as e:
        logger.warning(f"PyPDF2 extraction failed: {e}")
    
    return None

def convert_pdf_to_img(pdf_file):
    """
    Convert a PDF into Images
    
    @params:
        - pdf_file: the file to be converted
    
    @returns:
        - an iterable containing image format of all the pages of the PDF
    """
    try:
        return convert_from_path(pdf_file)
    except Exception as e:
        logger.error(f"Error converting PDF to images: {e}")
        return []

def convert_image_to_text(file):
    """
    Extract text from image using OCR
    
    @params:
        - file: the image file to extract the content
    
    @returns:
        - the textual content of single image
    """
    try:
        text = image_to_string(file)
        return text
    except Exception as e:
        logger.error(f"Error in OCR: {e}")
        return ""

def extract_tables_with_camelot(pdf_path):
    """
    Extract tables from PDF using Camelot
    
    @params:
        - pdf_path: path to the PDF file
        
    @returns:
        - a dictionary with page numbers as keys and list of tables as values
    """
    tables_by_page = {}
    
    try:
        # Try lattice mode first (for tables with borders)
        tables = camelot.read_pdf(pdf_path, pages='all', flavor='lattice')
        
        # If no tables found with lattice, try stream mode (for tables without clear borders)
        if len(tables) == 0:
            tables = camelot.read_pdf(pdf_path, pages='all', flavor='stream')
        
        # Process each table
        for i, table in enumerate(tables):
            if table.df.empty:
                continue
                
            page_num = table.parsing_report['page']
            
            # Format table text
            table_text = f"\n\n{'-'*20} TABLE {i+1} {'-'*20}\n"
            table_text += table.df.to_string(index=False) + "\n"
            table_text += f"{'-'*50}\n"
            
            # Add to dictionary, creating list if page not already present
            if page_num not in tables_by_page:
                tables_by_page[page_num] = []
            tables_by_page[page_num].append(table_text)
            
    except Exception as e:
        logger.warning(f"Camelot table extraction failed: {str(e)}")
        try:
            # Get total page count
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                
            # Process pages individually
            for page_num in range(1, total_pages + 1):
                try:
                    page_tables = camelot.read_pdf(pdf_path, pages=str(page_num), flavor='lattice')
                    if len(page_tables) == 0:
                        page_tables = camelot.read_pdf(pdf_path, pages=str(page_num), flavor='stream')
                    
                    for i, table in enumerate(page_tables):
                        if table.df.empty:
                            continue
                            
                        # Format table text
                        table_idx = len(tables_by_page.get(page_num, [])) + 1
                        table_text = f"\n\n{'-'*20} TABLE ON PAGE {page_num} ({table_idx}) {'-'*20}\n"
                        table_text += table.df.to_string(index=False) + "\n"
                        table_text += f"{'-'*50}\n"
                        
                        # Add to dictionary
                        if page_num not in tables_by_page:
                            tables_by_page[page_num] = []
                        tables_by_page[page_num].append(table_text)
                except Exception as page_e:
                    continue
        except Exception as fallback_e:
            logger.warning(f"Fallback table extraction failed: {str(fallback_e)}")
    
    return tables_by_page

def get_text_from_any_pdf(pdf_path):
    """
    Extract both regular text and tables from a PDF, 
    
    @params:
        - pdf_path: path to the PDF file
        
    @returns:
        - combined text from the PDF with tables in context
    """
    tables_by_page = extract_tables_with_camelot(pdf_path)
    
    total_pages = 0
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
    except Exception as e:
        total_pages = 1000
    
    # Try to extract text using PyPDF2
    pypdf_text = extract_text_with_pypdf2(pdf_path)
    
    if pypdf_text:
        logger.info(f"Successfully extracted text with PyPDF2")   
        combined_text = ""   
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num in range(len(pdf_reader.pages)):
                    actual_page_num = page_num + 1  
                    page_text = pdf_reader.pages[page_num].extract_text()
                    
                    combined_text += f"\n\nPAGE {actual_page_num}:\n{page_text}\n"
                    
                    # Insert tables for this page if present
                    if actual_page_num in tables_by_page:
                        for table in tables_by_page[actual_page_num]:
                            combined_text += table
        except Exception as e:
            logger.warning(f"Page-by-page extraction failed: {e}")
            
            # Fallback: use the whole text with tables inserted at the end
            combined_text = pypdf_text
            
            for page_num, tables in sorted(tables_by_page.items()):
                for table in tables:
                    combined_text += f"\n\nFrom Page {page_num}:\n{table}"
    
    else:
        # Fall back to OCR for scanned PDFs
        logger.info(f"Using OCR for text extraction")
        images = convert_pdf_to_img(pdf_path)
        combined_text = ""
        
        # Process each page
        for pg, img in enumerate(images):
            page_num = pg + 1  
            page_text = convert_image_to_text(img)
            
            # Add page header
            combined_text += f"\n\nPAGE {page_num}:\n{page_text}"
            
            # Insert tables for this page if present
            if page_num in tables_by_page:
                for table in tables_by_page[page_num]:
                    combined_text += table
    
    return combined_text

def process_pdfs(input_folder, output_folder):
    """
    Process all PDFs in a folder
    
    @params:
        - input_folder: folder containing PDF files
        - output_folder: folder to save extracted text files
    """
    os.makedirs(output_folder, exist_ok=True)
    
    pdf_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.pdf')]
    total_files = len(pdf_files)
    
    # Loop through each PDF file in the input folder
    for counter, filename in enumerate(tqdm(pdf_files, desc="Processing PDFs"), 1):
        pdf_path = os.path.join(input_folder, filename)
        
        try:
            logger.info(f"Processing {counter}/{total_files}: {filename}")
            
            text = get_text_from_any_pdf(pdf_path)
            
            base_name = os.path.splitext(filename)[0]
            output_file = base_name + ".txt"
            output_path = os.path.join(output_folder, output_file)
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)
                
            logger.info(f"Completed {filename} -> {output_file} ({counter}/{total_files})")
            
        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    input_folder = "input_folder"      
    output_folder = "output_folder"     
    process_pdfs(input_folder, output_folder)