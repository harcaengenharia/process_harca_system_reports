import boto3
from datetime import datetime
import os
import pandas as pd
import requests

# Para executar localmente, descomente a linha abaixo:
# from dotenv import load_dotenv
# load_dotenv()

BASE_URL = os.getenv('BASE_URL', 'https://sistema.harcaengenharia.com.br/api')
CREDENTIALS = {'email': os.getenv('EMAIL'), 'password': os.getenv('PASSWORD')}
S3_BUCKET = os.getenv('S3_BUCKET', 'sistemaharca')
S3_FOLDER = os.getenv('S3_FOLDER', 'reports')

s3_client = boto3.client('s3')

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

def process_construction(data):
    format_currency = lambda x: f'{float(x):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    format_percentage = lambda x: f'{float(x) * 100:.2f}%'.replace('.', ',')

    def item_sort_key(s):
        item = s.get('item', '')
        try:
            return (0, int(item))
        except (ValueError, TypeError):
            return (1, str(item))
    services = sorted(data.get('services', []), key=item_sort_key)
    total_services = sum(float(s.get('total', 0)) for s in services)

    construction_name = data.get('name', '')
    city = data.get('city', {}).get('name', '')
    state = data.get('city', {}).get('state', {}).get('acronym', '')
    construction_type = data.get('construction_type', {}).get('name', '')

    months = set()
    for s in services:
        schedules = s.get('schedules', {})
        if isinstance(schedules, dict):
            months.update(schedules.keys())
        measurements = s.get('measurements', {})
        if isinstance(measurements, dict):
            months.update(measurements.keys())
    months = sorted(months, key=lambda x: datetime.strptime(x, '%m/%Y'))

    df_data = []
    for month in months:
        measurement_date = datetime.strptime(month, '%m/%Y').strftime('%Y-%m-01')
        for s in services:
            schedules = s.get('schedules', {})
            if not isinstance(schedules, dict):
                schedules = {}
            measurements = s.get('measurements', {})
            if not isinstance(measurements, dict):
                measurements = {}

            material = float(s.get('material', 0))
            labor = float(s.get('labor', 0))
            total = float(s.get('total', 0))

            schedule_value = sum(float(v.get('value', 0)) for m, v in schedules.items() if datetime.strptime(m, '%m/%Y') <= datetime.strptime(month, '%m/%Y'))
            schedule_percentage = sum(float(v.get('percentage', 0)) for m, v in schedules.items() if datetime.strptime(m, '%m/%Y') <= datetime.strptime(month, '%m/%Y'))
            measurement_value = sum(float(v.get('value', 0)) for m, v in measurements.items() if datetime.strptime(m, '%m/%Y') <= datetime.strptime(month, '%m/%Y'))
            measurement_percentage = sum(float(v.get('percentage', 0)) for m, v in measurements.items() if datetime.strptime(m, '%m/%Y') <= datetime.strptime(month, '%m/%Y'))

            current_sched_value = float(schedules.get(month, {}).get('value', 0))
            current_sched_perc = float(schedules.get(month, {}).get('percentage', 0))
            current_meas_value = float(measurements.get(month, {}).get('value', 0))
            current_meas_perc = float(measurements.get(month, {}).get('percentage', 0))
            number = measurements.get(month, {}).get('number', 0)

            if not number:
                continue

            row = {
                'Nome da Obra': construction_name,
                'Cidade': city,
                'Estado': state,
                'Tipo de Obra': construction_type,
                'Número da Medição': number,
                'Mês de referência': month,
                'Data da Medição': measurement_date,
                'Item': s.get('item', ''),
                'Serviço': s.get('name', ''),
                'Material (R$)': format_currency(material),
                'Mão de Obra (R$)': format_currency(labor),
                'Total (R$)': format_currency(total),
                'Peso (%)': format_percentage(total / total_services if total_services else 0),
                'Previsto Acumulado (R$)': format_currency(schedule_value),
                'Previsto Acumulado (%)': format_percentage(schedule_percentage),
                'Previsto no Período (R$)': format_currency(current_sched_value),
                'Previsto no Período (%)': format_percentage(current_sched_perc),
                'Executado Acumulado (R$)': format_currency(measurement_value),
                'Executado Acumulado (%)': format_percentage(measurement_percentage),
                'Executado no Período (R$)': format_currency(current_meas_value),
                'Executado no Período (%)': format_percentage(current_meas_perc),
                'Saldo (R$)': format_currency(total - measurement_value),
                'Saldo (%)': format_percentage(1 - measurement_percentage),
                'Atraso/Adiantamento (R$)': format_currency(measurement_value - schedule_value),
                'Atraso/Adiantamento (%)': format_percentage(measurement_percentage - schedule_percentage)
            }
            df_data.append(row)

    return df_data

def view_services(data, info='value'):
    df_dict = {}
    services = sorted(data.get('services', []), key=lambda s: int(s.get('item', 0)) if s.get('item', '').isdigit() else s.get('item', ''))
    for service in services:
        service_name = service.get('name', '')
        df_dict[service_name] = {month: details.get(info, 0) for month, details in service.get('measurements', {}).items()}
    df = pd.DataFrame.from_dict(df_dict, orient='index')
    df = df.reindex(sorted(df.columns, key=lambda x: pd.to_datetime(x, format='%m/%Y')), axis=1)
    return df

def lambda_handler(event, context):
    """Handler principal da AWS Lambda"""
    try:
        return main()
    except Exception as e:
        print(f"Erro na execução: {e}")
        return {
            'statusCode': 500,
            'body': f'Erro: {str(e)}'
        }

def main():
    """Função principal para processar os relatórios"""
    store_data = request_session('/client/sessions', CREDENTIALS)

    all_data = []
    if store_data:
        for construction in store_data.get('constructions', []):
            print(f"Processando obra: {construction.get('name', '')}")
            construction_data = request_report(construction.get('id'), store_data.get('access_token'))
            if construction_data:
                all_data.extend(process_construction(construction_data))
    
    if all_data:
        df = pd.DataFrame(all_data)
        filename = 'data.csv'
        df.to_csv(f'/tmp/{filename}', index=False, sep=';')
        s3_path = upload_to_s3(f'/tmp/{filename}', S3_BUCKET, f'{S3_FOLDER}/{filename}')
        print(f'Arquivo gerado e enviado para S3: {s3_path}')
        return {
            'statusCode': 200,
            'body': f'Relatório gerado com sucesso: {s3_path}'
        }
    else:
        return {
            'statusCode': 200,
            'body': 'Nenhum dado encontrado para gerar relatório'
        }

if __name__ == '__main__':
    # Para execução local, descomente as linhas abaixo:
    from dotenv import load_dotenv
    load_dotenv()
    
    # Recria o cliente S3 com credenciais locais
    s3_client = boto3.client(
        's3',
        aws_access_key_id=os.getenv('ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('SECRET_ACCESS_KEY'),
    )
    
    result = main()
    print(result)
