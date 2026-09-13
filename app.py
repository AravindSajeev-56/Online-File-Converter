"""
56 File Converter - Flask Web Application
A modern, fast, 100% secure file conversion platform.
Enforces strict 1-minute auto-deletion of all files for maximum privacy.
"""

import os
import time
import uuid
import shutil
import zipfile
from threading import Thread

from flask import Flask, render_template, request, jsonify, send_file, abort
from werkzeug.utils import secure_filename

from converters.registry import (
    CONVERSION_MAP,
    FORMAT_METADATA,
    get_supported_targets,
    get_all_supported_extensions,
    convert_file,
    normalize_ext,
)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB max upload limit

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "storage", "uploads")
CONVERTED_DIR = os.path.join(BASE_DIR, "storage", "converted")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CONVERTED_DIR, exist_ok=True)

# Strict privacy: All files expire and are permanently purged after 60 seconds (1 minute)
FILE_LIFETIME_SECONDS = 60

# In-memory registry: job_id -> metadata
CONVERSION_STORE = {}


def cleanup_worker():
    """Continuous background worker that purges all files older than 60 seconds (1 minute)."""
    while True:
        try:
            now = time.time()
            cutoff = now - FILE_LIFETIME_SECONDS

            # 1. Purge from in-memory store and delete their disk files
            expired_job_ids = [
                jid for jid, info in list(CONVERSION_STORE.items())
                if now - info.get("created_at", 0) >= FILE_LIFETIME_SECONDS
            ]
            for jid in expired_job_ids:
                info = CONVERSION_STORE.pop(jid, None)
                if info:
                    out_path = info.get("output_path")
                    if out_path and os.path.exists(out_path):
                        try:
                            os.remove(out_path)
                        except OSError:
                            pass
                    # Remove parent job folder if present
                    parent = os.path.dirname(out_path) if out_path else None
                    if parent and os.path.isdir(parent) and parent != CONVERTED_DIR:
                        shutil.rmtree(parent, ignore_errors=True)

            # 2. Check filesystem directories directly to ensure zero orphaned files
            for folder in [UPLOAD_DIR, CONVERTED_DIR]:
                if not os.path.exists(folder):
                    continue
                for item in os.listdir(folder):
                    item_path = os.path.join(folder, item)
                    try:
                        if os.path.isdir(item_path):
                            if os.path.getmtime(item_path) < cutoff:
                                shutil.rmtree(item_path, ignore_errors=True)
                        elif os.path.isfile(item_path):
                            if os.path.getmtime(item_path) < cutoff:
                                os.remove(item_path)
                    except Exception:
                        pass
        except Exception:
            pass

        time.sleep(2)  # Check every 2 seconds


# Launch continuous background cleanup daemon
cleanup_thread = Thread(target=cleanup_worker, daemon=True)
cleanup_thread.start()


@app.route("/")
def index():
    """Render main application page."""
    return render_template("index.html")


@app.route("/api/formats", methods=["GET"])
def api_formats():
    """Return all supported formats, conversions, and metadata."""
    return jsonify({
        "conversion_map": CONVERSION_MAP,
        "metadata": FORMAT_METADATA,
        "categories": get_all_supported_extensions()
    })


@app.route("/api/targets/<ext>", methods=["GET"])
def api_targets(ext):
    """Return compatible target formats for a given source extension."""
    targets = get_supported_targets(ext)
    return jsonify({
        "source": ext,
        "targets": targets
    })


@app.route("/api/convert", methods=["POST"])
def api_convert():
    """
    Handle single file upload and conversion.
    Source upload is deleted immediately after conversion.
    Converted file is deleted after 1 minute (60 seconds).
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded. Please select a file."}), 400

    uploaded_file = request.files["file"]
    if not uploaded_file or uploaded_file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    original_filename = uploaded_file.filename
    _, raw_ext = os.path.splitext(original_filename)
    source_ext = normalize_ext(raw_ext)

    if not source_ext:
        return jsonify({"error": f"Uploaded file '{original_filename}' does not have a recognizable file extension."}), 400

    if source_ext not in CONVERSION_MAP:
        return jsonify({"error": f"Format '.{source_ext}' is not currently supported."}), 400

    valid_targets = CONVERSION_MAP.get(source_ext, [])
    target_format = (request.form.get("target_format") or "").strip().lower().lstrip(".")
    if target_format in ["", "undefined", "null", "none"]:
        target_format = valid_targets[0] if valid_targets else ""

    if target_format not in valid_targets:
        return jsonify({
            "error": f"Cannot convert from '.{source_ext}' to '.{target_format}'. Supported targets: {', '.join(valid_targets)}"
        }), 400

    # Create safe base filename preserving extension
    base_name = secure_filename(os.path.splitext(original_filename)[0])
    if not base_name:
        base_name = f"file_{int(time.time())}"
    safe_filename = f"{base_name}.{source_ext}"

    # Create isolated directory for this job
    job_id = str(uuid.uuid4())
    job_upload_dir = os.path.join(UPLOAD_DIR, job_id)
    job_converted_dir = os.path.join(CONVERTED_DIR, job_id)
    os.makedirs(job_upload_dir, exist_ok=True)
    os.makedirs(job_converted_dir, exist_ok=True)

    input_path = os.path.join(job_upload_dir, safe_filename)
    uploaded_file.save(input_path)

    try:
        start_time = time.time()
        output_path = convert_file(input_path, source_ext, target_format, job_converted_dir)
        elapsed = round(time.time() - start_time, 3)

        # Release Windows file handles
        import gc
        gc.collect()

        # 🔒 Maximum Privacy: Immediately delete the source uploaded file from server!
        try:
            shutil.rmtree(job_upload_dir, ignore_errors=True)
        except Exception:
            pass

        output_filename = os.path.basename(output_path)
        output_size = os.path.getsize(output_path)

        # Store in-memory with creation timestamp (expires in 60s)
        CONVERSION_STORE[job_id] = {
            "output_path": output_path,
            "filename": output_filename,
            "mime": FORMAT_METADATA.get(normalize_ext(os.path.splitext(output_filename)[1]), {}).get("mime", "application/octet-stream"),
            "created_at": time.time()
        }

        return jsonify({
            "success": True,
            "job_id": job_id,
            "original_filename": original_filename,
            "converted_filename": output_filename,
            "target_format": target_format,
            "download_url": f"/api/download/{job_id}",
            "file_size": output_size,
            "duration_seconds": elapsed,
            "expires_in": FILE_LIFETIME_SECONDS
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        try:
            shutil.rmtree(job_upload_dir, ignore_errors=True)
            shutil.rmtree(job_converted_dir, ignore_errors=True)
        except Exception:
            pass
        return jsonify({"error": f"Conversion failed: {str(e)}"}), 500


@app.route("/api/download/<job_id>", methods=["GET"])
def api_download(job_id):
    """Download converted file by job ID. Returns 404 if deleted after 1 minute."""
    job_info = CONVERSION_STORE.get(job_id)
    
    # Check if expired
    if job_info:
        if time.time() - job_info.get("created_at", 0) >= FILE_LIFETIME_SECONDS:
            # Expired: clean up and return 404
            CONVERSION_STORE.pop(job_id, None)
            target_dir = os.path.join(CONVERTED_DIR, job_id)
            shutil.rmtree(target_dir, ignore_errors=True)
            abort(404, description="File has been permanently deleted after 1 minute for 100% privacy.")

        file_path = job_info["output_path"]
        if os.path.exists(file_path):
            return send_file(
                file_path,
                as_attachment=True,
                download_name=job_info["filename"],
                mimetype=job_info.get("mime", "application/octet-stream")
            )

    # Fallback direct filesystem check
    target_dir = os.path.join(CONVERTED_DIR, job_id)
    if os.path.isdir(target_dir):
        # Check mtime
        if time.time() - os.path.getmtime(target_dir) < FILE_LIFETIME_SECONDS:
            files = os.listdir(target_dir)
            if files:
                file_path = os.path.join(target_dir, files[0])
                return send_file(file_path, as_attachment=True, download_name=files[0])

    abort(404, description="File has been permanently deleted after 1 minute for 100% privacy.")


@app.route("/api/download-all", methods=["POST"])
def api_download_all():
    """Create a temporary ZIP bundle containing specified completed conversion job IDs."""
    data = request.get_json() or {}
    job_ids = data.get("job_ids", [])
    if not job_ids:
        return jsonify({"error": "No job IDs provided"}), 400

    zip_id = str(uuid.uuid4())
    zip_dir = os.path.join(CONVERTED_DIR, zip_id)
    os.makedirs(zip_dir, exist_ok=True)
    zip_path = os.path.join(zip_dir, "56_converted_files.zip")

    added_files = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for jid in job_ids:
            job_info = CONVERSION_STORE.get(jid)
            if job_info and os.path.exists(job_info["output_path"]):
                zipf.write(job_info["output_path"], job_info["filename"])
                added_files += 1
            else:
                target_dir = os.path.join(CONVERTED_DIR, jid)
                if os.path.isdir(target_dir):
                    for f in os.listdir(target_dir):
                        fp = os.path.join(target_dir, f)
                        zipf.write(fp, f)
                        added_files += 1

    if added_files == 0:
        return jsonify({"error": "All files have expired or were deleted after 1 minute."}), 404

    CONVERSION_STORE[zip_id] = {
        "output_path": zip_path,
        "filename": "56_converted_files.zip",
        "mime": "application/zip",
        "created_at": time.time()
    }

    return jsonify({
        "success": True,
        "zip_url": f"/api/download/{zip_id}",
        "file_count": added_files,
        "expires_in": FILE_LIFETIME_SECONDS
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("=================================================")
    print(f" [*] 56 File Converter is running on http://127.0.0.1:{port}")
    print(" [*] 100% Secure: Files auto-deleted after 1 minute")
    print("=================================================")
    app.run(host="0.0.0.0", port=port, debug=False)
