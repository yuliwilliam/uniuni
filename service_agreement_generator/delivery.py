import os

import pandas as pd
from docx import Document

from utils import replace_term_in_word, find_state_name

if __name__ == '__main__':
    # Example usage
    weekly_agreement_template_path = "Form Delivery Services Agreement 8.19.2024 - (Weekly Invoicing).docx"
    two_week_agreement_template_path = "Form Delivery Services Agreement 8.19.2024 - (Two Week Invoicing).docx"

    agreement_data_path = "./朕的excel.xlsx"


    if not os.path.exists(f"./{weekly_agreement_template_path.replace('.docx', '')}"):
        os.makedirs(f"./{weekly_agreement_template_path.replace('.docx', '')}")
    if not os.path.exists(f"./{two_week_agreement_template_path.replace('.docx', '')}"):
        os.makedirs(f"./{two_week_agreement_template_path.replace('.docx', '')}")

    df = pd.read_excel(agreement_data_path)
    for index, row in df.iterrows():
        legal_name = row["Legal Name"]
        email = row["email"]
        company_address = row["Company Address"]
        payment_term = row["payment term"]

        agreement_template_path = weekly_agreement_template_path
        if payment_term == "two week invoice":
            agreement_template_path = two_week_agreement_template_path
        agreement_template = Document(agreement_template_path)

        replace_term_in_word(agreement_template, "__________________ 202____", "September 10, 2024")
        replace_term_in_word(agreement_template, "legal@uniuni.com (“Company”) AND _______________________________,", f"legal@uniuni.com (“Company”) AND {legal_name.upper()},")
        replace_term_in_word(agreement_template, "under the laws of _____________________________,", f"under the laws of the State of {find_state_name(company_address)},")
        replace_term_in_word(agreement_template, "with an address at _________________________________________________;", f"with an address at {company_address};")
        replace_term_in_word(agreement_template, "Email: ______________________ (“Contractor”).", f"Email: {email.lower()} (“Contractor”).")
        replace_term_in_word(agreement_template, "[NAME OF CONTRACTOR]", legal_name.upper())

        agreement_template.save(f"./{agreement_template_path.replace('.docx', '')}/{legal_name} {agreement_template_path}")

        print(f"{index + 1}/{len(df)} done")

    print("Term replaced and document saved successfully.")