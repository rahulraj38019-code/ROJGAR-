// ROZGAR AI - R YADAV PRODUCTION (script.js)
let currentMaster = 'govt';
let currentQ = "";
let pageNum = 1;

// Naya Updated Filter List (Education & Bihar Special)
const filters = {
    govt: [
        { id: 'g-all', label: 'All India Jobs 🇮🇳', q: 'latest central govt jobs notification 2026' },
        { id: 'g-iti', label: 'ITI Apprentice/Jobs 🛠️', q: 'ITI apprentice railway ncl drdo latest jobs 2026' },
        { id: 'g-10th', label: '10th/12th Pass 🎓', q: 'govt jobs for 10th 12th pass students 2026' },
        { id: 'g-bihar', label: 'Bihar Special 🚩', q: 'bihar police bssc ssc vacancy notification 2026' },
        { id: 'r-admit', label: 'Admit Card 🎟️', q: 'latest govt exam admit card download 2026' },
        { id: 'r-ssc', label: 'Results ✅', q: 'SSC GD BSSC Bihar Police result marksheet 2026' }
    ],
    private: [
        { id: 'p-wfh', label: 'Work From Home 🏠', q: 'remote work from home jobs india 2026' },
        { id: 'p-delivery', label: 'Delivery/Driver 🚚', q: 'zomato swiggy porter delivery boy jobs' },
        { id: 'p-apna', label: 'Local Office Jobs 📱', q: 'site:apna.co office staff jobs for freshers 2026' },
        { id: 'p-pt', label: 'Part Time ⏰', q: 'part time evening jobs for students india' }
    ]
};

// Tabs switch karne ka function
function switchMaster(type) {
    currentMaster = type;
    document.getElementById('master-govt').classList.toggle('active-btn', type === 'govt');
    document.getElementById('master-private').classList.toggle('active-btn', type === 'private');
    renderFilters();
}

// Sub-filters render karne ka function
function renderFilters() {
    const container = document.getElementById('filter-tabs');
    container.innerHTML = "";
    filters[currentMaster].forEach((f, index) => {
        const btn = document.createElement('button');
        btn.id = 'f-' + f.id;
        btn.className = `px-5 py-2.5 border-2 border-slate-200 rounded-xl text-[9px] font-black uppercase whitespace-nowrap transition-all flex-shrink-0 mr-2 ${index === 0 ? 'active-sub-btn' : ''}`;
        btn.innerText = f.label;
        btn.onclick = () => {
            document.querySelectorAll('#filter-tabs button').forEach(b => b.classList.remove('active-sub-btn'));
            btn.classList.add('active-sub-btn');
            loadData(f.q);
        };
        container.appendChild(btn);
    });
    loadData(filters[currentMaster][0].q);
}

// Data load karne ka function (Fetch API)
async function loadData(q, isMore = false) {
    const box = document.getElementById('results-box');
    const ldr = document.getElementById('loader');
    const lm = document.getElementById('load-more-div');

    if(!isMore) { box.innerHTML = ""; pageNum = 1; }
    currentQ = q;
    ldr.classList.remove('hidden');
    lm.classList.add('hidden');
    
    try {
        const res = await fetch('/search', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ interest: q + " " + (isMore ? pageNum : ""), ts: Date.now() })
        });
        const data = await res.json();
        ldr.classList.add('hidden');
        
        // Result aur Admit card ke liye alag color theme
        const isResult = q.toLowerCase().includes('result') || q.toLowerCase().includes('admit');
        const themeColor = isResult ? 'emerald-600' : (currentMaster === 'govt' ? 'blue-950' : 'indigo-600');
        const btnText = isResult ? 'CHECK NOW ✅' : 'DETAILS & APPLY 🚀';

        data.forEach(item => {
            const liveBadge = item.is_live ? `<span class="live-tag bg-red-600 text-white px-2 py-0.5 rounded text-[7px] font-bold">LIVE FORM</span>` : '';
            box.innerHTML += `
            <div class="job-card p-6 bg-white border-2 border-slate-100 shadow-xl border-l-[10px] border-${themeColor}">
                <div class="flex justify-between items-start mb-2">
                    <button onclick="copyMyInfo()" class="bg-yellow-400 text-black px-3 py-1 rounded-lg text-[8px] font-black uppercase shadow-md active:scale-95">📋 Copy My Info</button>
                    ${liveBadge}
                </div>
                <h3 class="font-black text-sm uppercase mb-3 mt-1 text-slate-900 leading-tight">${item.title}</h3>
                <p class="text-[10px] text-slate-500 mb-6 line-clamp-2 italic">${item.snippet}</p>
                <a href="${item.link}" target="_blank" class="block w-full text-center bg-${themeColor} text-white py-4 rounded-2xl font-black text-[10px] shadow-lg uppercase tracking-wider">${btnText}</a>
            </div>`;
        });
        if(data.length > 0) lm.classList.remove('hidden');
    } catch(e) { 
        console.error("Data load nahi ho paya:", e);
        ldr.classList.add('hidden'); 
    }
}

// Clipboard copy function
function copyMyInfo() {
    const info = `Name: ${localStorage.getItem('user_n')}\nEmail: ${localStorage.getItem('user_e')}\nPhone: ${localStorage.getItem('user_p')}\nResume: ${localStorage.getItem('user_r')}`;
    navigator.clipboard.writeText(info);
    const t = document.getElementById('toast');
    t.classList.remove('hidden');
    setTimeout(() => t.classList.add('hidden'), 2000);
}

// Profile UI functions
function showProfile() {
    document.getElementById('p-name-in').value = localStorage.getItem('user_n') || '';
    document.getElementById('p-email-in').value = localStorage.getItem('user_e') || '';
    document.getElementById('p-phone-in').value = localStorage.getItem('user_p') || '';
    document.getElementById('p-resume-in').value = localStorage.getItem('user_r') || '';
    document.getElementById('profile-ui').style.display = 'flex';
}
function hideProfile() { document.getElementById('profile-ui').style.display = 'none'; }

function updateProfile() {
    localStorage.setItem('user_n', document.getElementById('p-name-in').value);
    localStorage.setItem('user_e', document.getElementById('p-email-in').value);
    localStorage.setItem('user_p', document.getElementById('p-phone-in').value);
    localStorage.setItem('user_r', document.getElementById('p-resume-in').value);
    alert("Profile Update Ho Gayi, Bhai!");
    hideProfile();
}

// Login logic
function doLogin() {
    const n = document.getElementById('un').value;
    const e = document.getElementById('ue').value;
    const p = document.getElementById('u-phone').value;
    const r = document.getElementById('u-resume').value;
    if(!n || !e) return alert("Bhai, kam se kam Naam aur Email toh dalo!");
    localStorage.setItem('user_n', n); 
    localStorage.setItem('user_e', e); 
    localStorage.setItem('user_p', p); 
    localStorage.setItem('user_r', r);
    location.reload();
}

// AI Chat functions
function showChat() { document.getElementById('chat-ui').style.display = 'flex'; }
function hideChat() { document.getElementById('chat-ui').style.display = 'none'; }

async function sendChat() {
    const inp = document.getElementById('chat-in'), box = document.getElementById('msg-box');
    if(!inp.value) return;
    const msg = inp.value;
    box.innerHTML += `<div class="bg-blue-950 text-white p-4 rounded-2xl ml-10 font-bold text-sm shadow-md">${msg}</div>`;
    inp.value = "";
    box.scrollTop = box.scrollHeight;
    try {
        const res = await fetch('/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ message: msg, name: localStorage.getItem('user_n') })
        });
        const d = await res.json();
        box.innerHTML += `<div class="bg-white border-2 p-5 rounded-2xl mr-10 shadow-xl text-sm border-l-8 border-blue-950 font-medium whitespace-pre-line">${d.reply}</div>`;
    } catch(e) { }
    box.scrollTop = box.scrollHeight;
}

// App start hone par check
window.onload = () => {
    if(localStorage.getItem('user_n')) {
        document.getElementById('login-view').classList.add('hidden');
        document.getElementById('dash-view').classList.remove('hidden');
        document.getElementById('floating-support').classList.remove('hidden');
        switchMaster('govt');
    } else {
        document.getElementById('login-view').classList.remove('hidden');
        document.getElementById('dash-view').classList.add('hidden');
        document.getElementById('floating-support').classList.add('hidden');
    }
};

function clearData() { localStorage.clear(); location.reload(); }
function loadMore() { pageNum++; loadData(currentQ, true); }
