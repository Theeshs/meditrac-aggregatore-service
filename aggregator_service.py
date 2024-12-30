from redshift_connection import connect_to_redshift
import requests
from collections import defaultdict

def create_table(conn):
    sql = """CREATE TABLE IF NOT EXISTS appointment_aggregations (
                doctor_id VARCHAR(255),
                appointment_date DATE,
                appointments_count INT,
                aggregated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );"""
    sql2 ="""
        CREATE TABLE IF NOT EXISTS patient_aggregations (
            patient_id VARCHAR(255),
            total_appointments INT,
            no_show_count INT,
            last_appointment_date DATE,
            aggregated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.execute(sql2)
    conn.commit()
    cursor.close()
    

# Fetch and aggregate data
def run():
    # Fetch data from appointment service
    appointment_service_url = "http://appointment-service-api.local"
    response = requests.get(appointment_service_url)
    response.raise_for_status()
    appointments = response.json()
    print(appointments)

    # Aggregate appointments per doctor
    appointments_per_doctor = defaultdict(int)
    for appointment in appointments:
        appointments_per_doctor[appointment['doctorId']] += 1

    # Aggregate appointment frequency over time
    frequency = defaultdict(int)
    for appointment in appointments:
        date = appointment['appointmentDate'][:10]  # Extract YYYY-MM-DD
        frequency[date] += 1
    
    # Aggregate patient metrics
    patient_aggregations = defaultdict(lambda: {
        'total_appointments': 0,
        'last_appointment_date': None,
        'no_show_count': 0,
    })
    for appointment in appointments:
        patient_id = appointment['patientId']
        patient_aggregations[patient_id]['total_appointments'] += 1

        if appointment['status'] == 'no-show':
            patient_aggregations[patient_id]['no_show_count'] += 1

        appointment_date = appointment['appointmentDate'][:10]  # Extract YYYY-MM-DD
        if (patient_aggregations[patient_id]['last_appointment_date'] is None or
                appointment_date > patient_aggregations[patient_id]['last_appointment_date']):
            patient_aggregations[patient_id]['last_appointment_date'] = appointment_date

    # Store aggregated data in Redshift
    conn = connect_to_redshift()
    create_table(conn)
    cursor = conn.cursor()

    # Insert per-doctor metrics
    for doctor_id, count in appointments_per_doctor.items():
        cursor.execute(
            """
            INSERT INTO appointment_aggregations (doctor_id, appointment_date, appointments_count)
            VALUES (%s, NULL, %s)
            """,
            (doctor_id, count)
        )

    # Insert frequency metrics
    for date, count in frequency.items():
        cursor.execute(
            """
            INSERT INTO appointment_aggregations (doctor_id, appointment_date, appointments_count)
            VALUES (%s, %s, %s)
            """,
            (None, date, count)
        )
    
    # Insert patient metrics
    for patient_id, data in patient_aggregations.items():
        # Step 1: Delete existing record for the patient
        cursor.execute(
            """
            DELETE FROM patient_aggregations
            WHERE patient_id = %s
            """,
            (patient_id,)
        )

        # Step 2: Insert the new record
        cursor.execute(
            """
            INSERT INTO patient_aggregations (
                patient_id, total_appointments, no_show_count, last_appointment_date, aggregated_at
            )
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
            """,
            (
                patient_id,
                data['total_appointments'],
                data['no_show_count'],
                data['last_appointment_date'],
            )
        )

    conn.commit()
    cursor.close()
    conn.close()

    return {
        "statusCode": 200,
        "body": "Data aggregated and stored successfully."
    }


if __name__ == "__main__":
    run()