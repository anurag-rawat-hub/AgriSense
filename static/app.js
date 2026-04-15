// ---------- ELEMENTS ----------
const uploadBtn = document.getElementById("upload-btn");
const fileInput = document.getElementById("file-input");

const statusText = document.getElementById("status");
const resultsDiv = document.getElementById("results");

const diseaseEl = document.getElementById("disease");
const confidenceEl = document.getElementById("confidence");
const aiEl = document.getElementById("ai");

const container = document.getElementById("canvas-container");

// ---------- CREATE SCANNING UI ----------
container.style.position = "relative";
container.style.overflow = "hidden";

// grid background
const grid = document.createElement("div");
grid.style.position = "absolute";
grid.style.width = "100%";
grid.style.height = "100%";
grid.style.backgroundImage =
  "linear-gradient(rgba(0,255,136,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(0,255,136,0.1) 1px, transparent 1px)";
grid.style.backgroundSize = "30px 30px";
container.appendChild(grid);

// scanning line
const scanLine = document.createElement("div");
scanLine.style.position = "absolute";
scanLine.style.width = "100%";
scanLine.style.height = "2px";
scanLine.style.background = "#00ff88";
scanLine.style.boxShadow = "0 0 10px #00ff88";
scanLine.style.top = "0";
container.appendChild(scanLine);

// particles
for (let i = 0; i < 30; i++) {
  const dot = document.createElement("div");
  dot.style.position = "absolute";
  dot.style.width = "4px";
  dot.style.height = "4px";
  dot.style.background = "#00ff88";
  dot.style.borderRadius = "50%";
  dot.style.left = Math.random() * 100 + "%";
  dot.style.top = Math.random() * 100 + "%";
  dot.style.opacity = 0.3;
  container.appendChild(dot);

  animateDot(dot);
}

// animation function
function animateDot(dot) {
  setInterval(() => {
    dot.style.transform = `translateY(${Math.random() * -20}px)`;
  }, 1000 + Math.random() * 1000);
}

// scan animation
let pos = 0;
function animateScan() {
  pos += 2;
  if (pos > container.clientHeight) pos = 0;
  scanLine.style.top = pos + "px";
  requestAnimationFrame(animateScan);
}
animateScan();

// ---------- IMAGE PREVIEW ----------
const img = document.createElement("img");
img.style.position = "absolute";
img.style.width = "100%";
img.style.height = "100%";
img.style.objectFit = "cover";
img.style.display = "none";
container.appendChild(img);

// overlay
const overlay = document.createElement("div");
overlay.innerText = "🔍 Scanning...";
overlay.style.position = "absolute";
overlay.style.width = "100%";
overlay.style.height = "100%";
overlay.style.display = "none";
overlay.style.alignItems = "center";
overlay.style.justifyContent = "center";
overlay.style.background = "rgba(0,255,136,0.2)";
overlay.style.color = "#00ff88";
overlay.style.fontSize = "22px";
container.appendChild(overlay);

// ---------- CAMERA ELEMENTS ----------
const cameraBtn = document.getElementById("camera-btn");
const cameraContainer = document.getElementById("camera-container");
const cameraFeed = document.getElementById("camera-feed");
const snapBtn = document.getElementById("snap-btn");
const cameraCanvas = document.getElementById("camera-canvas");

let stream = null;

cameraBtn.onclick = async () => {
  if (cameraContainer.style.display === "none" || !cameraContainer.style.display) {
    
    // Check hardware & context security api support
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        alert("Camera feature is not supported in this browser or environment. Make sure you are using 'localhost' or '127.0.0.1' over HTTP, or an HTTPS connection.");
        statusText.innerText = "❌ Security policy blocked camera access.";
        return;
    }

    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: true });
      cameraFeed.srcObject = stream;
      cameraContainer.style.display = "block";
      statusText.innerText = "📷 Camera active. Ready to capture...";
    } catch (err) {
      console.error("Camera Error:", err);
      if (err.name === 'NotAllowedError') {
          alert("We need camera permission to take a live photo. Please click the camera icon near the URL bar to allow access, then refresh.");
      }
      statusText.innerText = `❌ Error: ${err.name} - ${err.message}`;
    }
  } else {
    // stop camera
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }
    cameraContainer.style.display = "none";
    statusText.innerText = "Awaiting image upload for analysis...";
  }
};

snapBtn.onclick = () => {
  if (!stream) return;
  
  // draw feed to canvas
  cameraCanvas.width = cameraFeed.videoWidth;
  cameraCanvas.height = cameraFeed.videoHeight;
  cameraCanvas.getContext('2d').drawImage(cameraFeed, 0, 0);
  
  // convert to blob
  cameraCanvas.toBlob(async (blob) => {
    // Stop camera
    stream.getTracks().forEach(track => track.stop());
    cameraContainer.style.display = "none";
    
    // UI Preview
    img.src = URL.createObjectURL(blob);
    img.style.display = "block";
    
    overlay.style.display = "flex";
    statusText.innerText = "🔍 Analyzing captured leaf...";
    resultsDiv.style.display = "none";
    
    let formData = new FormData();
    formData.append("image", blob, "capture.jpg");
    
    await submitImage(formData);

  }, 'image/jpeg');
};

// ---------- UPLOAD ----------
uploadBtn.onclick = () => fileInput.click();

// ---------- HANDLE UPLOADED FILE ----------
fileInput.onchange = async () => {
  const file = fileInput.files[0];
  if (!file) return;

  // Make sure camera is closed if open
  if (stream) {
    stream.getTracks().forEach(track => track.stop());
    cameraContainer.style.display = "none";
  }

  img.src = URL.createObjectURL(file);
  img.style.display = "block";

  overlay.style.display = "flex";
  statusText.innerText = "🔍 Analyzing leaf...";
  resultsDiv.style.display = "none";

  let formData = new FormData();
  formData.append("image", file);

  await submitImage(formData);
};

// ---------- API SUBMISSION ----------
async function submitImage(formData) {
  try {
    const res = await fetch("/predict/", {
      method: "POST",
      body: formData
    });

    const data = await res.json();

    overlay.style.display = "none";
    diseaseEl.innerText = data.disease || "Unknown";
    confidenceEl.innerText = data.confidence
      ? (data.confidence * 100).toFixed(2) + "%"
      : "N/A";

    aiEl.innerText = data.ai || "No recommendation";

    resultsDiv.style.display = "block";
    statusText.innerText = "✅ Analysis complete";

    // 🔥 visual feedback
    if (data.disease && data.disease.toLowerCase().includes("blight")) {
      img.style.filter = "hue-rotate(320deg) brightness(0.7)";
    } else {
      img.style.filter = "none";
    }

  } catch (err) {
    console.error(err);
    overlay.style.display = "none";
    statusText.innerText = "❌ Error processing image";
  }
}