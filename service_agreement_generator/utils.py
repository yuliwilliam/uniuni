import re

from service_agreement_generator.us_state_abbrev import abbrev_to_us_state


def replace_term_in_word(doc, old_term, new_term):
    # Iterate through paragraphs and replace the term
    for paragraph in doc.paragraphs:
        if old_term in paragraph.text:
            paragraph.text = paragraph.text.replace(old_term, new_term)

    # Iterate through tables (if your document has any tables)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if old_term in cell.text:
                    cell.text = cell.text.replace(old_term, new_term)


def find_state_name(address):
    pattern = r"[\s,]([A-Za-z]{2})[\s,]+\d{5}"
    match = re.search(pattern, address)
    state_abbrev = match.group(1)
    return abbrev_to_us_state[state_abbrev.upper()]
