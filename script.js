// ---------------------------------------------------
// MODULE 6: script.js (Frontend)
// Purpose: Switch between tabs, and send the image +
// message to Express using fetch(), then show the result.
// ---------------------------------------------------

function showTab(name) {
  document.getElementById("tab-hide").classList.toggle("active", name === "hide");
  document.getElementById("tab-reveal").classList.toggle("active", name === "reveal");
  document.getElementById("tab-hide-btn").classList.toggle("active", name === "hide");
  document.getElementById("tab-reveal-btn").classList.toggle("active", name === "reveal");
}

async function hideMessage() {
  const fileInput = document.getElementById("hide-image-input");
  const message = document.getElementById("hide-message-input").value;
  const resultBox = document.getElementById("hide-result");

  if (!fileInput.files[0] || !message.trim()) {
    resultBox.className = "result error";
    resultBox.textContent = "Please choose an image and type a message first.";
    return;
  }

  const formData = new FormData();
  formData.append("image", fileInput.files[0]);
  formData.append("message", message);

  resultBox.className = "result success";
  resultBox.textContent = "Hiding your message...";

  try {
    const response = await fetch("/api/hide", { method: "POST", body: formData });
    const data = await response.json();

    if (data.status === "success") {
      resultBox.className = "result success";
      resultBox.innerHTML = `Done! <a href="${data.downloadUrl}" download>Click here to download your secret image</a>`;
    } else {
      resultBox.className = "result error";
      resultBox.textContent = data.error;
    }
  } catch (err) {
    resultBox.className = "result error";
    resultBox.textContent = "Something went wrong talking to the server.";
  }
}

async function revealMessage() {
  const fileInput = document.getElementById("reveal-image-input");
  const resultBox = document.getElementById("reveal-result");

  if (!fileInput.files[0]) {
    resultBox.className = "result error";
    resultBox.textContent = "Please choose an image first.";
    return;
  }

  const formData = new FormData();
  formData.append("image", fileInput.files[0]);

  resultBox.className = "result success";
  resultBox.textContent = "Searching for a hidden message...";

  try {
    const response = await fetch("/api/reveal", { method: "POST", body: formData });
    const data = await response.json();

    if (data.status === "success") {
      resultBox.className = "result success";
      resultBox.textContent = "Hidden message: " + data.message;
    } else {
      resultBox.className = "result error";
      resultBox.textContent = data.error;
    }
  } catch (err) {
    resultBox.className = "result error";
    resultBox.textContent = "Something went wrong talking to the server.";
  }
}
