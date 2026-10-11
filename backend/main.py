from pathlib import Path
from io import BytesIO, StringIO
import csv
import re
import time

import pytesseract
from PIL import Image, ImageOps, UnidentifiedImageError
from rapidfuzz import fuzz
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="TTB Label Verification API",
    version="0.3.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "healthy"}


def extract_text(image_bytes: bytes) -> str:
    try:
        image = Image.open(BytesIO(image_bytes))
        image = ImageOps.exif_transpose(image).convert("RGB")

        # Keep enough resolution for small label text without making OCR too slow.
        max_dimension = 1800
        current_max = max(image.size)

        if current_max > max_dimension:
            scale = max_dimension / current_max
            image = image.resize(
                (
                    int(image.width * scale),
                    int(image.height * scale),
                )
            )

        # OCR version 1: grayscale with improved contrast.
        grayscale = image.convert("L")
        grayscale = ImageOps.autocontrast(grayscale)

        try:
            structured_text = pytesseract.image_to_string(
                grayscale,
                config="--oem 3 --psm 6",
                timeout=2.5
            )
        except RuntimeError:
            structured_text = ""

        # OCR version 2: sparse-text mode catches separated label elements.
        try:
            sparse_text = pytesseract.image_to_string(
                grayscale,
                config="--oem 3 --psm 11",
                timeout=2.5
            )
        except RuntimeError:
            sparse_text = ""

        # Combine the passes while removing duplicate lines.
        lines = []
        seen = set()

        for result in (structured_text, sparse_text):
            for line in result.splitlines():
                cleaned = line.strip()

                if cleaned and cleaned not in seen:
                    seen.add(cleaned)
                    lines.append(cleaned)

        return "\n".join(lines)

    except UnidentifiedImageError:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file could not be read as an image."
        )

def normalize_text(value: str) -> str:
    value = value.upper()
    value = re.sub(r"[^A-Z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def best_text_match(expected: str, ocr_text: str):
    expected_normalized = normalize_text(expected)

    lines = [
        normalize_text(line)
        for line in ocr_text.splitlines()
        if normalize_text(line)
    ]

    if not lines:
        return 0, ""

    best_line = ""
    best_score = 0

    for line in lines:
        score = fuzz.ratio(expected_normalized, line)

        if score > best_score:
            best_score = score
            best_line = line

    return round(best_score), best_line


def verify_text_field(field_name: str, expected: str, ocr_text: str):
    score, matched_text = best_text_match(expected, ocr_text)

    if score >= 90:
        status = "PASS"
    elif score >= 70:
        status = "REVIEW"
    else:
        status = "FAIL"

    return {
        "field": field_name,
        "status": status,
        "expected": expected,
        "detected": matched_text if score >= 70 else None,
        "similarity": score
    }


def extract_percentage(value: str):
    match = re.search(r"(\d+(?:\.\d+)?)\s*%", value)

    if match:
        return float(match.group(1))

    return None


def verify_alcohol(expected: str, ocr_text: str):
    expected_value = extract_percentage(expected)

    percentages = re.findall(
        r"(\d+(?:\.\d+)?)\s*%",
        ocr_text
    )

    detected_values = [float(value) for value in percentages]

    if expected_value is None:
        return {
            "field": "Alcohol Content",
            "status": "REVIEW",
            "expected": expected,
            "detected": detected_values or None,
            "reason": "Expected alcohol percentage could not be interpreted."
        }

    if expected_value in detected_values:
        status = "PASS"
    elif detected_values:
        status = "FAIL"
    else:
        status = "FAIL"

    return {
        "field": "Alcohol Content",
        "status": status,
        "expected": f"{expected_value:g}%",
        "detected": detected_values or None
    }


def normalize_volume(value: str):
    match = re.search(
        r"(\d+(?:\.\d+)?)\s*(ML|L|OZ)",
        value.upper()
    )

    if not match:
        return None

    amount = float(match.group(1))
    unit = match.group(2)

    return amount, unit


def verify_net_contents(expected: str, ocr_text: str):
    expected_volume = normalize_volume(expected)

    if expected_volume is None:
        return {
            "field": "Net Contents",
            "status": "REVIEW",
            "expected": expected,
            "detected": None,
            "reason": "Expected net contents could not be interpreted."
        }

    detected_matches = re.findall(
        r"(\d+(?:\.\d+)?)\s*(ML|L|OZ)",
        ocr_text.upper()
    )

    detected_volumes = [
        (float(amount), unit)
        for amount, unit in detected_matches
    ]

    status = (
        "PASS"
        if expected_volume in detected_volumes
        else "FAIL"
    )

    detected_display = [
        f"{amount:g} {unit}"
        for amount, unit in detected_volumes
    ]

    return {
        "field": "Net Contents",
        "status": status,
        "expected": f"{expected_volume[0]:g} {expected_volume[1]}",
        "detected": detected_display or None
    }




def verify_optional_text_field(field_name: str, expected: str, ocr_text: str):
    if not expected.strip():
        return None

    expected_normalized = normalize_text(expected)

    lines = [
        normalize_text(line)
        for line in ocr_text.splitlines()
        if normalize_text(line)
    ]

    best_score = 0
    best_line = ""

    for line in lines:
        score = fuzz.partial_ratio(expected_normalized, line)

        if score > best_score:
            best_score = score
            best_line = line

    best_score = round(best_score)

    if best_score >= 90:
        status = "PASS"
    elif best_score >= 70:
        status = "REVIEW"
    else:
        status = "FAIL"

    return {
        "field": field_name,
        "status": status,
        "expected": expected,
        "detected": best_line if best_score >= 70 else None,
        "similarity": best_score
    }

REQUIRED_WARNING = """
GOVERNMENT WARNING:
(1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects.
(2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.
""".strip()


def normalize_warning(value: str) -> str:
    value = value.replace("\n", " ")
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"\s+([.,:;])", r"\1", value)
    return value.strip()


def verify_government_warning(ocr_text: str):
    normalized_ocr = normalize_warning(ocr_text)
    normalized_required = normalize_warning(REQUIRED_WARNING)

    heading_present = "GOVERNMENT WARNING:" in ocr_text

    body_required = normalize_warning(
        REQUIRED_WARNING.replace("GOVERNMENT WARNING:", "")
    )

    body_present = body_required.lower() in normalized_ocr.lower()

    if heading_present and body_present:
        status = "PASS"
        detected = "Required warning text detected"
        reason = (
            "Warning wording and uppercase heading were detected. "
            "Font weight should be confirmed manually."
        )
    elif heading_present:
        status = "REVIEW"
        detected = "Government warning heading detected"
        reason = (
            "The warning heading was found, but the complete required wording "
            "was not confidently detected."
        )
    else:
        status = "FAIL"
        detected = None
        reason = "The required government warning was not detected."

    return {
        "field": "Government Warning",
        "status": status,
        "expected": "Required government health warning",
        "detected": detected,
        "reason": reason
    }

@app.post("/verify")
async def verify_label(
    brand_name: str = Form(...),
    class_type: str = Form(...),
    alcohol_content: str = Form(...),
    net_contents: str = Form(...),
    producer: str = Form(""),
    country_of_origin: str = Form(""),
    label_image: UploadFile = File(...)
):
    if (
        not label_image.content_type
        or not label_image.content_type.startswith("image/")
    ):
        raise HTTPException(
            status_code=400,
            detail="Please upload an image file."
        )

    image_bytes = await label_image.read()

    if not image_bytes:
        raise HTTPException(
            status_code=400,
            detail="The uploaded image is empty."
        )

    processing_started = time.perf_counter()
    ocr_text = extract_text(image_bytes)
    processing_time_ms = round((time.perf_counter() - processing_started) * 1000)

    checks = [
        verify_text_field(
            "Brand Name",
            brand_name,
            ocr_text
        ),
        verify_text_field(
            "Class / Type",
            class_type,
            ocr_text
        ),
        verify_alcohol(
            alcohol_content,
            ocr_text
        ),
        verify_net_contents(
            net_contents,
            ocr_text
        ),
        verify_government_warning(
            ocr_text
        )
    ]

    producer_check = verify_optional_text_field(
        "Producer / Bottler",
        producer,
        ocr_text
    )

    if producer_check:
        checks.append(producer_check)

    country_check = verify_optional_text_field(
        "Country of Origin",
        country_of_origin,
        ocr_text
    )

    if country_check:
        checks.append(country_check)

    if all(check["status"] == "PASS" for check in checks):
        overall_status = "CHECKS PASSED"
    else:
        overall_status = "MANUAL REVIEW REQUIRED"

    return {
        "status": "processed",
        "overall_status": overall_status,
        "checks": checks,
        "ocr": {"text": ocr_text},
        "processing_time_ms": processing_time_ms,
        "performance_target_met": processing_time_ms <= 5000,
        "image": {
            "filename": label_image.filename
        }
    }


@app.post("/verify-batch")
async def verify_batch(
    manifest: UploadFile = File(...),
    label_images: list[UploadFile] = File(...)
):
    if not manifest.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Batch manifest must be a CSV file."
        )

    manifest_bytes = await manifest.read()

    try:
        manifest_text = manifest_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Batch manifest must use UTF-8 encoding."
        )

    reader = csv.DictReader(StringIO(manifest_text))

    required_columns = {
        "filename",
        "brand_name",
        "class_type",
        "alcohol_content",
        "net_contents",
    }

    if not reader.fieldnames or not required_columns.issubset(reader.fieldnames):
        raise HTTPException(
            status_code=400,
            detail=(
                "CSV must contain filename, brand_name, class_type, "
                "alcohol_content, and net_contents columns."
            )
        )

    rows = list(reader)

    if len(rows) > 20:
        raise HTTPException(
            status_code=400,
            detail="Prototype batch processing is limited to 20 labels per upload."
        )

    image_map = {
        image.filename: image
        for image in label_images
    }

    results = []

    for row in rows:
        filename = row.get("filename", "").strip()

        if not filename:
            results.append({
                "filename": None,
                "overall_status": "ERROR",
                "error": "Manifest row is missing a filename."
            })
            continue

        image = image_map.get(filename)

        if image is None:
            results.append({
                "filename": filename,
                "overall_status": "ERROR",
                "error": "Matching image was not uploaded."
            })
            continue

        if not image.content_type or not image.content_type.startswith("image/"):
            results.append({
                "filename": filename,
                "overall_status": "ERROR",
                "error": "Uploaded file is not a supported image."
            })
            continue

        image_bytes = await image.read()

        if not image_bytes:
            results.append({
                "filename": filename,
                "overall_status": "ERROR",
                "error": "Uploaded image is empty."
            })
            continue

        processing_started = time.perf_counter()
        ocr_text = extract_text(image_bytes)
        processing_time_ms = round((time.perf_counter() - processing_started) * 1000)

        checks = [
            verify_text_field(
                "Brand Name",
                row.get("brand_name", ""),
                ocr_text
            ),
            verify_text_field(
                "Class / Type",
                row.get("class_type", ""),
                ocr_text
            ),
            verify_alcohol(
                row.get("alcohol_content", ""),
                ocr_text
            ),
            verify_net_contents(
                row.get("net_contents", ""),
                ocr_text
            ),
            verify_government_warning(
                ocr_text
            )
        ]

        producer_check = verify_optional_text_field(
            "Producer / Bottler",
            row.get("producer", ""),
            ocr_text
        )

        if producer_check:
            checks.append(producer_check)

        country_check = verify_optional_text_field(
            "Country of Origin",
            row.get("country_of_origin", ""),
            ocr_text
        )

        if country_check:
            checks.append(country_check)

        if all(check["status"] == "PASS" for check in checks):
            overall_status = "CHECKS PASSED"
        else:
            overall_status = "MANUAL REVIEW REQUIRED"

        results.append({
            "filename": filename,
            "overall_status": overall_status,
            "passed": sum(
                1 for check in checks
                if check["status"] == "PASS"
            ),
            "total_checks": len(checks),
            "checks": checks,
            "ocr": {"text": ocr_text},
            "processing_time_ms": processing_time_ms,
            "performance_target_met": processing_time_ms <= 5000
        })

    return {
        "status": "processed",
        "batch_size": len(rows),
        "results": results
    }

# Serve the production React build when it is available.
frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if frontend_dist.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(frontend_dist), html=True),
        name="frontend",
    )

