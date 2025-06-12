from text_extractor_utilities import process_pdfs
from text_proccessor_utilities import process_text_files,filter_species,filter_date_loc,combine_chunks
import json
PDF_FOLDER = "pdf_folder"
TEXT_FOLDER  = "text_folder"
OUTPUT_FILE = "input.json"
def prepare_input(pdf_folder=PDF_FOLDER,text_folder=TEXT_FOLDER,input=OUTPUT_FILE):
    """
    wrap up the process to prepare the input from folder of pdfs to input

    @params:
        - pdf_folder: folder that contains the pdfs
        - text_folder: folder that contains the texts
        - input : the input file 
    """

    process_pdfs(pdf_folder, text_folder)
    data = process_text_files(text_folder)
    data = filter_species(data)
    data = filter_date_loc(data)
    data = combine_chunks(data)

    with open(input,"w") as f:
        json.dump(data,f,indent=4)


if __name__=="__main__":
    prepare_input()



