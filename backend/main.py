from io import BytesIO
import re

import pytesseract
from PIL import Image, ImageOps, UnidentifiedImageError
from rapidfuzz import fuzz
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


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "TTB Label Verification API is running"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


def extract_text(image_bytes: bytes) -> str:
    try:
        image = Image.open(BytesIO(image_bytes))
        image = ImageOps.exif_transpose(image)
        image = image.convert("L")
        image = ImageOps.autocontrast(image)

        text = pytesseract.image_to_string(
            image,
            config="--psm 6"
        )

        return text.strip()

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

    ocr_text = extract_text(image_bytes)

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
        )
    ]

    if all(check["status"] == "PASS" for check in checks):
        overall_status = "CHECKS PASSED"
    else:
        overall_status = "MANUAL REVIEW REQUIRED"

    return {
        "status": "processed",
        "overall_status": overall_status,
        "checks": checks,
        "ocr": {
            "text": ocr_text
        },
        "image": {
            "filename": label_image.filename
        }
    }
