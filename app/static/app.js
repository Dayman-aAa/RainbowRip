document.addEventListener("DOMContentLoaded", () => {
    const urlForm = document.getElementById("url-form");
    const urlInput = document.getElementById("url-input");
    const fetchBtn = document.getElementById("fetch-btn");
    const errorMessage = document.getElementById("error-message");
    const loadingSpinner = document.getElementById("loading-spinner");
    const previewCard = document.getElementById("preview-card");

    const thumbImg = document.getElementById("thumb-img");
    const videoDuration = document.getElementById("video-duration");
    const videoTitle = document.getElementById("video-title");
    const videoChannel = document.querySelector("#video-channel span");
    const videoDesc = document.getElementById("video-desc");

    const tabBtns = document.querySelectorAll(".tab-btn");
    const qualitySelect = document.getElementById("quality-select");
    const downloadBtn = document.getElementById("download-btn");

    const progressContainer = document.getElementById("progress-container");
    const progressText = document.getElementById("progress-text");
    const progressPercent = document.getElementById("progress-percent");
    const progressBarFill = document.getElementById("progress-bar-fill");
    const saveFileBtn = document.getElementById("save-file-btn");

    let currentVideoData = null;
    let selectedType = "video"; // "video" or "audio"
    let activePollInterval = null;

    function showError(msg) {
        errorMessage.textContent = msg;
        errorMessage.classList.remove("hidden");
    }

    function clearError() {
        errorMessage.textContent = "";
        errorMessage.classList.add("hidden");
    }

    // Format tab switching (Video / Audio)
    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            tabBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            selectedType = btn.dataset.type;
            updateQualityOptions();
        });
    });

    function updateQualityOptions() {
        if (!currentVideoData) return;
        qualitySelect.innerHTML = "";

        if (selectedType === "video") {
            const qualities = currentVideoData.video_qualities || ["best"];
            qualities.forEach(q => {
                const opt = document.createElement("option");
                opt.value = q;
                opt.textContent = q;
                qualitySelect.appendChild(opt);
            });
        } else {
            const formats = currentVideoData.audio_formats || ["mp3", "m4a", "wav"];
            formats.forEach(f => {
                const opt = document.createElement("option");
                opt.value = f;
                opt.textContent = f.toUpperCase() + " Format";
                qualitySelect.appendChild(opt);
            });
        }
    }

    // Handle Form Submit (Analyze URL)
    urlForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        clearError();
        previewCard.classList.add("hidden");
        progressContainer.classList.add("hidden");
        saveFileBtn.classList.add("hidden");
        if (activePollInterval) clearInterval(activePollInterval);

        const url = urlInput.value.trim();
        if (!url) {
            showError("Please enter a valid YouTube URL.");
            return;
        }

        loadingSpinner.classList.remove("hidden");
        fetchBtn.disabled = true;

        try {
            const res = await fetch("/api/info", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url })
            });

            const data = await res.json();
            if (!res.ok) {
                throw new Error(data.error || "Failed to fetch video details.");
            }

            currentVideoData = data;

            // Populate preview card
            thumbImg.src = data.thumbnail || "";
            videoDuration.textContent = data.duration || "00:00";
            videoTitle.textContent = data.title || "Video";
            videoChannel.textContent = data.uploader || "Unknown Channel";
            videoDesc.textContent = data.description || "";

            updateQualityOptions();
            previewCard.classList.remove("hidden");

        } catch (err) {
            showError(err.message);
        } finally {
            loadingSpinner.classList.add("hidden");
            fetchBtn.disabled = false;
        }
    });

    // Handle Download Start
    downloadBtn.addEventListener("click", async () => {
        if (!currentVideoData) return;
        clearError();

        const quality = qualitySelect.value;
        downloadBtn.disabled = true;
        progressContainer.classList.remove("hidden");
        saveFileBtn.classList.add("hidden");
        progressText.textContent = "Initiating download...";
        progressPercent.textContent = "0%";
        progressBarFill.style.width = "0%";

        try {
            const res = await fetch("/api/download", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    url: currentVideoData.url,
                    type: selectedType,
                    quality: quality
                })
            });

            const data = await res.json();
            if (!res.ok) {
                throw new Error(data.error || "Failed to start download.");
            }

            pollProgress(data.download_id);

        } catch (err) {
            showError(err.message);
            downloadBtn.disabled = false;
        }
    });

    function pollProgress(downloadId) {
        if (activePollInterval) clearInterval(activePollInterval);

        activePollInterval = setInterval(async () => {
            try {
                const res = await fetch(`/api/progress/${downloadId}`);
                if (!res.ok) return;

                const data = await res.json();
                if (data.status === "downloading") {
                    const pct = data.progress || 0;
                    progressText.textContent = "Downloading from YouTube...";
                    progressPercent.textContent = `${pct}%`;
                    progressBarFill.style.width = `${pct}%`;
                } else if (data.status === "processing") {
                    progressText.textContent = "Processing / Converting file...";
                    progressPercent.textContent = "99%";
                    progressBarFill.style.width = "99%";
                } else if (data.status === "completed") {
                    clearInterval(activePollInterval);
                    progressText.textContent = "Download & Conversion Complete!";
                    progressPercent.textContent = "100%";
                    progressBarFill.style.width = "100%";
                    downloadBtn.disabled = false;

                    saveFileBtn.href = `/api/files/${encodeURIComponent(data.filename)}`;
                    saveFileBtn.classList.remove("hidden");
                } else if (data.status === "error") {
                    clearInterval(activePollInterval);
                    showError("Download failed: " + (data.error || "Unknown error"));
                    downloadBtn.disabled = false;
                }
            } catch (err) {
                console.error("Progress check error:", err);
            }
        }, 1000);
    }
});
