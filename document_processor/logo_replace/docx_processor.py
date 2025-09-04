import zipfile
import os
import io
import shutil
import tempfile
from pathlib import Path
from PIL import Image

from document_processor.logo_replace.utils.clip_utils import (
    get_clip_model, get_image_embedding, is_similar_to_target
)

# ───────────────────────── helper ──────────────────────────
def _encode_logo_for_ext(src_logo: str, ext: str) -> bytes:
    """
    Re-encode *src_logo* to the requested extension.
    • JPG / JPEG / BMP  →  RGB (no alpha)
    • PNG / GIF / TIF   →  RGBA (alpha kept / added)
    """
    img = Image.open(src_logo)
    if ext.lower() in {"jpg", "jpeg", "bmp"}:
        img = img.convert("RGB")
        fmt = "JPEG" if ext.lower() != "bmp" else "BMP"
    else:
        img = img.convert("RGBA")
        fmt = "PNG" if ext.lower() == "png" else ext.upper()

    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


# ───────────────────────── main ────────────────────────────
def replace_logo_in_docx(
    docx_path: str,
    new_logo_path: str,
    old_logo_path: str,
    output_path: str | None = None,
    similarity_threshold: float = 0.93,
) -> bool:
    """
    Replace occurrences of *old_logo_path* with *new_logo_path* inside a DOCX.
    Transpar­ency is preserved when the original embedded file is PNG/GIF/TIF.
    """
    docx_path = Path(docx_path)
    if output_path is None:
        output_path = docx_path.with_stem(f"{docx_path.stem}_updated")

    # CLIP setup
    model, preprocess = get_clip_model()
    old_emb = get_image_embedding(old_logo_path, model, preprocess)

    # working dir
    tmp_dir = Path(tempfile.mkdtemp(prefix="docx_"))
    shutil.rmtree(tmp_dir, ignore_errors=True)
    tmp_dir.mkdir()

    logo_cache: dict[str, bytes] = {}     # ext → encoded bytes
    replaced_any = False

    try:
        # ── unzip ────────────────────────────────────────────────
        with zipfile.ZipFile(docx_path) as zf:
            zf.extractall(tmp_dir)

        media_dir = tmp_dir / "word" / "media"
        if not media_dir.exists():
            print("No embedded images found.")
            return False

        # ── iterate over media files ─────────────────────────────
        for img_path in media_dir.iterdir():
            try:
                image = Image.open(img_path)
                similar, sim = is_similar_to_target(
                    image, old_emb, model, preprocess, similarity_threshold
                )
                if not similar:
                    continue

                ext = img_path.suffix.lstrip(".").lower()
                if ext not in logo_cache:
                    logo_cache[ext] = _encode_logo_for_ext(new_logo_path, ext)

                img_path.write_bytes(logo_cache[ext])
                replaced_any = True
                print(f"{img_path.name}: replaced (sim={sim:.3f})")

            except Exception as e:
                print(f"Warning: {img_path.name} skipped – {e}")

        if not replaced_any:
            print("No matching logos found.")
            return False

        # ── re-zip ──────────────────────────────────────────────
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in tmp_dir.rglob("*"):
                zf.write(f, f.relative_to(tmp_dir))

        print(f"Successfully replaced logo(s) → {output_path}")
        return True

    except Exception as e:
        print(f"Error processing DOCX: {e}")
        return False

    finally:
        try:
            shutil.rmtree(tmp_dir)
        except Exception as e:
            print(f"Note: could not remove temp dir {tmp_dir}: {e}")
