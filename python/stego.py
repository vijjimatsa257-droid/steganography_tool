# ---------------------------------------------------
# MODULE 1: stego.py  (Python)  -- FAST VERSION
# Purpose: The actual steganography logic.
#
# HOW IT WORKS (simple explanation):
# Every pixel in an image has a Red, Green, Blue value
# from 0-255. Changing the LAST bit of that number
# (e.g. 200 -> 201) changes the color so slightly that
# the human eye cannot see any difference.
#
# So we hide our secret message by writing it, letter by
# letter, bit by bit, into those "last bits" of the pixels.
# To read it back, we just look at those same last bits
# again, in the same order.
#
# WHY numpy: reading pixels one at a time with a Python
# loop (img.getpixel()) is very slow on real photos with
# millions of pixels. numpy processes the whole image as
# one block of numbers at once, which is dramatically
# faster - this is the fix for the "taking too long" issue.
# ---------------------------------------------------

import numpy as np
from PIL import Image

DELIMITER = "#####"   # marks the end of the hidden message

# How many characters worth of bits to check at a time while
# searching for the delimiter. Keeps decoding fast even on huge
# images, since we usually find the message in the very first chunk.
CHUNK_CHARS = 4000
CHUNK_BITS = CHUNK_CHARS * 8


def _text_to_bits(text):
    return ''.join(format(ord(char), '08b') for char in text)


def _bits_to_text(bits):
    chars = []
    for i in range(0, len(bits) - 7, 8):
        chars.append(chr(int(bits[i:i + 8], 2)))
    return ''.join(chars)


def encode_image(input_path, message, output_path):
    """
    Hides `message` inside the image at input_path,
    and saves the result as a NEW image at output_path.
    """
    img = Image.open(input_path).convert("RGB")
    arr = np.array(img)
    flat = arr.reshape(-1)  # treat all R,G,B values as one long list of numbers

    message_with_marker = message + DELIMITER
    binary_message = _text_to_bits(message_with_marker)
    data_len = len(binary_message)

    if data_len > flat.size:
        raise ValueError("Message is too long to hide in this image. Use a bigger image or shorter message.")

    bit_array = np.array([int(b) for b in binary_message], dtype=np.uint8)

    # Clear the last bit of each needed number, then set it to our message bit.
    # This is the vectorized (fast) version of what the old pixel-by-pixel loop did.
    flat[:data_len] = (flat[:data_len] & np.uint8(0xFE)) | bit_array

    new_arr = flat.reshape(arr.shape)
    Image.fromarray(new_arr, "RGB").save(output_path, "PNG")


def decode_image(image_path):
    """
    Reads the hidden message back out of an image that
    was created by encode_image(). Reads the image in
    small chunks and stops as soon as the message is
    found, instead of processing the whole photo.
    """
    img = Image.open(image_path).convert("RGB")
    arr = np.array(img)
    flat = arr.reshape(-1)
    total_bits = flat.size

    decoded_so_far = ""
    start = 0

    while start < total_bits:
        end = min(start + CHUNK_BITS, total_bits)
        chunk_bits = (flat[start:end] & 1)
        chunk_str = ''.join(map(str, chunk_bits.tolist()))
        decoded_so_far += _bits_to_text(chunk_str)

        if DELIMITER in decoded_so_far:
            return decoded_so_far[:decoded_so_far.index(DELIMITER)]

        start = end

    raise ValueError("No hidden message found in this image.")
