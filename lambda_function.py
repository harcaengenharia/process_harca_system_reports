import boto3
from datetime import datetime
import os
from dotenv import load_dotenv
import pandas as pd
import requests

load_dotenv()

BASE_URL = os.getenv('BASE_URL', 'https://sistema.harcaengenharia.com.br/api')
CREDENTIALS = {'email': os.getenv('EMAIL'), 'password': os.getenv('PASSWORD')}
S3_BUCKET = os.getenv('S3_BUCKET', 'sistema-harca')
S3_FOLDER = os.getenv('S3_FOLDER', 'reports')

s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
)

def request_session(endpoint, payload):
    response = requests.post(f'{BASE_URL}{endpoint}', json=payload)
    return response.json() if response.status_code in [200, 201] else None

def request_report(construction_id, access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.post(f'{BASE_URL}/client/report/summary/{construction_id}', headers=headers)
    return response.json() if response.status_code in [200, 201] else None

def upload_to_s3(file_path, bucket, object_name):
    s3_client.upload_file(file_path, bucket, object_name)
    os.remove(file_path)
    return f's3://{bucket}/{object_name}'

def process_construction(data, month=None):
    format_currency = lambda x: f'{float(x):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    format_percentage = lambda x: f'{float(x) * 100:.2f}%'.replace('.', ',')

    services = sorted(data['services'], key=lambda s: int(s['item']) if s['item'].isdigit() else s['item'])
    now = datetime.now()
    current_month_key = month if month else now.strftime('%m/%Y')
    current_month = datetime.strptime(current_month_key, '%m/%Y')
    total_services = sum(float(s['total']) for s in services)

    df_data = []

    total_material = total_labor = total_total = 0
    total_schedule_value = total_schedule_percentage = 0
    total_measurement_value = total_measurement_percentage = 0
    total_current_schedule_value = total_current_measurement_value = 0
    total_current_schedule_percentage = total_current_measurement_percentage = 0

    for s in services:
        schedules = s.get('schedules', {})
        measurements = s.get('measurements', {})

        material = float(s['material'])
        labor = float(s['labor'])
        total = float(s['total'])

        schedule_value = sum(float(v['value']) for m, v in schedules.items() if datetime.strptime(m, '%m/%Y') <= current_month)
        schedule_percentage = sum(float(v['percentage']) for m, v in schedules.items() if datetime.strptime(m, '%m/%Y') <= current_month)
        measurement_value = sum(float(v['value']) for m, v in measurements.items() if datetime.strptime(m, '%m/%Y') <= current_month)
        measurement_percentage = sum(float(v['percentage']) for m, v in measurements.items() if datetime.strptime(m, '%m/%Y') <= current_month)

        current_sched_value = float(schedules.get(current_month_key, {}).get('value', 0))
        current_sched_perc = float(schedules.get(current_month_key, {}).get('percentage', 0))
        current_meas_value = float(measurements.get(current_month_key, {}).get('value', 0))
        current_meas_perc = float(measurements.get(current_month_key, {}).get('percentage', 0))

        df_data.append({
            'Item': s['item'],
            'Serviço': s['name'],
            'Material (R$)': format_currency(material),
            'Labor (R$)': format_currency(labor),
            'Total (R$)': format_currency(total),
            'Peso (%)': format_percentage(total / total_services if total_services else 0),
            'Previsto acumulado (R$)': format_currency(schedule_value),
            'Previsto acumulado (%)': format_percentage(schedule_percentage),
            'Previsto no período (R$)': format_currency(current_sched_value),
            'Previsto no período (%)': format_percentage(current_sched_perc),
            'Executado acumulado (R$)': format_currency(measurement_value),
            'Executado acumulado (%)': format_percentage(measurement_percentage),
            'Executado no período (R$)': format_currency(current_meas_value),
            'Executado no período (%)': format_percentage(current_meas_perc),
            'Saldo (R$)': format_currency(total - measurement_value),
            'Saldo (%)': format_percentage(1 - measurement_percentage),
            'Atraso/Adiantamento (R$)': format_currency(measurement_value - schedule_value),
            'Atraso/Adiantamento (%)': format_percentage(measurement_percentage - schedule_percentage)
        })

        total_material += material
        total_labor += labor
        total_total += total
        total_schedule_value += schedule_value
        total_schedule_percentage += schedule_percentage
        total_current_schedule_value += current_sched_value
        total_current_schedule_percentage += current_sched_perc
        total_measurement_value += measurement_value
        total_measurement_percentage += measurement_percentage
        total_current_measurement_value += current_meas_value
        total_current_measurement_percentage += current_meas_perc

    df_data.append({
        'Item': '',
        'Serviço': 'Total',
        'Material (R$)': format_currency(total_material),
        'Labor (R$)': format_currency(total_labor),
        'Total (R$)': format_currency(total_total),
        'Peso (%)': '100,00%',
        'Previsto acumulado (R$)': format_currency(total_schedule_value),
        'Previsto acumulado (%)': format_percentage(total_schedule_value / total_total if total_total else 0),
        'Previsto no período (R$)': format_currency(total_current_schedule_value),
        'Previsto no período (%)': format_percentage(total_current_schedule_value / total_total if total_total else 0),
        'Executado acumulado (R$)': format_currency(total_measurement_value),
        'Executado acumulado (%)': format_percentage(total_measurement_value / total_total if total_total else 0),
        'Executado no período (R$)': format_currency(total_current_measurement_value),
        'Executado no período (%)': format_percentage(total_current_measurement_value / total_total if total_total else 0),
        'Saldo (R$)': format_currency(total_total - total_measurement_value),
        'Saldo (%)': format_percentage(1 - (total_measurement_value / total_total if total_total else 0)),
        'Atraso/Adiantamento (R$)': format_currency(total_measurement_value - total_schedule_value),
        'Atraso/Adiantamento (%)': format_percentage((total_measurement_value - total_schedule_value) / total_total if total_total else 0)
    })

    df = pd.DataFrame(df_data)
    filename = f"{data['city']['state']['acronym']}_{data['city']['name']}_{data['name']}_{now.strftime('%Y%m%d')}.csv".replace(' ', '_')
    df.to_csv(filename, index=False, sep=';')
    s3_path = upload_to_s3(filename, S3_BUCKET, f'{S3_FOLDER}/{filename}')

    return s3_path

def view_services(data, info='value'):
    df_dict = {}
    services = sorted(data['services'], key=lambda s: int(s['item']) if s['item'].isdigit() else s['item'])
    for service in services:
        service_name = service['name']
        df_dict[service_name] = {month: details[info] for month, details in service['measurements'].items()}
    df = pd.DataFrame.from_dict(df_dict, orient='index')
    df = df.reindex(sorted(df.columns, key=lambda x: pd.to_datetime(x, format='%m/%Y')), axis=1)
    return df

if __name__ == '__main__':
    store_data = request_session('/client/sessions', CREDENTIALS)

    if store_data:
        for construction in store_data.get('constructions', []):
            construction_data = request_report(construction['id'], store_data.get('access_token'))
            # print(view_services(construction_data))
            process_construction(construction_data, '03/2025')
