/**
 * 56 File Converter - Frontend Application Logic
 */

(function () {
  'use strict';

  // --- STATE ---
  const DEFAULT_CONVERSION_MAP = {
    "docx": ["pdf", "txt", "html"],
    "pdf": ["docx", "txt", "png", "jpg", "html"],
    "txt": ["pdf", "docx", "html"],
    "md": ["html", "pdf", "docx", "txt"],
    "html": ["pdf", "docx", "txt"],
    "jpg": ["png", "webp", "bmp", "gif", "tiff", "pdf", "ico"],
    "jpeg": ["png", "webp", "bmp", "gif", "tiff", "pdf", "ico"],
    "png": ["jpg", "webp", "bmp", "gif", "tiff", "pdf", "ico"],
    "webp": ["jpg", "png", "bmp", "gif", "tiff", "pdf", "ico"],
    "bmp": ["jpg", "png", "webp", "gif", "tiff", "pdf"],
    "tiff": ["jpg", "png", "webp", "bmp", "pdf"],
    "tif": ["jpg", "png", "webp", "bmp", "pdf"],
    "gif": ["png", "jpg", "webp"],
    "ico": ["png", "jpg", "webp"],
    "xlsx": ["csv", "json", "html", "pdf"],
    "csv": ["xlsx", "json", "html", "pdf"],
    "json": ["csv", "xlsx", "html"]
  };
  let conversionMap = Object.assign({}, DEFAULT_CONVERSION_MAP);
  let formatMetadata = {};
  let fileQueue = [];
  let nextQueueId = 1;
  let preferredDefaultTarget = null;

  // --- DOM ELEMENTS ---
  const htmlEl = document.documentElement;
  const themeToggleBtn = document.getElementById('themeToggle');
  const themeLabel = document.getElementById('themeLabel');
  const sunIcon = themeToggleBtn.querySelector('.sun-icon');
  const moonIcon = themeToggleBtn.querySelector('.moon-icon');

  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('fileInput');
  const fileQueueEl = document.getElementById('fileQueue');
  const queueList = document.getElementById('queueList');
  const queueCount = document.getElementById('queueCount');
  const convertAllBtn = document.getElementById('convertAllBtn');
  const downloadAllBtn = document.getElementById('downloadAllBtn');
  const clearAllBtn = document.getElementById('clearAllBtn');
  const shareBtn = document.getElementById('shareBtn');
  const toastContainer = document.getElementById('toastContainer');

  // --- 1. THEME MANAGEMENT ---
  function updateThemeUI(theme) {
    htmlEl.setAttribute('data-theme', theme);
    localStorage.setItem('56_theme', theme);
    if (theme === 'dark') {
      sunIcon.style.display = 'block';
      moonIcon.style.display = 'none';
      themeLabel.textContent = 'Light Mode';
    } else {
      sunIcon.style.display = 'none';
      moonIcon.style.display = 'block';
      themeLabel.textContent = 'Dark Mode';
    }
  }

  function initTheme() {
    const currentTheme = htmlEl.getAttribute('data-theme') || 'light';
    updateThemeUI(currentTheme);

    themeToggleBtn.addEventListener('click', () => {
      const active = htmlEl.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      updateThemeUI(active);
    });
  }

  // --- 2. TOAST NOTIFICATIONS ---
  function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = 'ℹ️';
    if (type === 'success') icon = '✅';
    if (type === 'error') icon = '⚠️';

    toast.innerHTML = `
      <span style="font-size: 1.1rem;">${icon}</span>
      <div style="flex:1;">${escapeHtml(message)}</div>
    `;

    toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => toast.remove(), 250);
    }, 4000);
  }

  // --- 3. FORMAT REGISTRY & UTILS ---
  function normalizeExt(ext) {
    if (!ext) return '';
    return ext.trim().toLowerCase().replace(/^\./, '');
  }

  function formatBytes(bytes, decimals = 1) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>"']/g, function (m) {
      return {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
      }[m];
    });
  }

  async function loadFormats() {
    try {
      const res = await fetch('/api/formats');
      const data = await res.json();
      conversionMap = data.conversion_map || {};
      formatMetadata = data.metadata || {};
    } catch (err) {
      console.warn('Could not fetch server formats list:', err);
    }
  }

  // --- 4. FILE QUEUE & DROPZONE ---
  function initDropzone() {
    dropzone.addEventListener('click', () => fileInput.click());

    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add('drag-active');
      }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove('drag-active');
      }, false);
    });

    dropzone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      const files = dt.files;
      handleFiles(files);
    });

    fileInput.addEventListener('change', (e) => {
      handleFiles(e.target.files);
      fileInput.value = ''; // reset so same file can be re-selected
    });
  }

  function getDefaultTarget(srcExt) {
    const ext = normalizeExt(srcExt);
    const defaults = {
      'docx': 'pdf',
      'pdf': 'docx',
      'jpg': 'png',
      'jpeg': 'png',
      'png': 'webp',
      'webp': 'png',
      'bmp': 'png',
      'tiff': 'jpg',
      'gif': 'png',
      'ico': 'png',
      'xlsx': 'csv',
      'csv': 'xlsx',
      'json': 'csv',
      'txt': 'pdf',
      'md': 'pdf',
      'html': 'pdf'
    };
    if (preferredDefaultTarget) {
      const pref = preferredDefaultTarget;
      preferredDefaultTarget = null;
      const validTargets = conversionMap[ext] || [];
      if (validTargets.includes(pref)) {
        return pref;
      }
    }
    return defaults[ext] || (conversionMap[ext] && conversionMap[ext][0]) || 'pdf';
  }

  function handleFiles(files) {
    if (!files || files.length === 0) return;

    let addedCount = 0;
    Array.from(files).forEach(file => {
      const ext = normalizeExt(file.name.split('.').pop());
      const targets = conversionMap[ext];

      if (!targets || targets.length === 0) {
        showToast(`Format '.${ext}' is not supported yet.`, 'error');
        return;
      }

      const defaultTgt = getDefaultTarget(ext);

      const queueItem = {
        id: nextQueueId++,
        file: file,
        name: file.name,
        size: file.size,
        ext: ext,
        targetFormat: defaultTgt,
        targets: targets,
        status: 'ready', // 'ready', 'converting', 'done', 'error'
        jobId: null,
        downloadUrl: null,
        convertedName: null,
        error: null,
        progress: 0
      };

      fileQueue.push(queueItem);
      addedCount++;
    });

    if (addedCount > 0) {
      renderQueue();
      showToast(`Added ${addedCount} file(s) to conversion queue.`, 'info');
    }
  }

  function renderQueue() {
    if (fileQueue.length === 0) {
      fileQueueEl.style.display = 'none';
      downloadAllBtn.style.display = 'none';
      return;
    }

    fileQueueEl.style.display = 'block';
    queueCount.textContent = `${fileQueue.length} ${fileQueue.length === 1 ? 'file' : 'files'}`;

    // Check if any completed items exist for ZIP download button
    const hasCompleted = fileQueue.some(item => item.status === 'done' && item.jobId);
    downloadAllBtn.style.display = hasCompleted ? 'inline-flex' : 'none';

    queueList.innerHTML = '';

    fileQueue.forEach(item => {
      const itemEl = document.createElement('div');
      itemEl.className = 'file-item';
      itemEl.id = `queue-item-${item.id}`;

      // Status pill HTML
      let statusHtml = `<span class="status-tag status-ready">Ready</span>`;
      if (item.status === 'converting') {
        statusHtml = `<span class="status-tag status-converting"><span class="spinner" style="width:12px;height:12px;border-width:2px;"></span> Converting...</span>`;
      } else if (item.status === 'done') {
        const remainingSec = Math.max(0, Math.ceil(((item.expiresAt || 0) - Date.now()) / 1000));
        statusHtml = `<span class="status-tag status-done">✓ Converted</span> <span class="countdown-badge" id="countdown-${item.id}">⏱️ Deletes in ${remainingSec}s</span>`;
      } else if (item.status === 'expired') {
        statusHtml = `<span class="status-tag status-expired">🗑️ Auto-deleted from server (100% Secure)</span>`;
      } else if (item.status === 'error') {
        statusHtml = `<span class="status-tag status-error" title="${escapeHtml(item.error || '')}">✕ Failed</span>`;
      }

      // Format select options
      const optionsHtml = item.targets.map(tgt => {
        const selected = tgt === item.targetFormat ? 'selected' : '';
        const meta = formatMetadata[tgt] || {};
        const label = meta.name ? `${tgt.toUpperCase()} (${meta.name})` : tgt.toUpperCase();
        return `<option value="${tgt}" ${selected}>${label}</option>`;
      }).join('');

      // Actions buttons
      let actionButtons = '';
      if (item.status === 'ready') {
        actionButtons = `
          <button class="btn btn-primary btn-sm convert-single-btn" data-id="${item.id}">
            Convert
          </button>
        `;
      } else if (item.status === 'done') {
        actionButtons = `
          <a href="${item.downloadUrl}" class="btn btn-success btn-sm download-single-btn" download="${escapeHtml(item.convertedName)}">
            <svg style="width:14px;height:14px;fill:currentColor;" viewBox="0 0 24 24"><path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg>
            Download
          </a>
        `;
      } else if (item.status === 'expired') {
        actionButtons = `
          <button class="btn btn-outline btn-sm" disabled style="opacity: 0.6; cursor: not-allowed;" title="Permanently deleted after 1 minute for privacy">
            Deleted
          </button>
        `;
      } else if (item.status === 'error') {
        actionButtons = `
          <button class="btn btn-outline btn-sm retry-btn" data-id="${item.id}">
            Retry
          </button>
        `;
      }

      itemEl.innerHTML = `
        <div class="file-info">
          <div class="file-badge">${item.ext.toUpperCase()}</div>
          <div class="file-meta">
            <div class="file-name" title="${escapeHtml(item.name)}">${escapeHtml(item.name)}</div>
            <div class="file-size-status">
              <span>${formatBytes(item.size)}</span>
              <span>&bull;</span>
              ${statusHtml}
            </div>
          </div>
        </div>

        <div class="file-controls">
          <div class="format-select-wrap">
            <span class="format-label">Convert to:</span>
            <select class="format-select" data-id="${item.id}" ${item.status === 'converting' ? 'disabled' : ''}>
              ${optionsHtml}
            </select>
          </div>

          <div class="file-buttons">
            ${actionButtons}
            <button class="btn btn-icon-only remove-btn" data-id="${item.id}" title="Remove file">
              <svg style="width:16px;height:16px;fill:currentColor;" viewBox="0 0 24 24">
                <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- Progress bar line -->
        <div class="item-progress-bar" style="width: ${item.progress}%"></div>
      `;

      queueList.appendChild(itemEl);
    });

    // Attach listeners to items
    queueList.querySelectorAll('.format-select').forEach(sel => {
      sel.addEventListener('change', (e) => {
        const id = parseInt(e.target.dataset.id, 10);
        const item = fileQueue.find(f => f.id === id);
        if (item) {
          item.targetFormat = e.target.value;
          if (item.status === 'done') {
            item.status = 'ready';
            renderQueue();
          }
        }
      });
    });

    queueList.querySelectorAll('.convert-single-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const id = parseInt(e.target.dataset.id, 10);
        convertQueueItem(id);
      });
    });

    queueList.querySelectorAll('.retry-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const id = parseInt(e.target.dataset.id, 10);
        convertQueueItem(id);
      });
    });

    queueList.querySelectorAll('.remove-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const id = parseInt(e.currentTarget.dataset.id, 10);
        fileQueue = fileQueue.filter(f => f.id !== id);
        renderQueue();
      });
    });
  }

  // --- 5. CONVERSION ACTIONS ---
  async function convertQueueItem(id) {
    const item = fileQueue.find(f => f.id === id);
    if (!item || item.status === 'converting') return;

    item.status = 'converting';
    item.progress = 20;
    renderQueue();

    const target = (item.targetFormat || (item.targets && item.targets[0]) || 'pdf').toLowerCase();
    const formData = new FormData();
    formData.append('file', item.file);
    formData.append('target_format', target);

    try {
      item.progress = 50;
      updateProgressBar(id, 50);

      let response;
      try {
        response = await fetch('/api/convert', {
          method: 'POST',
          body: formData
        });
      } catch (networkErr) {
        throw new Error('Could not connect to conversion server. Please ensure the server is running on your device (or deployed to the cloud).');
      }

      let result;
      const rawText = await response.text();
      try {
        result = JSON.parse(rawText);
      } catch (jsonErr) {
        if (response.status === 500) {
          throw new Error('Server encountered an internal error. Please make sure the backend server is running properly.');
        } else if (response.status === 502 || response.status === 503 || response.status === 504) {
          throw new Error('Server is currently offline or unreachable. Please keep the server running on your device or deploy to cloud hosting.');
        } else {
          throw new Error(`Server returned error (HTTP ${response.status})`);
        }
      }

      if (!response.ok || !result.success) {
        throw new Error(result.error || 'Conversion failed');
      }

      item.status = 'done';
      item.jobId = result.job_id;
      item.downloadUrl = result.download_url;
      item.convertedName = result.converted_filename;
      item.progress = 100;
      item.expiresAt = Date.now() + ((result.expires_in || 60) * 1000);
      updateProgressBar(id, 100);

      showToast(`Converted ${item.name} to ${item.targetFormat.toUpperCase()}! Auto-deletes in 60s for 100% privacy.`, 'success');
    } catch (err) {
      item.status = 'error';
      item.error = err.message;
      item.progress = 0;
      showToast(`Failed converting ${item.name}: ${err.message}`, 'error');
    } finally {
      renderQueue();
    }
  }

  function updateProgressBar(id, pct) {
    const el = document.getElementById(`queue-item-${id}`);
    if (el) {
      const bar = el.querySelector('.item-progress-bar');
      if (bar) bar.style.width = `${pct}%`;
    }
  }

  async function convertAll() {
    const pending = fileQueue.filter(f => f.status === 'ready' || f.status === 'error');
    if (pending.length === 0) {
      showToast('All files have already been converted.', 'info');
      return;
    }

    convertAllBtn.disabled = true;
    convertAllBtn.innerHTML = `
      <span class="spinner"></span> Converting (${pending.length})...
    `;

    for (const item of pending) {
      await convertQueueItem(item.id);
    }

    convertAllBtn.disabled = false;
    convertAllBtn.innerHTML = `
      <svg style="width:16px;height:16px;fill:currentColor;" viewBox="0 0 24 24">
        <path d="M12 4V1L8 5l4 4V6c3.31 0 6 2.69 6 6 0 1.01-.25 1.97-.7 2.8l1.46 1.46C19.54 15.03 20 13.57 20 12c0-4.42-3.58-8-8-8zm0 14c-3.31 0-6-2.69-6-6 0-1.01.25-1.97.7-2.8L5.24 7.74C4.46 8.97 4 10.43 4 12c0 4.42 3.58 8 8 8v3l4-4-4-4v3z"/>
      </svg>
      Convert All
    `;
    renderQueue();
  }

  async function downloadAllZip() {
    const completedJobIds = fileQueue
      .filter(f => f.status === 'done' && f.jobId)
      .map(f => f.jobId);

    if (completedJobIds.length === 0) {
      showToast('No completed conversions to bundle.', 'info');
      return;
    }

    downloadAllBtn.disabled = true;
    downloadAllBtn.innerHTML = `<span class="spinner"></span> Zipping...`;

    try {
      const res = await fetch('/api/download-all', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_ids: completedJobIds })
      });

      const data = await res.json();
      if (!res.ok || !data.success) {
        throw new Error(data.error || 'Failed to generate ZIP archive.');
      }

      // Trigger download
      const tempLink = document.createElement('a');
      tempLink.href = data.zip_url;
      tempLink.download = '56_converted_files.zip';
      document.body.appendChild(tempLink);
      tempLink.click();
      tempLink.remove();

      showToast(`ZIP created with ${data.file_count} files! Downloading...`, 'success');
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      downloadAllBtn.disabled = false;
      downloadAllBtn.innerHTML = `
        <svg style="width:16px;height:16px;fill:currentColor;" viewBox="0 0 24 24"><path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg>
        Download All (.ZIP)
      `;
    }
  }

  // --- 6. EVENT BINDINGS ---
  function initEvents() {
    convertAllBtn.addEventListener('click', convertAll);
    downloadAllBtn.addEventListener('click', downloadAllZip);
    clearAllBtn.addEventListener('click', () => {
      fileQueue = [];
      renderQueue();
      showToast('Queue cleared.', 'info');
    });

    // Quick conversion pill tags
    document.querySelectorAll('.pill-tag').forEach(pill => {
      pill.addEventListener('click', () => {
        const fromExt = pill.dataset.from;
        const toExt = pill.dataset.to;
        preferredDefaultTarget = toExt;
        fileInput.click();
      });
    });

    // Share Website Button
    if (shareBtn) {
      shareBtn.addEventListener('click', () => {
        const shareData = {
          title: '56 File Converter',
          text: 'Free, Unlimited & 100% Secure File Converter. All files auto-deleted after 1 minute.',
          url: window.location.href
        };
        if (navigator.share) {
          navigator.share(shareData).catch(err => {
            if (err.name !== 'AbortError') {
              copyLinkToClipboard();
            }
          });
        } else {
          copyLinkToClipboard();
        }
      });
    }

    function copyLinkToClipboard() {
      const url = window.location.href;
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url)
          .then(() => showToast('Website link copied to clipboard!', 'success'))
          .catch(() => fallbackCopy(url));
      } else {
        fallbackCopy(url);
      }
    }

    function fallbackCopy(text) {
      const input = document.createElement('input');
      input.value = text;
      document.body.appendChild(input);
      input.select();
      try {
        document.execCommand('copy');
        showToast('Website link copied to clipboard!', 'success');
      } catch (err) {
        showToast('Could not copy link.', 'error');
      }
      document.body.removeChild(input);
    }

    // Formats directory filter tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        const tab = e.target.dataset.tab;
        document.querySelectorAll('.matrix-item').forEach(item => {
          if (tab === 'all' || item.dataset.cat === tab) {
            item.style.display = 'flex';
          } else {
            item.style.display = 'none';
          }
        });
      });
    });
  }

  // --- 1-MINUTE EXPIRY TIMER TICKER ---
  setInterval(() => {
    const now = Date.now();
    let needRender = false;

    fileQueue.forEach(item => {
      if (item.status === 'done' && item.expiresAt) {
        const remainingMs = item.expiresAt - now;
        const remainingSec = Math.max(0, Math.ceil(remainingMs / 1000));
        const badge = document.getElementById(`countdown-${item.id}`);

        if (remainingSec <= 0) {
          item.status = 'expired';
          needRender = true;
          showToast(`File "${item.name}" has been permanently deleted from server (100% Privacy).`, 'info');
        } else if (badge) {
          badge.textContent = `⏱️ Deletes in ${remainingSec}s`;
        }
      }
    });

    if (needRender) {
      renderQueue();
    }
  }, 1000);

  // --- INIT ---
  window.addEventListener('DOMContentLoaded', async () => {
    initTheme();
    initDropzone();
    initEvents();
    await loadFormats();
  });

})();
