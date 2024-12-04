from pymongo import MongoClient

from parcel import DSP, Parcel

client = MongoClient("mongodb://localhost:27017/")
db = client['UniUni']
dsp_collection = db['DSP']
parcel_collection = db['Parcel']


# Method to insert DSP data into MongoDB
def save_dsp_to_mongodb(dsp: DSP):
    dsp_data = {
        "team_name": dsp.team_name,
        "team_id": dsp.team_id,
        "warehouse_code": dsp.warehouse_code,
        "period_to_salary": dsp.period_to_salary,
        "parcels": [dsp.tracking_number for dsp in dsp.parcels.values()]
    }

    # Update if the team_id and warehouse_code combination exists, insert if it doesn't (upsert=True)
    dsp_collection.update_one(
        {"team_id": dsp.team_id, "warehouse_code": dsp.warehouse_code},  # Filter by team_id and warehouse_code
        {"$set": dsp_data},  # Set the new data
        upsert=True  # Insert if not found
    )


def save_parcel_to_mongodb(parcel: Parcel):
    # Prepare the parcel data to be stored, including adjustments
    parcel_data = {
        "tracking_number": parcel.tracking_number,
        "max_dnr_deduction": parcel.max_dnr_deduction,
        "adjustments": [
            {
                "adjustment_type": adjustment.adjustment_type.name,  # Store enum as a string
                "period": adjustment.period,
                "value": adjustment.value
            }
            for adjustment in parcel.adjustments
        ]
    }

    # Update if the tracking number exists, insert if it doesn't (upsert=True)
    parcel_collection.update_one(
        {"tracking_number": parcel.tracking_number},  # Filter by tracking number
        {"$set": parcel_data},  # Set the new data
        upsert=True  # Insert if not found
    )
