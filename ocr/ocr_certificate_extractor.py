# -*- coding: utf-8 -*-
"""
OCR Certificate Extraction Module

Description:
This script extracts structured academic certificate data from
PDF or image files using OCR (Tesseract) and custom parsing logic.

It is designed for semester grade report–style certificates and
produces JSON output that can be stored in a database.

Main Capabilities:
- Convert PDF/image certificates into images
- Perform OCR using pytesseract
- Preprocess images using OpenCV to improve text recognition
- Parse extracted text into structured fields
- Generate SHA-256 hashes for document integrity
- Export results as JSON

Input:
    PDF / PNG / JPG certificate file

Output:
    Structured JSON containing:
        student_name
        roll_number
        registration_number
        programme
        semester
        courses
        SGPA / CGPA
        document hash

Author: Trayambak Rai
Project: Blockchain-Based Certificate Authentication System
"""

# -------------------------
# IMPORTS
# -------------------------
import io
import os
import re
import json
import hashlib
import requests
from typing import List, Dict, Any, Optional

from PIL import Image
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
from pytesseract import Output
import cv2
import numpy as np
from pdf2image import convert_from_bytes


# -------------------------
# GLOBAL REGEX PATTERNS
# -------------------------
YEAR_PATTERN = re.compile(r"\b(20\d{2})\b")
ROLL_PATTERN = re.compile(r"^\d{6,}$")


# -------------------------
# HASH UTIL
# -------------------------
def compute_sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

# -------------------------
# OCR CONFIDENCE UTIL
# -------------------------
def compute_ocr_confidence(ocr_data: Dict[str, Any]) -> float:
    """
    Computes average OCR confidence from Tesseract output.
    Ignores invalid confidence values (-1).
    """

    confidences = []

    for conf in ocr_data.get("conf", []):
        try:
            c = float(conf)
            if c >= 0:  # ignore -1
                confidences.append(c)
        except:
            continue

    if not confidences:
        return 0.0

    return sum(confidences) / len(confidences)

# -------------------------
# TESSERACT CONFIG
# -------------------------
def get_tesseract_config():
    config = r"""
    --oem 3
    --psm 4
    -l eng
    -c preserve_interword_spaces=1
    -c tessedit_do_invert=0
    -c textord_tablefind_recognize_tables=1
    -c textord_tabfind_find_tables=1
    """
    return config


# -------------------------
# FILE LOADING (PDF / IMAGE)
# -------------------------
def load_file_to_pil(path_or_bytes: Any) -> List[Image.Image]:

    if isinstance(path_or_bytes, (bytes, bytearray)):
        try:
            imgs = convert_from_bytes(
                path_or_bytes,
                dpi=300,
                poppler_path=r"C:\Users\traya\Documents\poppler\Library\bin"
            )
            return imgs
        except Exception:
            return [Image.open(io.BytesIO(path_or_bytes)).convert("RGB")]

    elif isinstance(path_or_bytes, str):

        if path_or_bytes.lower().endswith('.pdf'):

            with open(path_or_bytes, 'rb') as f:
                pdf_bytes = f.read()

            imgs = convert_from_bytes(
                pdf_bytes,
                dpi=300,
                poppler_path=r"C:\Users\traya\Documents\poppler\Library\bin"
            )

            return imgs

        else:

            img = Image.open(path_or_bytes).convert("RGB")

            return [img]

    else:
        raise ValueError("Unsupported input type for load_file_to_pil")


# -------------------------
# PIL TO CV2 CONVERSION
# -------------------------
def pil_to_cv2(img: Image.Image) -> np.ndarray:

    arr = np.array(img)

    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)


# -------------------------
# IMAGE PREPROCESSING
# -------------------------
def preprocess_for_ocr_cv2(img_bgr: np.ndarray) -> np.ndarray:

    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    h, w = gray.shape

    if max(h, w) < 1000:

        scale = 1000 / max(h, w)

        new_w = int(w * scale)

        new_h = int(h * scale)

        gray = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

    denoised = cv2.fastNlMeansDenoising(gray, None, h=10)

    try:

        th = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            11
        )

    except Exception:

        th = denoised

    return th


# -------------------------
# OCR EXECUTION
# -------------------------
def ocr_image_to_text(pil_img: Image.Image) -> Dict[str, Any]:

    cv2_img = pil_to_cv2(pil_img)

    pre = preprocess_for_ocr_cv2(cv2_img)

    pil_pre = Image.fromarray(pre)

    ocr_data = pytesseract.image_to_data(
        pil_pre,
        output_type=Output.DICT,
        config=get_tesseract_config()
    )

    n = len(ocr_data['text'])

    lines = []

    current_line = []

    for i in range(n):

        txt = ocr_data['text'][i].strip()

        if not txt:

            if current_line:
                lines.append(" ".join(current_line))
                current_line = []

            continue

        current_line.append(txt)

        if (i + 1 < n and ocr_data['line_num'][i] != ocr_data['line_num'][i + 1]) or (i == n - 1):

            lines.append(" ".join(current_line))

            current_line = []

    raw_text = "\n".join(lines)

    full_text = pytesseract.image_to_string(
        pil_pre,
        config=get_tesseract_config()
    )

    return {
        "raw_text": raw_text,
        "full_text": full_text,
        "ocr_data": ocr_data
    }


# -------------------------
# NUMBER NORMALIZATION
# -------------------------
def normalize_number(val: str) -> float:

    val = val.replace("S", "5")

    if val.isdigit() and int(val) > 10:

        if len(val) == 3:
            return float(val[0] + "." + val[1:])

        elif len(val) == 2:
            return float(val[0] + "." + val[1:])

    return float(val)


# -------------------------
# OCR TEXT CLEANING
# -------------------------
def normalize_ocr_text(text: str) -> str:

    text = text.replace("PR0GRAMME", "PROGRAMME")
    text = text.replace("C0URSE", "COURSE")
    text = text.replace("CRED1T", "CREDIT")
    text = text.replace("ADM1SS10N", "ADMISSION")
    text = text.replace("PERF0RMANCE", "PERFORMANCE")

    text = text.replace("SCH00L", "SCHOOL")
    text = text.replace("1NST1TUTE", "INSTITUTE")
    text = text.replace("1NDUSTR1AL", "INDUSTRIAL")
    text = text.replace("TECHN0L0GY", "TECHNOLOGY")

    # course specific corrections
    text = text.replace("GenAl", "GenAI")
    text = text.replace("GenAl ", "GenAI ")
    text = text.replace("Project- |", "Project- I")
    text = text.replace("ICALINGA", "KALINGA")
    text = text.replace("IIIT", "KIIT")
    text = text.replace("$", "3")
    text = text.replace("0C", "OC")


    text = re.sub(r"\bCS331002\b", "CS31002", text)
    text = re.sub(r"\bom\b", "6th", text, flags=re.IGNORECASE)

    text = re.sub(r"(\d)S(\d)", r"\g<1>5\g<2>", text)
    text = re.sub(r"(\d\.\d)S", r"\g<1>5", text)

    return text 

def normalize_grade(g):

    g = g.upper()

    if g in ["0", "OO", "O0","Oo", "oO"]:
        return "O"

    if g in ["E", "EE", "E0", "Eo", "eE"]:
        return "E"

    if g in ["A", "AA", "A0", "Ao", "aA"]:
        return "A"

    if g in ["B", "BB", "B0", "Bo", "bB"]:
        return "B"
    
    if g in ["C", "CC", "C0", "Co", "cC"]:
        return "C"
    
    if g in ["D", "DD", "D0", "Do", "dD"]:
        return "D"
    
    if g in ["F", "FF", "F0", "Fo", "fF"]:
        return "F"
    
    return g

# -------------------------
# REPORT PARSING LOGIC
# -------------------------
def parse_semester_report_text(raw_text: str) -> Dict[str, Any]:

    lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]

    joined = "\n".join(lines)

    out: Dict[str, Any] = {

        "student_name": None,
        "roll_number": None,
        "registration_number": None,
        "programme": None,
        "year_of_admission": None,
        "semester": None,
        "courses": [],
        "remarks": None,
        "sgpa": None,
        "cgpa": None,
        "cumulative_credits": None,
        "raw_text_hash": compute_sha256_bytes(joined.encode("utf-8")),
    }

    # -------------------------
    # YEAR OF ADMISSION
    # -------------------------
    for ln in lines[:25]:

        if "YEAR" in ln.upper() and "ADMISSION" in ln.upper():

            m = YEAR_PATTERN.search(ln)

            if m:
                out["year_of_admission"] = m.group(0)

            break

    # -------------------------
    # STUDENT DETAILS
    # -------------------------
    for i, ln in enumerate(lines):

        if "STUDENT" in ln.upper() and "NAME" in ln.upper():

            if i + 1 < len(lines):

                candidate = lines[i + 1]

                tokens = candidate.split()

                name_parts = []

                numbers = []

                for t in tokens:

                    clean = re.sub(r"[^\d]", "", t)

                    if len(clean) >= 6:

                        numbers.append(clean)

                        continue

                    name_parts.append(t)

                if name_parts and name_parts[-1].lower() in ["om", "oh", "on"]:
                    name_parts = name_parts[:-1]

                name_parts = [p for p in name_parts if not re.match(r"\d+(st|nd|rd|th)", p, re.IGNORECASE)]

                if name_parts:
                    out["student_name"] = " ".join(name_parts)

                if len(numbers) >= 2:

                    out["roll_number"] = numbers[0]

                    out["registration_number"] = numbers[1]

                elif len(numbers) == 1:

                    out["roll_number"] = numbers[0]

                sem_match = re.search(r"\b(\d+(st|nd|rd|th))\b", candidate, re.IGNORECASE)

                if sem_match:
                    out["semester"] = sem_match.group(1)

            break

    # -------------------------
    # PROGRAMME
    # -------------------------
    for ln in lines:

        if "PROGRAMME" in ln.upper():

            prog_match = re.search(r"PROGRAMME\s*:?\s*(.+)", ln, re.IGNORECASE)

            if prog_match:
                out["programme"] = prog_match.group(1).strip()

            break

    # -------------------------
    # REMARKS
    # -------------------------
    for ln in lines:

        if "REMARK" in ln.upper():

            if "-" in ln:

                out["remarks"] = ln.split("-", 1)[1].strip()

            break

    # -------------------------
    # COURSE TABLE PARSING
    # -------------------------
   
    course_code_pattern = re.compile(r"^[A-Z]{2,4}\d{3,5}")

    for ln in lines:

        if not course_code_pattern.match(ln):
            continue

        parts = ln.split()

        if len(parts) < 4:
            continue

        code = parts[0]

        grade = normalize_grade(parts[-1])

        credits = parts[-2]

        name = re.sub(r"\s+", " ", " ".join(parts[1:-2])).strip()

        try:
            credits = int(credits)
        except:
            continue

        out["courses"].append({
            "course_code": code,
            "course_name": name.strip(),
            "credits": credits,
            "grade": grade
        })
    # -------------------------
    # PERFORMANCE BLOCK
    # -------------------------
    perf_idx = None

    for i, ln in enumerate(lines):

        if "PERFORMANCE" in ln.upper():

            perf_idx = i

            break

    if perf_idx is not None:

        for j in range(perf_idx, min(perf_idx + 15, len(lines))):

            row = re.sub(r"[^\d\.\s,]", " ", lines[j])

            row = row.replace(",", "")

            parts = re.findall(r"\d+(?:\.\d+)?", row)

            if len(parts) >= 6:

                out["credits"] = int(parts[0])
                out["credit_index"] = int(parts[1])
                out["sgpa"] = normalize_number(parts[2])
                out["cumulative_credits"] = int(parts[3])
                out["cumulative_credit_index"] = int(parts[4])
                out["cgpa"] = normalize_number(parts[5])

                break

    # -------------------------
    # FINAL STRING CLEANUP
    # -------------------------
    for k, v in out.items():

        if isinstance(v, str):

            out[k] = re.sub(r"\s+", " ", v).strip()

    return out


# -------------------------
# PUBLIC IP FETCH
# -------------------------
def get_public_ip(timeout=5) -> Optional[str]:

    try:

        resp = requests.get('https://api.ipify.org?format=text', timeout=timeout)

        if resp.status_code == 200:

            return resp.text.strip()

    except Exception:

        return None

    return None


# -------------------------
# MAIN EXTRACTION PIPELINE
# -------------------------
def extract_from_file(path_or_bytes: Any) -> Dict[str, Any]:

    pil_pages = load_file_to_pil(path_or_bytes)

    pil_img = pil_pages[0]

    buf = io.BytesIO()

    pil_img.save(buf, format='PNG')

    png_bytes = buf.getvalue()

    doc_hash = compute_sha256_bytes(png_bytes)

    ocr_res = ocr_image_to_text(pil_img)

    ocr_confidence = compute_ocr_confidence(ocr_res['ocr_data'])

    raw_text = ocr_res.get('raw_text') or ocr_res.get('full_text') or ""

    raw_text = normalize_ocr_text(raw_text)

    parsed = parse_semester_report_text(raw_text)

    parsed['document_image_hash'] = doc_hash

    parsed['ocr_engine'] = 'pytesseract'

    parsed['ocr_confidence'] = round(ocr_confidence, 2)

    parsed['is_low_quality'] = ocr_confidence < 60
    
    parsed['_raw_text'] = raw_text[:5000]

    return parsed


# -------------------------
# CLI ENTRY
# -------------------------
def main(input_path: str):

    print("Processing:", input_path)

    if input_path.lower().endswith('.pdf'):

        with open(input_path, 'rb') as f:

            b = f.read()

        parsed = extract_from_file(b)

    else:

        parsed = extract_from_file(input_path)

    parsed['_meta'] = {

        'public_ip': get_public_ip(),

        'processor': 'ocr_certificate_extractor.py'
    }

    print(json.dumps(parsed, indent=2, ensure_ascii=False))

    output_dir = os.path.join(os.path.dirname(__file__), "..", "json_op")
    os.makedirs(output_dir, exist_ok=True)

    out_fn = os.path.join(
        output_dir,
        os.path.splitext(os.path.basename(input_path))[0] + '_extracted.json'
    )

    with open(out_fn, 'w', encoding='utf-8') as fw:

        json.dump(parsed, fw, indent=2, ensure_ascii=False)

    print("Saved result to", out_fn)
    return out_fn

# -------------------------
# SCRIPT EXECUTION
# -------------------------
if __name__ == "__main__":

    import sys

    if len(sys.argv) < 2:

        print("Usage: python ocr_certificate_extractor.py <file>")

    else:

        main(sys.argv[1])