document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("chat-form");
  const input = document.getElementById("user-input");
  const chatbox = document.getElementById("chatbox");
  const welcome = document.getElementById("welcome");
  const clearBtn = document.getElementById("clear-chat");
  const quickBtns = document.querySelectorAll(".quick-btn");

  function hideWelcome() {
    if (welcome) {
      welcome.style.display = "none";
    }
  }

  function showWelcome() {
    if (welcome) {
      welcome.style.display = "flex";
    }
  }

  function formatBotResponse(text) {
    const sections = [
      { pattern: /\*\*What I found[:\s]?\*\*/gi, label: "What I Found" },
      { pattern: /\*\*What it means[:\s]?\*\*/gi, label: "What It Means" },
      { pattern: /\*\*What I can fix[:\s]?\*\*/gi, label: "What I Can Fix" },
      { pattern: /\*\*(?:Next step|What you should do next)[:\s]?\*\*/gi, label: "Next Step" },
    ];

    let hasDiagnosis = sections.some(s => s.pattern.test(text));
    if (!hasDiagnosis) {
      return escapeAndFormat(text);
    }

    let parts = text;
    let diagParts = [];
    let beforeDiag = "";

    let firstIdx = Infinity;
    for (const s of sections) {
      const m = parts.match(s.pattern);
      if (m) {
        const idx = parts.indexOf(m[0]);
        if (idx < firstIdx) firstIdx = idx;
      }
    }

    if (firstIdx > 0 && firstIdx < Infinity) {
      beforeDiag = parts.substring(0, firstIdx).trim();
      parts = parts.substring(firstIdx);
    }

    const splitPattern = /\*\*(What I found|What it means|What I can fix|Next step|What you should do next)[:\s]?\*\*/gi;
    const tokens = parts.split(splitPattern);

    for (let i = 1; i < tokens.length; i += 2) {
      const label = tokens[i];
      const content = (tokens[i + 1] || "").trim();
      diagParts.push({ label, content });
    }

    let html = "";
    if (beforeDiag) {
      html += `<p>${escapeAndFormat(beforeDiag)}</p>`;
    }

    if (diagParts.length > 0) {
      html += '<div class="diagnosis-card">';
      html += '<div class="diag-header">PingPal Diagnosis</div>';
      for (const part of diagParts) {
        html += `<div class="diag-step"><div class="diag-label">${escapeHtml(part.label)}</div>${escapeAndFormat(part.content)}</div>`;
      }
      html += '</div>';
    }

    return html || escapeAndFormat(text);
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function escapeAndFormat(text) {
    let html = escapeHtml(text);
    html = html.replace(/\n/g, "<br>");
    html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    return html;
  }

  function appendMessage(sender, text) {
    hideWelcome();

    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${sender}`;

    const avatarDiv = document.createElement("div");
    avatarDiv.className = "message-avatar";
    avatarDiv.textContent = sender === "user" ? "You" : "PP";

    const bodyDiv = document.createElement("div");
    bodyDiv.className = "message-body";

    const bubbleDiv = document.createElement("div");
    bubbleDiv.className = "message-bubble";

    if (sender === "bot") {
      bubbleDiv.innerHTML = formatBotResponse(text);
    } else {
      bubbleDiv.innerHTML = escapeAndFormat(text);
    }

    bodyDiv.appendChild(bubbleDiv);
    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(bodyDiv);
    chatbox.appendChild(messageDiv);
    chatbox.scrollTop = chatbox.scrollHeight;
  }

  function showTyping() {
    const typingDiv = document.createElement("div");
    typingDiv.className = "typing-indicator";
    typingDiv.id = "typing";

    typingDiv.innerHTML = `
      <div class="message-avatar">PP</div>
      <div class="typing-dots">
        <span></span><span></span><span></span>
      </div>
    `;

    chatbox.appendChild(typingDiv);
    chatbox.scrollTop = chatbox.scrollHeight;
  }

  function removeTyping() {
    const typing = document.getElementById("typing");
    if (typing) typing.remove();
  }

  async function sendMessage(message) {
    if (!message.trim()) return;

    appendMessage("user", message);
    input.value = "";
    showTyping();

    try {
      const response = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });

      removeTyping();

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const data = await response.json();
      appendMessage("bot", data.response || "I couldn't process that request. Please try again.");
    } catch (error) {
      removeTyping();
      console.error("Fetch error:", error);
      appendMessage("bot", "I'm having trouble connecting right now. Please check your connection and try again.");
    }
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    sendMessage(input.value.trim());
  });

  quickBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const message = btn.getAttribute("data-message");
      if (message) sendMessage(message);
    });
  });

  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      const messages = chatbox.querySelectorAll(".message, .typing-indicator");
      messages.forEach((m) => m.remove());
      showWelcome();
    });
  }

  const navItems = document.querySelectorAll(".nav-item[data-nav]");
  const pageTitle = document.querySelector(".page-title");
  const pageSubtitle = document.querySelector(".page-subtitle");

  const navMeta = {
    troubleshoot: { title: "Troubleshoot", subtitle: "Describe your issue and PingPal will diagnose it" },
    network: { title: "Network", subtitle: "Check connectivity, DNS, Wi-Fi, and internet status" },
    device: { title: "Device Health", subtitle: "Disk space, uptime, performance, and system checks" },
    reports: { title: "Reports", subtitle: "Generate ISP, IT, or system diagnostic reports" },
  };

  navItems.forEach((item) => {
    item.addEventListener("click", (e) => {
      e.preventDefault();
      const nav = item.getAttribute("data-nav");
      const message = item.getAttribute("data-message");

      navItems.forEach((n) => n.classList.remove("active"));
      item.classList.add("active");

      if (navMeta[nav]) {
        if (pageTitle) pageTitle.textContent = navMeta[nav].title;
        if (pageSubtitle) pageSubtitle.textContent = navMeta[nav].subtitle;
      }

      if (message) {
        sendMessage(message);
      }
    });
  });
});
