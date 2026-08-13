const VYRE_URL = "http://localhost:59124";
const el = (id) => document.getElementById(id);

let currentUserId = null;
let currentUsername = null;

function showStatus(targetId, msg, type) {
  const s = el(targetId);
  s.textContent = msg;
  s.className = "status " + type;
}

function timeoutFetch(url, options, ms) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), ms);
  return fetch(url, { ...options, signal: controller.signal }).finally(() => clearTimeout(timer));
}

function checkVyre() {
  const dot = el("vyreDot");
  const text = el("vyreText");
  timeoutFetch(VYRE_URL + "/", { method: "GET" }, 1500)
    .then(() => { dot.className = "dot on"; text.textContent = "Connected"; })
    .catch(() => { dot.className = "dot off"; text.textContent = "Offline"; });
}

function getCookie() {
  return new Promise((resolve) => {
    chrome.cookies.getAll({ domain: "roblox.com", name: ".ROBLOSECURITY" }, (cookies) => {
      resolve(cookies && cookies.length ? cookies[0].value : "");
    });
  });
}

function chip(value, label, cls) {
  return `<span class="chip${cls ? " " + cls : ""}"><b>${value}</b> ${label}</span>`;
}

function formatNumber(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + "M";
  if (n >= 1000) return (n / 1000).toFixed(1) + "K";
  return String(n);
}

function timeSince(dateStr) {
  const seconds = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
  const intervals = [
    [31536000, "y"], [2592000, "mo"], [86400, "d"],
    [3600, "h"], [60, "m"]
  ];
  for (const [secs, label] of intervals) {
    const count = Math.floor(seconds / secs);
    if (count >= 1) return count + label + " ago";
  }
  return "just now";
}

function loadAccount() {
  fetch("https://users.roblox.com/v1/users/authenticated", { credentials: "include" })
    .then((res) => (res.ok ? res.json() : Promise.reject()))
    .then((me) => {
      currentUserId = me.id;
      currentUsername = me.name;
      el("accName").textContent = me.displayName || me.name;
      el("accHandle").textContent = "@" + me.name;
      el("accUid").textContent = "ID: " + me.id;
      if (!el("accountName").value.trim()) el("accountName").value = me.name;
      loadAvatar(me.id);
      loadStats(me.id);
      loadAccountAge(me.name);
    })
    .catch(() => {
      currentUserId = null;
      currentUsername = null;
      el("accName").textContent = "Not logged in";
      el("accHandle").textContent = "Open roblox.com and sign in";
      el("accUid").textContent = "";
      el("avatar").removeAttribute("src");
      el("stats").innerHTML = "";
    });
}

function loadAvatar(userId) {
  fetch(`https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds=${userId}&size=150x150&format=Png&isCircular=true`)
    .then((res) => res.json())
    .then((data) => {
      const item = data.data && data.data[0];
      if (item && item.imageUrl) el("avatar").src = item.imageUrl;
    })
    .catch(() => {});
}

function loadStats(userId) {
  const stats = el("stats");
  stats.innerHTML = "";
  fetch("https://economy.roblox.com/v1/user/currency", { credentials: "include" })
    .then((res) => (res.ok ? res.json() : Promise.reject()))
    .then((data) => { stats.innerHTML += chip("R$ " + formatNumber(data.robux ?? 0), "", "robux"); })
    .catch(() => {});
  fetch(`https://friends.roblox.com/v1/users/${userId}/friends/count`)
    .then((res) => res.json())
    .then((data) => { stats.innerHTML += chip(formatNumber(data.count ?? 0), "Friends"); })
    .catch(() => {});
  fetch(`https://friends.roblox.com/v1/users/${userId}/followers/count`)
    .then((res) => res.json())
    .then((data) => { stats.innerHTML += chip(formatNumber(data.count ?? 0), "Followers"); })
    .catch(() => {});
  fetch(`https://premiumfeatures.roblox.com/v1/users/${userId}/validate`, { credentials: "include" })
    .then((res) => (res.ok ? res.json() : false))
    .then((isPremium) => { if (isPremium) stats.innerHTML += chip("✦", "Premium", "premium"); })
    .catch(() => {});
}

function loadAccountAge(username) {
  fetch(`https://users.roblox.com/v1/users/search?keyword=${encodeURIComponent(username)}&limit=10`)
    .then((res) => res.json())
    .then((data) => {
      const user = data.data && data.data.find((u) => u.name === username);
      if (!user) return;
      return fetch(`https://users.roblox.com/v1/users/${user.id}`);
    })
    .then((res) => res && res.ok ? res.json() : null)
    .then((user) => {
      if (user && user.created) {
        const age = timeSince(user.created);
        el("stats").innerHTML += chip(age, "Account Age");
      }
    })
    .catch(() => {});
}

function loadFriends() {
  if (!currentUserId) {
    el("friendList").innerHTML = '<div class="empty">Log in to see friends</div>';
    el("offlineFriendList").innerHTML = "";
    el("onlineCount").textContent = "0";
    return;
  }
  el("friendList").innerHTML = '<div class="empty loading">Loading…</div>';
  el("offlineFriendList").innerHTML = "";

  fetch(`https://friends.roblox.com/v1/users/${currentUserId}/friends`)
    .then((res) => res.json())
    .then((data) => {
      const friends = data.data || [];
      if (!friends.length) {
        el("friendList").innerHTML = '<div class="empty">No friends found</div>';
        el("onlineCount").textContent = "0";
        return;
      }
      const userIds = friends.map((f) => f.id);
      return fetch("https://presence.roblox.com/v1/presence/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ userIds }),
        credentials: "include",
      })
        .then((res) => res.json())
        .then((presenceData) => {
          const presenceMap = {};
          (presenceData.userPresences || []).forEach((p) => { presenceMap[p.userId] = p; });

          const thumbIds = userIds.join(",");
          return fetch(`https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds=${thumbIds}&size=48x48&format=Png&isCircular=true`)
            .then((res) => res.json())
            .then((thumbData) => {
              const thumbMap = {};
              (thumbData.data || []).forEach((t) => { thumbMap[t.targetId] = t.imageUrl; });

              const online = [];
              const offline = [];

              friends.forEach((f) => {
                const p = presenceMap[f.id] || {};
                const thumb = thumbMap[f.id] || "";
                const item = { ...f, presence: p, thumb };
                if (p.userPresenceType > 0) online.push(item);
                else offline.push(item);
              });

              el("onlineCount").textContent = String(online.length);
              el("friendList").innerHTML = online.length
                ? online.map(renderFriend).join("")
                : '<div class="empty">No friends online</div>';
              el("offlineFriendList").innerHTML = offline.length
                ? offline.slice(0, 30).map(renderFriend).join("")
                : '<div class="empty">—</div>';
            });
        });
    })
    .catch(() => {
      el("friendList").innerHTML = '<div class="empty">Failed to load friends</div>';
    });
}

function renderFriend(f) {
  const p = f.presence || {};
  const type = p.userPresenceType || 0;
  const dotClass = type === 2 ? "ingame" : type === 3 ? "studio" : type === 1 ? "online" : "offline";
  const statusClass = dotClass;
  let statusText = "Offline";
  if (type === 2) statusText = p.lastLocation || "In Game";
  else if (type === 3) statusText = "Roblox Studio";
  else if (type === 1) statusText = "Online";

  const thumbHtml = f.thumb
    ? `<img class="friend-avatar" src="${f.thumb}" alt="">`
    : `<div class="friend-avatar"></div>`;

  return `<div class="friend-item" data-uid="${f.id}">
    ${thumbHtml}
    <div class="friend-info">
      <div class="friend-name">${f.displayName || f.name}</div>
      <div class="friend-status ${statusClass}">${statusText}</div>
    </div>
    <div class="presence-dot ${dotClass}"></div>
  </div>`;
}

function save() {
  const btn = el("captureBtn");
  btn.disabled = true;
  showStatus("status", "Reading session…", "info");
  getCookie().then((cookie) => {
    if (!cookie) {
      showStatus("status", "No Roblox session found. Log in first.", "error");
      btn.disabled = false;
      return;
    }
    const name = el("accountName").value.trim() || "Roblox Account";
    const proxy = el("proxy").value.trim();
    const color = el("color").value;
    chrome.storage.local.set({ proxy, color });
    showStatus("status", "Saving to Vyre…", "info");
    timeoutFetch(VYRE_URL + "/add_account", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, cookie, proxy, color }),
    }, 4000)
      .then((res) => { if (!res.ok) throw new Error("status " + res.status); })
      .then(() => {
        showStatus("status", "Saved " + name + " to Vyre.", "success");
        btn.disabled = false;
        addHistory(name);
      })
      .catch(() => {
        showStatus("status", "Could not reach Vyre. Is the app open?", "error");
        btn.disabled = false;
      });
  });
}

function copyCookie() {
  getCookie().then((cookie) => {
    if (!cookie) { showStatus("status", "No session found.", "error"); return; }
    navigator.clipboard.writeText(cookie)
      .then(() => showStatus("status", "Cookie copied to clipboard.", "success"))
      .catch(() => showStatus("status", "Could not copy.", "error"));
  });
}

function viewCookie() {
  const box = el("cookieBox");
  if (box.style.display !== "none") { box.style.display = "none"; return; }
  getCookie().then((cookie) => {
    if (!cookie) { showStatus("status", "No session found.", "error"); return; }
    box.textContent = cookie.substring(0, 40) + "…" + cookie.substring(cookie.length - 20);
    box.style.display = "block";
  });
}

function checkHealth() {
  showStatus("toolStatus", "Checking cookie health…", "info");
  getCookie().then((cookie) => {
    if (!cookie) { showStatus("toolStatus", "No session cookie found.", "error"); return; }
    fetch("https://users.roblox.com/v1/users/authenticated", {
      headers: { Cookie: ".ROBLOSECURITY=" + cookie },
      credentials: "include",
    })
      .then((res) => {
        if (res.ok) showStatus("toolStatus", "Cookie is valid and active.", "success");
        else showStatus("toolStatus", "Cookie may be expired or invalid (status " + res.status + ").", "error");
      })
      .catch(() => showStatus("toolStatus", "Could not verify cookie.", "error"));
  });
}

function exportCookie() {
  getCookie().then((cookie) => {
    if (!cookie) { showStatus("toolStatus", "No session found.", "error"); return; }
    const data = {
      cookie,
      username: currentUsername || "unknown",
      userId: currentUserId || 0,
      exportedAt: new Date().toISOString(),
      source: "Vyre Companion",
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = (currentUsername || "roblox") + "_session.json";
    a.click();
    URL.revokeObjectURL(url);
    showStatus("toolStatus", "Session exported as JSON file.", "success");
  });
}

function addHistory(name) {
  chrome.storage.local.get(["captureHistory"], (result) => {
    const history = result.captureHistory || [];
    history.unshift({ name, time: Date.now() });
    if (history.length > 50) history.length = 50;
    chrome.storage.local.set({ captureHistory: history });
    renderHistory(history);
  });
}

function renderHistory(history) {
  const list = el("historyList");
  if (!history || !history.length) {
    list.innerHTML = '<div class="empty">No captures yet</div>';
    return;
  }
  list.innerHTML = history.slice(0, 20).map((h) => {
    const ago = timeSince(new Date(h.time).toISOString());
    return `<div class="history-item"><span class="history-name">${h.name}</span><span class="history-time">${ago}</span></div>`;
  }).join("");
}

function loadHistory() {
  chrome.storage.local.get(["captureHistory"], (result) => {
    renderHistory(result.captureHistory || []);
  });
}

function clearHistory() {
  chrome.storage.local.set({ captureHistory: [] });
  renderHistory([]);
  showStatus("status", "Capture history cleared.", "info");
}

function clearAllData() {
  chrome.storage.local.clear();
  el("proxy").value = "";
  el("color").value = "#e5484d";
  el("colorText").textContent = "#e5484d";
  el("accountName").value = "";
  el("quickPlaceId").value = "";
  el("autoCapture").checked = false;
  el("loginNotify").checked = true;
  el("friendAlerts").checked = false;
  el("cookieExpiry").checked = true;
  renderHistory([]);
}

function initTabs() {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
      document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
      tab.classList.add("active");
      const panel = el("panel-" + tab.dataset.tab);
      panel.classList.add("active");
      if (tab.dataset.tab === "friends") loadFriends();
    });
  });
}

function initQuickActions() {
  const actions = {
    qaProfile: () => currentUserId && chrome.tabs.create({ url: `https://www.roblox.com/users/${currentUserId}/profile` }),
    qaAvatar: () => chrome.tabs.create({ url: "https://www.roblox.com/my/avatar" }),
    qaInventory: () => currentUserId && chrome.tabs.create({ url: `https://www.roblox.com/users/${currentUserId}/inventory` }),
    qaTrades: () => chrome.tabs.create({ url: "https://www.roblox.com/trades" }),
    qaMessages: () => chrome.tabs.create({ url: "https://www.roblox.com/my/messages" }),
    qaSettings: () => chrome.tabs.create({ url: "https://www.roblox.com/my/account" }),
    qaCreate: () => chrome.tabs.create({ url: "https://create.roblox.com/dashboard/creations" }),
    qaCatalog: () => chrome.tabs.create({ url: "https://www.roblox.com/catalog" }),
  };
  Object.entries(actions).forEach(([id, fn]) => {
    el(id).addEventListener("click", fn);
  });
}

function initSettings() {
  const keys = ["autoCapture", "loginNotify", "friendAlerts", "cookieExpiry", "quickPlaceId"];
  chrome.storage.local.get(keys, (saved) => {
    if (saved.autoCapture !== undefined) el("autoCapture").checked = saved.autoCapture;
    if (saved.loginNotify !== undefined) el("loginNotify").checked = saved.loginNotify;
    if (saved.friendAlerts !== undefined) el("friendAlerts").checked = saved.friendAlerts;
    if (saved.cookieExpiry !== undefined) el("cookieExpiry").checked = saved.cookieExpiry;
    if (saved.quickPlaceId) el("quickPlaceId").value = saved.quickPlaceId;
  });

  ["autoCapture", "loginNotify", "friendAlerts", "cookieExpiry"].forEach((key) => {
    el(key).addEventListener("change", (e) => {
      chrome.storage.local.set({ [key]: e.target.checked });
      chrome.runtime.sendMessage({ type: "settingChanged", key, value: e.target.checked });
    });
  });

  el("quickPlaceId").addEventListener("change", (e) => {
    chrome.storage.local.set({ quickPlaceId: e.target.value.trim() });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  chrome.storage.local.get(["proxy", "color"], (saved) => {
    if (saved.proxy) el("proxy").value = saved.proxy;
    if (saved.color) { el("color").value = saved.color; el("colorText").textContent = saved.color; }
  });

  el("color").addEventListener("input", (e) => { el("colorText").textContent = e.target.value; });
  el("captureBtn").addEventListener("click", save);
  el("copyBtn").addEventListener("click", copyCookie);
  el("viewCookieBtn").addEventListener("click", viewCookie);
  el("refreshAll").addEventListener("click", () => { checkVyre(); loadAccount(); });
  el("refreshFriends").addEventListener("click", loadFriends);
  el("healthBtn").addEventListener("click", checkHealth);
  el("exportBtn").addEventListener("click", exportCookie);
  el("clearHistoryBtn").addEventListener("click", clearHistory);
  el("clearAllBtn").addEventListener("click", clearAllData);
  el("accUid").addEventListener("click", () => {
    if (currentUserId) {
      navigator.clipboard.writeText(String(currentUserId));
      showStatus("status", "User ID copied.", "success");
    }
  });

  initTabs();
  initQuickActions();
  initSettings();
  checkVyre();
  loadAccount();
  loadHistory();
});
