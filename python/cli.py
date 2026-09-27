# ---------------------------------------------------
# MODULE 2: cli.py  (Python)
# Purpose: This is the "bridge" file. Node.js cannot
# call Python functions directly, but it CAN run a
# command-line program and read what it prints.
#
# So this file takes instructions from the command line,
# calls the real logic in stego.py, and prints the
# result as JSON so Node can easily read it.
#
# Usage from the command line:
#   python3 cli.py encode input.png "secret text" output.png
#   python3 cli.py decode output.png
# ---------------------------------------------------

import sys
import json
from stego import encode_image, decode_image


def main():
    try:
        command = sys.argv[1]

        if command == "encode":
            input_path = sys.argv[2]
            message = sys.argv[3]
            output_path = sys.argv[4]
            encode_image(input_path, message, output_path)
            print(json.dumps({"status": "success", "output": output_path}))

        elif command == "decode":
            input_path = sys.argv[2]
            message = decode_image(input_path)
            print(json.dumps({"status": "success", "message": message}))

        else:
            print(json.dumps({"status": "error", "error": f"Unknown command: {command}"}))

    except Exception as e:
        # Always print valid JSON, even on failure, so Node can parse it safely
        print(json.dumps({"status": "error", "error": str(e)}))


if __name__ == "__main__":
    main()
