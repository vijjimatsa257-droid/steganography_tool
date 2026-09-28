# ---------------------------------------------------
# MODULE 1: stego.py  (Python)  -- UNIVERSAL VERSION
#
# HIDE : works with any image type (PNG, JPG, BMP...),
#        any language (English, Telugu, emoji...).
#        Output is always PNG (lossless).
#
# REVEAL: tries, in this order:
#   1. This tool's own format
#   2. Common LSB layouts used by other tools
#      (RGB/BGR/single channel, MSB/LSB bit order,
#       "5:hello" style, length-prefixed, plain text)
#   3. Text added at the end of the image file
#   4. Metadata (PNG text chunks, JPG comment, EXIF)
#
# NOTE: no code can read EVERY image, because each tool
# hides text in its own way. Password-protected/encrypted
# data and JPG-DCT tools (steghide, outguess) are not covered.
# ---------------------------------------------------

import re
import numpy as np
import itertools
from PIL import Image

DELIMITER = b"#####"          # end-of-message marker for THIS tool
SCAN_VALUES = 8 * 65536       # how much of the image generic scans read (first 64 KB of hidden data)
MIN_PLAIN_RUN = 10            # plain-text scans need at least this many readable characters


# ================= HIDE =================

def encode_image(input_path, message, output_path):
    img = Image.open(input_path).convert("RGB")
    flat = np.array(img).reshape(-1)

    payload = message.encode("utf-8") + DELIMITER
    bits = np.unpackbits(np.frombuffer(payload, dtype=np.uint8))

    if bits.size > flat.size:
        raise ValueError("Message is too long to hide in this image. Use a bigger image or shorter message.")

    flat[:bits.size] = (flat[:bits.size] & 0xFE) | bits
    Image.fromarray(flat.reshape(np.array(img).shape)).save(output_path, "PNG")


# ================= helpers =================

def _printable_text(data, min_len=1):
    """Strict check: bytes must be valid UTF-8 and readable. Returns str or None."""
    if len(data) < min_len:
        return None
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    if all(ch.isprintable() or ch in "\n\r\t" for ch in text):
        return text
    return None


def _leading_ascii_run(data, min_len):
    i = 0
    while i < len(data) and (32 <= data[i] < 127 or data[i] in (9, 10, 13)):
        i += 1
    return data[:i].decode("ascii") if i >= min_len else None


def _bytes_from_bits(values, bitorder):
    bits = (values[:SCAN_VALUES] & 1).astype(np.uint8)
    return np.packbits(bits, bitorder=bitorder).tobytes()


def _found(method, text):
    return f"[Found via: {method}] {text}"


# ================= method 1: this tool's format =================

def _decode_own_format(img):
    flat = np.array(img.convert("RGB")).reshape(-1)
    data = np.packbits((flat & 1).astype(np.uint8)).tobytes()
    idx = data.find(DELIMITER)
    if idx > 0:
        return data[:idx].decode("utf-8", errors="replace")
    return None


# ================= method 2: common LSB layouts =================

def _lsb_variants(img):
    rgb = np.array(img.convert("RGB"))
    variants = [
        ("RGB pixels, row by row", rgb.reshape(-1)),
        ("BGR pixel order", rgb[..., ::-1].reshape(-1)),
        ("Red channel only", rgb[..., 0].reshape(-1)),
        ("Green channel only", rgb[..., 1].reshape(-1)),
        ("Blue channel only", rgb[..., 2].reshape(-1)),
        ("RGB pixels, column by column", rgb.transpose(1, 0, 2).reshape(-1)),
    ]
    if img.mode == "RGBA":
        variants.insert(1, ("RGBA pixels (with alpha)", np.array(img).reshape(-1)))
    if img.mode in ("L", "P"):
        variants.insert(0, ("Grayscale/palette values", np.array(img).reshape(-1)))
    return variants


def _decode_generic_lsb(img):
    for name, values in _lsb_variants(img):
        for bitorder, order_name in (("big", "MSB-first"), ("little", "LSB-first")):
            data = _bytes_from_bits(values, bitorder)
            label = f"LSB scan - {name}, {order_name}"

            # "5:hello" style (length, colon, text)
            m = re.match(rb"(\d{1,6}):", data)
            if m:
                n = int(m.group(1))
                body = data[m.end():m.end() + n]
                if n >= 2 and len(body) == n:
                    text = _printable_text(body)
                    if text:
                        return _found(label + ' ("length:text" style)', text)

            # 4-byte length prefix, then text
            for endian in ("big", "little"):
                if len(data) >= 8:
                    n = int.from_bytes(data[:4], endian)
                    if 2 <= n <= len(data) - 4:
                        text = _printable_text(data[4:4 + n])
                        if text:
                            return _found(label + " (length-prefixed)", text)

            # plain readable text at the start
            run = _leading_ascii_run(data, MIN_PLAIN_RUN)
            if run:
                return _found(label + " (extra characters may appear at the end)", run)
    return None


# ================= method 3: text after end of file =================

def _decode_trailing(path):
    with open(path, "rb") as f:
        raw = f.read()
    tail = b""
    if raw.startswith(b"\x89PNG"):
        pos = 8                                   # skip the PNG signature, then walk chunk by chunk
        while pos + 8 <= len(raw):
            length = int.from_bytes(raw[pos:pos + 4], "big")
            if raw[pos + 4:pos + 8] == b"IEND":
                tail = raw[pos + 12 + length:]     # everything after the IEND chunk
                break
            pos += 12 + length
    elif raw.startswith(b"\xff\xd8"):
        i = raw.rfind(b"\xff\xd9")
        if i != -1:
            tail = raw[i + 2:]
    if not tail:
        return None
    if tail.startswith(b"PK\x03\x04"):
        return _found("data added after the image",
                      f"A hidden ZIP file ({len(tail)} bytes) is attached. Copy the image, rename it to .zip and open it.")
    text = _printable_text(tail.strip(b"\x00\r\n \t"), min_len=3)
    if text:
        return _found("text added after the end of the image file", text)
    return None


# ================= method 4: metadata =================

_SKIP_KEYS = {"dpi", "gamma", "icc_profile", "exif", "transparency", "srgb", "chromaticity",
              "interlace", "progressive", "progression", "jfif", "jfif_version", "jfif_unit",
              "jfif_density", "adobe", "adobe_transform", "aspect", "duration", "loop",
              "background", "version", "compression", "photoshop", "xmp", "software",
              "creation time", "raw profile type exif", "xml:com.adobe.xmp"}


def _decode_metadata(img):
    for key, value in img.info.items():
        if str(key).lower() in _SKIP_KEYS:
            continue
        if isinstance(value, bytes):
            text = _printable_text(value.strip(b"\x00"), min_len=3)
        elif isinstance(value, str) and len(value) >= 3:
            text = value if value.isprintable() or "\n" in value else None
        else:
            text = None
        if text and len(text) <= 2000:
            return _found(f"image metadata field '{key}'", text)

    try:
        exif = img.getexif()
        candidates = [("ImageDescription", exif.get(0x010E))]
        candidates.append(("UserComment", exif.get_ifd(0x8769).get(0x9286)))
        for name, value in candidates:
            if isinstance(value, bytes):
                for prefix in (b"ASCII\x00\x00\x00", b"UNICODE\x00", b"\x00" * 8):
                    if value.startswith(prefix):
                        value = value[len(prefix):]
                        break
                value = _printable_text(value.strip(b"\x00"), min_len=3)
            if isinstance(value, str) and len(value.strip()) >= 3:
                return _found(f"EXIF field '{name}'", value.strip())
    except Exception:
        pass
    return None

def _decode_bruteforce(img, max_bytes=2048, min_run=8):
    """Try many LSB layouts; return text if a long printable run is found."""
    arr = np.array(img.convert("RGB"))
    ch_combos = [c for n in (1, 2, 3)
                 for c in itertools.permutations([0, 1, 2], n)]
    for transpose in (False, True):
        a = arr.transpose(1, 0, 2) if transpose else arr
        for ch in ch_combos:
            flat = a[..., list(ch)].reshape(-1)[: max_bytes * 8]
            for plane in (0, 1, 2):
                bits = (flat >> plane) & 1
                for order in ("big", "little"):
                    data = np.packbits(bits, bitorder=order).tobytes()
                    end = 0
                    while end < len(data) and (32 <= data[end] < 127
                                               or data[end] in (9, 10, 13)):
                        end += 1
                    if end >= min_run:
                        text = data[:end].decode("ascii", errors="ignore")
                        label = ("bruteforce: channels=%s plane=%d order=%s%s"
                                 % ("".join("RGB"[c] for c in ch), plane,
                                    order, " column-wise" if transpose else ""))
                        return _found(label, text)
    return None  


# ================= REVEAL =================

def decode_image(image_path):
    img = Image.open(image_path)
    img.load()

    for step in (
        lambda: _decode_own_format(img),
        lambda: _decode_generic_lsb(img),
        lambda: _decode_trailing(image_path),
        lambda: _decode_metadata(img),
        lambda: _decode_bruteforce(img),
    ):
        result = step()
        if result:
            return result

    raise ValueError(
        "No hidden message found. Checked: this tool's format, common LSB layouts, "
        "text added after the image, and metadata. The image may have no hidden text, "
        "may have been compressed/edited (JPG, WhatsApp, screenshot), or may use a password "
        "or a different hiding method."
    )