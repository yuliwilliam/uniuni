import os

import pandas as pd

from payment_merger import split_dnr_pod
from payment_merger import find_tracking_number_column_name, find_amount_column_name, \
    find_warehouse_column_name, find_team_id_column_name


def list_xlsx_files(directory):
    result = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.xlsx'):
                result.append(f"{directory}/{file}")
    return result


if __name__ == '__main__':
    split_dnr_pod("./W41/DNR&POD1013.xlsx")
