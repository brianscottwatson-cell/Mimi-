/**
 * Mimi Gateway v1.0
 * Chat with file uploads (images → Claude vision, docs → text extraction)
 * and voice input via browser Speech Recognition API.
 */
(function () {
  'use strict';

  // ---------------------------------------------------------------------------
  // Config
  // ---------------------------------------------------------------------------

  var API_BASE = '';
  var AUTH_TOKEN = 'netrunner-1';
  var IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
  var VOICE_ENABLED_KEY = 'mimi-voice-enabled';
  var MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

  // ---------------------------------------------------------------------------
  // DOM
  // ---------------------------------------------------------------------------

  var chatMessages = document.getElementById('chat-messages');
  var messageInput = document.getElementById('message-input');
  var sendBtn = document.getElementById('send-btn');
  var statusText = document.getElementById('status-text');
  var hamburgerBtn = document.getElementById('hamburger-btn');
  var sidebarOverlay = document.getElementById('sidebar-overlay');
  var historySidebar = document.getElementById('history-sidebar');
  var sidebarClose = document.getElementById('sidebar-close');
  var historyList = document.getElementById('history-list');
  var historySearch = document.getElementById('history-search');
  var newChatBtn = document.getElementById('new-chat-btn');
  var bootOverlay = document.getElementById('boot-overlay');
  var bootText = document.getElementById('boot-text');
  var bootProgressBar = document.getElementById('boot-progress-bar');
  var metricLatency = document.getElementById('metric-latency');
  var metricPackets = document.getElementById('metric-packets');
  var hudClock = document.getElementById('hud-clock');
  var uploadBtn = document.getElementById('upload-btn');
  var fileInput = document.getElementById('file-input');
  var filePreviewStrip = document.getElementById('file-preview-strip');
  var voiceBtn = document.getElementById('voice-btn');

  // ---------------------------------------------------------------------------
  // State
  // ---------------------------------------------------------------------------

  var isSending = false;
  var packetCount = 0;
  var conversations = [];
  var pendingFiles = []; // { file, dataUrl, type: 'image'|'doc' }
  var isListening = false;
  var recognition = null;
  var voiceOutputEnabled = localStorage.getItem(VOICE_ENABLED_KEY) !== 'false'; // on by default
  var currentAudio = null;
  var browserSynth = window.speechSynthesis || null;
  var preferredBrowserVoice = null;

  // ---------------------------------------------------------------------------
  // Boot Sequence
  // ---------------------------------------------------------------------------

  var bootLines = [
    'MIMI.SOUL v1.0',
    'Initializing personal agent...',
    'Loading cognitive modules.........OK',
    'Health recomp protocol............ACTIVE',
    'Work planner.....................LOADED',
    'Book curator.....................READY',
    'Dashboard overseer...............STANDBY',
    'Secure channel...................OPEN',
    '',
    'ALL SYSTEMS NOMINAL.',
    'Hey Brian. Ready when you are.'
  ];

  function runBootSequence() {
    if (!bootOverlay || !bootText || !bootProgressBar) {
      initChat();
      return;
    }
    var lineIndex = 0;
    var displayed = '';
    var totalLines = bootLines.length;

    function typeLine() {
      if (lineIndex >= totalLines) {
        bootProgressBar.style.width = '100%';
        setTimeout(function () {
          bootOverlay.classList.add('hidden');
          initChat();
        }, 600);
        return;
      }
      var line = bootLines[lineIndex];
      displayed += (lineIndex > 0 ? '\n' : '') + line;
      bootText.textContent = displayed;
      bootProgressBar.style.width = ((lineIndex + 1) / totalLines * 100) + '%';
      lineIndex++;
      setTimeout(typeLine, line === '' ? 200 : (80 + Math.random() * 120));
    }
    typeLine();
  }

  // ---------------------------------------------------------------------------
  // HUD Clock
  // ---------------------------------------------------------------------------

  function updateClock() {
    if (!hudClock) return;
    var now = new Date();
    hudClock.textContent =
      now.getHours().toString().padStart(2, '0') + ':' +
      now.getMinutes().toString().padStart(2, '0') + ':' +
      now.getSeconds().toString().padStart(2, '0');
  }
  setInterval(updateClock, 1000);
  updateClock();

  // ---------------------------------------------------------------------------
  // API
  // ---------------------------------------------------------------------------

  function apiHeaders(isJson) {
    var h = { 'X-Netrunner-Token': AUTH_TOKEN };
    if (isJson) h['Content-Type'] = 'application/json';
    return h;
  }

  function sendChatMessage(text, files) {
    var start = performance.now();

    // Build form data if files present, otherwise JSON
    if (files && files.length > 0) {
      var formData = new FormData();
      formData.append('message', text);
      files.forEach(function (f) {
        formData.append('files', f.file);
      });
      return fetch(API_BASE + '/api/chat', {
        method: 'POST',
        headers: { 'X-Netrunner-Token': AUTH_TOKEN },
        body: formData
      }).then(function (res) {
        var elapsed = Math.round(performance.now() - start);
        if (metricLatency) metricLatency.textContent = elapsed + 'ms';
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.json();
      });
    }

    return fetch(API_BASE + '/api/chat', {
      method: 'POST',
      headers: apiHeaders(true),
      body: JSON.stringify({ message: text })
    }).then(function (res) {
      var elapsed = Math.round(performance.now() - start);
      if (metricLatency) metricLatency.textContent = elapsed + 'ms';
      if (!res.ok) throw new Error('HTTP ' + res.status);
      return res.json();
    });
  }

  function fetchHistory() {
    return fetch(API_BASE + '/api/history', { headers: apiHeaders(false) })
      .then(function (res) { if (!res.ok) throw new Error('HTTP ' + res.status); return res.json(); });
  }

  function clearHistory() {
    return fetch(API_BASE + '/api/history', { method: 'DELETE', headers: apiHeaders(false) })
      .then(function (res) { if (!res.ok) throw new Error('HTTP ' + res.status); return res.json(); });
  }

  // ---------------------------------------------------------------------------
  // Time
  // ---------------------------------------------------------------------------

  function formatTime(isoString) {
    var d = new Date(isoString);
    return d.getHours().toString().padStart(2, '0') + ':' +
           d.getMinutes().toString().padStart(2, '0') + ':' +
           d.getSeconds().toString().padStart(2, '0');
  }

  // ---------------------------------------------------------------------------
  // File Upload
  // ---------------------------------------------------------------------------

  if (uploadBtn && fileInput) {
    uploadBtn.addEventListener('click', function () {
      fileInput.click();
    });

    fileInput.addEventListener('change', function () {
      var files = fileInput.files;
      for (var i = 0; i < files.length; i++) {
        addPendingFile(files[i]);
      }
      fileInput.value = '';
    });
  }

  // Drag and drop on chat viewport
  if (chatMessages) {
    chatMessages.addEventListener('dragover', function (e) {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'copy';
    });
    chatMessages.addEventListener('drop', function (e) {
      e.preventDefault();
      var files = e.dataTransfer.files;
      for (var i = 0; i < files.length; i++) {
        addPendingFile(files[i]);
      }
    });
  }

  function addPendingFile(file) {
    if (file.size > MAX_FILE_SIZE) {
      alert('File too large: ' + file.name + ' (max 10MB)');
      return;
    }

    var isImage = IMAGE_TYPES.indexOf(file.type) !== -1;
    var entry = { file: file, dataUrl: null, type: isImage ? 'image' : 'doc' };

    if (isImage) {
      var reader = new FileReader();
      reader.onload = function (e) {
        entry.dataUrl = e.target.result;
        renderFilePreview();
      };
      reader.readAsDataURL(file);
    }

    pendingFiles.push(entry);
    renderFilePreview();
  }

  function removePendingFile(index) {
    pendingFiles.splice(index, 1);
    renderFilePreview();
  }

  function renderFilePreview() {
    if (!filePreviewStrip) return;
    filePreviewStrip.innerHTML = '';

    if (pendingFiles.length === 0) {
      filePreviewStrip.classList.remove('has-files');
      return;
    }

    filePreviewStrip.classList.add('has-files');

    pendingFiles.forEach(function (entry, idx) {
      var item = document.createElement('div');
      item.className = 'file-preview-item ' + (entry.type === 'image' ? 'is-image' : 'is-doc');

      if (entry.type === 'image' && entry.dataUrl) {
        var img = document.createElement('img');
        img.src = entry.dataUrl;
        img.alt = entry.file.name;
        item.appendChild(img);
      } else {
        var icon = document.createElement('span');
        icon.className = 'doc-icon';
        icon.textContent = '\u{1F4C4}';
        var nameEl = document.createElement('div');
        var nameText = document.createElement('div');
        nameText.className = 'doc-name';
        nameText.textContent = entry.file.name;
        var sizeText = document.createElement('div');
        sizeText.className = 'doc-size';
        sizeText.textContent = formatFileSize(entry.file.size);
        nameEl.appendChild(nameText);
        nameEl.appendChild(sizeText);
        item.appendChild(icon);
        item.appendChild(nameEl);
      }

      var removeBtn = document.createElement('button');
      removeBtn.className = 'file-preview-remove';
      removeBtn.textContent = '\u00D7';
      removeBtn.setAttribute('data-idx', idx);
      removeBtn.addEventListener('click', function () {
        removePendingFile(parseInt(this.getAttribute('data-idx')));
      });
      item.appendChild(removeBtn);

      filePreviewStrip.appendChild(item);
    });
  }

  function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }

  // ---------------------------------------------------------------------------
  // Voice Input (Browser Speech Recognition)
  // ---------------------------------------------------------------------------

  function initVoice() {
    var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition || !voiceBtn) return;

    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = function () {
      isListening = true;
      voiceBtn.classList.add('listening');
      setStatus('LISTENING...');
    };

    recognition.onresult = function (event) {
      var transcript = '';
      for (var i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }
      messageInput.value = transcript;
      autoResize();

      // If final result, auto-send
      if (event.results[event.results.length - 1].isFinal) {
        setTimeout(function () {
          if (messageInput.value.trim()) handleSend();
        }, 300);
      }
    };

    recognition.onerror = function () {
      isListening = false;
      voiceBtn.classList.remove('listening');
      setStatus('ONLINE');
    };

    recognition.onend = function () {
      isListening = false;
      voiceBtn.classList.remove('listening');
      setStatus('ONLINE');
    };

    voiceBtn.addEventListener('click', function () {
      if (isListening) {
        recognition.stop();
      } else {
        recognition.start();
      }
    });
  }

  // ---------------------------------------------------------------------------
  // TTS — Speak bot responses aloud
  // ---------------------------------------------------------------------------

  function speakResponse(text) {
    if (!voiceOutputEnabled || !text) return;

    // Stop any currently playing audio
    stopSpeaking();

    // Try server-side TTS (ElevenLabs) first
    fetch(API_BASE + '/api/tts', {
      method: 'POST',
      headers: apiHeaders(true),
      body: JSON.stringify({ text: text })
    }).then(function (res) {
      var contentType = res.headers.get('content-type') || '';

      if (contentType.indexOf('audio') !== -1) {
        // Got audio back from ElevenLabs
        return res.blob().then(function (blob) {
          var url = URL.createObjectURL(blob);
          currentAudio = new Audio(url);
          currentAudio.onended = function () { URL.revokeObjectURL(url); currentAudio = null; };
          currentAudio.play().catch(function () {});
        });
      }

      // JSON response = fallback to browser speech
      return res.json().then(function (data) {
        if (data.fallback && data.text) {
          speakWithBrowser(data.text);
        }
      });
    }).catch(function () {
      // Network error — try browser speech directly
      speakWithBrowser(text);
    });
  }

  function speakWithBrowser(text) {
    if (!browserSynth) return;
    browserSynth.cancel();

    var utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.05;
    utterance.volume = 1.0;

    // Pick the best female voice available
    if (!preferredBrowserVoice) {
      var voices = browserSynth.getVoices();
      // Preference order: Samantha (macOS), Google UK Female, any female English voice
      var prefs = ['samantha', 'google uk english female', 'karen', 'moira', 'fiona', 'victoria', 'google us english'];
      for (var p = 0; p < prefs.length; p++) {
        for (var v = 0; v < voices.length; v++) {
          if (voices[v].name.toLowerCase().indexOf(prefs[p]) !== -1) {
            preferredBrowserVoice = voices[v];
            break;
          }
        }
        if (preferredBrowserVoice) break;
      }
      // Fallback: any English voice
      if (!preferredBrowserVoice) {
        for (var vi = 0; vi < voices.length; vi++) {
          if (voices[vi].lang && voices[vi].lang.indexOf('en') === 0) {
            preferredBrowserVoice = voices[vi];
            break;
          }
        }
      }
    }
    if (preferredBrowserVoice) utterance.voice = preferredBrowserVoice;

    browserSynth.speak(utterance);
  }

  function stopSpeaking() {
    if (currentAudio) {
      currentAudio.pause();
      currentAudio = null;
    }
    if (browserSynth) browserSynth.cancel();
  }

  function toggleVoiceOutput() {
    voiceOutputEnabled = !voiceOutputEnabled;
    localStorage.setItem(VOICE_ENABLED_KEY, voiceOutputEnabled);
    updateVoiceToggleUI();
    if (!voiceOutputEnabled) stopSpeaking();
  }

  function updateVoiceToggleUI() {
    var toggle = document.getElementById('voice-output-toggle');
    if (toggle) {
      toggle.classList.toggle('active', voiceOutputEnabled);
      toggle.title = voiceOutputEnabled ? 'Voice output ON (click to mute)' : 'Voice output OFF (click to unmute)';
    }
  }

  // Pre-load browser voices (they load async in some browsers)
  if (browserSynth && browserSynth.onvoiceschanged !== undefined) {
    browserSynth.onvoiceschanged = function () { preferredBrowserVoice = null; };
  }

  // ---------------------------------------------------------------------------
  // Message Rendering
  // ---------------------------------------------------------------------------

  function createMessageEl(role, text, timestamp, isError, attachments) {
    var msg = document.createElement('div');
    var className = 'message';
    if (isError) className += ' error';
    else className += ' ' + (role === 'user' ? 'user' : 'bot');
    msg.className = className;

    var card = document.createElement('div');
    card.className = 'msg-card';

    if (!isError) {
      var sender = document.createElement('div');
      sender.className = 'msg-sender';
      if (role === 'bot') {
        var miniAvatar = document.createElement('span');
        miniAvatar.className = 'mini-avatar';
        miniAvatar.textContent = 'M';
        sender.appendChild(miniAvatar);
        sender.appendChild(document.createTextNode('MIMI'));
      } else {
        sender.textContent = 'BRIAN';
      }
      card.appendChild(sender);
    }

    // Attachments (image thumbnails / doc badges)
    if (attachments && attachments.length > 0) {
      var attachDiv = document.createElement('div');
      attachDiv.className = 'msg-attachments';
      attachments.forEach(function (a) {
        if (a.type === 'image' && a.dataUrl) {
          var thumb = document.createElement('img');
          thumb.className = 'msg-attachment-thumb';
          thumb.src = a.dataUrl;
          thumb.alt = a.name || 'image';
          attachDiv.appendChild(thumb);
        } else {
          var badge = document.createElement('span');
          badge.className = 'msg-attachment-doc';
          badge.textContent = '\u{1F4C4} ' + (a.name || 'document');
          attachDiv.appendChild(badge);
        }
      });
      card.appendChild(attachDiv);
    }

    var body = document.createElement('div');
    body.className = 'msg-text';
    body.textContent = text;
    card.appendChild(body);

    if (timestamp && !isError) {
      var time = document.createElement('div');
      time.className = 'msg-time';
      time.textContent = formatTime(timestamp);
      card.appendChild(time);
    }

    msg.appendChild(card);

    if (!isError && window.innerWidth > 640) {
      card.addEventListener('mousemove', function (e) {
        var rect = card.getBoundingClientRect();
        var x = (e.clientX - rect.left) / rect.width - 0.5;
        var y = (e.clientY - rect.top) / rect.height - 0.5;
        card.style.transform = 'perspective(600px) rotateY(' + (x * 4) + 'deg) rotateX(' + (-y * 4) + 'deg)';
      });
      card.addEventListener('mouseleave', function () { card.style.transform = ''; });
    }

    return msg;
  }

  function appendMessage(role, text, timestamp, isError, attachments) {
    var el = createMessageEl(role, text, timestamp, isError, attachments);
    chatMessages.appendChild(el);
    scrollToBottom();
  }

  function scrollToBottom() {
    requestAnimationFrame(function () {
      chatMessages.scrollTop = chatMessages.scrollHeight;
    });
  }

  // ---------------------------------------------------------------------------
  // Typing Indicator
  // ---------------------------------------------------------------------------

  var typingEl = null;

  function showTyping() {
    if (typingEl) return;
    typingEl = document.createElement('div');
    typingEl.className = 'typing-indicator';
    var card = document.createElement('div');
    card.className = 'msg-card';
    card.innerHTML = '<div class="dot"></div><div class="dot"></div><div class="dot"></div>';
    typingEl.appendChild(card);
    chatMessages.appendChild(typingEl);
    scrollToBottom();
    setStatus('PROCESSING...');
  }

  function hideTyping() {
    if (typingEl && typingEl.parentNode) typingEl.parentNode.removeChild(typingEl);
    typingEl = null;
    setStatus('ONLINE');
  }

  function setStatus(text) {
    if (statusText) statusText.textContent = text;
  }

  // ---------------------------------------------------------------------------
  // Send (with files)
  // ---------------------------------------------------------------------------

  function handleSend() {
    var text = messageInput.value.trim();
    var filesToSend = pendingFiles.slice();

    if (!text && filesToSend.length === 0) return;
    if (isSending) return;

    isSending = true;
    messageInput.value = '';
    autoResize();

    // Build attachment info for display
    var attachmentInfo = filesToSend.map(function (f) {
      return { type: f.type, dataUrl: f.dataUrl, name: f.file.name };
    });

    // Clear pending files
    pendingFiles = [];
    renderFilePreview();

    packetCount++;
    if (metricPackets) metricPackets.textContent = packetCount;

    var displayText = text || ('[Sent ' + filesToSend.length + ' file' + (filesToSend.length > 1 ? 's' : '') + ']');
    appendMessage('user', displayText, new Date().toISOString(), false, attachmentInfo);
    showTyping();

    sendChatMessage(text || 'Please analyze the attached file(s).', filesToSend)
      .then(function (data) {
        hideTyping();
        packetCount++;
        if (metricPackets) metricPackets.textContent = packetCount;
        appendMessage('bot', data.reply, data.timestamp);
        speakResponse(data.reply);
        updateSidebarHistory();
      })
      .catch(function (err) {
        hideTyping();
        appendMessage('bot', '[LINK ERROR] ' + err.message, new Date().toISOString(), true);
        setStatus('LINK ERROR');
      })
      .finally(function () {
        isSending = false;
        messageInput.focus();
      });
  }

  // ---------------------------------------------------------------------------
  // Input
  // ---------------------------------------------------------------------------

  function autoResize() {
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
  }

  messageInput.addEventListener('input', autoResize);

  messageInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  });

  sendBtn.addEventListener('click', function (e) {
    e.preventDefault();
    handleSend();
  });

  // Paste images from clipboard
  messageInput.addEventListener('paste', function (e) {
    var items = e.clipboardData && e.clipboardData.items;
    if (!items) return;
    for (var i = 0; i < items.length; i++) {
      if (items[i].type.indexOf('image') !== -1) {
        var file = items[i].getAsFile();
        if (file) addPendingFile(file);
      }
    }
  });

  // ---------------------------------------------------------------------------
  // Sidebar
  // ---------------------------------------------------------------------------

  function openSidebar() {
    historySidebar.classList.add('open');
    sidebarOverlay.classList.add('active');
    updateSidebarHistory();
  }

  function closeSidebar() {
    historySidebar.classList.remove('open');
    sidebarOverlay.classList.remove('active');
  }

  hamburgerBtn.addEventListener('click', openSidebar);
  sidebarOverlay.addEventListener('click', closeSidebar);
  sidebarClose.addEventListener('click', closeSidebar);

  function updateSidebarHistory() {
    fetchHistory().then(function (data) {
      conversations = data || [];
      renderHistoryList(conversations);
    }).catch(function () {});
  }

  function renderHistoryList(items) {
    historyList.innerHTML = '';
    if (!items.length) {
      var empty = document.createElement('li');
      empty.className = 'history-item';
      empty.innerHTML = '<div class="history-item-title" style="color:var(--text-ghost)">NO RECORDS</div>';
      historyList.appendChild(empty);
      return;
    }
    var userMsgs = items.filter(function (m) { return m.role === 'user'; });
    var seen = {};
    userMsgs.forEach(function (msg) {
      var preview = msg.content.substring(0, 50);
      if (seen[preview]) return;
      seen[preview] = true;
      var li = document.createElement('li');
      li.className = 'history-item';
      var title = document.createElement('div');
      title.className = 'history-item-title';
      title.textContent = preview + (msg.content.length > 50 ? '...' : '');
      var date = document.createElement('div');
      date.className = 'history-item-date';
      date.textContent = msg.timestamp ? formatTime(msg.timestamp) : '--:--:--';
      li.appendChild(title);
      li.appendChild(date);
      historyList.appendChild(li);
    });
  }

  if (historySearch) {
    historySearch.addEventListener('input', function () {
      var q = historySearch.value.toLowerCase();
      renderHistoryList(conversations.filter(function (m) {
        return m.content.toLowerCase().indexOf(q) !== -1;
      }));
    });
  }

  if (newChatBtn) {
    newChatBtn.addEventListener('click', function () {
      clearHistory().then(function () {
        conversations = [];
        renderHistoryList([]);
        chatMessages.innerHTML = '';
        var notice = document.createElement('div');
        notice.className = 'system-notice';
        notice.innerHTML =
          '<div class="notice-line"></div>' +
          '<div class="notice-content">' +
          '<span class="notice-icon">&#9670;</span>' +
          '<span class="notice-text">NEW SESSION // MIMI READY</span>' +
          '<span class="notice-icon">&#9670;</span>' +
          '</div>' +
          '<div class="notice-line"></div>';
        chatMessages.appendChild(notice);
        packetCount = 0;
        if (metricPackets) metricPackets.textContent = '0';
        if (metricLatency) metricLatency.textContent = '--ms';
        closeSidebar();
      }).catch(function () {});
    });
  }

  // ---------------------------------------------------------------------------
  // Swipe Gestures
  // ---------------------------------------------------------------------------

  var touchStartX = 0, touchCurrentX = 0, swiping = false;
  document.addEventListener('touchstart', function (e) {
    var t = e.touches[0]; touchStartX = t.clientX; touchCurrentX = t.clientX;
    if (touchStartX < 30 && !historySidebar.classList.contains('open')) swiping = true;
    if (historySidebar.classList.contains('open')) swiping = true;
  }, { passive: true });
  document.addEventListener('touchmove', function (e) {
    if (swiping) touchCurrentX = e.touches[0].clientX;
  }, { passive: true });
  document.addEventListener('touchend', function () {
    if (!swiping) return; swiping = false;
    var dx = touchCurrentX - touchStartX;
    if (!historySidebar.classList.contains('open') && dx > 60) openSidebar();
    else if (historySidebar.classList.contains('open') && dx < -60) closeSidebar();
  }, { passive: true });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && historySidebar.classList.contains('open')) closeSidebar();
  });

  // ---------------------------------------------------------------------------
  // Init
  // ---------------------------------------------------------------------------

  function initChat() {
    messageInput.focus();
    initVoice();
    // Set up voice output toggle
    var voiceToggle = document.getElementById('voice-output-toggle');
    if (voiceToggle) {
      voiceToggle.addEventListener('click', toggleVoiceOutput);
      updateVoiceToggleUI();
    }
    fetchHistory().then(function (data) {
      if (!data || !data.length) return;
      conversations = data;
      packetCount = data.length;
      if (metricPackets) metricPackets.textContent = packetCount;
      data.forEach(function (msg) {
        appendMessage(msg.role, msg.content, msg.timestamp);
      });
    }).catch(function () {});
  }

  runBootSequence();
})();
