# 🎓 Cert_Authenticator - OCR + Blockchain Certificate Verification System

Cert_Authenticator

---

## 📌 Overview

Cert_Authenticator is a backend-focused system that combines **OCR (Optical Character Recognition)** and **Blockchain technology** to verify academic certificates.

The system extracts structured data from certificate documents (PDF/Image), generates a secure **SHA-256 hash**, and stores it on the **Ethereum blockchain (Sepolia testnet)**. This ensures that certificates cannot be tampered with and can be independently verified.

This repository focuses only on the **core engine**:

* OCR extraction pipeline
* Blockchain storage & verification

---

## 🚀 Features

* 📄 Certificate Data Extraction (PDF/Image → JSON)
* 🔍 OCR with preprocessing (OpenCV + Tesseract)
* 📊 Structured parsing of semester reports
* 🔐 SHA-256 document hashing
* ⛓️ Blockchain storage (Ethereum Sepolia)
* ✅ Certificate authenticity verification
* 📁 JSON output generation for further backend/database use
* 📈 OCR confidence scoring & quality detection

---

## 🧠 How It Works

```text
Certificate (PDF/Image)
        ↓
Image Preprocessing (OpenCV)
        ↓
OCR Extraction (Tesseract)
        ↓
Structured Parsing → JSON
        ↓
Generate SHA-256 Hash
        ↓
Store Hash on Blockchain
        ↓
Verification (Hash Matching)
```

---

## 🛠️ Tech Stack

### OCR & Processing

* Python
* OpenCV
* Pytesseract
* Pillow
* pdf2image
* NumPy

### Blockchain

* Web3.py
* Solidity (Smart Contract)
* Ethereum Sepolia Testnet
* Alchemy RPC

---

## 🔐 Blockchain Design (Brief)

* A smart contract is deployed on Ethereum Sepolia
* Stores:

  * Document hash
  * Issuer address
  * Timestamp
* Prevents duplicate entries
* Enables:

  * Hash verification
  * Certificate lookup

### Key Functions

* `storeHash()` → stores certificate hash
* `verifyHash()` → checks existence
* `getCertificate()` → fetch metadata

---

## 📊 OCR Accuracy & Quality Handling

* Uses Tesseract confidence scores
* Computes average OCR confidence
* Adds fields:

  * `ocr_confidence`
  * `is_low_quality`

### Example:

```json
{
  "ocr_confidence": 90.09,
  "is_low_quality": false
}
```

---

## 📂 Project Structure

```text
Certi_Authenticator/
│
├── ocr/
│   └── ocr_certificate_extractor.py
│
├── blockchain/
│   └── web3_integration.py
│
├── json_op/
│   └── extracted JSON outputs
│
├── samples/
│   └── sample certificates
│
├── requirements.txt
└── README.md
```

---

## 🔧 Installation & Setup

### 1️⃣ Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/Cert_Authenticator.git
cd Cert_Authenticator
```

---

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

---

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Usage

### Run OCR Extraction

```bash
python ocr/ocr_certificate_extractor.py samples/kiit_sem6.pdf
```

👉 Output JSON will be saved in:

```text
json_op/
```

---

### Run Blockchain Integration

```bash
python blockchain/web3_integration.py
```

---

## 📊 Sample Output

```json
{
  "student_name": "RAI TRAYAMBAK ANANDKUMAR",
  "semester": "6th",
  "sgpa": 8.75,
  "cgpa": 8.41,
  "document_image_hash": "...",
  "ocr_confidence": 90.09
}
```

---

## 🔍 Verification Logic

* Extract hash from document
* Compare with blockchain

| Condition     | Result     |
| ------------- | ---------- |
| Hash match    | ✅ Valid    |
| Hash mismatch | ❌ Tampered |

---

## 🚧 Future Scope

* Dual hash system (image + text hash)
* REST API (FastAPI backend)
* Frontend dashboard
* Database integration
* Multi-format certificate support

---

## 📬 Author

**Trayambak Rai**

---

## ⭐ If you like this project, give it a star!
