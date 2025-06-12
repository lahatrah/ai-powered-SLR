# AI-Powered Curation of Updated Aedes Datasets for Global Mosquito Distribution Mapping using LLMs

This project consists of Building spatiotemporal datasets of `Aedes aegypti` and `Aedes albopictus` by leveraging state-of-the-art
Artificial Intelligence to extract the information from scientific publications.


## Context

The ongoing crisis of climate change forces us to have a constant monitoring of disease burden, namely arboviruses diseases such as
Dengue, Chikungunya, Yellow Fever, Zika, which are climate-sensitive. The datasets fed in the risk assessments models are outdated and the need to update them is urgent to have efficient public health policy and measures. To update the datasets, information should be gathered from various sources, and there comes the AI!!! Let us let the AI sift through these sources, Thank you AI!!!

## Main files

- `pubmed_full_text.py` : Retrieve the full text of papers from Pubmed based on a query
- `input_prep.py` : Prepare the input to be fed in the LLM
- `data_extraction.ipynb` : Extract the information from the input
- `post_processing.ipynb` : Post-process the retrieved information

### utilities 

- `authentification.json` : authentification information
- `visualization.py` : functions to build the visualizations
- `prompts.json` : search query and prompts
- `text_processor_utilities.py` : functions to prepare the inputs

### Old version

If papers are not available on PubMed and pdfs are available :

- `input_prep_pdf.py` instead of `input_prep.py`




