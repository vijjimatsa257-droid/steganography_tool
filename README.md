# Steganography Tool (Hide & Reveal Secret Messages in Images)

A security mini-project that hides a secret text message inside an
image using LSB (Least Significant Bit) steganography, and can reveal
it back later. To anyone just looking at the image, nothing looks
different.

## How it works (in plain words)

Every pixel in an image is made of a Red, Green and Blue number
(0-255). Changing the very last bit of that number (for example 200
becomes 201) is far too small a color change for the human eye to
notice. So we hide our message letter-by-letter, bit-by-bit, in those
"last bits". To read the message back, we just look at the same bits
again, in the same order.

## Architecture (how the pieces connect)

```
Browser (HTML/CSS/JS)  --uploads image+message-->  Express (server.js)
                                                          |
                                                   runs python/cli.py
                                                          |
                                                     python/stego.py
                                                   (hides/reveals text)
                                                          |
                                                  <--sends back result--
```

- **Python** (`stego.py` + `cli.py`) does the actual hiding/revealing.
- **Node/Express** (`server.js`) receives the uploaded image from the
  browser, runs the Python script, and sends the result back.
- **HTML/CSS/JS** is the page you use to upload images and type
  messages.

## Modules

| File | Layer | Role |
|---|---|---|
| `python/stego.py` | Python | Core logic: hide message in pixels / read it back |
| `python/cli.py` | Python | Bridge — lets Node run the Python logic as a command |
| `server/server.js` | Node/Express | Receives uploads, calls Python, serves the frontend |
| `server/public/index.html` | Frontend | Page structure (Hide / Reveal tabs) |
| `server/public/style.css` | Frontend | Styling |
| `server/public/script.js` | Frontend | Sends image+message to Express, shows the result |

## 1. Set up Python

```bash
cd python
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

You don't run Python by itself for this project — Express will call
it automatically. This step just installs Pillow (the image library).

## 2. Set up and run Express

```bash
cd server
npm install
npm start
```

You'll see: `Steganography tool running at http://localhost:3000`

## 3. Use it

Open **http://localhost:3000**.

- **Hide tab**: choose an image, type a secret message, click "Hide
  message in image", then download the new image it gives you.
- **Reveal tab**: upload that downloaded image, click "Reveal hidden
  message", and it will show you the secret text.

Important: always download and share the image as **PNG**. JPG
compresses images and would destroy the hidden bits.

## 4. Publish on GitHub

```bash
git init
git add .
git commit -m "Steganography tool - security mini project"
git remote add origin https://github.com/<your-username>/steganography-tool.git
git branch -M main
git push -u origin main
```

Add a `.gitignore` with `node_modules/`, `venv/`, `__pycache__/`, and
`server/uploads/*` (but keep `server/uploads/.gitkeep`) before your
first commit, so you don't upload temporary files.

## Why this counts as a "security" project

Steganography is a real branch of information security — it's about
**hiding the existence of data**, which is different from encryption
(which hides the *content* but not the fact that a secret exists).
It's used in real-world contexts like watermarking and covert
communication, and is a common topic in security coursework.
