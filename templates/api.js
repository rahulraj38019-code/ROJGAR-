/* ========= VIDYAJOBS.AI API WRAPPER ========= */

const API_BASE = "";

/* ===== AI CHAT ===== */
async function askAI(data) {
    return fetch("/ask_ai_v10", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    }).then(res => res.json());
}

async function saveChat(data) {
    return fetch("/save_chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    });
}

async function loadChat(data) {
    return fetch("/load_chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    }).then(res => res.json());
}

async function getRecentChats() {
    return fetch("/recent_chats")
        .then(res => res.json());
}

async function deleteChat(data) {
    return fetch("/delete_chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    });
}

/* ===== JOB SYSTEM ===== */
async function fetchJobs(data) {
    return fetch("/fetch_jobs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    }).then(res => res.json());
}

async function getLiveUpdates() {
    return fetch("/get_live_updates")
        .then(res => res.json());
}

/* ===== COMMUNITY CHAT ===== */
async function getMessages() {
    return fetch("/get_messages")
        .then(res => res.json());
}

async function sendMessage(data) {
    return fetch("/send_message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    });
}

/* ===== OCR + PDF ===== */
async function uploadOCR(file) {
    let fd = new FormData();
    fd.append("file", file);

    return fetch("/ocr", {
        method: "POST",
        body: fd
    }).then(res => res.json());
}

async function uploadPDF(file) {
    let fd = new FormData();
    fd.append("file", file);

    return fetch("/read_pdf", {
        method: "POST",
        body: fd
    }).then(res => res.json());
}

/* ===== RESUME ===== */
async function generateResume(formData) {
    return fetch("/generate_resume", {
        method: "POST",
        body: formData
    }).then(res => res.blob());
}
