# 🔌 Exemplo de Uso da API - Sistema Harca Engenharia

Este projeto demonstra como integrar com a **API da Harca Engenharia**, realizando autenticação, consulta de obras e extração de dados de orçamento, cronograma e medições.

---

## 📌 Funcionalidades

- 🔐 Login na API Harca (`/client/sessions`)
- 🏗️ Listagem de obras do cliente autenticado
- 📊 Consulta de dados detalhados da obra (`/client/report/summary/:id`)
- 🧮 Processamento e análise de medições e cronogramas
- ☁️ Upload dos dados processados para o Amazon S3 (como exemplo de uso)

---

## ⚙️ Setup

### 1. Clone o repositório
```bash
git clone https://github.com/harcaengenharia/process_harca_system_reports.git
cd process_harca_system_reports
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Configure o ambiente

Copie o `.env.example` para `.env` e preencha com suas credenciais:

```bash
cp .env.example .env
```

## 🧪 Como usar

```bash
python lambda_function.py
```

Esse script:

1. Faz login via `/client/sessions`
2. Lista todas as obras associadas ao cliente
3. Para cada obra, busca os dados via `/client/report/summary/:id`
4. Processa os dados e salva um `.csv`
5. Faz upload do arquivo para o Amazon S3

> **Obs:** Essa lógica pode ser adaptada facilmente para outras finalidades: dashboards, BI, relatórios internos, etc.

---

## 📤 Endpoints usados

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/client/sessions` | Autenticação e geração de token |
| `POST` | `/client/report/summary/:id` | Retorna resumo da obra com serviços, cronogramas e medições |

---

## 📎 Exemplo de estrutura de dados retornada

A resposta de `/client/report/summary/:id` inclui:

```json
{
  "name": "Obra Exemplo",
  "city": { "name": "São Paulo", "state": { "acronym": "SP" } },
  "services": [
    {
      "item": "1",
      "name": "Fundação",
      "material": "1000.00",
      "labor": "2000.00",
      "total": "3000.00",
      "schedules": { "03/2025": { "value": 1500.0, "percentage": 0.5 } },
      "measurements": { "03/2025": { "value": 1000.0, "percentage": 0.33 } }
    },
    ...
  ]
}
```

---

## ✅ Resultado

Ao final, você terá arquivos `.csv` com os dados processados da obra, enviados ao S3 (ou armazenados localmente, se preferir).

---

## 📚 Referência

Para mais informações sobre o sistema Harca, acesse: [https://sistema.harcaengenharia.com.br](https://sistema.harcaengenharia.com.br)
