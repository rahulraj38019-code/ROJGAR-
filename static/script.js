
// ========= GLOBAL STATE & CORE VARS =========
const API = ""; 
let user = {}; let resType = ''; let currentCategory = ''; let lastResults = []; let currentType = ''; 
let pageCount = 1; let currentScreen = 'home';
let isAIModalOpen = false;

// NAYA STATE
let currentChatId = localStorage.getItem("chat_uid") || createNewChatId();
let chatHistory = [];
let isTyping = false;

window.onload = async () => {
    if(localStorage.getItem('darkMode') === 'true') document.body.classList.add('dark-mode');
    checkLogin();
    fetchLive();
    loadMessages();
    setInterval(loadMessages, 5000);
    
    injectV10UI(); 
    
    // Init AI Chat
    localStorage.setItem("chat_uid", currentChatId);
    await loadChatFromCloud();
    await loadRecentChats();
    initVoiceInput();

    if(localStorage.getItem('userHub')) {
        history.replaceState({screen: 'home'}, '');
    }
};

function createNewChatId() { return "chat_" + Date.now(); }

function injectV10UI() {
    document.body.insertAdjacentHTML("beforeend", `
    <div id="v10-home" style="position:fixed;top:0;left:0;width:100%;height:100%;background:var(--bg);color:var(--main);z-index:1999;overflow:auto;display:none;">
        <div style="padding:18px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #eee; background:var(--white);">
            <div style="display:flex; align-items:center; gap:10px;">
                <button onclick="closeV10Home()" style="background:none; border:none; font-size:22px; color:var(--blue); cursor:pointer;">⬅</button>
                <div style="font-size:20px;font-weight:900;color:var(--blue);">AI CHAT HISTORY</div>
            </div>
        </div>
        <div style="padding:15px;font-size:12px;opacity:.7;font-weight:800;">RECENT CONVERSATIONS</div>
        <div id="recentChats" style="padding-bottom:100px;"></div>
        <button onclick="startNewChat()" style="position:fixed;right:20px;bottom:100px;background:var(--ai-gradient);color:#fff;border:none;padding:15px 20px;border-radius:40px;font-weight:900;font-size:14px;box-shadow:0 5px 15px rgba(0,0,0,0.2);z-index:2001;">+ NEW AI CHAT</button>
    </div>
    `);
}

// ==========================================
// AI LOGIC
// ==========================================

async function startNewChat() {
    if (chatHistory.length > 0) await saveChatToCloud();
    currentChatId = createNewChatId();
    localStorage.setItem("chat_uid", currentChatId);
    chatHistory = [];
    clearChatUI();
    addBotMessage("New chat started 🚀");
    await loadRecentChats();
    openAIModal();
}

function clearChatUI() {
    const body = document.getElementById("ai-chat-body");
    if (body) body.innerHTML = "";
}

function addUserMessage(text) {
    const body = document.getElementById("ai-chat-body");
    body.innerHTML += `<div class="chat-bubble bubble-right"><span class="chat-user">You</span>${escapeHtml(text)}</div>`;
    body.scrollTop = body.scrollHeight;
}

function addBotMessage(text) {
    const body = document.getElementById("ai-chat-body");
    body.innerHTML += `<div class="chat-bubble bubble-left"><span class="chat-user">VidyaJobs.AI</span>${formatMessage(text)}</div>`;
    body.scrollTop = body.scrollHeight;
}

function showTyping() {
    if (isTyping) return;
    isTyping = true;
    const body = document.getElementById("ai-chat-body");
    body.innerHTML += `
        <div class="chat-bubble bubble-left" id="typingBox">
            <span class="chat-user">VidyaJobs.AI</span>
            <span class="typing-dot">●</span><span class="typing-dot">●</span><span class="typing-dot">●</span>
        </div>`;
    body.scrollTop = body.scrollHeight;
}

function hideTyping() { isTyping = false; const box = document.getElementById("typingBox"); if (box) box.remove(); }

async function askOpenRouter() {
    const input = document.getElementById("ai-input");
    const msg = input.value.trim();
    if (!msg) return;

    addUserMessage(msg);
    input.value = "";
    chatHistory.push({ role: "user", content: msg });
    showTyping();

    try {
        const res = await fetch("/ask_ai_v10", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ uid: currentChatId, message: msg })
        });
        const data = await res.json();
        hideTyping();
        addBotMessage(data.reply || "No reply");
        chatHistory.push({ role: "assistant", content: data.reply });
        await saveChatToCloud();
        await loadRecentChats();
    } catch (err) {
        hideTyping();
        addBotMessage("Server error 😔");
    }
}

async function saveChatToCloud() {
    try {
        await fetch("/save_chat", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ uid: currentChatId, chats: chatHistory })
        });
    } catch (e) {}
}

async function loadChatFromCloud() {
    try {
        const res = await fetch("/load_chat", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ uid: currentChatId })
        });
        const data = await res.json();
        chatHistory = data.chats || [];
        clearChatUI();
        if (chatHistory.length === 0) {
            addBotMessage("Namaste 👋 Main VidyaJobs.AI hoon.");
        } else {
            chatHistory.forEach(m => {
                if (m.role === "user") addUserMessage(m.content);
                else addBotMessage(m.content);
            });
        }
    } catch (e) {}
}

async function loadRecentChats() {
    try {
        const res = await fetch("/recent_chats");
        const data = await res.json();
        const box = document.getElementById("recentChats");
        if (!box) return;
        box.innerHTML = "";
        data.users.reverse().forEach(uid => {
            box.innerHTML += `
                <div class="recent-chat-item">
                    <span onclick="openRecentChat('${uid}')">${uid}</span>
                    <button onclick="deleteRecentChat('${uid}')" style="border:none; background:none; cursor:pointer;">🗑️</button>
                </div>`;
        });
    } catch (e) {}
}

async function openRecentChat(uid) {
    currentChatId = uid;
    localStorage.setItem("chat_uid", uid);
    await loadChatFromCloud();
    openAIModal();
}

async function deleteRecentChat(uid) {
    await fetch("/delete_chat", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ uid })
    });
    await loadRecentChats();
}

function initVoiceInput() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;
    const recog = new SpeechRecognition();
    recog.lang = "hi-IN";
    const micBtn = document.getElementById("voiceBtn");
    if (micBtn) {
        micBtn.onclick = () => recog.start();
        recog.onresult = e => {
            document.getElementById("ai-input").value = e.results[0][0].transcript;
            askOpenRouter();
        };
    }
}

function openV10Home() { document.getElementById("v10-home").style.display = "block"; loadRecentChats(); }
function closeV10Home() { document.getElementById("v10-home").style.display = "none"; }
function backHomeV10() { closeAIModal(); openV10Home(); }

function formatMessage(text) { return text.replace(/\n/g, "<br>").replace(/\*\*(.*?)\*\*/g, "<b>$1</b>"); }
function escapeHtml(str) { return str.replace(/</g, "&lt;").replace(/>/g, "&gt;"); }

// ==========================================
// NEW V10 ULTRA DASHBOARD LOGIC
// ==========================================
function showV10UltraDash() {
    hideAll();
    document.getElementById('v10-ultra-dash').classList.remove('hidden');
    document.getElementById('main-header').classList.remove('hidden');
    document.getElementById('bottom-bar').classList.remove('hidden');
    if(document.getElementById('sideMenu').classList.contains('active')) toggleMenu();
}

function showBox(id) {
    document.querySelectorAll('.box').forEach(b => b.style.display = 'none');
    document.getElementById(id).style.display = 'block';
}

async function performOCR() {
    let file = document.getElementById('img-input').files[0];
    if(!file) return alert("Select image first!");
    document.getElementById('ocrout').innerText = "Processing OCR...";
    let fd = new FormData(); fd.append("file", file);
    try {
        let res = await fetch("/ocr", {method:"POST", body:fd});
        let data = await res.json();
        document.getElementById('ocrout').innerText = data.text || "No text found.";
    } catch(e) { document.getElementById('ocrout').innerText = "OCR Failed!"; }
}

async function readPDFFile() {
    let file = document.getElementById('pdfFile-input').files[0];
    if(!file) return alert("Select PDF first!");
    document.getElementById('pdfout').innerText = "Reading PDF...";
    let fd = new FormData(); fd.append("file", file);
    try {
        let res = await fetch("/read_pdf", {method:"POST", body:fd});
        let data = await res.json();
        document.getElementById('pdfout').innerText = data.text || "Could not extract text.";
    } catch(e) { document.getElementById('pdfout').innerText = "PDF Reading Failed!"; }
}

// ==========================================
// APP UI LOGIC
// ==========================================

window.onpopstate = function(event) {
    if (isAIModalOpen) { closeAIModal(); return; }
    if (document.getElementById("v10-home").style.display === "block") { closeV10Home(); return; }
    if (event.state) {
        const screen = event.state.screen;
        if (screen === 'home') showDash(false);
        else if (screen === 'results') showResults(false);
        else if (screen === 'chat') showCommunityChat(false);
        else if (screen === 'resume') showResumeSection(false);
        else if (screen === 'list') {
            hideAll();
            document.getElementById('main-header').classList.remove('hidden'); 
            document.getElementById('feed-sec').classList.remove('hidden'); 
            document.getElementById('bottom-bar').classList.remove('hidden');
            renderList(lastResults);
        }
    } else { showDash(false); }
};

function openAIModal() { 
    document.getElementById('ai-modal').classList.add('active'); 
    document.body.style.overflow = 'hidden'; 
    isAIModalOpen = true;
    history.pushState({modal: 'ai'}, '');
}
function closeAIModal() { 
    document.getElementById('ai-modal').classList.remove('active');
    document.body.style.overflow = 'auto';
    isAIModalOpen = false;
}

function checkLogin() {
    let saved = localStorage.getItem('userHub');
    if(saved) {
        user = JSON.parse(saved);
        document.getElementById('user-initial').innerText = user.name ? user.name.charAt(0).toUpperCase() : 'U';
        showDash(false);
    } else {
        hideAll();
        document.getElementById('login-sec').classList.remove('hidden');
    }
}

function saveLogin() {
    let name = document.getElementById('u-name').value;
    if(!name || !user.edu) return alert("Please fill Name and Select Education!");
    user.name = name;
    localStorage.setItem('userHub', JSON.stringify(user));
    location.reload();
}

function toggleEdu(chip, val) {
    document.querySelectorAll('.edu-chip').forEach(c => c.classList.remove('selected'));
    chip.classList.add('selected');
    user.edu = val;
}

function hideAll() {
    ['login-sec','dash-sec','res-sec','feed-sec','main-header','bottom-bar','resume-sec','chat-sec','v10-ultra-dash'].forEach(id => {
        let el = document.getElementById(id);
        if(el) el.classList.add('hidden');
    });
}

function showDash(push = true) {
    hideAll();
    document.getElementById('main-header').classList.remove('hidden');
    document.getElementById('dash-sec').classList.remove('hidden');
    document.getElementById('bottom-bar').classList.remove('hidden');
    setActiveNav(0);
    currentScreen = 'home';
    if(push) history.pushState({screen: 'home'}, '');
}

function showResults(push = true) {
    hideAll();
    document.getElementById('main-header').classList.remove('hidden');
    document.getElementById('res-sec').classList.remove('hidden');
    document.getElementById('bottom-bar').classList.remove('hidden');
    setActiveNav(1);
    currentScreen = 'results';
    if(push) history.pushState({screen: 'results'}, '');
}

function showResumeSection(push = true) {
    hideAll();
    document.getElementById('main-header').classList.remove('hidden');
    document.getElementById('resume-sec').classList.remove('hidden');
    document.getElementById('bottom-bar').classList.remove('hidden');
    if(document.getElementById('sideMenu').classList.contains('active')) toggleMenu();
    if(push) history.pushState({screen: 'resume'}, '');
}

function showCommunityChat(push = true) {
    hideAll();
    document.getElementById('main-header').classList.remove('hidden');
    document.getElementById('chat-sec').classList.remove('hidden');
    document.getElementById('bottom-bar').classList.remove('hidden');
    loadMessages();
    if(push) history.pushState({screen: 'chat'}, '');
}

async function downloadResume() {
    const btn = document.querySelector('.resume-btn');
    btn.innerText = "Generating...";
    const formData = new FormData();
    formData.append('name', user.name || 'User');
    formData.append('father', document.getElementById('res-father').value || 'N/A');
    formData.append('edu', user.edu || 'N/A');
    formData.append('skills', document.getElementById('res-skills').value || 'N/A');
    formData.append('exp', document.getElementById('res-exp').value || 'N/A');
    try {
        const response = await fetch('/generate_resume', { method: 'POST', body: formData });
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url; a.download = 'My_Resume.pdf';
            document.body.appendChild(a); a.click();
            btn.innerText = "Download Success!";
            setTimeout(() => btn.innerText = "Download Resume 📥", 2000);
        }
    } catch (err) { alert("Download fail!"); btn.innerText = "Try Again"; }
}

async function loadMessages() {
    const chatBox = document.getElementById('chat-display');
    if(!chatBox || document.getElementById('chat-sec').classList.contains('hidden')) return;
    try {
        const res = await fetch('/get_messages');
        const messages = await res.json();
        chatBox.innerHTML = messages.map(m => `
            <div class="chat-bubble ${m.user.includes('Admin') ? 'bubble-right' : 'bubble-left'}">
                <span class="chat-user">@${m.user}</span>
                ${m.msg}<span class="chat-time">${m.time}</span>
            </div>
        `).join('');
        chatBox.scrollTop = chatBox.scrollHeight;
    } catch (e) {}
}

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const msg = input.value;
    if(!msg) return;
    await fetch('/send_message', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ user: user.name || "Guest", msg: msg })
    });
    input.value = ''; loadMessages();
}

async function fetchLive() {
    try {
        const res = await fetch('/get_live_updates');
        const data = await res.json();
        if(data.jobs && data.jobs.length) {
            document.getElementById('job-ticker').innerHTML = data.jobs.map(j => `<div onclick="showDetailsDirect('${j.title}', '${j.link}', 'Job')" class="ticker-item">${j.title}</div>`).join('');
        }
        if(data.admits && data.admits.length) {
            document.getElementById('admit-ticker').innerHTML = data.admits.map(a => `<div onclick="showDetailsDirect('${a.title}', '${a.link}', 'Admit Card')" class="ticker-item">${a.title}</div>`).join('');
        }
    } catch(e) {}
}

function setActiveNav(idx) {
    document.querySelectorAll('.nav-item').forEach((n,i) => i === idx ? n.classList.add('active') : n.classList.remove('active'));
}

function toggleMenu() { document.getElementById('sideMenu').classList.toggle('active'); document.getElementById('overlay').classList.toggle('active'); }
function toggleDarkMode() { document.body.classList.toggle('dark-mode'); localStorage.setItem('darkMode', document.body.classList.contains('dark-mode')); }
function editProfile() { localStorage.removeItem('userHub'); location.reload(); }
function logout() { localStorage.removeItem('userHub'); location.reload(); }
function clearAllV10() { if(confirm("Saari AI Chat delete kar dein?")) { localStorage.removeItem("chat_uid"); location.reload(); } }

function triggerSearch() { 
    let v = document.getElementById('main-search-inp').value; 
    if(!v) return; openJobs(v);
}

function startMicV10Search() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;
    const rec = new SpeechRecognition();
    rec.lang = "hi-IN";
    rec.start();
    rec.onresult = function(e) {
        document.getElementById("main-search-inp").value = e.results[0][0].transcript;
        triggerSearch();
    };
}

function toggleResSub(id) { 
    document.querySelectorAll('#res-sec .card').forEach(c => c.classList.add('hidden')); 
    const sub = document.getElementById('sub-'+id);
    if(sub) sub.classList.remove('hidden'); 
    resType = ''; 
}

function setResType(btn, type) { 
    btn.parentElement.querySelectorAll('.pill').forEach(p => p.classList.remove('active-pill')); 
    btn.classList.add('active-pill'); resType = type; 
}

function finalResSearch(cat, yearId) { 
    let yearVal = document.getElementById(yearId).value;
    if(!resType) return alert("Pehle option select karein!"); 
    if(!yearVal) return alert("Pehle Year (saal) daalein!");
    let query = `${cat} ${resType} Result ${yearVal} official direct portal`;
    openJobs(query); 
}

function updateMUSemButtons() {
    const session = document.getElementById('mu-session').value;
    const semDiv = document.getElementById('mu-sem-container');
    const partDiv = document.getElementById('mu-part-container');
    const examBtn = document.getElementById('mu-btn-exam');
    const admBtn = document.getElementById('mu-btn-adm');
    resType = '';
    document.querySelectorAll('.pill').forEach(p => p.classList.remove('active-pill'));
    if (!session) { semDiv.classList.add('hidden'); partDiv.classList.add('hidden'); return; }
    if (session === "2023-27" || session === "2024-28") { semDiv.classList.remove('hidden'); partDiv.classList.add('hidden'); }
    else { semDiv.classList.add('hidden'); partDiv.classList.remove('hidden'); }
    if (["2020-23", "2021-24"].includes(session)) { examBtn.classList.add('hidden'); admBtn.classList.add('hidden'); }
    else { examBtn.classList.remove('hidden'); admBtn.classList.remove('hidden'); }
}

function muAction(actionType) {
    let session = document.getElementById('mu-session').value;
    if(!session) return alert("Pehle Session chunein!");
    if(!resType) return alert("Pehle Semester ya Year chunein!");
    let query = `Magadh University ${session} ${resType} ${actionType} official direct link portal`;
    openJobs(query); 
}

async function openJobs(cat, isLoadMore = false) { 
    if(!isLoadMore) {
        lastResults = []; pageCount = 1;
        document.getElementById('list').innerHTML = "<div style='padding:40px; text-align:center; font-weight:700; color:var(--blue);'>🔍 Searching...</div>";
        history.pushState({screen: 'list'}, '');
    }
    currentCategory = cat;
    let lowerCat = cat.toLowerCase();
    if(lowerCat.includes('result')) { currentType = 'Result'; }
    else if(lowerCat.includes('admit')) { currentType = 'Admit Card'; }
    else if(lowerCat.includes('admission')) { currentType = 'Admission'; }
    else { currentType = 'Info'; }
    hideAll(); 
    document.getElementById('main-header').classList.remove('hidden'); 
    document.getElementById('bottom-bar').classList.remove('hidden'); 
    document.getElementById('feed-sec').classList.remove('hidden'); 
    document.getElementById('f-title').innerText = cat.substring(0, 20).toUpperCase() + (cat.length > 20 ? '...' : ''); 
    try {
        const response = await fetch('/fetch_jobs', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category: cat, edu: user.edu || '10th', page: pageCount })
        });
        let newResults = await response.json();
        lastResults = [...lastResults, ...newResults];
        renderList(lastResults);
        if(newResults.length > 0) document.getElementById('load-more-container').classList.remove('hidden');
        else document.getElementById('load-more-container').classList.add('hidden');
    } catch(e) { document.getElementById('list').innerHTML = "<div style='padding:40px; text-align:center;'>⚠️ Error!</div>"; }
}

function loadMore() { pageCount++; openJobs(currentCategory, true); }

function renderList(results) {
    const listDiv = document.getElementById('list');
    if(!results || results.length === 0) { listDiv.innerHTML = "<div style='padding:40px; text-align:center;'>❌ No data found.</div>"; return; }
    listDiv.innerHTML = results.map((item, index) => `
        <div class="job-card" onclick="viewDetails(${index})">
            <div class="job-title">${item.title}</div>
            <div class="job-desc">${item.snippet ? item.snippet.substring(0, 120) : 'Details...'}</div>
            <div style="font-size:11px; color:var(--blue); margin-top:10px; font-weight:800;">READ MORE →</div>
        </div>
    `).join('');
}

function viewDetails(index) {
    const item = lastResults[index];
    const listDiv = document.getElementById('list');
    document.getElementById('back-btn').classList.remove('hidden');
    document.getElementById('load-more-container').classList.add('hidden');
    history.pushState({screen: 'details'}, '');
    let btnText = "Open Link 🚀";
    if(currentType === 'Result') btnText = "Check Result ✅";
    if(currentType === 'Admit Card') btnText = "Download Card 📥";
    if(currentType === 'Admission') btnText = "Apply For Admission 🎓";
    listDiv.innerHTML = `
        <div class="details-card">
            <h2 style="color:var(--blue); margin-top:0; font-size:18px;">${item.title}</h2>
            <p style="font-size:14px; line-height:1.6; color:var(--main); margin-top:15px;">${item.snippet || 'No extra info.'}</p>
            <button onclick="window.open('${item.link}', '_blank')" class="btn-primary" style="margin-top:20px;">${btnText}</button>
        </div>
    `;
}

function showDetailsDirect(title, link, type) {
    currentType = type;
    hideAll();
    document.getElementById('main-header').classList.remove('hidden'); 
    document.getElementById('feed-sec').classList.remove('hidden');
    document.getElementById('bottom-bar').classList.remove('hidden');
    history.pushState({screen: 'details'}, '');
    document.getElementById('list').innerHTML = `
        <div class="details-card">
            <h2 style="color:var(--blue); margin-top:0;">${title}</h2>
            <button onclick="window.open('${link}', '_blank')" class="btn-primary" style="margin-top:25px;">Check Now 🚀</button>
        </div>
    `;
}

function goBackToList() { history.back(); }

document.addEventListener("keydown", e => {
    if (e.key === "Enter") {
        const active = document.activeElement;
        if (active && active.id === "ai-input") {
            askOpenRouter();
        }
    }
});
