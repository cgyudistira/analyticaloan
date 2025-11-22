# Document Service

Document upload, OCR processing, and financial data extraction service.

## Features

- **Document Upload**: Support for PDF, JPG, PNG (max 10MB)
- **Storage**: S3/MinIO/GCS abstraction
- **OCR Processing**: Google Cloud Vision API (with Tesseract fallback)
- **Financial Statement Parsing**: 
  - Income Statement (Laporan Laba Rugi)
  - Balance Sheet (Neraca)
  - Cash Flow Statement (Laporan Arus Kas)
- **Bank Statement Analysis**:
  - Multi-bank support (BCA, Mandiri, BRI, BNI, etc.)
  - Transaction extraction
  - Cash flow metrics
  - Income/expense volatility

## Running the Service

```bash
# Install dependencies
pip install -r requirements.txt

# Setup Google Cloud credentials (optional, falls back to Tesseract)
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Run the service
uvicorn app.main:app --reload --port 8003
```

## API Endpoints

### Upload Document
```bash
curl -X POST http://localhost:8003/documents/upload \
  -F "application_id=<uuid>" \
  -F "document_type=INCOME_STATEMENT" \
  -F "file=@financial_statement.pdf"
```

### Trigger OCR
```bash
curl -X POST http://localhost:8003/documents/<document_id>/ocr
```

### Get Document
```bash
curl http://localhost:8003/documents/<document_id>
```

### List Application Documents
```bash
curl http://localhost:8003/applications/<application_id>/documents
```

## Document Types

- `INCOME_STATEMENT`
- `BALANCE_SHEET`
- `CASH_FLOW`
- `BANK_STATEMENT`
- `TAX_RETURN`
- `SALARY_SLIP`
- `BUSINESS_LICENSE`
- `ID_CARD`

## Parser Usage

```python
from app.parsers import IncomeStatementParser, BankStatementParser

# Parse income statement
parser = IncomeStatementParser()
metrics = parser.parse(ocr_text)
print(metrics['revenue'], metrics['net_income'])

# Parse bank statement
bank_parser = BankStatementParser()
bank_metrics = bank_parser.parse(ocr_text)
print(bank_metrics.avg_monthly_income)
```

## Storage Providers

Configure via environment variables:

**MinIO (local dev):**
```
STORAGE_PROVIDER=minio
STORAGE_ENDPOINT=http://localhost:9000
STORAGE_ACCESS_KEY=minioadmin
STORAGE_SECRET_KEY=minioadmin123
```

**AWS S3:**
```
STORAGE_PROVIDER=s3
STORAGE_ACCESS_KEY=<aws_key>
STORAGE_SECRET_KEY=<aws_secret>
STORAGE_BUCKET=analyticaloan-documents
```

**Google Cloud Storage:**
```
STORAGE_PROVIDER=gcs
GCS_BUCKET_NAME=analyticaloan-documents
GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
```
