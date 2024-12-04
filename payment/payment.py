import pandas as pd

from db import save_dsp_to_mongodb, save_parcel_to_mongodb
from parcel import DSP, Parcel, AdjustmentType, deduction_type_to_reason


def find_deduction_type(value):
    for deduction_type, value_list in deduction_type_to_reason.items():
        if value in value_list:
            return deduction_type
    return AdjustmentType.DEDUCTION_TNU_PARCEL_LOST


def read_deductions():
    source_file_name = "March.xlsx"

    # Read the Excel file
    deduction_df = pd.read_excel(source_file_name)
    reimbursement_df = pd.read_excel(source_file_name, sheet_name=1)

    deductions = {}

    for _, row in deduction_df.iterrows():
        tracking_number = row["TNO"]
        value = row["$Net fined"]
        period = row["Date"]
        d_type = find_deduction_type(row["Reason"])

        # Remove dollar sign if present and convert to float
        if isinstance(value, str) and '$' in value:
            value = float(value.replace('$', ''))
        if isinstance(value, str) and value.strip() == "":
            value = 0

        value = -1 * abs(value)  # the number is always negative since it is deduction

        deduction = deductions.get(tracking_number, Parcel(tracking_number))
        deduction.add_deduction(d_type, value, period)
        deductions[tracking_number] = deduction

    for _, row in reimbursement_df.iterrows():
        tracking_number = row["TNO"]
        value = row["reimbursement"]
        period = row["Date"]

        if isinstance(value, str) and '$' in value:
            value = float(value.replace('$', ''))
        if isinstance(value, str) and value.strip() == "":
            value = 0

        deduction = deductions.get(tracking_number, Parcel(tracking_number))
        deduction.add_reimbursement(value, period)
        deductions[tracking_number] = deduction

    return deductions


def read_salary():
    source_file_name = "us_dsp_1099_salary_v4_2024-08-26_w35.xlsx"
    df = pd.read_excel(source_file_name)

    dsps = []

    for _, row in df.iterrows():
        dsp = DSP(row["team_name"], row["team_id"], row["warehouse"])
        dsp.add_salary("temp", row["total_salary"])
        dsps.append(dsp)

    return dsps


def read_TNU():
    source_file_name = "Week 34 断更罚款.xlsx"
    df = pd.read_excel(source_file_name)

    deductions = {}
    # for _, row in df.iterrows():


#         tracking_number = row["包裹號
# Tracking Number (TNO)"]
#
#         deduction = deductions.get(tracking_number, Deduction(tracking_number))
#         deduction.add_reimbursement(value, period)
#         deductions[tracking_number] = deduction

if __name__ == '__main__':

    period = "w34"
    dsps = {}

    source_file_name = "./payment/us_dsp_1099_salary_v4_2024-08-26_w35.xlsx"
    salary_df = pd.read_excel(source_file_name)

    for _, row in salary_df.iterrows():
        dsp = DSP(row["team_name"], row["team_id"], row["warehouse"])
        dsp.add_salary(period, row["total_salary"])
        dsps[dsp.get_key()] = dsp

    source_file_name = "./payment/Week 34 断更罚款.xlsx"
    tnu_df = pd.read_excel(source_file_name)

    for _, row in tnu_df.iterrows():
        team_id = row["team_id"]
        team_name = row["DSP号\nDSP Code"]
        if team_id == 0:
            continue

        warehouse_code = row["所属仓库\nWarehouse "]
        tracking_number = row["包裹號\nTracking Number (TNO)"]

        value = row["罚款金额$60\nFine Amount $60/parcel"]
        if isinstance(value, str) and '$' in value:
            value = float(value.replace('$', ''))
        if isinstance(value, str) and value.strip() == "":
            value = 0
        value = -1 * abs(value)  # the number is always negative since it is deduction

        dsp_key = warehouse_code + str(team_id)
        dsp = dsps.get(dsp_key, DSP(team_name, team_id, warehouse_code))
        parcel = dsp.get_parcel(tracking_number)

        parcel.add_deduction(AdjustmentType.DEDUCTION_TNU, value, period)
        dsp.update_parcel(parcel)

    for dsp in dsps.values():
        print(dsp.get_key(), dsp.period_to_salary[period], dsp.calculate_salary(period))
        save_dsp_to_mongodb(dsp)

        for parcel in dsp.parcels.values():
            print(parcel)
            save_parcel_to_mongodb(parcel)
