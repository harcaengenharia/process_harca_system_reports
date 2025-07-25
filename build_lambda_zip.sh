#!/bin/bash

# Script para criar o pacote Lambda ZIP com dependências

echo "Criando pacote Lambda..."

# Remove arquivos antigos
rm -rf lambda_package
rm -f lambda_function.zip

# Cria diretório temporário
mkdir lambda_package

# Instala dependências no diretório
pip install -r requirements.txt -t lambda_package/

# Copia o código da função
cp lambda_function.py lambda_package/

# Cria o arquivo ZIP
cd lambda_package
zip -r ../lambda_function.zip .
cd ..

# Remove diretório temporário
rm -rf lambda_package

echo "Pacote criado: lambda_function.zip"
echo "Agora você pode fazer upload deste arquivo na AWS Lambda Console"
