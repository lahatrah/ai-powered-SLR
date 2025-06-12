from text_proccessor_utilities import filter_species,filter_date_loc,combine_chunks
import json

FILE = "input.json"
def prepare_input(input=FILE):
    """
    wrap up the process to prepare the input

    @params:
        - FILE: the input file

    """

    data = filter_species(data)
    data = filter_date_loc(data)
    data = combine_chunks(data)

    with open(FILE,"w") as f:
        json.dump(data,f,indent=4)


if __name__=="__main__":
    prepare_input()



