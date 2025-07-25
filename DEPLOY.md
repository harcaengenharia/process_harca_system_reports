# Instruções para Deploy da Lambda

## Deploy via ZIP (Recomendado)

```bash
bash build_lambda_zip.sh
```

Isso criará o arquivo `lambda_function.zip` que você pode fazer upload diretamente no AWS Lambda Console.

## Opção 2: Deploy via Docker/ECR

1. Faça login no ECR:
```bash
aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin 626635402412.dkr.ecr.us-east-2.amazonaws.com
```

2. Build e push da imagem:
```bash
docker buildx build --platform linux/amd64 --provenance=false -t process-harca-system-report:latest .
docker tag process-harca-system-report:latest 626635402412.dkr.ecr.us-east-2.amazonaws.com/process-harca-system-report:latest
docker push 626635402412.dkr.ecr.us-east-2.amazonaws.com/process-harca-system-report:latest
```

## Configuração da Lambda

### Variáveis de Ambiente (configurar no AWS Console):
- `BASE_URL`: https://sistema.harcaengenharia.com.br/api
- `EMAIL`: seu_email@domain.com
- `PASSWORD`: sua_senha
- `S3_BUCKET`: sistemaharca
- `S3_FOLDER`: reports

### Handler:
- Para ZIP: `lambda_function.lambda_handler`
- Para Container: já configurado no Dockerfile

### Timeout:
- Recomendado: 5-15 minutos (dependendo da quantidade de dados)

### Memória:
- Recomendado: 512MB ou mais

### Permissões IAM:
A função Lambda precisa das seguintes permissões:
- `s3:PutObject` no bucket de destino
- `s3:DeleteObject` no bucket de destino (se usar a função de limpeza)

## Teste
O handler da Lambda pode ser testado com qualquer evento (não usa dados do evento).

Exemplo de evento de teste:
```json
{}
```
