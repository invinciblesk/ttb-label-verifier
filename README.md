# AI-Powered Alcohol Label Verification

A prototype web application that compares information from an alcohol label application against text detected on uploaded label artwork.

The project was built as a proof of concept for a regulatory label-review workflow. It uses local OCR and structured comparison rules to help reviewers identify likely matches, discrepancies, and labels that need manual review.

The application does **not** automatically approve or reject alcohol labels. Final regulatory decisions remain with the reviewer.

---

## Deployed Application

**Application URL:** To be added after deployment.

---

## GitHub Repository

https://github.com/invinciblesk/ttb-label-verifier

---

## Features

- Single-label verification
- Batch label verification
- Local OCR using Tesseract
- Brand-name comparison
- Class / type comparison
- Alcohol-content verification
- Net-contents verification
- Producer / bottler verification
- Country-of-origin verification
- Government health warning detection
- Case- and punctuation-tolerant comparison
- Fuzzy text matching for OCR differences
- PASS, REVIEW, and FAIL-style results
- OCR text available for reviewer inspection
- Processing-time measurement
- Five-second performance-target indicator
- Error handling for unreadable or incomplete submissions
- Automated verification tests
- No external AI or OCR API required

---

# Requirements

Before installing the project, make sure the following software is available on the computer.

## Required Software

- Git
- Python 3.11 or later
- Node.js and npm
- Tesseract OCR

Tesseract is a **system dependency**. Installing the Python package `pytesseract` alone is not enough.

---

# Install Tesseract OCR

## macOS

If Homebrew is installed:

```bash
brew install tesseract
```

Confirm installation:

```bash
tesseract --version
```

---

## Ubuntu / Debian

```bash
sudo apt update
sudo apt install tesseract-ocr
```

Confirm installation:

```bash
tesseract --version
```

---

## Windows

Install Tesseract OCR and make sure the Tesseract executable is available through the Windows `PATH`.

After installation, open a new terminal and run:

```text
tesseract --version
```

If the command is not recognized, the Tesseract installation directory must be added to the system `PATH`.

---

# Installation

## 1. Clone the Repository

Open a terminal and run:

```bash
git clone https://github.com/invinciblesk/ttb-label-verifier.git
cd ttb-label-verifier
```

The project contains separate backend and frontend applications.

```text
ttb-label-verifier/
├── backend/
├── frontend/
└── README.md
```

---

# Backend Setup

## 2. Enter the Backend Directory

```bash
cd backend
```

## 3. Create a Python Virtual Environment

### macOS / Linux

```bash
python3 -m venv .venv
```

### Windows

```text
python -m venv .venv
```

---

## 4. Activate the Virtual Environment

### macOS / Linux

```bash
source .venv/bin/activate
```

### Windows PowerShell

```text
.venv\Scripts\Activate.ps1
```

### Windows Command Prompt

```text
.venv\Scripts\activate
```

---

## 5. Install Python Dependencies

With the virtual environment activated:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The backend uses packages including:

- FastAPI
- Uvicorn
- pytesseract
- Pillow
- RapidFuzz
- python-multipart

---

## 6. Confirm Tesseract Is Available

Before starting the backend:

```bash
tesseract --version
```

The command should display the installed Tesseract version.

---

## 7. Start the Backend

From the `backend` directory:

```bash
python -m uvicorn main:app --reload
```

The API should start at:

```text
http://127.0.0.1:8000
```

Keep this terminal open while using the application.

---

## 8. Test the Backend Health Endpoint

Open:

```text
http://127.0.0.1:8000/health
```

or run:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "healthy"
}
```

---

# Frontend Setup

Open a **second terminal**.

From the project root:

```bash
cd frontend
```

## 9. Install Frontend Dependencies

```bash
npm install
```

This installs the dependencies listed in `frontend/package.json`.

---

## 10. Start the Frontend

```bash
npm run dev
```

Vite will display the local development address, normally:

```text
http://localhost:5173
```

Open that address in a browser.

The backend and frontend must both remain running during local use.

---

# Quick Start After Initial Installation

Once the project has already been installed, start it using two terminals.

## Terminal 1 — Backend

```bash
cd ttb-label-verifier/backend
source .venv/bin/activate
python -m uvicorn main:app --reload
```

## Terminal 2 — Frontend

```bash
cd ttb-label-verifier/frontend
npm run dev
```

Then open:

```text
http://localhost:5173
```

---

# How to Use the Application

The interface provides two modes:

- **Single Label**
- **Batch Upload**

---

# Single Label Verification

Select **Single Label** and enter the information from the label application.

The current application fields are:

- Brand Name
- Class / Type
- Alcohol Content
- Net Contents
- Producer / Bottler
- Country of Origin

Producer / Bottler and Country of Origin are optional comparison fields.

Upload a supported label image and select:

```text
Verify Label
```

The application extracts text from the image and compares it with the submitted application information.

---

# Verification Results

Each field is evaluated separately.

Possible outcomes are:

## Match

The detected information matches the application information with sufficient confidence.

## Review

The system found a possible match but confidence is not high enough for an automatic match.

## Potential Issue

The expected value was not detected or appears inconsistent with the application.

The overall application result is either:

```text
CHECKS PASSED
```

or:

```text
MANUAL REVIEW REQUIRED
```

The system deliberately avoids using terms such as **Approved** or **Rejected** because regulatory judgment remains with the reviewer.

---

# Current Verification Checks

The prototype currently performs up to seven checks:

1. Brand Name
2. Class / Type
3. Alcohol Content
4. Net Contents
5. Government Warning
6. Producer / Bottler
7. Country of Origin

Producer / Bottler and Country of Origin are included when values are supplied.

---

# OCR Processing

The backend uses Tesseract OCR through `pytesseract`.

Uploaded images are processed locally.

The image-processing flow includes:

```text
Uploaded image
      |
      v
EXIF orientation correction
      |
      v
Image normalization
      |
      v
Grayscale conversion
      |
      v
Contrast enhancement
      |
      v
Tesseract OCR
      |
      v
Extracted text
      |
      v
Verification rules
```

Multiple OCR segmentation approaches are used to improve extraction of text positioned in different areas of a label.

---

# Why Local OCR Was Used

This prototype intentionally avoids dependence on an external OCR or machine-learning API.

Using local Tesseract OCR provides several advantages for the prototype:

- no API key is required
- label artwork does not need to be transmitted to a third-party service
- the application can function when outbound network access is restricted
- development and testing do not depend on third-party service availability
- there are no per-request OCR API costs

A production implementation could evaluate other OCR engines if infrastructure and security requirements allow them.

---

# Text Matching

OCR results do not always reproduce label text exactly.

For example:

```text
STONE'S THROW
```

and:

```text
Stone's Throw
```

should not automatically be treated as different brands.

The application normalizes text before comparison and uses fuzzy matching where appropriate.

Normalization reduces differences caused by:

- capitalization
- punctuation
- spacing
- minor OCR variations

Numeric fields are handled separately where possible.

---

# Alcohol Content Verification

Alcohol percentages are extracted numerically.

For example, an application value of:

```text
45%
```

can match label text such as:

```text
45% Alc./Vol. (90 Proof)
```

A label showing:

```text
50% ALC/VOL
```

against an application containing:

```text
45%
```

is treated as a discrepancy.

---

# Net Contents Verification

The application extracts common volume formats such as:

```text
750 mL
```

The comparison normalizes capitalization so values such as:

```text
750 ML
```

and:

```text
750 mL
```

can be treated consistently.

---

# Producer / Bottler Verification

The producer field can be matched within a longer OCR line.

For example, an application containing:

```text
Old Tom Distillery
```

can match:

```text
Produced and Bottled by Old Tom Distillery
```

---

# Country of Origin Verification

Country information can also be detected within a longer address.

For example:

```text
United States
```

can match OCR text such as:

```text
Louisville, Kentucky, United States
```

---

# Government Warning Verification

The prototype checks for the government health warning in the OCR output.

It checks for:

- the `GOVERNMENT WARNING:` heading
- uppercase heading text
- expected warning wording

The prototype can verify text content but cannot reliably determine whether OCR text was visually printed in **bold**.

Font-weight verification therefore remains a manual-review item.

This limitation is intentionally surfaced rather than presenting uncertain formatting analysis as a confirmed compliance result.

---

# Extracted Label Text

The reviewer can expand:

```text
View extracted label text
```

to inspect the text returned by OCR.

This helps explain why a field passed, failed, or was sent for review.

It is particularly useful when image quality causes incomplete OCR.

---

# Batch Verification

Select:

```text
Batch Upload
```

to process multiple label applications.

Batch mode requires:

1. A CSV manifest
2. The label image files referenced in that manifest

---

# Batch CSV Format

Required columns:

```text
filename,brand_name,class_type,alcohol_content,net_contents
```

Optional columns:

```text
producer,country_of_origin
```

Example:

```csv
filename,brand_name,class_type,alcohol_content,net_contents,producer,country_of_origin
old_tom_test_label.png,OLD TOM DISTILLERY,Kentucky Straight Bourbon Whiskey,45%,750 mL,Old Tom Distillery,United States
```

The value in the `filename` column must match the corresponding uploaded image filename.

---

# Prototype Batch Limit

Batch processing is currently limited to:

```text
20 labels per upload
```

The limit keeps the demonstration responsive while OCR is performed locally.

The stakeholder workflow may involve much larger batches. A production architecture could move OCR jobs to queued or parallel background workers so large submissions can be processed without blocking a browser request.

---

# Performance Target

Fast response time is important to the intended review workflow.

The backend records processing time for every image using a high-resolution timer.

Results include:

```text
processing_time_ms
```

and:

```text
performance_target_met
```

The current prototype evaluates each image against a:

```text
5-second target
```

The browser displays the result as, for example:

```text
Processed in 0.53 seconds · Within 5-second target
```

Actual performance depends on:

- image resolution
- image complexity
- OCR difficulty
- available CPU resources
- photograph quality

---

# Test Label

A synthetic test label is included at:

```text
backend/old_tom_test_label.png
```

It contains predictable text that can be used to verify the complete workflow.

The test image includes:

```text
OLD TOM DISTILLERY
Kentucky Straight Bourbon Whiskey
45% Alc./Vol. (90 Proof)
750 mL
Produced and Bottled by Old Tom Distillery
Louisville, Kentucky, United States
GOVERNMENT WARNING:
```

The test image can be recreated with:

```bash
cd backend
source .venv/bin/activate
python create_test_label.py
```

---

# Automated Tests

Development tests use `pytest`.

From the backend directory:

```bash
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Run:

```bash
python -m pytest -q
```

The automated test suite covers:

- normalization of capitalization and punctuation
- brand-name matching
- fuzzy text comparison
- alcohol-content matches
- alcohol-content mismatches
- net-content matching
- government-warning detection
- missing government-warning detection
- producer / bottler matching
- country-of-origin matching

---

# Example API Request

The single-label endpoint is:

```text
POST /verify
```

Example using `curl`:

```bash
curl -X POST http://127.0.0.1:8000/verify \
  -F "brand_name=OLD TOM DISTILLERY" \
  -F "class_type=Kentucky Straight Bourbon Whiskey" \
  -F "alcohol_content=45%" \
  -F "net_contents=750 mL" \
  -F "producer=Old Tom Distillery" \
  -F "country_of_origin=United States" \
  -F "label_image=@old_tom_test_label.png"
```

---

# Batch API

The batch endpoint is:

```text
POST /verify-batch
```

Example:

```bash
curl -X POST http://127.0.0.1:8000/verify-batch \
  -F "manifest=@sample_batch_manifest.csv" \
  -F "label_images=@old_tom_test_label.png"
```

---

# Error Handling

The prototype handles several common failure conditions, including:

- no image selected
- unreadable image
- empty image file
- OCR timeout
- missing CSV manifest
- malformed batch manifest
- missing required CSV columns
- image referenced in CSV but not uploaded
- unsupported batch files
- uncertain OCR matches

Where OCR confidence is insufficient, the application favors manual review rather than presenting an uncertain result as a confirmed match.

---

# Project Structure

```text
ttb-label-verifier/
│
├── backend/
│   ├── main.py
│   ├── create_test_label.py
│   ├── old_tom_test_label.png
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── sample_batch_manifest.csv
│   └── tests/
│       └── test_verification.py
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.js
│
├── .gitignore
└── README.md
```

---

# Architecture

```text
                    Browser
                       |
                       v
                React / Vite UI
                       |
                       | HTTP multipart requests
                       v
                   FastAPI
                       |
          +------------+-------------+
          |                          |
          v                          v
   Pillow processing          Verification rules
          |
          v
    Tesseract OCR
          |
          v
    Extracted text
          |
          +--------------------------+
                       |
                       v
               RapidFuzz / Regex
                       |
                       v
          PASS / REVIEW / FAIL
                       |
                       v
                Reviewer decision
```

---

# Technology Stack

## Frontend

- React
- Vite
- JavaScript
- CSS

## Backend

- Python
- FastAPI
- Uvicorn
- Tesseract OCR
- pytesseract
- Pillow
- RapidFuzz
- python-multipart

## Testing

- pytest

---

# Design Decisions

## Local OCR Instead of External OCR APIs

The prototype was designed to avoid external OCR dependencies because the intended environment may restrict outbound access to external services.

## Human Review Is Preserved

OCR is imperfect, particularly with photographs of real bottles.

For that reason, uncertain results are routed to manual review instead of being treated as definitive regulatory failures or approvals.

## Structured Numeric Verification

Alcohol content and net contents are evaluated separately from general fuzzy-text matching because numeric discrepancies can be significant even when surrounding text is similar.

## Simple Interface

The primary interaction is intentionally limited to entering application values, uploading a label, and viewing the comparison results.

## Batch Support

Batch processing is included because review workflows may involve many labels submitted together.

---

# Known Limitations

OCR quality can decrease when images contain:

- curved bottle surfaces
- decorative fonts
- glare
- reflections
- angled photographs
- poor lighting
- low resolution
- very small print
- partially obstructed text

For example, a bottle photograph may display `750 ML`, but OCR may only extract part of the value.

The application does not infer missing characters simply to create a match. In such cases, the result is sent for manual review.

Other prototype limitations include:

- no COLA integration
- no user authentication
- no database
- no persistent document storage
- no PII-retention workflow
- no audit-log implementation
- no automatic final regulatory decision
- no reliable visual font-weight verification
- no implementation of every possible TTB labeling regulation
- sequential local OCR for batch processing

---

# Production Considerations

A production implementation would likely require additional work in areas such as:

- identity and access management
- document-retention policies
- audit logging
- encryption
- secure storage
- accessibility testing
- monitoring
- centralized logging
- scalable OCR workers
- queued batch processing
- deployment within approved government infrastructure
- integration with existing regulatory systems
- expanded regulatory-rule coverage
- model and OCR performance monitoring

Those items are intentionally outside the scope of this standalone prototype.

---

# Privacy and Data Handling

The prototype does not require an external OCR service.

Uploaded label images are processed by the FastAPI application using local Tesseract OCR.

The current prototype does not implement permanent application-document storage.

A production environment would require formal retention, access-control, logging, and security policies before handling sensitive production records.

---

# Development Notes

The backend API is currently configured for the local React development environment.

Local development normally uses:

```text
Frontend: http://localhost:5173
Backend:  http://127.0.0.1:8000
```

Deployment configuration may use a different frontend/backend origin.

---

# Scope

This project demonstrates an OCR-assisted label-comparison workflow.

It is intended to show how automated extraction and comparison can reduce repetitive review work while keeping compliance decisions with a human reviewer.

It is not intended to represent a complete regulatory compliance engine.

---

# Deployment

The assessment requires a publicly accessible application.

The deployment URL will be added here after deployment is completed:

```text
TBD
```

---

# Repository

Source code:

```text
https://github.com/invinciblesk/ttb-label-verifier
```

---

# License

This project was created as a take-home technical assessment prototype.
