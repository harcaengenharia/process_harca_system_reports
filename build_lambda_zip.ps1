# Script PowerShell para criar o pacote Lambda ZIP com dependências

Write-Host "Criando pacote Lambda..."

# Remove arquivos antigos
if (Test-Path "lambda_package") {
    Remove-Item -Recurse -Force "lambda_package"
}
if (Test-Path "lambda_function.zip") {
    Remove-Item -Force "lambda_function.zip"
}

# Cria diretório temporário
New-Item -ItemType Directory -Name "lambda_package"

# Instala dependências no diretório
pip install -r requirements.txt -t lambda_package/

# Copia o código da função
Copy-Item "lambda_function.py" "lambda_package/"

# Cria o arquivo ZIP
Compress-Archive -Path "lambda_package/*" -DestinationPath "lambda_function.zip"

# Remove diretório temporário
Remove-Item -Recurse -Force "lambda_package"

Write-Host "Pacote criado: lambda_function.zip"
Write-Host "Agora você pode fazer upload deste arquivo na AWS Lambda Console"
