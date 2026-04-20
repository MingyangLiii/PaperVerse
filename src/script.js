const API_URL = "http://127.0.0.1:8000";
const paperList = document.getElementById('paperList');
const pdfViewer = document.getElementById('pdfViewer');
const currentTitle = document.getElementById('currentTitle');
const placeholder = document.getElementById('placeholder');

async function fetchPapers() {
    try {
        const response = await fetch(`${API_URL}/api/papers`);
        const data = await response.json();
        renderSidebar(data.papers);
    } catch (error) {
        console.error("Failed to fetch papers:", error);
        paperList.innerHTML = "<p style='color:red; padding:10px;'>Backend offline</p>";
    }
}

function renderSidebar(papers) {
    paperList.innerHTML = ""; // Clear list
    
    papers.forEach(fileName => {
        const item = document.createElement('div');
        item.className = 'paper-item';
        
        // Formatting the name for the UI
        const displayName = fileName.replace('.pdf', '').replace(/_/g, ' ');
        item.textContent = displayName;

        item.onclick = () => {
            // UI styling updates
            document.querySelectorAll('.paper-item').forEach(el => el.classList.remove('active'));
            item.classList.add('active');

            // Set the iframe source to the FastAPI static mount point
            placeholder.style.display = 'none';
            pdfViewer.style.display = 'block';
            pdfViewer.src = `${API_URL}/static/${fileName}`;
            currentTitle.textContent = displayName;
        };

        paperList.appendChild(item);
    });
}

window.onload = fetchPapers;

// Upload PDF functionality
const uploadBtn = document.getElementById('uploadBtn');
const pdfUploadInput = document.getElementById('pdfUploadInput');

uploadBtn.addEventListener('click', () => pdfUploadInput.click());

pdfUploadInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file || !file.name.endsWith('.pdf')) return;

    const formData = new FormData();
    formData.append('pdf', file);

    try {
        const response = await fetch(`${API_URL}/api/upload`, {
            method: 'POST',
            body: formData
        });
        if (response.ok) {
            pdfUploadInput.value = '';
            await fetchPapers(); // Refresh the paper list
        } else {
            alert('Upload failed. Please try again.');
        }
    } catch (error) {
        console.error("Upload error:", error);
        alert('Upload failed. Is the backend running?');
    }
});