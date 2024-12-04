import os

import pandas as pd
from docx import Document

from utils import replace_term_in_word, find_state_name

if __name__ == '__main__':
    # Example usage
    agreement_template_path = "Sorting Services Agreement U.S - Template.docx"

    agreement_data_path = "./Payment term for US DSPs checklist.xlsx"


    if not os.path.exists(f"./{agreement_template_path.replace('.docx', '')}"):
        os.makedirs(f"./{agreement_template_path.replace('.docx', '')}")

    df = pd.read_excel(agreement_data_path)
    for index, row in df.iterrows():
        legal_name = row["Legal Name"]
        email = row["email"]
        company_address = row["Company Address"]

        agreement_template = Document(agreement_template_path)

        replace_term_in_word(agreement_template, "June 3, 2024", "October 11, 2024")
        replace_term_in_word(agreement_template, "[Full legal name of entity]", legal_name.upper())
        replace_term_in_word(agreement_template, "[jurisdiction of formation]", find_state_name(company_address))
        replace_term_in_word(agreement_template, "[Contractor Address]", company_address)
        replace_term_in_word(agreement_template, "[email address] ", email.lower())
        replace_term_in_word(agreement_template, "[Legal Entity Name TBC]", legal_name.upper())

        agreement_template.save \
            (f"./{agreement_template_path.replace('.docx', '')}/{legal_name} {agreement_template_path}")

        print(f"{index + 1}/{len(df)} done")

