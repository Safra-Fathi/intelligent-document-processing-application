# Intelligent Document Processing Application

An end-to-end intelligent document processing system that combines OCR, machine learning, business-rule validation, confidence-based human review, secure document management, and audit tracking.

The application allows authenticated users to upload business documents such as invoices, quotations, and receipts. Documents are processed through an OCR and ML pipeline to identify their type, extract structured information, validate the extracted data, and determine whether human review is required.

---

## Features

- Secure user registration and authentication
- JWT-based protected API access
- PDF, PNG, and JPEG document upload
- Secure server-side file validation and storage
- OCR for scanned documents and images
- Native text extraction for digital PDFs
- Document classification using machine learning
- Invoice, quotation, and receipt classification
- UNKNOWN handling for unsupported or low-confidence documents
- Structured field extraction
- Line-item extraction
- Field-level confidence scores
- Business-rule validation
- Confidence-based human review routing
- Duplicate document-number detection
- Human correction workflow
- Original machine values preserved after correction
- Correction and processing audit trail
- Secure document preview
- Document processing history
- Ownership-based access control
- Automated validation and extraction tests

---

## Application Screenshots

### User Registration
<img width="597" height="852" alt="Register" src="https://github.com/user-attachments/assets/a801b93f-2764-46c2-90f8-44a09559b8ee" />

### User Login

<img width="656" height="772" alt="Sign in" src="https://github.com/user-attachments/assets/efa5e9b5-78d2-499b-8876-dbf139866107" />


### Document Dashboard

<img width="1855" height="851" alt="Dashboard" src="https://github.com/user-attachments/assets/5a5e3ec0-259d-406b-a44c-b0033fa7ddbf" />

### Document Processing Result

<img width="1616" height="872" alt="document-result" src="https://github.com/user-attachments/assets/35dc2ddf-5727-418b-9296-7d2de92e68e5" />


### Validation and Human Review
<img width="1487" height="856" alt="validation-review" src="https://github.com/user-attachments/assets/e398d772-a028-4dd1-b343-ef8fd109a34e" />



### Human Correction
<img width="1522" height="526" alt="human-correction" src="https://github.com/user-attachments/assets/df99b573-236b-4d3b-9c01-9aceaa8cd490" />


### Audit History

<img width="1367" height="672" alt="audit-history" src="https://github.com/user-attachments/assets/ee9d9e90-503f-4bf9-b296-4e278029bfac" />


---

## System Architecture

The application separates the frontend, API, processing pipeline, validation logic, persistence layer, and machine-learning components.

```text
                    ┌─────────────────────┐
                    │   React Frontend    │
                    │   TypeScript/Vite   │
                    └──────────┬──────────┘
                               │
                         HTTP / JWT
                               │
                    ┌──────────▼──────────┐
                    │    FastAPI API      │
                    │ Auth / Documents /  │
                    │ Review / Audit      │
                    └──────────┬──────────┘
                               │
             ┌─────────────────┼──────────────────┐
             │                 │                  │
             ▼                 ▼                  ▼
    ┌────────────────┐ ┌───────────────┐ ┌────────────────┐
    │ File Storage   │ │  PostgreSQL   │ │   Processing   │
    │ UUID filenames │ │   Database    │ │    Pipeline    │
    └────────────────┘ └───────────────┘ └───────┬────────┘
                                                  │
                                      ┌───────────▼──────────┐
                                      │ Text/OCR Extraction  │
                                      │ PyMuPDF + Tesseract  │
                                      └───────────┬──────────┘
                                                  │
                                      ┌───────────▼──────────┐
                                      │ Document Classifier  │
                                      │ TF-IDF + Logistic    │
                                      │ Regression           │
                                      └───────────┬──────────┘
                                                  │
                                      ┌───────────▼──────────┐
                                      │ Field & Line Item    │
                                      │ Extraction           │
                                      └───────────┬──────────┘
                                                  │
                                      ┌───────────▼──────────┐
                                      │ Business Validation  │
                                      └───────────┬──────────┘
                                                  │
                                      ┌───────────▼──────────┐
                                      │ Review Routing       │
                                      │ Auto / Review /      │
                                      │ Manual               │
                                      └──────────────────────┘
```

---

## Document Processing Workflow

The processing workflow is:

```text
Upload
  ↓
Secure file validation
  ↓
Private file storage
  ↓
Text extraction / OCR
  ↓
Document classification
  ↓
UNKNOWN threshold handling
  ↓
Structured field extraction
  ↓
Line-item extraction
  ↓
Field confidence calculation
  ↓
Business-rule validation
  ↓
Review routing
  ↓
Database persistence
  ↓
Human review / correction
  ↓
Audit history
```

A document being successfully processed does not necessarily mean that its extracted information is automatically trusted.

For example, a document can have:

```text
Processing Status: COMPLETED
Review Status: MANUAL_REQUIRED
```

`COMPLETED` means the technical processing pipeline completed successfully, while `MANUAL_REQUIRED` means the result requires human verification.

---

## Supported Document Categories

The classifier currently supports:

- `INVOICE`
- `QUOTATION`
- `RECEIPT`
- `UNKNOWN`

The UNKNOWN category is used when classification confidence is below the configured threshold or when the document does not sufficiently resemble a supported category.

This prevents the system from forcing an unsupported document into an incorrect business category.

---

## Machine Learning

Document classification uses:

- TF-IDF text features
- Logistic Regression
- `predict_proba()` classification confidence
- Confidence-based UNKNOWN handling

The classifier is trained separately from the FastAPI application and stored as a versioned model artifact.

```text
ml/
├── data/
│   ├── train/
│   ├── dev/
│   └── eval/
└── artifacts/
    └── classifier-v1/
        ├── model.joblib
        └── metadata.json
```

The processing application loads the trained model for inference rather than training a model during an API request.

### Classification Confidence

The application uses classification probability when determining whether a predicted document category should be accepted.

Documents with insufficient classification confidence are assigned:

```text
UNKNOWN
```

and routed for manual review.

---

## OCR and Preprocessing

The system uses two text-extraction paths.

### Digital PDFs

PyMuPDF is used first to extract embedded text.

If sufficient native text is available, OCR is avoided.

### Scanned PDFs and Images

Scanned documents and image uploads are processed using:

- Pillow
- OpenCV
- Tesseract OCR

Image preprocessing includes operations such as:

- grayscale conversion
- Gaussian blur
- adaptive thresholding

PDF pages requiring OCR are rendered at increased resolution before being passed to Tesseract.

---

## Extracted Information

The extraction pipeline supports fields including:

- document number
- document date
- due date
- validity date
- vendor
- customer
- address
- contact information
- currency
- subtotal
- discount
- tax
- additional charges
- grand total

Line items can include:

- description
- quantity
- unit price
- line total

The extracted values are stored separately from subsequent human corrections.

---

## Confidence and Human Review

Classification confidence and field extraction confidence are intentionally treated separately.

The current review strategy follows approximately:

| Confidence | Review Action |
|---|---|
| >= 0.90 | Auto acceptance may be allowed |
| 0.70 - 0.89 | Review recommended |
| < 0.70 | Manual review required |

Business validation errors can override confidence-based routing.

Therefore, even a high-confidence extraction can still require human review if business rules fail.

---

## Business Validation

Validation is implemented separately from extraction.

Examples include:

- required-field validation
- unsupported/unknown document type
- low-confidence critical fields
- malformed numeric values
- malformed dates
- quantity × unit price vs. line total
- sum of line totals vs. subtotal
- subtotal - discount + tax + charges vs. grand total
- duplicate document numbers

For example:

```text
quantity × unit_price ≈ line_total
```

and:

```text
subtotal - discount + tax + charges ≈ grand_total
```

A tolerance is used for arithmetic comparisons to account for decimal rounding.

Duplicate document detection is performed against previously processed documents owned by the authenticated user.

---

## Review Status

The application uses three review states:

### AUTO_ACCEPTED

The document has sufficiently high confidence and no validation issue requiring human intervention.

### REVIEW_RECOMMENDED

The processing result is usable but contains medium confidence or validation warnings that should be reviewed.

### MANUAL_REQUIRED

Human review is required due to conditions such as:

- UNKNOWN classification
- low classification confidence
- critical validation errors
- missing critical fields
- duplicate document numbers

---

## Human Corrections

Extracted values are never silently overwritten.

The original machine-generated value remains stored in the `extracted_fields` table.

A correction creates a separate database record containing information such as:

- extracted field
- corrected value
- user
- timestamp
- optional reason

This provides traceability between machine output and human-reviewed data.

The result screen displays the latest correction as the current value while retaining the original extraction.

---

## Correction History Protection

The current MVP prevents a corrected document from being reprocessed.

Reprocessing replaces machine-generated extraction records, while corrections reference those extraction records.

To prevent accidental loss of audit history, attempting to reprocess a corrected document returns:

```text
409 Conflict
```

A future production implementation could replace this restriction with versioned extraction runs.

---

## Audit Trail

Important operations generate audit events.

Examples include:

```text
PROCESSING_STARTED
PROCESSING_COMPLETED
PROCESSING_FAILED
FIELD_CORRECTED
```

Audit records include the related document, user, event type, timestamp, and event details.

This makes document processing and human intervention traceable.

---

## Database Design

PostgreSQL is used for persistent application data.

Main tables include:

### users

Stores:

- user ID
- full name
- email
- password hash
- active status
- timestamps

### documents

Stores:

- owner
- original filename
- private stored filename
- MIME type
- file size
- processing status
- predicted document type
- classification confidence
- review status
- pipeline version
- classifier version
- processing error information
- timestamps

### extracted_fields

Stores the original machine-extracted field values and confidence.

### validation_issues

Stores validation warnings and errors generated during processing.

### corrections

Stores human corrections separately from the original machine output.

### audit_events

Stores document processing and human-review events.

---

## Security

The application includes several security controls.

### Authentication

Passwords are hashed using Argon2.

Authentication uses JWT bearer tokens.

Protected API endpoints require a valid authenticated user.

### Authorization

Document queries include ownership checks.

A user cannot retrieve another user's document simply by changing the document ID.

Unauthorized document access returns a not-found response rather than exposing another user's document information.

### Upload Security

Uploads are validated server-side.

Supported types are limited to:

- PDF
- PNG
- JPEG

Additional protections include:

- maximum upload size
- empty-file rejection
- PDF signature validation
- image verification
- randomly generated stored filenames
- private server-side storage

### Secret Management

Database credentials and JWT secrets are loaded through environment variables.

Secrets are not intended to be committed to source control.

---

## Technology Stack

### Frontend

- React
- TypeScript
- Vite
- React Router
- Axios

### Backend

- Python
- FastAPI
- SQLAlchemy
- Pydantic
- Alembic
- Uvicorn

### Database

- PostgreSQL

### Authentication

- JWT
- Argon2 password hashing

### Document Processing

- PyMuPDF
- Tesseract OCR
- Pillow
- OpenCV

### Machine Learning

- scikit-learn
- TF-IDF
- Logistic Regression
- joblib
- pandas

### Testing

- pytest

---

## Project Structure

```text
intelligent-document-processing/
├── backend/
│   ├── alembic/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── pipeline/
│   │   ├── schemas/
│   │   └── services/
│   ├── ml/
│   │   ├── artifacts/
│   │   └── data/
│   ├── tests/
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   └── api.ts
│   └── package.json
│
├── docs/
│   └── screenshots/
│
└── README.md
```

---

# Local Development

## Prerequisites

Install:

- Python 3.11+
- Node.js
- PostgreSQL
- Tesseract OCR

---

## Backend Setup

Move into the backend:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv .venv
```

### Windows

Activate it using:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## PostgreSQL

Create a PostgreSQL database.

Example:

```text
document_intelligence
```

Configure the database connection through the backend environment file.

---

## Environment Variables

Create:

```text
backend/.env
```

Example configuration:

```env
APP_NAME=Document Intelligence
APP_ENV=development

DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/document_intelligence

JWT_SECRET_KEY=YOUR_SECURE_RANDOM_SECRET
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Do not commit real credentials or JWT secrets.

---

## Database Migrations

Apply all migrations:

```bash
python -m alembic upgrade head
```

The migrations create and update the application database schema.

---

## Tesseract

Tesseract OCR must be installed on the backend machine.

For local Windows development, configure the application to use the installed Tesseract executable if it is not already available through the system PATH.

---

## Start Backend

From:

```text
backend/
```

run:

```bash
uvicorn app.main:app --reload
```

The API is available locally at:

```text
http://127.0.0.1:8000
```

FastAPI interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

---

## Frontend Setup

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Vite will display the local frontend address in the terminal.

---

## API Overview

Important API operations include:

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/auth/register` | Register user |
| POST | `/auth/login` | Authenticate user |
| GET | `/auth/me` | Get authenticated user |
| POST | `/documents/upload` | Upload document |
| GET | `/documents` | Document history |
| GET | `/documents/{id}` | Document metadata |
| GET | `/documents/{id}/file` | Secure document preview |
| POST | `/documents/{id}/process` | Process document |
| GET | `/documents/{id}/result` | Processing result |
| POST | `/documents/{id}/fields/{field_id}/corrections` | Correct extracted field |
| GET | `/documents/{id}/audit` | Document audit history |

The exact request and response schemas can also be inspected through FastAPI's generated OpenAPI documentation.

---

## Testing

Run backend tests from the backend directory:

```bash
python -m pytest -v
```

The automated tests cover important extraction and validation behavior, including normal and failure scenarios.

Before submission, the frontend production build can be verified with:

```bash
npm run build
```

---

## Model Evaluation

A separate labelled evaluation split is maintained rather than evaluating the classifier using its training data.

The current synthetic/template-based evaluation produced very strong classification performance, including 1.00 accuracy, precision, recall, and F1 on the held-out synthetic evaluation split.

These results should be interpreted as a controlled baseline rather than evidence of equivalent real-world performance.

The synthetic train/dev/evaluation samples share structural characteristics, making the evaluation less challenging than diverse production documents.

Confidence testing has also demonstrated that supported document examples can receive high category confidence while unrelated documents can fall below the classification threshold and be routed to `UNKNOWN`.

---

## Failure Analysis

Real-world documents can differ substantially from the synthetic training templates.

During testing, a real bill containing terminology such as:

```text
Bill Number
Bill Date
Bill From
Bill To
```

received lower classification confidence than the synthetic invoice examples.

OCR layout loss also affected table interpretation, particularly where product identifiers, quantities, prices, tax values, and totals appeared close together.

The system handled this case by assigning the document to `UNKNOWN` and routing it to:

```text
MANUAL_REQUIRED
```

rather than automatically trusting an uncertain result.

This demonstrates the reason for combining ML confidence, deterministic validation, and human review.

---

## Current Limitations

The current version is an MVP developed for the technical assessment.

Known limitations include:

- classifier training data is primarily synthetic
- real-world document layouts may generalize differently
- OCR quality depends on scan/image quality
- rule-based field extraction may miss unfamiliar labels
- complex tables can reduce line-item extraction accuracy
- extraction confidence is currently heuristic rather than statistically calibrated
- duplicate detection primarily uses machine-extracted document numbers
- corrected documents cannot currently be reprocessed
- file storage is local rather than object storage
- synchronous processing is used instead of a background job queue

These limitations are intentionally exposed through confidence scoring, validation issues, UNKNOWN classification, and human-review routing.

---

## Future Improvements

Potential production improvements include:

- larger real-world labelled training dataset
- greater layout variation during training
- document-layout-aware models
- improved table detection and reconstruction
- calibrated field confidence models
- versioned extraction runs
- correction-aware duplicate detection
- asynchronous processing using a worker queue
- cloud object storage
- malware scanning
- refresh-token/session management
- role-based review workflows
- monitoring and model drift detection
- containerized deployment
- automated CI/CD

---

## Demonstration Workflow

A recommended demonstration sequence is:

1. Register a new user.
2. Sign in.
3. Upload a supported invoice, quotation, or receipt.
4. Process the document.
5. Show the predicted document type and classification confidence.
6. Show extracted fields and field confidence.
7. Show extracted line items.
8. Show validation results.
9. Explain the calculated review status.
10. Open the protected original-document preview.
11. Correct an extracted field.
12. Show that the original machine value is preserved.
13. Show the human correction.
14. Open the audit history.
15. Demonstrate an unsupported or low-confidence document being classified as `UNKNOWN`.
16. Show that it is routed to `MANUAL_REQUIRED`.

---

## Design Decisions

### Why separate extraction and validation?

Extraction answers:

> What information appears to be present in the document?

Validation answers:

> Does that information make business sense?

Keeping them separate makes failures easier to understand, test, and maintain.

### Why PostgreSQL?

The application contains relational data involving users, documents, extracted fields, corrections, validation issues, and audit events.

A relational database provides appropriate ownership relationships and transactional consistency for this workflow.

### Why preserve original extracted values?

Human review should not destroy the original model output.

Keeping corrections separate makes it possible to determine:

- what the system originally extracted
- what confidence it assigned
- what a human changed
- who changed it
- when the correction occurred

### Why use UNKNOWN?

Forcing every uploaded document into a known category can create confidently incorrect results.

UNKNOWN provides an explicit safe path when the classifier does not have sufficient evidence.

---

## Assessment Scope

This project demonstrates an end-to-end intelligent document processing workflow rather than only a standalone ML notebook.

It combines:

```text
Machine Learning
       +
OCR / Document Processing
       +
Backend Engineering
       +
Database Persistence
       +
Security
       +
Business Validation
       +
Human Review
       +
Frontend Application
       +
Testing
       +
Auditability
```

The objective is not only to generate a prediction, but to build a system that can handle uncertain machine output safely and transparently.
