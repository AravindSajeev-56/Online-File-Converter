"""
Central Format Registry for 56 File Converter
"""

import os
from typing import Dict, List, Optional, Tuple

FORMAT_METADATA = {
    # Documents
    "docx": {
        "name": "Microsoft Word",
        "category": "document",
        "description": "Microsoft Word OpenXML Document",
        "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "badge": "DOCX"
    },
    "pdf": {
        "name": "PDF Document",
        "category": "document",
        "description": "Portable Document Format",
        "mime": "application/pdf",
        "badge": "PDF"
    },
    "txt": {
        "name": "Plain Text",
        "category": "document",
        "description": "Unformatted Text File",
        "mime": "text/plain",
        "badge": "TXT"
    },
    "md": {
        "name": "Markdown Document",
        "category": "document",
        "description": "Markdown Formatted Text",
        "mime": "text/markdown",
        "badge": "MD"
    },
    "html": {
        "name": "HTML Document",
        "category": "document",
        "description": "HyperText Markup Language",
        "mime": "text/html",
        "badge": "HTML"
    },
    # Images
    "jpg": {
        "name": "JPEG Image",
        "category": "image",
        "description": "Joint Photographic Experts Group",
        "mime": "image/jpeg",
        "badge": "JPG"
    },
    "jpeg": {
        "name": "JPEG Image",
        "category": "image",
        "description": "Joint Photographic Experts Group",
        "mime": "image/jpeg",
        "badge": "JPEG"
    },
    "png": {
        "name": "PNG Image",
        "category": "image",
        "description": "Portable Network Graphics",
        "mime": "image/png",
        "badge": "PNG"
    },
    "webp": {
        "name": "WebP Image",
        "category": "image",
        "description": "Modern Web Picture Format",
        "mime": "image/webp",
        "badge": "WEBP"
    },
    "bmp": {
        "name": "Bitmap Image",
        "category": "image",
        "description": "Windows Bitmap Graphic",
        "mime": "image/bmp",
        "badge": "BMP"
    },
    "tiff": {
        "name": "TIFF Image",
        "category": "image",
        "description": "Tagged Image File Format",
        "mime": "image/tiff",
        "badge": "TIFF"
    },
    "tif": {
        "name": "TIFF Image",
        "category": "image",
        "description": "Tagged Image File Format",
        "mime": "image/tiff",
        "badge": "TIFF"
    },
    "gif": {
        "name": "GIF Image",
        "category": "image",
        "description": "Graphics Interchange Format",
        "mime": "image/gif",
        "badge": "GIF"
    },
    "ico": {
        "name": "Icon",
        "category": "image",
        "description": "Windows Icon File",
        "mime": "image/x-icon",
        "badge": "ICO"
    },
    # Spreadsheets & Data
    "xlsx": {
        "name": "Excel Spreadsheet",
        "category": "data",
        "description": "Microsoft Excel OpenXML Spreadsheet",
        "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "badge": "XLSX"
    },
    "csv": {
        "name": "CSV Spreadsheet",
        "category": "data",
        "description": "Comma Separated Values",
        "mime": "text/csv",
        "badge": "CSV"
    },
    "json": {
        "name": "JSON Data",
        "category": "data",
        "description": "JavaScript Object Notation",
        "mime": "application/json",
        "badge": "JSON"
    },
    "zip": {
        "name": "ZIP Archive",
        "category": "archive",
        "description": "Compressed ZIP Archive",
        "mime": "application/zip",
        "badge": "ZIP"
    }
}

# Source extension -> Available target formats
CONVERSION_MAP = {
    # Documents
    "docx": ["pdf", "txt", "html"],
    "pdf": ["docx", "txt", "png", "jpg", "html"],
    "txt": ["pdf", "docx", "html"],
    "md": ["html", "pdf", "docx", "txt"],
    "html": ["pdf", "docx", "txt"],

    # Images
    "jpg": ["png", "webp", "bmp", "gif", "tiff", "pdf", "ico"],
    "jpeg": ["png", "webp", "bmp", "gif", "tiff", "pdf", "ico"],
    "png": ["jpg", "webp", "bmp", "gif", "tiff", "pdf", "ico"],
    "webp": ["jpg", "png", "bmp", "gif", "tiff", "pdf", "ico"],
    "bmp": ["jpg", "png", "webp", "gif", "tiff", "pdf"],
    "tiff": ["jpg", "png", "webp", "bmp", "pdf"],
    "tif": ["jpg", "png", "webp", "bmp", "pdf"],
    "gif": ["png", "jpg", "webp"],
    "ico": ["png", "jpg", "webp"],

    # Data
    "xlsx": ["csv", "json", "html", "pdf"],
    "csv": ["xlsx", "json", "html", "pdf"],
    "json": ["csv", "xlsx", "html"]
}

def normalize_ext(ext: str) -> str:
    """Normalize extension to lowercase without leading dot."""
    if not ext:
        return ""
    ext = ext.strip().lower()
    if ext.startswith("."):
        ext = ext[1:]
    return ext

def get_format_info(ext: str) -> Optional[Dict]:
    """Get metadata for a specific extension."""
    ext = normalize_ext(ext)
    return FORMAT_METADATA.get(ext)

def get_supported_targets(source_ext: str) -> List[Dict]:
    """Get list of target formats with metadata for a given source extension."""
    norm = normalize_ext(source_ext)
    target_exts = CONVERSION_MAP.get(norm, [])
    result = []
    for tgt in target_exts:
        info = FORMAT_METADATA.get(tgt, {
            "name": tgt.upper(),
            "category": "other",
            "description": f"{tgt.upper()} file",
            "mime": "application/octet-stream",
            "badge": tgt.upper()
        })
        result.append({
            "extension": tgt,
            "name": info["name"],
            "category": info["category"],
            "description": info["description"],
            "badge": info["badge"]
        })
    return result

def get_all_supported_extensions() -> Dict[str, List[str]]:
    """Get all supported input and output extensions grouped by category."""
    categories = {"document": [], "image": [], "data": []}
    for ext, targets in CONVERSION_MAP.items():
        meta = FORMAT_METADATA.get(ext, {})
        cat = meta.get("category", "other")
        if cat in categories and ext not in categories[cat]:
            categories[cat].append(ext)
    return categories

def convert_file(input_path: str, source_ext: str, target_ext: str, output_dir: str) -> str:
    """
    Route conversion to the appropriate converter module.
    Returns path to the converted output file.
    """
    from .document_converter import convert_document
    from .image_converter import convert_image
    from .data_converter import convert_data

    src = normalize_ext(source_ext)
    tgt = normalize_ext(target_ext)

    if src not in CONVERSION_MAP:
        raise ValueError(f"Unsupported source format: '{src}'")
    if tgt not in CONVERSION_MAP[src]:
        raise ValueError(f"Cannot convert from '{src}' to '{tgt}'")

    src_cat = FORMAT_METADATA.get(src, {}).get("category")
    tgt_cat = FORMAT_METADATA.get(tgt, {}).get("category")

    # Document conversions
    if src in ["docx", "txt", "md", "html"]:
        return convert_document(input_path, src, tgt, output_dir)
    elif src == "pdf":
        if tgt in ["png", "jpg"]:
            return convert_document(input_path, src, tgt, output_dir)
        else:
            return convert_document(input_path, src, tgt, output_dir)

    # Image conversions
    elif src in ["jpg", "jpeg", "png", "webp", "bmp", "tiff", "tif", "gif", "ico"]:
        return convert_image(input_path, src, tgt, output_dir)

    # Data conversions
    elif src in ["xlsx", "csv", "json"]:
        return convert_data(input_path, src, tgt, output_dir)

    raise ValueError(f"No converter implementation for {src} -> {tgt}")
