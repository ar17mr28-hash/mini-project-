/**
 * AquaSentinel - Frontend Interactive Controller
 * Handles image upload preview, drag-and-drop, sample selection, and telemetry interactions.
 */

document.addEventListener("DOMContentLoaded", () => {
  initFileUpload();
  initDemoSamples();
  initTableSearch();
  initLoadingIndicator();
});

/**
 * Image Upload & Preview Logic
 */
function initFileUpload() {
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("sonarFileInput");
  const previewPanel = document.getElementById("previewPanel");
  const previewImg = document.getElementById("previewImg");
  const previewName = document.getElementById("previewName");
  const previewSize = document.getElementById("previewSize");
  const previewDim = document.getElementById("previewDim");
  const analyzeBtn = document.getElementById("analyzeBtn");
  const demoInput = document.getElementById("demoSampleInput");

  if (!fileInput || !dropzone) return;

  // Drag-and-drop visual states
  ["dragenter", "dragover"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove("dragover");
    });
  });

  // Handle Drop
  dropzone.addEventListener("drop", (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files && files.length > 0) {
      fileInput.files = files;
      handleFileSelected(files[0]);
    }
  });

  // Handle Standard Input Change
  fileInput.addEventListener("change", () => {
    if (fileInput.files && fileInput.files.length > 0) {
      handleFileSelected(fileInput.files[0]);
    }
  });

  function handleFileSelected(file) {
    if (demoInput) demoInput.value = ""; // Clear demo sample if uploading custom file

    const validExtensions = ["image/jpeg", "image/png", "image/jpg"];
    if (!validExtensions.includes(file.type) && !/\.(jpe?g|png)$/i.test(file.name)) {
      alert("Invalid format! Please upload a valid JPG, JPEG, or PNG side-scan sonar image.");
      fileInput.value = "";
      return;
    }

    if (file.size > 16 * 1024 * 1024) {
      alert("File size exceeds 16 MB limit. Please select a smaller sonar image.");
      fileInput.value = "";
      return;
    }

    // Read and preview
    const reader = new FileReader();
    reader.onload = (e) => {
      previewImg.src = e.target.result;
      previewName.textContent = file.name;
      previewSize.textContent = `${(file.size / 1024).toFixed(1)} KB`;

      // Measure dimensions
      const img = new Image();
      img.onload = () => {
        previewDim.textContent = `${img.naturalWidth} × ${img.naturalHeight} px`;
      };
      img.src = e.target.result;

      previewPanel.style.display = "block";
      if (analyzeBtn) analyzeBtn.disabled = false;
    };
    reader.readAsDataURL(file);
  }
}

/**
 * Pre-loaded Demo Sonar Samples (1-Click faculty demonstration)
 */
function initDemoSamples() {
  const sampleCards = document.querySelectorAll(".sample-card");
  const demoInput = document.getElementById("demoSampleInput");
  const previewPanel = document.getElementById("previewPanel");
  const previewImg = document.getElementById("previewImg");
  const previewName = document.getElementById("previewName");
  const previewSize = document.getElementById("previewSize");
  const previewDim = document.getElementById("previewDim");
  const analyzeBtn = document.getElementById("analyzeBtn");
  const fileInput = document.getElementById("sonarFileInput");

  sampleCards.forEach((card) => {
    card.addEventListener("click", () => {
      const filename = card.getAttribute("data-filename");
      const url = card.getAttribute("data-url");
      const name = card.getAttribute("data-name");

      if (demoInput) demoInput.value = filename;
      if (fileInput) fileInput.value = ""; // Clear file input

      // Highlight active sample
      sampleCards.forEach((c) => (c.style.borderColor = "var(--border-subtle)"));
      card.style.borderColor = "var(--cyan-primary)";
      card.style.boxShadow = "0 0 15px rgba(0, 229, 255, 0.4)";

      if (previewImg) {
        previewImg.src = url;
        previewName.textContent = `${filename} (Preloaded Acoustic Sample)`;
        previewSize.textContent = "Demo Dataset";

        const img = new Image();
        img.onload = () => {
          if (previewDim) previewDim.textContent = `${img.naturalWidth} × ${img.naturalHeight} px`;
        };
        img.src = url;

        if (previewPanel) previewPanel.style.display = "block";
        if (analyzeBtn) analyzeBtn.disabled = false;

        // Smooth scroll to preview
        previewPanel.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    });
  });
}

/**
 * Filter Detection History Table by search term
 */
function initTableSearch() {
  const searchInput = document.getElementById("historySearch");
  const tableRows = document.querySelectorAll("#historyTableBody tr");

  if (!searchInput || !tableRows.length) return;

  searchInput.addEventListener("input", () => {
    const query = searchInput.value.toLowerCase().trim();
    tableRows.forEach((row) => {
      const text = row.textContent.toLowerCase();
      row.style.display = text.includes(query) ? "" : "none";
    });
  });
}

/**
 * Show High-Tech Sonar Scanning Spinner on Submit
 */
function initLoadingIndicator() {
  const uploadForm = document.getElementById("uploadForm");
  const analyzeBtn = document.getElementById("analyzeBtn");

  if (uploadForm && analyzeBtn) {
    uploadForm.addEventListener("submit", () => {
      analyzeBtn.disabled = true;
      analyzeBtn.innerHTML = `
        <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true" 
              style="width: 18px; height: 18px; border: 2px solid #060b17; border-top-color: #00e5ff; border-radius: 50%; display: inline-block; animation: spin 0.8s linear infinite;"></span>
        Executing Sonar CV Pipeline...
      `;
    });
  }
}

// Add CSS keyframe for spinner dynamically if not defined
const style = document.createElement("style");
style.innerHTML = `
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;
document.head.appendChild(style);
