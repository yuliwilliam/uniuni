from enum import Enum


class AdjustmentType(Enum):
    DEDUCTION_POD = 1
    DEDUCTION_DNR = 2
    DEDUCTION_TNU = 3
    DEDUCTION_TNU_PARCEL_LOST = 4
    REIMBURSEMENT = 5
    COMPENSATION = 6


class DSP:
    def __init__(self, team_name: str, team_id: int, warehouse_code: str):
        self.team_name: str = team_name
        self.team_id: int = team_id
        self.warehouse_code: str = warehouse_code
        self.period_to_salary: dict[str, float] = {}
        self.parcels: dict[str, Parcel] = {}

    def get_key(self):
        return self.warehouse_code + str(self.team_id)

    def add_salary(self, period, salary):
        self.period_to_salary[period] = salary

    def update_parcel(self, parcel):
        self.parcels[parcel.tracking_number] = parcel

    def get_parcel(self, tracking_number):
        return self.parcels.get(tracking_number, Parcel(tracking_number))


    def calculate_deductions(self):
        total = 0
        for parcel in self.parcels.values():
            total += parcel.calculate_deduction()
        return round(total, 2)

    def calculate_reimbursements(self):
        total = 0
        for parcel in self.parcels.values():
            total += parcel.calculate_reimbursement()
        return round(total, 2)

    def calculate_adjustments(self):
        total = 0
        for parcel in self.parcels.values():
            total += parcel.calculate_adjustment()
        return round(total, 2)

    def calculate_adjustments_by_type(self, adjustment_type):
        total = 0
        for parcel in self.parcels.values():
            total += parcel.get_total_adjustment_value_by_type(adjustment_type)
        return round(total, 2)

    def calculate_salary(self, period):
        if period not in self.period_to_salary:
            self.period_to_salary[period] = 0

        salary = self.period_to_salary[period]
        for parcel in self.parcels.values():
            parcel_salary = parcel.calculate_adjustment()
            salary += parcel_salary
        return round(salary, 2)


class Adjustment:
    def __init__(self, adjustment_type: AdjustmentType, period: str, value: float):
        self.adjustment_type = adjustment_type
        self.period = period
        self.value = value

    def __str__(self):
        return f"Adjustment(type={self.adjustment_type.name}, period={self.period}, value={self.value})"


class Parcel:
    def __init__(self, tracking_number: str):
        super().__init__()
        self.tracking_number: str = tracking_number
        self.adjustments: list[Adjustment] = []
        self.max_dnr_deduction: float = -60

    def __str__(self):
        adjustments_str = ", ".join(str(adj) for adj in self.adjustments)
        return (f"Parcel(tracking_number={self.tracking_number}, "
                f"max_dnr_deduction={self.max_dnr_deduction}, "
                f"adjustments=[{adjustments_str}])")

    def add_deduction(self, deduction_type, value, period):
        assert value <= 0
        self.add_adjustment(Adjustment(deduction_type, period, value))

    def add_reimbursement(self, value, period):
        self.add_adjustment(Adjustment(AdjustmentType.REIMBURSEMENT, period, value))

    def add_adjustment(self, adjustment: Adjustment):
        self.adjustments.append(adjustment)

    def get_total_adjustment_value_by_type(self, adjustment_type: AdjustmentType):
        return sum(
            [adjustment.value for adjustment in self.adjustments if adjustment.adjustment_type == adjustment_type])

    def calculate_deduction(self):
        tnu = self.get_total_adjustment_value_by_type(
            AdjustmentType.DEDUCTION_TNU) + self.get_total_adjustment_value_by_type(
            AdjustmentType.DEDUCTION_TNU_PARCEL_LOST)
        pod = self.get_total_adjustment_value_by_type(AdjustmentType.DEDUCTION_POD)
        dnr = self.get_total_adjustment_value_by_type(AdjustmentType.DEDUCTION_DNR)

        if dnr < 0 and dnr + tnu + pod < self.max_dnr_deduction:
            dnr = min(self.max_dnr_deduction - tnu - pod, 0)  # must be non-negative

        return dnr + tnu + pod

    def calculate_reimbursement(self):
        return self.get_total_adjustment_value_by_type(AdjustmentType.REIMBURSEMENT)

    def calculate_adjustment(self):
        return self.calculate_deduction() + self.calculate_reimbursement()
