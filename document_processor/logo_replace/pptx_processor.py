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


# ───────────────────────── helpers ──────────────────────────
def _logo_bytes_for_ext(src_logo: str, ext: str) -> bytes:
    """
    Return bytes of `src_logo` re-encoded in `ext` (png, jpg, gif …).
    Keeps transparency when the format supports it.
    """
    img = Image.open(src_logo)
    if ext.lower() in {"jpg", "jpeg", "bmp"}:
        img = img.convert("RGB")          # alpha not supported
    else:                                 # png, gif, tif …
        img = img.convert("RGBA")         # keep/add alpha
    buf = io.BytesIO()
    img.save(buf, format="PNG" if ext.lower() == "png" else ext.upper())
    return buf.getvalue()


# ───────────────────────── main function ────────────────────
def replace_logo_in_pptx(
    pptx_path: str,
    new_logo_path: str,
    old_logo_path: str,
    output_path: str | None = None,
    similarity_threshold: float = 0.93,
) -> bool:
    """
    Replace occurrences of `old_logo_path` with `new_logo_path` inside a PPTX.
    Supports RGB, RGBA, grayscale, and monochrome logos.  Transparency is
    preserved whenever the original embedded file is PNG/GIF/TIF.
    """
    if output_path is None:
        output_path = Path(pptx_path).with_stem(
            f"{Path(pptx_path).stem}_updated"
        )

    # Load CLIP once
    model, preprocess = get_clip_model()
    try:
        old_emb = get_image_embedding(old_logo_path, model, preprocess)
    except Exception as e:
        print(f"Failed to embed old logo: {e}")
        return False

    # Temporary working directory
    tmp_dir = tempfile.mkdtemp(prefix="pptx_")
    replaced_any = False
    logo_cache: dict[str, bytes] = {}  # ext → bytes

    try:
        # ── unzip the PPTX ───────────────────────────────────────────
        with zipfile.ZipFile(pptx_path) as zf:
            zf.extractall(tmp_dir)

        media_dir = Path(tmp_dir) / "ppt" / "media"
        if not media_dir.exists():
            print("No embedded images found.")
            return False

        # ── iterate over images in /ppt/media ───────────────────────
        for img_path in media_dir.iterdir():
            try:
                image = Image.open(img_path)
                # ① similarity test
                similar, sim = is_similar_to_target(
                    image, old_emb, model, preprocess, similarity_threshold
                )
                if not similar:
                    continue

                print(f"{img_path.name}: matched (sim={sim:.3f})")

                ext = img_path.suffix.lstrip(".").lower()

                # ② build replacement bytes once per ext
                if ext not in logo_cache:
                    logo_cache[ext] = _logo_bytes_for_ext(new_logo_path, ext)

                # ③ overwrite the file inside /media
                img_path.write_bytes(logo_cache[ext])
                replaced_any = True

            except Exception as e:
                print(f"Warning: skipped {img_path.name}: {e}")

        if not replaced_any:
            print("No matching logos found for replacement.")
            return False

        # ── re-zip into the final PPTX ──────────────────────────────
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in Path(tmp_dir).rglob("*"):
                arcname = f.relative_to(tmp_dir)
                zf.write(f, arcname)

        print(f"Successfully replaced logo(s) → {output_path}")
        return True

    except Exception as e:
        print(f"Error processing PPTX: {e}")
        return False

    finally:
        # Always clean up temp directory
        try:
            shutil.rmtree(tmp_dir)
        except Exception as e:
            print(f"Note: could not remove temp dir {tmp_dir}: {e}")
