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

// Chat Panel functionality
const chatBtn = document.getElementById('chatBtn');
const chatPanel = document.getElementById('chatPanel');
const chatBackBtn = document.getElementById('chatBackBtn');
const chatInput = document.getElementById('chatInput');
const chatSendBtn = document.getElementById('chatSendBtn');
const chatMessages = document.getElementById('chatMessages');

chatBtn.addEventListener('click', () => {
    chatPanel.style.display = 'flex';
});

chatBackBtn.addEventListener('click', () => {
    chatPanel.style.display = 'none';
});

async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message) return;

    // Get current selected paper name
    const displayName = currentTitle.textContent === "Select a Paper" ? "none" : currentTitle.textContent + ".pdf";

    // Add user message (rendered as markdown)
    const msgDiv = document.createElement('div');
    msgDiv.className = 'chat-message';
    msgDiv.innerHTML = `<strong>You:</strong> <div class="md-content">${marked.parse(message)}</div>`;
    chatMessages.appendChild(msgDiv);

    chatInput.value = '';
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Send to backend
    try {
        const response = await fetch(`${API_URL}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, paper_name: displayName })
        });
        const data = await response.json();

        const replyDiv = document.createElement('div');
        replyDiv.className = 'chat-message';
        replyDiv.innerHTML = `<strong>Assistant:</strong> <div class="md-content">${marked.parse(data.response)}</div>`;
        chatMessages.appendChild(replyDiv);
        // Add empty line separator after each QA pair
        const sep = document.createElement('div');
        sep.className = 'chat-separator';
        chatMessages.appendChild(sep);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    } catch (error) {
        console.error("Chat error:", error);
        const errDiv = document.createElement('div');
        errDiv.className = 'chat-message';
        errDiv.style.color = 'red';
        errDiv.innerHTML = `<strong>Error:</strong> Failed to get response. Is the backend running?`;
        chatMessages.appendChild(errDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

chatSendBtn.addEventListener('click', sendMessage);
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});