import boto3
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

S3_BUCKET = os.getenv('S3_BUCKET', 'sistemaharca')
S3_FOLDER = os.getenv('S3_FOLDER', 'reports')

s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('SECRET_ACCESS_KEY'),
    region_name=os.getenv('REGION', 'us-east-2')
)

def list_files(bucket=S3_BUCKET, prefix=None):
    """Lista arquivos no bucket S3"""
    try:
        if prefix:
            response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        else:
            response = s3_client.list_objects_v2(Bucket=bucket)
        
        if 'Contents' in response:
            print(f"Arquivos no bucket '{bucket}':")
            for obj in response['Contents']:
                print(f"  - {obj['Key']} ({obj['Size']} bytes) - {obj['LastModified']}")
            return [obj['Key'] for obj in response['Contents']]
        else:
            print(f"Nenhum arquivo encontrado no bucket '{bucket}'")
            return []
    except Exception as e:
        print(f"Erro ao listar arquivos: {e}")
        return []

def upload_file(local_file_path, bucket=S3_BUCKET, s3_key=None):
    """Faz upload de um arquivo para o S3"""
    try:
        if not s3_key:
            s3_key = f"{S3_FOLDER}/{os.path.basename(local_file_path)}"
        
        s3_client.upload_file(local_file_path, bucket, s3_key)
        print(f"Arquivo '{local_file_path}' enviado para 's3://{bucket}/{s3_key}'")
        return f's3://{bucket}/{s3_key}'
    except Exception as e:
        print(f"Erro ao fazer upload: {e}")
        return None

def download_file(s3_key, local_file_path, bucket=S3_BUCKET):
    """Baixa um arquivo do S3"""
    try:
        s3_client.download_file(bucket, s3_key, local_file_path)
        print(f"Arquivo 's3://{bucket}/{s3_key}' baixado para '{local_file_path}'")
        return True
    except Exception as e:
        print(f"Erro ao baixar arquivo: {e}")
        return False

def delete_file(s3_key, bucket=S3_BUCKET):
    """Apaga um arquivo do S3"""
    try:
        s3_client.delete_object(Bucket=bucket, Key=s3_key)
        print(f"Arquivo 's3://{bucket}/{s3_key}' removido")
        return True
    except Exception as e:
        print(f"Erro ao apagar arquivo: {e}")
        return False

def create_test_file():
    """Cria um arquivo de teste local"""
    test_filename = f"test_file_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(test_filename, 'w') as f:
        f.write(f"Arquivo de teste criado em {datetime.now()}\n")
        f.write("Este é um arquivo para testar operações com S3.\n")
    print(f"Arquivo de teste criado: {test_filename}")
    return test_filename

def test_bucket_access():
    """Testa se consegue acessar o bucket"""
    try:
        response = s3_client.head_bucket(Bucket=S3_BUCKET)
        print(f"✅ Acesso ao bucket '{S3_BUCKET}' confirmado")
        return True
    except Exception as e:
        print(f"❌ Erro ao acessar bucket '{S3_BUCKET}': {e}")
        return False

def download_all_files(bucket=S3_BUCKET, prefix=None, local_dir="downloads"):
    """Lista e baixa todos os arquivos do bucket/prefixo para o diretório local"""
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)
    files = list_files(bucket, prefix)
    for s3_key in files:
        local_path = os.path.join(local_dir, os.path.basename(s3_key))
        print(f"Baixando {s3_key} para {local_path}...")
        download_file(s3_key, local_path, bucket)
    print(f"Download concluído de {len(files)} arquivos para a pasta '{local_dir}'")

def main():
    """Função principal para testar todas as operações"""
    print("=== TESTE DE OPERAÇÕES S3 ===\n")

    # 1. Testar acesso ao bucket
    print("1. Testando acesso ao bucket...")
    if not test_bucket_access():
        print("Não é possível continuar sem acesso ao bucket.")
        return
    print()

    # 2. Listar arquivos existentes
    print("2. Listando arquivos existentes...")
    existing_files = list_files(prefix=S3_FOLDER)
    print()

    # 3. Criar e fazer upload de um arquivo de teste
    print("3. Criando e fazendo upload de arquivo de teste...")
    test_file = create_test_file()
    s3_path = upload_file(test_file)
    print()

    # 4. Listar arquivos novamente (deve mostrar o novo arquivo)
    print("4. Listando arquivos após upload...")
    new_files = list_files(prefix=S3_FOLDER)
    print()

    # 5. Baixar o arquivo de volta
    print("5. Baixando arquivo de volta...")
    downloaded_file = f"downloaded_{test_file}"
    if s3_path:
        s3_key = s3_path.replace(f's3://{S3_BUCKET}/', '')
        download_file(s3_key, downloaded_file)
    print()

    # 6. Apagar o arquivo do S3
    print("6. Removendo arquivo de teste do S3...")
    if s3_path:
        s3_key = s3_path.replace(f's3://{S3_BUCKET}/', '')
        delete_file(s3_key)
    print()

    # 7. Listar arquivos final (não deve mostrar o arquivo de teste)
    print("7. Listando arquivos após remoção...")
    final_files = list_files(prefix=S3_FOLDER)
    print()

    # Limpar arquivos locais de teste
    print("8. Limpando arquivos locais de teste...")
    try:
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"Arquivo local '{test_file}' removido")
        if os.path.exists(downloaded_file):
            os.remove(downloaded_file)
            print(f"Arquivo local '{downloaded_file}' removido")
    except Exception as e:
        print(f"Erro ao limpar arquivos locais: {e}")

    print("\n=== TESTE CONCLUÍDO ===")

if __name__ == '__main__':
    # Você pode executar a função principal ou testar operações individuais

    # Para executar todos os testes:
    # main()

    # Para baixar todos os arquivos do bucket/pasta:
    print("Baixando todos os arquivos do bucket...")
    download_all_files(prefix=S3_FOLDER)
