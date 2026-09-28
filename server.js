// ---------------------------------------------------
// MODULE 3: server.js  (Node.js + Express)
// Purpose: The "connector". It does 3 jobs:
//   1. Serves the frontend (HTML/CSS/JS) in public/
//   2. Accepts an uploaded image
//   3. Runs python/cli.py with the right arguments,
//      waits for the answer, and sends it back to
//      the browser as JSON.
//
// SECURITY NOTE: We use execFile() instead of exec().
// execFile() passes each argument separately, so even
// if someone types weird symbols in the message box,
// it can NEVER be used to run extra commands on the
// server. This is called avoiding "command injection".
// ---------------------------------------------------

const express = require("express");
const multer = require("multer");
const path = require("path");
const fs = require("fs");
const { execFile } = require("child_process");

const app = express();
const PORT = 3000;

const UPLOAD_DIR = path.join(__dirname, "uploads");
const PYTHON_DIR = path.join(__dirname, "..", "python");

if (!fs.existsSync(UPLOAD_DIR)) fs.mkdirSync(UPLOAD_DIR);

const upload = multer({ dest: UPLOAD_DIR });

app.use(express.static(path.join(__dirname, "public")));
app.use("/uploads", express.static(UPLOAD_DIR)); // so download links work

// ---------- HIDE a message inside an uploaded image ----------
app.post("/api/hide", upload.single("image"), (req, res) => {
  const message = req.body.message;
  if (!req.file || !message) {
    return res.status(400).json({ status: "error", error: "Image and message are both required." });
  }

  const inputPath = req.file.path;
  const outputFilename = "encoded-" + Date.now() + ".png";
  const outputPath = path.join(UPLOAD_DIR, outputFilename);

  execFile("python3", ["cli.py", "encode", inputPath, message, outputPath], { cwd: PYTHON_DIR }, (err, stdout) => {
    if (err) {
      return res.status(500).json({ status: "error", error: "Python script failed to run." });
    }
    const result = JSON.parse(stdout);
    if (result.status === "error") {
      return res.status(400).json(result);
    }
    // Send back a link the frontend can use to download the image
    res.json({ status: "success", downloadUrl: "/uploads/" + outputFilename });
  });
});

// ---------- REVEAL a message from an uploaded image ----------
app.post("/api/reveal", upload.single("image"), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ status: "error", error: "An image is required." });
  }

  const inputPath = req.file.path;

  execFile("python3", ["cli.py", "decode", inputPath], { cwd: PYTHON_DIR }, (err, stdout) => {
    if (err) {
      return res.status(500).json({ status: "error", error: "Python script failed to run." });
    }
    const result = JSON.parse(stdout);
    res.json(result);
  });
});

app.listen(PORT, () => {
  console.log(`Steganography tool running at http://localhost:${PORT}`);
});
