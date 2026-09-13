# 56 File Converter

A modern, lightning-fast, 100% secure, and completely free universal file conversion studio. Convert documents, images, and spreadsheets across 50+ formats with zero limits, zero watermarks, and strict zero-data retention.

---

## ✨ Key Highlights

- **100% Free Forever**: No hidden fees, no subscriptions, no credit cards, no watermarks.
- **No Daily Limits**: Convert as many files as you want; supports multi-file batch uploads.
- **100% Secure & Extreme Privacy**: 
  - Source files are deleted **immediately** after conversion.
  - Converted files and temporary folders are permanently deleted from everywhere (server, memory, disk, and site) after **1 minute**.
  - Zero databases, zero permanent storage, zero third-party access.
- **Instant Lightning Speed**: Powered by Python native engines (`PyMuPDF`, `Pillow`, `ReportLab`, `pdf2docx`, `openpyxl`).
- **50+ Conversion Pairs**: Full coverage across Word, PDF, JPG, PNG, WebP, Excel, CSV, JSON, Markdown, and more.
- **Seamless Light & Dark Mode**: One-click toggle with smooth theme transition and persistence.
- **Batch Processing & ZIP Download**: Convert multiple files at once and download everything in a single archive before the 1-minute auto-deletion.

---

## 🚀 Supported Conversions

### 📄 Documents
- **Word (.docx)** &rarr; PDF, TXT, HTML
- **PDF (.pdf)** &rarr; Word (.docx), TXT, Images (PNG / JPG), HTML
- **Plain Text (.txt)** &rarr; PDF, Word (.docx), HTML
- **Markdown (.md)** &rarr; HTML, PDF, Word (.docx), TXT
- **HTML (.html)** &rarr; PDF, Word (.docx), TXT

### 🖼️ Images
- **JPG / JPEG** &rarr; PNG, WebP, BMP, GIF, TIFF, PDF, ICO
- **PNG** &rarr; JPG, WebP, BMP, GIF, TIFF, PDF, ICO
- **WebP** &rarr; JPG, PNG, BMP, GIF, TIFF, PDF, ICO
- **BMP** &rarr; JPG, PNG, WebP, GIF, TIFF, PDF
- **TIFF** &rarr; JPG, PNG, WebP, BMP, PDF
- **GIF** &rarr; PNG, JPG, WebP
- **ICO** &rarr; PNG, JPG, WebP

### 📊 Spreadsheets & Data
- **Excel (.xlsx)** &rarr; CSV, JSON, HTML, PDF
- **CSV (.csv)** &rarr; Excel (.xlsx), JSON, HTML, PDF
- **JSON (.json)** &rarr; CSV, Excel (.xlsx), HTML

---

## 🛠️ Quick Start

### Option 1: One-Click Windows Launch
Double-click `run.bat` or run:
```bat
run.bat
```

### Option 2: Python Command Line
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the application
python app.py
```

Then open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your web browser.

---

## 🌐 Free 24/7 Online Deployment (Render.com)

To make your converter accessible to anyone on the internet 24/7—even when your personal computer is turned off:

1. Create a free account at **[Render.com](https://render.com/)**.
2. Click **New +** &rarr; **Web Service**.
3. Select your GitHub repository: `AravindSajeev-56/Online-File-Converter`.
4. Configure settings:
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
5. Click **Create Web Service**.

Render will automatically build and host your website with a free HTTPS URL (e.g. `https://online-file-converter-56.onrender.com`) that stays online 24/7!

---

## 🧪 Running Automated Tests

```bash
python test_converters.py
python test_web_api.py
```
