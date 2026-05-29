import os
import io
import json
import base64
import logging
import tempfile
from pathlib import Path

import fitz
from PIL import Image

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

import google.generativeai as genai


# ═══════════════════════════════════════════════════════════════
# CONFIG  — put your key here
# ═══════════════════════════════════════════════════════════════

GEMINI_API_KEY  = "AIzaSyAttRuQhQw3LfcFtug7Cjb6WiOi-uo2Rso"   # ← replace this
GEMINI_MODEL_ID = "gemini-3-flash-preview"            # change model here if needed

UPLOAD_TMP    = Path(tempfile.gettempdir()) / "gemini_uploads"
UPLOAD_TMP.mkdir(parents=True, exist_ok=True)

MAX_PDF_PAGES = 10
PDF_DPI_SCALE = 2
MAX_IMAGE_SIDE = 1600

ALLOWED_EXT = {"png", "jpg", "jpeg", "gif", "webp", "pdf"}

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# GEMINI INIT
# ═══════════════════════════════════════════════════════════════

genai.configure(api_key=GEMINI_API_KEY)
log.info("Gemini API configured with model: %s", GEMINI_MODEL_ID)


# ═══════════════════════════════════════════════════════════════
# FLASK APP
# ═══════════════════════════════════════════════════════════════

app = Flask(__name__)
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024


# ═══════════════════════════════════════════════════════════════
# HTML — served inline (no templates folder needed)
# ═══════════════════════════════════════════════════════════════

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>GeminiVision</title>
<link href="https://fonts.googleapis.com/css2?family=Clash+Display:wght@400;500;600;700&family=Instrument+Serif:ital@0;1&family=JetBrains+Mono:wght@300;400;500&display=swap" rel="stylesheet"/>
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg:       #f5f2eb;
  --cream:    #ede9df;
  --paper:    #faf8f3;
  --ink:      #1a1714;
  --ink2:     #3d3830;
  --muted:    #8a8278;
  --border:   #d8d2c4;
  --gem-blue: #1a73e8;
  --gem-red:  #ea4335;
  --gem-yell: #fbbc04;
  --gem-grn:  #34a853;
  --accent:   #1a73e8;
  --surface:  #ffffff;
  --shadow:   0 2px 16px rgba(26,23,20,0.08);
  --shadow-lg:0 8px 40px rgba(26,23,20,0.12);
  --r:        10px;
  --r-lg:     16px;
}

html, body { height: 100%; }
body {
  background: var(--bg);
  color: var(--ink);
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  line-height: 1.6;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

body::after {
  content: '';
  position: fixed; inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E");
  pointer-events: none; z-index: 9999; opacity: 0.5;
}

/* Header */
header {
  height: 56px; padding: 0 24px;
  display: flex; align-items: center; justify-content: space-between;
  border-bottom: 1px solid var(--border);
  background: var(--paper); flex-shrink: 0;
  position: relative; z-index: 10;
}

.logo { display: flex; align-items: center; gap: 10px; }
.gemini-mark { width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; }
.gemini-mark svg { width: 28px; height: 28px; }
.logo-text {
  font-family: 'Clash Display', sans-serif;
  font-weight: 600; font-size: 18px; letter-spacing: -0.5px; color: var(--ink);
}
.logo-text span { color: var(--gem-blue); }

.header-right { display: flex; align-items: center; gap: 10px; }

.status-badge {
  display: flex; align-items: center; gap: 6px;
  padding: 5px 14px; border-radius: 100px;
  border: 1px solid var(--gem-grn);
  font-size: 11px; color: var(--gem-grn);
  background: var(--surface);
}
.status-badge .dot { width: 6px; height: 6px; border-radius: 50%; background: var(--gem-grn); }

.model-tag {
  padding: 5px 12px; border-radius: 100px;
  border: 1px solid var(--border);
  font-size: 11px; color: var(--muted);
  background: var(--surface); font-family: 'JetBrains Mono', monospace;
}

/* Layout */
.app {
  display: grid; grid-template-columns: 380px 1fr;
  height: calc(100vh - 56px); overflow: hidden;
}

/* Left panel */
.left-panel {
  display: flex; flex-direction: column;
  border-right: 1px solid var(--border);
  background: var(--cream); overflow: hidden;
}
.panel-head {
  padding: 16px 20px 12px;
  border-bottom: 1px solid var(--border);
  background: var(--paper);
}
.panel-label {
  font-size: 9px; letter-spacing: 2px; text-transform: uppercase;
  color: var(--muted); font-family: 'Clash Display', sans-serif;
  font-weight: 500; margin-bottom: 10px;
}

/* Dropzone */
.dropzone {
  margin: 16px 20px;
  border: 2px dashed var(--border);
  border-radius: var(--r-lg);
  padding: 28px 20px; text-align: center; cursor: pointer;
  transition: all 0.2s; background: var(--surface); position: relative;
}
.dropzone:hover, .dropzone.drag-over {
  border-color: var(--gem-blue);
  background: rgba(26,115,232,0.03);
}
.dropzone input[type="file"] { position: absolute; inset: 0; opacity: 0; cursor: pointer; }
.drop-icon-row { display: flex; justify-content: center; gap: 8px; margin-bottom: 12px; }
.drop-type-icon {
  width: 36px; height: 36px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; border: 1px solid var(--border); background: var(--cream);
}
.drop-title {
  font-family: 'Clash Display', sans-serif; font-weight: 600;
  font-size: 14px; color: var(--ink); margin-bottom: 4px;
}
.drop-sub { font-size: 11px; color: var(--muted); }

/* Preview */
.preview-area {
  padding: 0 20px 16px;
  display: grid; grid-template-columns: repeat(2, 1fr);
  gap: 8px; overflow-y: auto; flex: 1;
}
.preview-card {
  border-radius: var(--r); overflow: hidden;
  border: 1px solid var(--border); background: var(--surface);
  position: relative; aspect-ratio: 4/3; cursor: pointer;
  transition: all 0.15s; animation: popIn 0.2s ease;
}
@keyframes popIn {
  from { opacity: 0; transform: scale(0.95); }
  to   { opacity: 1; transform: scale(1); }
}
.preview-card:hover { border-color: var(--gem-blue); box-shadow: var(--shadow); }
.preview-card img { width: 100%; height: 100%; object-fit: cover; }
.preview-card .remove-btn {
  position: absolute; top: 5px; right: 5px;
  width: 20px; height: 20px; border-radius: 50%;
  background: rgba(26,23,20,0.7); color: #fff; border: none;
  font-size: 11px; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  opacity: 0; transition: opacity 0.15s;
}
.preview-card:hover .remove-btn { opacity: 1; }
.preview-card .card-label {
  position: absolute; bottom: 0; left: 0; right: 0;
  padding: 5px 8px;
  background: linear-gradient(transparent, rgba(26,23,20,0.7));
  color: #fff; font-size: 10px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.pdf-card {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: 6px; background: var(--cream);
}
.pdf-card .pdf-icon { font-size: 28px; }
.pdf-card .pdf-name {
  font-size: 10px; color: var(--ink2); text-align: center;
  padding: 0 6px; overflow: hidden; text-overflow: ellipsis;
  white-space: nowrap; width: 100%;
}

/* Presets */
.presets-section {
  border-top: 1px solid var(--border);
  padding: 12px 20px; background: var(--paper);
  overflow-y: auto; max-height: 210px; flex-shrink: 0;
}
.presets-grid { display: flex; flex-wrap: wrap; gap: 6px; }
.preset-chip {
  padding: 5px 11px; border-radius: 100px;
  border: 1px solid var(--border); background: var(--surface);
  color: var(--ink2); font-family: 'JetBrains Mono', monospace;
  font-size: 11px; cursor: pointer; transition: all 0.15s; white-space: nowrap;
}
.preset-chip:hover {
  border-color: var(--gem-blue); color: var(--gem-blue);
  background: rgba(26,115,232,0.05);
}

/* Right panel */
.right-panel { display: flex; flex-direction: column; background: var(--bg); overflow: hidden; }

.chat-area {
  flex: 1; overflow-y: auto; padding: 28px 40px;
  display: flex; flex-direction: column; gap: 24px;
}
.chat-area::-webkit-scrollbar { width: 4px; }
.chat-area::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

/* Empty state */
.empty-state {
  margin: auto; max-width: 460px; text-align: center;
  animation: fadeUp 0.5s ease;
}
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}
.empty-gem { margin: 0 auto 20px; width: 64px; height: 64px; }
.empty-title {
  font-family: 'Clash Display', sans-serif; font-weight: 700;
  font-size: 26px; color: var(--ink); margin-bottom: 10px; letter-spacing: -0.5px;
}
.empty-sub {
  font-family: 'Instrument Serif', serif; font-style: italic;
  color: var(--muted); font-size: 15px; line-height: 1.7;
}
.capability-row {
  display: flex; justify-content: center; gap: 10px; margin-top: 20px; flex-wrap: wrap;
}
.cap-badge {
  padding: 6px 14px; border-radius: 100px; font-size: 11px;
  border: 1px solid var(--border); color: var(--ink2); background: var(--surface);
}

/* Messages */
.msg { display: flex; gap: 14px; animation: fadeUp 0.25s ease; }
.msg.user { flex-direction: row-reverse; align-self: flex-end; max-width: 85%; }
.msg.assistant { align-self: flex-start; max-width: 88%; }
.msg-avatar {
  width: 32px; height: 32px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; flex-shrink: 0;
  border: 1px solid var(--border); background: var(--surface);
}
.msg-body { flex: 1; min-width: 0; }
.msg-thumbs { display: flex; gap: 6px; margin-bottom: 6px; flex-wrap: wrap; }
.msg-thumb { width: 60px; height: 44px; border-radius: 6px; overflow: hidden; border: 1px solid var(--border); }
.msg-thumb img { width: 100%; height: 100%; object-fit: cover; }
.msg-bubble { padding: 14px 18px; border-radius: var(--r-lg); line-height: 1.75; font-size: 13.5px; }
.msg.user .msg-bubble {
  background: var(--ink); color: #f5f2eb;
  border-radius: var(--r-lg) 4px var(--r-lg) var(--r-lg);
  font-family: 'JetBrains Mono', monospace;
}
.msg.assistant .msg-bubble {
  background: var(--surface); border: 1px solid var(--border); color: var(--ink);
  border-radius: 4px var(--r-lg) var(--r-lg) var(--r-lg);
  font-family: 'Instrument Serif', serif; font-size: 15px; box-shadow: var(--shadow);
}
.msg-meta {
  font-size: 10px; color: var(--muted); margin-top: 6px;
  font-family: 'JetBrains Mono', monospace; display: flex; gap: 10px;
}
.meta-model { display: inline-flex; align-items: center; gap: 4px; }
.gemini-star { display: inline-block; width: 8px; height: 8px; border-radius: 50%; }

/* Typing */
.typing-dots { display: flex; gap: 5px; align-items: center; height: 20px; padding: 0 4px; }
.typing-dots span {
  width: 7px; height: 7px; border-radius: 50%;
  animation: td 1.2s ease-in-out infinite;
}
.typing-dots span:nth-child(1) { background: var(--gem-blue);  animation-delay: 0s; }
.typing-dots span:nth-child(2) { background: var(--gem-red);   animation-delay: 0.15s; }
.typing-dots span:nth-child(3) { background: var(--gem-yell);  animation-delay: 0.3s; }
.typing-dots span:nth-child(4) { background: var(--gem-grn);   animation-delay: 0.45s; }
@keyframes td {
  0%, 70%, 100% { opacity: 0.3; transform: translateY(0); }
  35%            { opacity: 1;   transform: translateY(-5px); }
}

/* Input area */
.input-area {
  padding: 16px 40px 20px; border-top: 1px solid var(--border);
  background: var(--paper); flex-shrink: 0;
}
.input-box {
  display: flex; gap: 10px; align-items: flex-end;
  background: var(--surface); border: 1.5px solid var(--border);
  border-radius: var(--r-lg); padding: 10px 14px;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.input-box:focus-within {
  border-color: var(--gem-blue);
  box-shadow: 0 0 0 3px rgba(26,115,232,0.08);
}
textarea#prompt {
  flex: 1; background: transparent; border: none; outline: none;
  color: var(--ink); font-family: 'JetBrains Mono', monospace;
  font-size: 13px; resize: none; min-height: 24px; max-height: 120px; line-height: 1.5;
}
textarea#prompt::placeholder { color: var(--muted); }
.send-btn {
  width: 38px; height: 38px; border-radius: 10px; border: none; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; transition: all 0.2s; flex-shrink: 0;
  background: var(--ink); color: var(--bg);
}
.send-btn:hover { background: var(--gem-blue); transform: translateY(-1px); }
.send-btn:active { transform: translateY(0); }
.send-btn:disabled { opacity: 0.3; cursor: not-allowed; transform: none; }
.input-hint { text-align: center; margin-top: 8px; font-size: 10px; color: var(--muted); }

/* Toast */
#toast {
  position: fixed; bottom: 24px; right: 24px; z-index: 999;
  padding: 10px 18px; border-radius: var(--r); font-size: 12px;
  border: 1px solid var(--border); background: var(--paper); box-shadow: var(--shadow);
  opacity: 0; transform: translateY(6px); transition: all 0.22s ease; pointer-events: none;
}
#toast.show { opacity: 1; transform: translateY(0); }
#toast.success { border-color: var(--gem-grn); color: var(--gem-grn); }
#toast.error   { border-color: var(--gem-red);  color: var(--gem-red); }
#toast.info    { border-color: var(--gem-blue); color: var(--gem-blue); }

@media (max-width: 768px) {
  .app { grid-template-columns: 1fr; }
  .left-panel { display: none; }
  .chat-area { padding: 16px; }
  .input-area { padding: 12px 16px; }
}
</style>
</head>
<body>

<header>
  <div class="logo">
    <div class="gemini-mark">
      <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2C12 2 9.5 8 2 12C9.5 16 12 22 12 22C12 22 14.5 16 22 12C14.5 8 12 2 12 2Z"
          fill="url(#ggrad)"/>
        <defs>
          <linearGradient id="ggrad" x1="2" y1="2" x2="22" y2="22" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stop-color="#4285f4"/>
            <stop offset="33%" stop-color="#ea4335"/>
            <stop offset="66%" stop-color="#fbbc04"/>
            <stop offset="100%" stop-color="#34a853"/>
          </linearGradient>
        </defs>
      </svg>
    </div>
    <div class="logo-text">Gemini<span>Vision</span></div>
  </div>
  <div class="header-right">
    <div class="model-tag" id="model-tag">loading…</div>
    <div class="status-badge">
      <div class="dot"></div>
      <span>Connected</span>
    </div>
  </div>
</header>

<div class="app">
  <aside class="left-panel">
    <div class="panel-head">
      <div class="panel-label">Media Input</div>
      <div class="dropzone" id="dropzone">
        <input type="file" id="file-input" multiple accept=".pdf,.png,.jpg,.jpeg,.gif,.webp"/>
        <div class="drop-icon-row">
          <div class="drop-type-icon">🖼️</div>
          <div class="drop-type-icon">📄</div>
          <div class="drop-type-icon">📊</div>
        </div>
        <div class="drop-title">Drop files here</div>
        <div class="drop-sub">Images, PDFs, Charts · up to 50 MB</div>
      </div>
    </div>
    <div class="preview-area" id="preview-area"></div>
    <div class="presets-section">
      <div class="panel-label">Quick Prompts</div>
      <div class="presets-grid" id="presets-grid"></div>
    </div>
  </aside>

  <main class="right-panel">
    <div class="chat-area" id="chat-area">
      <div class="empty-state" id="empty-state">
        <div class="empty-gem">
          <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M32 4C32 4 24 22 4 32C24 42 32 60 32 60C32 60 40 42 60 32C40 22 32 4 32 4Z"
              fill="url(#eg)"/>
            <defs>
              <linearGradient id="eg" x1="4" y1="4" x2="60" y2="60" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stop-color="#4285f4"/>
                <stop offset="33%" stop-color="#ea4335"/>
                <stop offset="66%" stop-color="#fbbc04"/>
                <stop offset="100%" stop-color="#34a853"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <div class="empty-title">See beyond text</div>
        <div class="empty-sub">
          Upload images, PDFs, charts, handwritten notes —<br/>
          then ask Gemini anything about what it sees.
        </div>
        <div class="capability-row">
          <span class="cap-badge">📋 Document analysis</span>
          <span class="cap-badge">🔬 Medical reports</span>
          <span class="cap-badge">📊 Chart reading</span>
          <span class="cap-badge">✍️ Handwriting OCR</span>
          <span class="cap-badge">🧾 Invoice extraction</span>
        </div>
      </div>
    </div>
    <div class="input-area">
      <div class="input-box">
        <textarea id="prompt" rows="1"
          placeholder="Ask Gemini about your images or documents…"></textarea>
        <button class="send-btn" id="send-btn" onclick="send()" title="Send">➤</button>
      </div>
      <div class="input-hint">Enter to send · Shift+Enter for new line · Paste images directly</div>
    </div>
  </main>
</div>

<div id="toast"></div>

<script>
const API = '';   // same origin — no port needed

let mediaFiles = [];

async function init() {
  setupTextarea();
  setupPaste();
  await loadPresets();
  await loadModelInfo();
}

async function loadModelInfo() {
  try {
    const r = await fetch(`${API}/api/model`);
    const d = await r.json();
    document.getElementById('model-tag').textContent = d.label || d.id;
  } catch {
    document.getElementById('model-tag').textContent = 'Gemini';
  }
}

async function loadPresets() {
  try {
    const r = await fetch(`${API}/api/presets`);
    const d = await r.json();
    const grid = document.getElementById('presets-grid');
    grid.innerHTML = d.presets.map(p =>
      `<button class="preset-chip" onclick="usePreset(this)" data-prompt="${escHtml(p.prompt)}">${p.label}</button>`
    ).join('');
  } catch {}
}

function usePreset(btn) {
  const ta = document.getElementById('prompt');
  ta.value = btn.dataset.prompt;
  ta.dispatchEvent(new Event('input'));
}

/* File handling */
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('file-input');

dropzone.addEventListener('dragover', e => { e.preventDefault(); dropzone.classList.add('drag-over'); });
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag-over'));
dropzone.addEventListener('drop', e => { e.preventDefault(); dropzone.classList.remove('drag-over'); addFiles(e.dataTransfer.files); });
fileInput.addEventListener('change', () => { addFiles(fileInput.files); fileInput.value = ''; });

function setupPaste() {
  document.addEventListener('paste', e => {
    const items = e.clipboardData?.items;
    if (!items) return;
    for (const item of items) {
      if (item.type.startsWith('image/')) { const f = item.getAsFile(); if (f) addFiles([f]); }
    }
  });
}

async function addFiles(files) {
  for (const file of files) {
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['pdf','png','jpg','jpeg','gif','webp'].includes(ext)) continue;
    const b64 = await toBase64(file);
    const isImg = ext !== 'pdf';
    mediaFiles.push({ file, b64: b64.split(',')[1], mimeType: isImg ? file.type : 'application/pdf', label: file.name, isImg });
    renderPreview(mediaFiles[mediaFiles.length - 1], mediaFiles.length - 1);
  }
}

function toBase64(file) {
  return new Promise((res, rej) => {
    const r = new FileReader();
    r.onload = () => res(r.result);
    r.onerror = () => rej(new Error('read fail'));
    r.readAsDataURL(file);
  });
}

function renderPreview(item, idx) {
  const area = document.getElementById('preview-area');
  const div  = document.createElement('div');
  div.className = 'preview-card' + (item.isImg ? '' : ' pdf-card');
  div.dataset.idx = idx;
  if (item.isImg) {
    div.innerHTML = `
      <img src="data:${item.mimeType};base64,${item.b64}" alt="${escHtml(item.label)}"/>
      <button class="remove-btn" onclick="removeFile(${idx},this.closest('.preview-card'))">✕</button>
      <div class="card-label">${escHtml(item.label)}</div>`;
  } else {
    div.innerHTML = `
      <div class="pdf-icon">📄</div>
      <div class="pdf-name">${escHtml(item.label)}</div>
      <button class="remove-btn" style="position:absolute;top:5px;right:5px;opacity:1"
        onclick="removeFile(${idx},this.closest('.preview-card'))">✕</button>`;
  }
  area.appendChild(div);
}

function removeFile(idx, card) { mediaFiles.splice(idx, 1); card.remove(); }

/* Send */
async function send() {
  const ta = document.getElementById('prompt');
  const prompt = ta.value.trim();
  if (!prompt) return;

  document.getElementById('empty-state')?.remove();
  ta.value = ''; ta.style.height = '';

  const snapshotMedia = [...mediaFiles];
  const thumbsHtml = snapshotMedia.filter(m => m.isImg).slice(0, 4)
    .map(m => `<div class="msg-thumb"><img src="data:${m.mimeType};base64,${m.b64}"/></div>`).join('');

  appendMsg('user', prompt, thumbsHtml, null);
  const typingEl = appendTyping();
  document.getElementById('send-btn').disabled = true;

  try {
    const formData = new FormData();
    formData.append('prompt', prompt);
    for (const item of snapshotMedia) formData.append('files', item.file);

    const r = await fetch(`${API}/api/analyze`, { method: 'POST', body: formData });
    const d = await r.json();
    typingEl.remove();

    if (d.error) {
      appendMsg('assistant', `⚠️ ${d.error}`, '', null);
    } else {
      appendMsg('assistant', d.answer, '', d.model, d.files_processed);
    }
  } catch (e) {
    typingEl.remove();
    appendMsg('assistant', '⚠️ Could not reach backend.', '', null);
  }

  document.getElementById('send-btn').disabled = false;
}

function appendMsg(role, text, thumbsHtml, model, filesCount) {
  const area = document.getElementById('chat-area');
  const div  = document.createElement('div');
  div.className = `msg ${role}`;
  const avatar  = role === 'user' ? '👤' : '✦';
  const timeStr = new Date().toLocaleTimeString([], { hour:'2-digit', minute:'2-digit' });
  const metaExtra = (model && role === 'assistant')
    ? `<span class="meta-model"><span class="gemini-star" style="background:linear-gradient(135deg,#4285f4,#34a853)"></span>${model}</span>` : '';
  const filesInfo = filesCount ? `· ${filesCount} file(s) analyzed` : '';
  div.innerHTML = `
    <div class="msg-avatar">${avatar}</div>
    <div class="msg-body">
      ${thumbsHtml ? `<div class="msg-thumbs">${thumbsHtml}</div>` : ''}
      <div class="msg-bubble">${escHtml(text).replace(/\\n/g,'<br/>')}</div>
      <div class="msg-meta"><span>${timeStr}</span>${metaExtra}<span>${filesInfo}</span></div>
    </div>`;
  area.appendChild(div);
  area.scrollTop = area.scrollHeight;
  return div;
}

function appendTyping() {
  const area = document.getElementById('chat-area');
  const div  = document.createElement('div');
  div.className = 'msg assistant';
  div.innerHTML = `
    <div class="msg-avatar">✦</div>
    <div class="msg-body">
      <div class="msg-bubble">
        <div class="typing-dots"><span></span><span></span><span></span><span></span></div>
      </div>
    </div>`;
  area.appendChild(div);
  area.scrollTop = area.scrollHeight;
  return div;
}

function setupTextarea() {
  const ta = document.getElementById('prompt');
  ta.addEventListener('input', () => { ta.style.height = 'auto'; ta.style.height = Math.min(ta.scrollHeight, 120) + 'px'; });
  ta.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } });
}

let _tt;
function showToast(msg, type = 'info') {
  const t = document.getElementById('toast');
  t.textContent = msg; t.className = `show ${type}`;
  if (_tt) clearTimeout(_tt);
  _tt = setTimeout(() => { t.className = ''; }, 3200);
}

function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

init();
</script>
</body>
</html>"""


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


def resize_image(img: Image.Image, max_side=MAX_IMAGE_SIDE):
    w, h = img.size
    if max(w, h) <= max_side:
        return img
    scale = max_side / max(w, h)
    return img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)


def image_to_base64(img: Image.Image):
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return base64.b64encode(buf.getvalue()).decode()


def pdf_to_images(pdf_path: str):
    doc   = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        if i >= MAX_PDF_PAGES:
            break
        mat = fitz.Matrix(PDF_DPI_SCALE, PDF_DPI_SCALE)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img = resize_image(img)
        pages.append({"page": i + 1, "b64": image_to_base64(img), "mime_type": "image/jpeg"})
    doc.close()
    return pages


def build_parts(files_data, prompt):
    parts = []
    for item in files_data:
        parts.append({"text": f"[File: {item['label']}]"})
        parts.append({"inline_data": {"mime_type": item["mime_type"], "data": item["b64"]}})
    parts.append({"text": prompt})
    return parts


# ═══════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════

@app.route("/")
def home():
    return INDEX_HTML, 200, {"Content-Type": "text/html; charset=utf-8"}


@app.route("/api/model", methods=["GET"])
def get_model():
    labels = {
        "gemini-2.0-flash":  "Gemini 2.0 Flash ⚡",
        "gemini-1.5-pro":    "Gemini 1.5 Pro 🧠",
        "gemini-1.5-flash":  "Gemini 1.5 Flash ✦",
    }
    return jsonify({
        "id":    GEMINI_MODEL_ID,
        "label": labels.get(GEMINI_MODEL_ID, GEMINI_MODEL_ID),
    })


@app.route("/api/presets", methods=["GET"])
def presets():
    return jsonify({"presets": [
        {"label": "Extract all text",    "prompt": "Extract all visible text from this document."},
        {"label": "Patient details",     "prompt": "Extract patient name, age, gender and ID."},
        {"label": "Invoice amount",      "prompt": "What is the total bill amount?"},
        {"label": "Diagnosis",           "prompt": "What diagnosis or findings are mentioned?"},
        {"label": "Document summary",    "prompt": "Summarize this document."},
        {"label": "Handwriting OCR",     "prompt": "Transcribe handwritten text."},
    ]})


@app.route("/api/analyze", methods=["POST"])
def analyze():
    prompt = request.form.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "prompt required"}), 400

    files_data    = []
    uploaded_files = request.files.getlist("files")

    for f in uploaded_files:
        if not f or not f.filename:
            continue
        if not allowed(f.filename):
            continue
        filename = secure_filename(f.filename)
        ext      = filename.rsplit(".", 1)[1].lower()
        tmp_path = str(UPLOAD_TMP / filename)
        f.save(tmp_path)

        if ext == "pdf":
            for p in pdf_to_images(tmp_path):
                files_data.append({"b64": p["b64"], "mime_type": "image/jpeg",
                                    "label": f"{filename} page {p['page']}"})
            log.info("PDF processed: %s", filename)
        else:
            img  = Image.open(tmp_path)
            img  = resize_image(img)
            mime = "image/jpeg" if ext == "jpg" else f"image/{ext}"
            files_data.append({"b64": image_to_base64(img), "mime_type": mime, "label": filename})
            log.info("Image processed: %s", filename)

    model = genai.GenerativeModel(GEMINI_MODEL_ID)

    try:
        if files_data:
            content = [{"role": "user", "parts": build_parts(files_data, prompt)}]
        else:
            content = prompt

        response = model.generate_content(
            content,
            generation_config=genai.types.GenerationConfig(
                temperature=0.4,
                max_output_tokens=2048,
            ),
        )

        return jsonify({
            "answer":          response.text,
            "model":           GEMINI_MODEL_ID,
            "files_processed": len(files_data),
        })

    except Exception as e:
        log.error("Gemini Error: %s", str(e))
        return jsonify({"error": str(e)}), 500


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    log.info("🚀 Running on http://localhost:5001")
    app.run(host="0.0.0.0", port=5001, debug=True)