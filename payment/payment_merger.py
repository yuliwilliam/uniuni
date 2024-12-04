import math
import os
import re

import pandas as pd
from pandas import DataFrame

from parcel import DSP, AdjustmentType

adjustment_type_to_column_name = {
    AdjustmentType.DEDUCTION_POD: "Pod Penalty",
    AdjustmentType.DEDUCTION_DNR: "DNR Penalty",
    AdjustmentType.DEDUCTION_TNU: "Package Inactivity Penalty",
    AdjustmentType.DEDUCTION_TNU_PARCEL_LOST: "Lost Package Penalty",
    AdjustmentType.REIMBURSEMENT: "Reimbursement",
    AdjustmentType.COMPENSATION: "compensation"
}

adjustment_type_key_to_adjustment_type = {
    "DNR": AdjustmentType.DEDUCTION_DNR,
    "Penalty": AdjustmentType.COMPENSATION,
    "POD Fail": AdjustmentType.DEDUCTION_POD,
    "parcel lost": AdjustmentType.DEDUCTION_TNU_PARCEL_LOST,
    "Parcel Lost": AdjustmentType.DEDUCTION_TNU_PARCEL_LOST,
    "inactivity": AdjustmentType.DEDUCTION_TNU,
    "inactivity penalty": AdjustmentType.DEDUCTION_TNU,
    "Inactivity Penalty": AdjustmentType.DEDUCTION_TNU,
    "Penalty Gap": AdjustmentType.COMPENSATION
}


def validate_dsp_key(s):
    pattern = r'[A-Z]{3}\d{2,3}'
    return bool(re.fullmatch(pattern, s))


def find_str_with_most_targets(strings: [str], targets: [str]):
    # Function to count how many targets are in a string, case-insensitive
    def count_targets(s: str, targets: [str]):
        s_lower = s.lower()
        return sum(1 for target in targets if target.lower() in s_lower)

    # Find the string with the most targets
    max_string = max(strings, key=lambda s: count_targets(s, targets))

    if count_targets(max_string, targets) == 0:
        raise Exception("unable to find target")

    return max_string


def count_by_pattern(series, pattern_str):
    return series.apply(lambda x: bool(re.compile(pattern_str).match(str(x)))).sum()


def find_column_by_value_regex(df, pattern):
    code_counts = df.apply(lambda series: count_by_pattern(series, pattern))
    most_likely_column = code_counts.idxmax()

    return most_likely_column


def find_tracking_number_column_name(df: DataFrame):
    pattern = r'UUS\d{2}[A-Za-z]{1}\d{13}'
    targets = ["包裹號", "Tracking Number", "TNO", "包裹号", "运单号", "Tracking"]
    try:
        return find_str_with_most_targets(df.columns, targets)
    except Exception as e:
        if str(e) == "unable to find target":
            return find_column_by_value_regex(df, pattern)
        else:
            raise e


def find_warehouse_column_name(df: DataFrame):
    targets = ["所属仓库", "Warehouse", "Zone", "城市代码", "Area", "仓库ID", "whs"]
    return find_str_with_most_targets(df.columns, targets)


def find_team_id_column_name(df: DataFrame):
    targets = ["Team Id", "team_id", "TeamId", "DSP Name"]
    return find_str_with_most_targets(df.columns, targets)


def find_amount_column_name(df: DataFrame):
    targets = ["$Net fined", "Amount", "reimbursement", "罚款金额$60\nFine Amount $60/parcel", "罚款金额",
               "total_value", "Parcel Value", "reimbursement"]
    return find_str_with_most_targets(df.columns, targets)


def find_adjustment_type_column_name(df: DataFrame):
    targets = ["Reason", "Type"]
    return find_str_with_most_targets(df.columns, targets)


def list_xlsx_files(directory):
    result = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.xlsx'):
                result.append(f"{directory}/{file}")
    return result


#
# def find_dnr_file(file_names):
#     targets = ["DNR"]
#     return find_str_with_most_targets(file_names, targets)
#
# def find_tnu_file(file_names):
#     targets = ["inactivity penalty"]
#     return find_str_with_most_targets(file_names, targets)
#
# def find_tnu_parcel_lost_file(file_names):
#     targets = ["parcel lost"]
#     return find_str_with_most_targets(file_names, targets)
#
# def find_tnu_parcel_lost_file(file_names):
#     targets = ["parcel lost"]
#     return find_str_with_most_targets(file_names, targets)

def add_adjustment_from_file(dsps: dict[str, DSP], file_name: str, adjustment_type: AdjustmentType):
    df = pd.read_excel(file_name)

    team_id_column_name = find_team_id_column_name(df)
    tracking_number_column_name = find_tracking_number_column_name(df)
    amount_column_name = find_amount_column_name(df)

    warehouse_column_name = None
    try:
        warehouse_column_name = find_warehouse_column_name(df)
    except Exception:
        pass

    for i, row in df.iterrows():
        curr_adjustment_type = adjustment_type

        # check if it is a valid team id, not nan
        try:
            team_id = int(row[team_id_column_name])
            if team_id == 0:
                continue
        except Exception:
            print(row[warehouse_column_name], row[team_id_column_name])
            continue


        if warehouse_column_name is not None:
            dsp_key = row[warehouse_column_name].strip() + str(int(row[team_id_column_name])).strip()
        else:
            print(f"cannot find exact dsp key in {file_name}")
            dsp_key = ""
            for key in dsps.keys():
                if str(int(row[team_id_column_name])) in key:
                    dsp_key = key

        assert validate_dsp_key(
            dsp_key), f"[{file_name}][{i + 1}] invalid dsp key {dsp_key}, team id column name {team_id_column_name}, warehouse column name {warehouse_column_name}"

        dsp = dsps.get(dsp_key, DSP("", int(row[team_id_column_name]),
                                    row[warehouse_column_name] if warehouse_column_name is not None else ""))
        parcel = dsp.get_parcel(row[tracking_number_column_name])

        value = row[amount_column_name]
        # Remove dollar sign if present and convert to float
        if isinstance(value, str) and '$' in value:
            value = float(value.replace('$', ''))
        if isinstance(value, str) and value.strip() == "":
            value = 0
        if isinstance(value, int):
            value = float(value)

        assert isinstance(value, float) and not math.isnan(
            value), f"[{file_name}][{i + 1}][{amount_column_name}] {type(value)} {value} is not a valid amount"

        if curr_adjustment_type is None:
            adjustment_type_key = row[find_adjustment_type_column_name(df)]
            curr_adjustment_type = adjustment_type_key_to_adjustment_type[adjustment_type_key.strip()]

        assert curr_adjustment_type is not None, f"[{file_name}][{i + 1}]adjustment type is None"

        if curr_adjustment_type != AdjustmentType.REIMBURSEMENT:
            value = -1 * abs(value)  # the number is always negative since it is deduction
            parcel.add_deduction(curr_adjustment_type, value, "")
        else:
            parcel.add_reimbursement(value, "")

        dsp.update_parcel(parcel)
        dsps[dsp.get_key()] = dsp


def split_dnr_pod(file_name):
    df = pd.read_excel(file_name)

    # Split the DataFrame into two based on whether 'Type' contains 'abc' or not
    dnr_df = df[df['Type'].str.lower().str.contains('dnr')]
    pod_df = df[df['Type'].str.lower().str.contains('pod')]

    # Create a Pandas Excel writer using XlsxWriter as the engine
    dnr_df.to_excel('DNR.xlsx', index=False)
    pod_df.to_excel('POD.xlsx', index=False)

    return f"DNR.xlsx", f"POD.xlsx"


if __name__ == '__main__':
    week = "W47"
    dsps = {}

    source_file_name = f"./{week}/Payment Details.xlsx"
    payment_df = pd.read_excel(source_file_name)
    column_names = payment_df.columns

    # populate DSP dictionary in advance
    for index, row in payment_df.iterrows():
        dsp_key = row[find_warehouse_column_name(payment_df)] + str(int(row[find_team_id_column_name(payment_df)]))
        assert validate_dsp_key(dsp_key), f"invalid dsp key {dsp_key}"

        dsp = dsps.get(dsp_key,
                       DSP("", int(row[find_team_id_column_name(payment_df)]),
                           row[find_warehouse_column_name(payment_df)]))
        dsps[dsp.get_key()] = dsp

    add_adjustment_from_file(dsps, f"./{week}/deduction.xlsx", None)
    add_adjustment_from_file(dsps, f"./{week}/POD DNR 1125.xlsx", None)
    add_adjustment_from_file(dsps, f"./{week}/reimbursment.xlsx", AdjustmentType.REIMBURSEMENT)

    dsp_keys = set(dsps.keys())
    applied_adjustments = {}
    remaining_adjustments = {}

    for index, row in payment_df.iterrows():
        dsp_key = row[find_warehouse_column_name(payment_df)] + str(int(row[find_team_id_column_name(payment_df)]))

        if dsp_key in dsps:
            for adjustment_type in AdjustmentType:
                val = dsps[dsp_key].calculate_adjustments_by_type(adjustment_type)
                payment_df.at[index, adjustment_type_to_column_name[adjustment_type]] = val
                applied_adjustments[adjustment_type] = applied_adjustments.get(adjustment_type, 0) + val
            dsp_keys.remove(dsp_key)

    for dsp_key in dsp_keys:
        for adjustment_type in AdjustmentType:
            val = dsps[dsp_key].calculate_adjustments_by_type(adjustment_type)
            remaining_adjustments[adjustment_type] = remaining_adjustments.get(adjustment_type, 0) + val

    print(f"{len(dsp_keys)} DSPs not in payment: {', '.join(dsp_keys)}")

    summary_index = len(payment_df) + 5

    # Add empty rows up to the summary_index
    empty_rows_needed = summary_index - len(payment_df) + 1
    empty_rows = pd.DataFrame([[None] * len(payment_df.columns)] * empty_rows_needed, columns=payment_df.columns)
    payment_df = pd.concat([payment_df, empty_rows], ignore_index=True)

    print()
    print("applied total")
    payment_df.at[summary_index, 0] = "applied total"
    for adjustment_type, value in applied_adjustments.items():
        payment_df.at[summary_index, adjustment_type_to_column_name[adjustment_type]] = value
        print(f"{adjustment_type.name}: {value}")

    print()
    print("remaining total")
    summary_index += 1
    payment_df.at[summary_index, 0] = "remaining total"
    for adjustment_type, value in remaining_adjustments.items():
        payment_df.at[summary_index, adjustment_type_to_column_name[adjustment_type]] = value
        print(f"{adjustment_type.name}: {value}")

    payment_df.to_excel(f"./{week}/{week} Result.xlsx", index=False)
