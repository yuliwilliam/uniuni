import os

import pandas as pd
from docx import Document

from utils import replace_term_in_word, find_state_name

if __name__ == '__main__':
    # Example usage
    agreement_template_path = "Sorting Services Agreement U.S - Template V2.docx"

    agreement_data_path = "./Sorter list.xlsx"


    if not os.path.exists(f"./{agreement_template_path.replace('.docx', '')}"):
        os.makedirs(f"./{agreement_template_path.replace('.docx', '')}")

    df = pd.read_excel(agreement_data_path)
    for index, row in df.iterrows():
        legal_name = row["Full legal name of entity"]
        email = row["email address"]
        company_address = row["Contractor Address"]
        delivery_rate = row["rate"]

        agreement_template = Document(agreement_template_path)

        print(legal_name)

        replace_term_in_word(agreement_template, "June 3, 2024", "October 15, 2024")
        replace_term_in_word(agreement_template, "[Full legal name of entity]", legal_name.upper())
        replace_term_in_word(agreement_template, "[jurisdiction of formation]", find_state_name(company_address))
        replace_term_in_word(agreement_template, "[Contractor Address]", company_address)
        replace_term_in_word(agreement_template, "[email address] ", email.lower())
        replace_term_in_word(agreement_template, "[Legal Entity Name TBC]", legal_name.upper())
        replace_term_in_word(agreement_template, "[Delivery Rate]", delivery_rate)

        agreement_template.save \
            (f"./{agreement_template_path.replace('.docx', '')}/{legal_name} {agreement_template_path}")

        print(f"{index + 1}/{len(df)} done")

