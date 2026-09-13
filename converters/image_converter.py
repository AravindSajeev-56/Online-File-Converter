"""
Image Converter Module for 56 File Converter
Handles JPG, PNG, WEBP, BMP, TIFF, GIF, ICO, and Image-to-PDF conversions via Pillow.
"""

import os
from PIL import Image, ImageOps

PIL_FORMAT_MAP = {
    "jpg": "JPEG",
    "jpeg": "JPEG",
    "png": "PNG",
    "webp": "WEBP",
    "bmp": "BMP",
    "tiff": "TIFF",
    "tif": "TIFF",
    "gif": "GIF",
    "ico": "ICO",
    "pdf": "PDF"
}


def convert_image(input_path: str, source_ext: str, target_ext: str, output_dir: str) -> str:
    """Convert an image from source format to target format."""
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    out_file = os.path.join(output_dir, f"{base_name}.{target_ext}")

    pil_format = PIL_FORMAT_MAP.get(target_ext.lower())
    if not pil_format:
        raise ValueError(f"Unsupported image target format: '{target_ext}'")

    with Image.open(input_path) as img:
        # Correct image orientation based on EXIF
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        # Convert non-standard color spaces (CMYK, YCbCr) to RGB
        if img.mode in ("CMYK", "YCbCr"):
            img = img.convert("RGB")
        if target_ext in ["jpg", "jpeg", "bmp", "pdf"]:
            if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                # Create a solid white background and paste alpha image on top
                bg = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode != "RGBA":
                    img = img.convert("RGBA")
                bg.paste(img, mask=img.split()[3])
                img = bg
            elif img.mode != "RGB":
                img = img.convert("RGB")

        # Target is ICO (support multiple standard icon sizes)
        if target_ext == "ico":
            if img.mode not in ("RGBA", "RGB"):
                img = img.convert("RGBA")
            icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
            # Filter sizes that are not larger than original image (or keep at least 16 and 32)
            valid_sizes = [s for s in icon_sizes if s[0] <= max(img.size)]
            if not valid_sizes:
                valid_sizes = [(32, 32)]
            img.save(out_file, format="ICO", sizes=valid_sizes)
            return out_file

        # Target is GIF
        if target_ext == "gif":
            if img.mode not in ("P", "L"):
                img = img.convert("P", palette=Image.Palette.ADAPTIVE)
            img.save(out_file, format="GIF")
            return out_file

        # Target is WEBP or JPEG
        if target_ext in ["jpg", "jpeg"]:
            img.save(out_file, format="JPEG", quality=95, optimize=True)
            return out_file

        if target_ext == "webp":
            img.save(out_file, format="WEBP", quality=95, method=6)
            return out_file

        if target_ext == "png":
            img.save(out_file, format="PNG", optimize=True)
            return out_file

        if target_ext in ["tiff", "tif"]:
            img.save(out_file, format="TIFF", compression="tiff_deflate")
            return out_file

        if target_ext == "pdf":
            img.save(out_file, format="PDF", resolution=100.0)
            return out_file

        # Fallback default save
        img.save(out_file, format=pil_format)
        return out_file
