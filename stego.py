# ---------------------------------------------------
# MODULE 1: stego.py  (Python)
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
# ---------------------------------------------------

from PIL import Image

DELIMITER = "#####"   # marks the end of the hidden message


def encode_image(input_path, message, output_path):
    """
    Hides `message` inside the image at input_path,
    and saves the result as a NEW image at output_path.
    """
    img = Image.open(input_path).convert("RGB")
    encoded = img.copy()
    width, height = img.size

    message_with_marker = message + DELIMITER
    # Turn the message into a long string of 0s and 1s
    binary_message = ''.join(format(ord(char), '08b') for char in message_with_marker)

    data_len = len(binary_message)
    data_index = 0

    if data_len > width * height * 3:
        raise ValueError("Message is too long to hide in this image. Use a bigger image or shorter message.")

    for y in range(height):
        for x in range(width):
            if data_index >= data_len:
                break

            r, g, b = img.getpixel((x, y))

            if data_index < data_len:
                r = (r & ~1) | int(binary_message[data_index])
                data_index += 1
            if data_index < data_len:
                g = (g & ~1) | int(binary_message[data_index])
                data_index += 1
            if data_index < data_len:
                b = (b & ~1) | int(binary_message[data_index])
                data_index += 1

            encoded.putpixel((x, y), (r, g, b))

        if data_index >= data_len:
            break

    # IMPORTANT: must save as PNG. JPG compresses the image
    # and would destroy the hidden bits.
    encoded.save(output_path, "PNG")


def decode_image(image_path):
    """
    Reads the hidden message back out of an image that
    was created by encode_image().
    """
    img = Image.open(image_path).convert("RGB")
    width, height = img.size

    binary_data = []
    for y in range(height):
        for x in range(width):
            r, g, b = img.getpixel((x, y))
            binary_data.append(str(r & 1))
            binary_data.append(str(g & 1))
            binary_data.append(str(b & 1))

    binary_data = ''.join(binary_data)
    all_bytes = [binary_data[i:i + 8] for i in range(0, len(binary_data), 8)]

    decoded_chars = []
    message_so_far = ""
    for byte in all_bytes:
        if len(byte) < 8:
            break
        char = chr(int(byte, 2))
        decoded_chars.append(char)
        message_so_far = ''.join(decoded_chars)
        if message_so_far.endswith(DELIMITER):
            return message_so_far[:-len(DELIMITER)]

    # If we never found the delimiter, there was no hidden message
    raise ValueError("No hidden message found in this image.")
