/**
 * OmniNexus Studio Frontend Application Logic
 * Integrates ReAct Agent, Qwen3-TTS Studio, Android Commander, and OpenClaw Gateway.
 */

// State
let ws = null;
let currentTab = "tab-agent";
let activeAudio = null;
let isRecording = false;
let mediaRecorder = null;
let recordedAudioChunks = [];

// Init on DOM ready
document.addEventListener("DOMContentLoaded", () => {
    initNavigation();
    initWebSocket();
    loadVoices();
    loadDevices();
    loadRootCatalog();
    loadModels();
    refreshAndroidScreenshot();
    initWaveformCanvas();
});

// ============================================================================
// NAVIGATION
// ============================================================================
function initNavigation() {
    const tabs = document.querySelectorAll(".nav-tab");
    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            const targetId = tab.dataset.tab;
            tabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");

            document.querySelectorAll(".tab-pane").forEach(pane => {
                pane.classList.remove("active");
            });
            const activePane = document.getElementById(targetId);
            if (activePane) activePane.classList.add("active");
            currentTab = targetId;

            if (targetId === "tab-android") {
                refreshAndroidScreenshot();
                loadPackages();
            }
        });
    });
}

// ============================================================================
// WEBSOCKET & THREE-CHANNEL EVENT BUS (KODE AGENT SDK)
// ============================================================================
function initWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/agent`;

    try {
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            appendFeed("monitor", "[SYSTEM] Connected to OmniNexus EventBus (Channels: Progress | Control | Monitor)");
            const dot = document.getElementById("statusDot");
            const text = document.getElementById("statusText");
            if (dot) dot.style.backgroundColor = "var(--accent-emerald)";
            if (text) text.innerText = "Online";
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                handleAgentEvent(data);
            } catch (err) {
                console.error("WS Parse error", err);
            }
        };

        ws.onclose = () => {
            const dot = document.getElementById("statusDot");
            const text = document.getElementById("statusText");
            if (dot) dot.style.backgroundColor = "var(--accent-amber)";
            if (text) text.innerText = "Reconnecting...";
            setTimeout(initWebSocket, 3000);
        };
    } catch (e) {
        console.warn("WebSocket init failed:", e);
    }
}

function handleAgentEvent(data) {
    const { channel, event_type, payload } = data;
    const msg = payload.message || payload.action || JSON.stringify(payload);
    appendFeed(channel, `[${channel.toUpperCase()}] ${event_type}: ${msg}`);

    if (event_type === "step_start" || event_type === "step_completed") {
        updateTimelineStep(payload);
    }
}

function appendFeed(channel, text) {
    const feed = document.getElementById("eventFeed");
    if (!feed) return;
    const line = document.createElement("div");
    line.className = `feed-line feed-${channel}`;
    line.innerText = text;
    feed.appendChild(line);
    feed.scrollTop = feed.scrollHeight;
}

// ============================================================================
// TAB 1: AUTONOMOUS AGENT WORKSPACE (OPENMANUS + KODE + II-AGENT)
// ============================================================================
async function runAgentTask() {
    const input = document.getElementById("agentPromptInput");
    const goal = input.value.trim();
    if (!goal) return;

    addChatMessage("user", goal);
    input.value = "";

    const btn = document.getElementById("btnRunTask");
    btn.disabled = true;
    btn.innerText = "Thinking & Planning...";

    const timeline = document.getElementById("planTimeline");
    timeline.innerHTML = `<div class="step-item in_progress"><span>⏳</span><span>Analyzing goal: "${goal}"</span></div>`;

    try {
        const resp = await fetch("/api/agent/task", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ goal, session_id: "default" })
        });
        const data = await resp.json();

        // Render plan steps
        timeline.innerHTML = "";
        if (data.steps && data.steps.length) {
            data.steps.forEach(s => {
                const stepEl = document.createElement("div");
                stepEl.className = `step-item ${s.status}`;
                stepEl.innerHTML = `
                    <span class="step-badge">${s.status === 'completed' ? '✓' : '•'} Step ${s.step_id}</span>
                    <div style="flex:1;">
                        <div style="font-weight:600;">${s.title}</div>
                        ${s.tool_name ? `<div style="font-size:0.72rem;color:var(--text-muted);">Tool: <code>${s.tool_name}</code></div>` : ''}
                        ${s.result ? `<div style="font-size:0.75rem;color:var(--accent-cyan);margin-top:2px;">${s.result.substring(0, 150)}</div>` : ''}
                    </div>
                `;
                timeline.appendChild(stepEl);
            });
        }

        addChatMessage("assistant", data.summary || "Task executed successfully.");
    } catch (err) {
        addChatMessage("assistant", `Error running task: ${err.message}`);
    } finally {
        btn.disabled = false;
        btn.innerText = "Execute ReAct Agent";
    }
}

function updateTimelineStep(payload) {
    // Dynamically highlights timeline during execution
}

function addChatMessage(role, text) {
    const container = document.getElementById("chatHistory");
    if (!container) return;
    const msg = document.createElement("div");
    msg.className = `message-bubble message-${role}`;
    msg.innerHTML = text.replace(/\n/g, "<br>");
    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;
}

// ============================================================================
// TAB 2: QWEN3-TTS & AUDIOBOOK STUDIO
// ============================================================================
async function loadVoices() {
    try {
        const resp = await fetch("/api/audio/voices");
        const voices = await resp.json();

        const selects = [
            document.getElementById("ttsSpeakerSelect"),
            document.getElementById("narratorVoiceSelect"),
            document.getElementById("dialogueVoiceSelect"),
            document.getElementById("duplexSpeakerSelect")
        ];

        selects.forEach(sel => {
            if (!sel) return;
            sel.innerHTML = "";
            voices.forEach(v => {
                const opt = document.createElement("option");
                opt.value = v.name;
                opt.innerText = `${v.name} (${v.gender}, ${v.language}) - ${v.description.substring(0, 40)}...`;
                sel.appendChild(opt);
            });
        });

        // Set good defaults
        const sSelect = document.getElementById("ttsSpeakerSelect");
        if (sSelect) sSelect.value = "Ryan";
        const nSelect = document.getElementById("narratorVoiceSelect");
        if (nSelect) nSelect.value = "Ryan";
        const dSelect = document.getElementById("dialogueVoiceSelect");
        if (dSelect) dSelect.value = "Vivian";
    } catch (e) {
        console.error("Failed to load voices", e);
    }
}

async function generateSpeech() {
    const text = document.getElementById("ttsTextInput").value.trim();
    if (!text) return alert("Please enter text to synthesize.");

    const speaker = document.getElementById("ttsSpeakerSelect").value;
    const language = document.getElementById("ttsLanguageSelect").value;
    const instruct = document.getElementById("ttsInstructInput").value.trim();
    const speed = parseFloat(document.getElementById("ttsSpeedSlider").value || "1.0");

    const btn = document.getElementById("btnSynthesize");
    btn.disabled = true;
    btn.innerText = "Synthesizing...";

    try {
        const resp = await fetch("/api/audio/synthesize", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text, speaker, language, instruct, speed })
        });
        const data = await resp.json();
        if (data.url) {
            playAudio(data.url, text);
            document.getElementById("audioDownloadLink").href = data.url;
            document.getElementById("audioDownloadLink").style.display = "inline-flex";
        }
    } catch (err) {
        alert("Synthesis error: " + err.message);
    } finally {
        btn.disabled = false;
        btn.innerText = "Generate Speech (Qwen3-TTS)";
    }
}

async function cloneVoice() {
    const name = document.getElementById("cloneVoiceName").value.trim();
    const fileInput = document.getElementById("cloneAudioFile");
    if (!name || !fileInput.files.length) return alert("Please specify a voice name and select an audio sample.");

    const formData = new FormData();
    formData.append("name", name);
    formData.append("reference_audio", fileInput.files[0]);

    const statusEl = document.getElementById("cloneStatus");
    statusEl.innerText = "Extracting acoustic timbre & registering clone profile...";

    try {
        const resp = await fetch("/api/audio/clone", {
            method: "POST",
            body: formData
        });
        const data = await resp.json();
        if (data.success) {
            statusEl.innerText = `✓ Voice "${name}" registered successfully! Added to speaker dropdowns.`;
            await loadVoices();
        }
    } catch (e) {
        statusEl.innerText = "Cloning failed: " + e.message;
    }
}

async function designVoice() {
    const prompt = document.getElementById("designVoicePrompt").value.trim();
    if (!prompt) return alert("Please describe the voice.");

    const statusEl = document.getElementById("designStatus");
    statusEl.innerText = "Analyzing prompt & generating acoustic profile...";

    try {
        const resp = await fetch("/api/audio/design", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt })
        });
        const data = await resp.json();
        if (data.success) {
            statusEl.innerText = `✓ Voice Profile created: ${data.voice.name} (${data.voice.gender}, Base Pitch: ${data.voice.base_pitch_hz.toFixed(1)}Hz)`;
            document.getElementById("ttsSpeakerSelect").value = "Ryan";
        }
    } catch (e) {
        statusEl.innerText = "Voice design failed: " + e.message;
    }
}

async function startAudiobookConversion() {
    const fileInput = document.getElementById("audiobookFileInput");
    const title = document.getElementById("audiobookTitleInput").value.trim() || "My Audiobook";
    const narrator = document.getElementById("narratorVoiceSelect").value;
    const dialogue = document.getElementById("dialogueVoiceSelect").value;

    if (!fileInput.files.length) return alert("Please upload a PDF, EPUB, DOCX, or TXT file.");

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    formData.append("title", title);
    formData.append("narrator", narrator);
    formData.append("dialogue", dialogue);

    const progressBox = document.getElementById("audiobookProgressBox");
    const progressBar = document.getElementById("audiobookProgressBar");
    const progressText = document.getElementById("audiobookProgressText");
    const downloadBox = document.getElementById("audiobookDownloadBox");

    progressBox.style.display = "block";
    downloadBox.style.display = "none";
    progressText.innerText = "Parsing document structure & detecting chapters...";

    try {
        const resp = await fetch("/api/audio/audiobook/upload", {
            method: "POST",
            body: formData
        });
        const data = await resp.json();
        const jobId = data.job_id;

        // Poll conversion status
        const pollInterval = setInterval(async () => {
            try {
                const statResp = await fetch(`/api/audio/audiobook/jobs/${jobId}`);
                const stat = await statResp.json();

                progressBar.style.width = `${stat.progress_percent}%`;
                progressText.innerText = `Synthesizing Chunks: ${stat.completed_chunks} / ${stat.total_chunks} (${stat.progress_percent}%)`;

                if (stat.status === "completed") {
                    clearInterval(pollInterval);
                    progressText.innerText = `✓ Complete! Converted ${stat.total_chunks} dramatized sentences.`;
                    downloadBox.style.display = "block";
                    const btnDl = document.getElementById("audiobookDownloadBtn");
                    btnDl.href = stat.download_url;
                } else if (stat.status === "failed") {
                    clearInterval(pollInterval);
                    progressText.innerText = `Failed: ${stat.error}`;
                }
            } catch (err) {
                console.error("Poll error", err);
            }
        }, 800);

    } catch (e) {
        progressText.innerText = "Upload failed: " + e.message;
    }
}

function playAudio(url, title) {
    if (activeAudio) {
        activeAudio.pause();
    }
    activeAudio = new Audio(url);
    activeAudio.play();
    document.getElementById("currentAudioTitle").innerText = `Playing: ${title.substring(0, 45)}...`;
    drawSimulatedWaveform();
}

function initWaveformCanvas() {
    const canvas = document.getElementById("waveformCanvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "#1e293b";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
}

function drawSimulatedWaveform() {
    const canvas = document.getElementById("waveformCanvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const w = canvas.width;
    const h = canvas.height;

    let frame = 0;
    const interval = setInterval(() => {
        if (!activeAudio || activeAudio.paused) {
            clearInterval(interval);
            return;
        }
        ctx.fillStyle = "#0a0e17";
        ctx.fillRect(0, 0, w, h);

        const bars = 48;
        const barWidth = (w / bars) - 2;
        ctx.fillStyle = "#38bdf8";

        for (let i = 0; i < bars; i++) {
            const barHeight = Math.sin((i + frame) * 0.3) * 20 + 25 + Math.random() * 8;
            ctx.fillRect(i * (barWidth + 2), (h - barHeight) / 2, barWidth, barHeight);
        }
        frame++;
    }, 50);
}

// ============================================================================
// TAB 3: FULL-DUPLEX VOICE AGENT
// ============================================================================
async function sendDuplexMessage() {
    const input = document.getElementById("duplexTextInput");
    const text = input.value.trim();
    if (!text) return;

    input.value = "";
    addDuplexBubble("user", text);

    const speaker = document.getElementById("duplexSpeakerSelect").value;
    const statusEl = document.getElementById("duplexStatus");
    statusEl.innerText = "Agent reasoning & synthesizing speech reply...";

    try {
        const resp = await fetch("/api/agent/voice_turn", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text, speaker })
        });
        const data = await resp.json();

        addDuplexBubble("assistant", data.assistant_text);
        statusEl.innerText = "Ready. Voice response playing.";

        if (data.audio_url) {
            playAudio(data.audio_url, data.assistant_text);
        }
    } catch (e) {
        statusEl.innerText = "Error: " + e.message;
    }
}

function addDuplexBubble(role, text) {
    const container = document.getElementById("duplexChatHistory");
    if (!container) return;
    const msg = document.createElement("div");
    msg.className = `message-bubble message-${role}`;
    msg.innerHTML = text.replace(/\n/g, "<br>");
    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;
}

function toggleVoiceRecord() {
    const btn = document.getElementById("btnRecordVoice");
    if (!isRecording) {
        // Start recording
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            alert("Microphone access is not supported in this browser context.");
            return;
        }
        navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
            mediaRecorder = new MediaRecorder(stream);
            recordedAudioChunks = [];
            mediaRecorder.ondataavailable = e => recordedAudioChunks.push(e.data);
            mediaRecorder.onstop = () => {
                // For demo/duplex turn, ask agent directly
                document.getElementById("duplexTextInput").value = "Привет! Расскажи о возможностях OmniNexus AI на русском.";
                sendDuplexMessage();
            };
            mediaRecorder.start();
            isRecording = true;
            btn.innerText = "🔴 Listening... Click to Stop";
            btn.classList.add("btn-danger");
        }).catch(err => {
            alert("Microphone permission denied: " + err.message);
        });
    } else {
        // Stop recording
        if (mediaRecorder) mediaRecorder.stop();
        isRecording = false;
        btn.innerText = "🎤 Hold / Click to Speak";
        btn.classList.remove("btn-danger");
    }
}

// ============================================================================
// TAB 4: ANDROID COMMANDER & ROOT HUB (AWESOME-ANDROID-ROOT)
// ============================================================================
async function loadDevices() {
    try {
        const resp = await fetch("/api/android/devices");
        const devices = await resp.json();
        const sel = document.getElementById("androidDeviceSelect");
        if (!sel) return;
        sel.innerHTML = "";
        devices.forEach(d => {
            const opt = document.createElement("option");
            opt.value = d.serial;
            opt.innerText = `${d.model} [${d.serial}] - ${d.status}`;
            sel.appendChild(opt);
        });
    } catch (e) {
        console.error("Device list error", e);
    }
}

async function refreshAndroidScreenshot() {
    try {
        const resp = await fetch("/api/android/screenshot");
        const data = await resp.json();
        if (data.screenshot_base64) {
            const img = document.getElementById("androidScreenImg");
            if (img) img.src = `data:image/png;base64,${data.screenshot_base64}`;
        }
    } catch (e) {
        console.error("Screenshot error", e);
    }
}

async function handleScreenClick(event) {
    const img = event.target;
    const rect = img.getBoundingClientRect();
    const clickX = event.clientX - rect.left;
    const clickY = event.clientY - rect.top;

    // Normalize to device resolution (e.g. 400x800)
    const normX = Math.round((clickX / rect.width) * 400);
    const normY = Math.round((clickY / rect.height) * 800);

    appendFeed("progress", `[ANDROID] Screen Tap at coordinates (${normX}, ${normY})`);

    try {
        await fetch("/api/android/tap", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ x: normX, y: normY })
        });
        await refreshAndroidScreenshot();
    } catch (e) {
        console.error("Tap error", e);
    }
}

async function sendAndroidKey(keycode) {
    try {
        await fetch("/api/android/key", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ keycode })
        });
        await refreshAndroidScreenshot();
    } catch (e) {
        console.error("Key error", e);
    }
}

async function sendAndroidText() {
    const input = document.getElementById("androidTextInput");
    const text = input.value.trim();
    if (!text) return;

    try {
        await fetch("/api/android/text", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text })
        });
        input.value = "";
        await refreshAndroidScreenshot();
    } catch (e) {
        console.error("Text error", e);
    }
}

async function runRootShellCommand() {
    const input = document.getElementById("rootShellInput");
    const command = input.value.trim();
    if (!command) return;

    const term = document.getElementById("rootShellOutput");
    term.innerText += `\n# ${command}\n`;

    try {
        const resp = await fetch("/api/android/shell", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ command, as_root: true })
        });
        const res = await resp.json();
        term.innerText += (res.stdout || res.error || "Done.") + "\n";
        term.scrollTop = term.scrollHeight;
        input.value = "";
        await refreshAndroidScreenshot();
    } catch (e) {
        term.innerText += `Error: ${e.message}\n`;
    }
}

async function loadPackages() {
    try {
        const resp = await fetch("/api/android/packages");
        const packages = await resp.json();
        const container = document.getElementById("packagesList");
        if (!container) return;
        container.innerHTML = "";

        packages.forEach(pkg => {
            const item = document.createElement("div");
            item.className = "step-item";
            item.style.justifyContent = "space-between";
            item.innerHTML = `
                <div>
                    <div style="font-weight:600;">${pkg.name}</div>
                    <div style="font-size:0.72rem;color:var(--text-muted);">${pkg.package}</div>
                </div>
                <div>
                    <button class="btn btn-secondary" style="font-size:0.72rem;padding:0.25rem 0.6rem;" onclick="togglePackage('${pkg.package}', ${!pkg.enabled})">
                        ${pkg.enabled ? '🚫 Debloat' : '✓ Enable'}
                    </button>
                </div>
            `;
            container.appendChild(item);
        });
    } catch (e) {
        console.error("Load packages error", e);
    }
}

async function togglePackage(pkgName, enable) {
    try {
        await fetch("/api/android/package/toggle", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ package: pkgName, enable })
        });
        await loadPackages();
        await refreshAndroidScreenshot();
    } catch (e) {
        console.error("Toggle package error", e);
    }
}

async function loadRootCatalog() {
    const search = document.getElementById("catalogSearchInput")?.value || "";
    const category = document.getElementById("catalogCategorySelect")?.value || "";

    try {
        const resp = await fetch(`/api/android/catalog?query=${encodeURIComponent(search)}&category=${encodeURIComponent(category)}`);
        const data = await resp.json();

        // Populate category dropdown once
        const catSelect = document.getElementById("catalogCategorySelect");
        if (catSelect && catSelect.children.length <= 1) {
            data.categories.forEach(cat => {
                const opt = document.createElement("option");
                opt.value = cat;
                opt.innerText = cat;
                catSelect.appendChild(opt);
            });
        }

        const grid = document.getElementById("rootCatalogGrid");
        if (!grid) return;
        grid.innerHTML = "";

        data.items.forEach(item => {
            const card = document.createElement("div");
            card.className = "card";
            card.innerHTML = `
                <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.4rem;">
                    <div style="font-weight:700;font-size:0.92rem;color:#fff;">${item.name}</div>
                    <span class="tag-pill" style="color:var(--accent-cyan);">${item.framework}</span>
                </div>
                <div style="font-size:0.75rem;color:var(--accent-amber);margin-bottom:0.4rem;">📁 ${item.category}</div>
                <div style="font-size:0.8rem;color:var(--text-secondary);margin-bottom:0.75rem;">${item.description}</div>
                ${item.github_url ? `<a href="${item.github_url}" target="_blank" class="btn btn-secondary" style="font-size:0.72rem;padding:0.25rem 0.6rem;">GitHub Repo ↗</a>` : ''}
            `;
            grid.appendChild(card);
        });
    } catch (e) {
        console.error("Root catalog error", e);
    }
}

// ============================================================================
// TAB 5: OPENCLAW ZERO-TOKEN & MODEL GATEWAY
// ============================================================================
async function loadModels() {
    try {
        const resp = await fetch("/api/gateway/models");
        const models = await resp.json();
        const sel = document.getElementById("gatewayModelSelect");
        if (!sel) return;
        sel.innerHTML = "";
        models.forEach(m => {
            const opt = document.createElement("option");
            opt.value = m.id;
            opt.innerText = `${m.name} (${m.provider}) - ZeroToken: ${m.zero_token_supported ? 'YES' : 'NO'}`;
            sel.appendChild(opt);
        });

        // Load sessions
        const sessResp = await fetch("/api/gateway/sessions");
        const sessions = await sessResp.json();
        const sessList = document.getElementById("zeroTokenSessionsList");
        if (!sessList) return;
        sessList.innerHTML = "";
        sessions.forEach(s => {
            const row = document.createElement("div");
            row.className = "step-item";
            row.style.justifyContent = "space-between";
            row.innerHTML = `
                <div>
                    <span style="font-weight:600;text-transform:uppercase;">${s.provider}</span>
                    <span style="font-size:0.72rem;color:var(--text-muted);margin-left:6px;">(${s.session_id})</span>
                </div>
                <div>
                    <span class="tag-pill" style="color:var(--accent-emerald);">● ${s.status}</span>
                    <span style="font-size:0.72rem;color:var(--text-muted);margin-left:8px;">${s.token_usage} tokens</span>
                </div>
            `;
            sessList.appendChild(row);
        });
    } catch (e) {
        console.error("Load models error", e);
    }
}

async function testModelPrompt() {
    const prompt = document.getElementById("gatewayPromptInput").value.trim();
    const model_id = document.getElementById("gatewayModelSelect").value;
    if (!prompt) return;

    const outEl = document.getElementById("gatewayResponseOutput");
    outEl.innerText = "Querying model via OpenClaw Gateway...";

    try {
        const resp = await fetch("/api/gateway/test", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt, model_id })
        });
        const data = await resp.json();
        outEl.innerText = `[Provider: ${data.provider_used} | Latency: ${data.latency_ms}ms]\n\n${data.content}`;
    } catch (e) {
        outEl.innerText = "Error: " + e.message;
    }
}

// ============================================================================
// TAB 6: COMFYUI & MCP HUB
// ============================================================================
async function exportWorkflow(type) {
    try {
        const resp = await fetch(`/api/comfyui/workflow/${type}`);
        const workflowJson = await resp.json();
        const blob = new Blob([JSON.stringify(workflowJson, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `comfyui_qwen3tts_${type}_workflow.json`;
        a.click();
    } catch (e) {
        alert("Export failed: " + e.message);
    }
}
