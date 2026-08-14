const VYRE_URL = "http://localhost:59124";
const el = (id) => document.getElementById(id);

let currentUserId = null;
let currentUsername = null;

function showStatus(msg, type) {
  const s = el("status");
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
    .then((res) => res.json())
    .then((data) => {
      const wasOffline = dot.className === "dot off";
      dot.className = "dot on";
      text.textContent = "Connected (v" + data.version + ")";
      if (wasOffline) {
        loadVaultAccounts();
      }
    })
    .catch(() => {
      dot.className = "dot off";
      text.textContent = "Offline";
    });
}
setInterval(checkVyre, 2000);

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

function timeSince(ts) {
  const seconds = Math.floor((Date.now() - ts) / 1000);
  const intervals = [[86400, "d"], [3600, "h"], [60, "m"]];
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
      if (!el("accountName").value.trim()) el("accountName").value = me.name;
      loadAvatar(me.id);
      loadStats(me.id);
    })
    .catch(() => {
      currentUserId = null;
      currentUsername = null;
      el("accName").textContent = "Not logged in";
      el("accHandle").textContent = "Open roblox.com and sign in";
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
}

function loadVaultAccounts() {
  const list = el("accountList");
  list.innerHTML = '<div class="empty loading">Loading…</div>';
  timeoutFetch(VYRE_URL + "/list_accounts", { method: "GET" }, 3000)
    .then((res) => {
      if (!res.ok) throw new Error();
      return res.json();
    })
    .then((accounts) => {
      el("accBadge").textContent = String(accounts.length);
      if (!accounts.length) {
        list.innerHTML = '<div class="empty">No accounts saved in Vyre yet</div>';
        return;
      }
      list.innerHTML = accounts.map((a) => {
        const displayName = a.display_name || a.username || a.name;
        const sub = a.username ? "@" + a.username : a.name;
        return `<div class="acc-item" style="display:flex; justify-content:space-between; align-items:center;">
          <div style="display:flex; align-items:center; gap:8px; min-width:0; flex:1;">
            <div class="acc-dot" style="background:${a.color};border-color:${a.color}"></div>
            <div class="acc-info" style="min-width:0; flex:1;">
              <div class="acc-name" style="white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${displayName}</div>
              <div class="acc-user" style="white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${sub}</div>
            </div>
          </div>
          <button class="btn ghost sm play-btn" data-id="${a.id}" style="padding:4px 8px; font-size:10px; width:auto; flex-shrink:0;">▶ Launch</button>
        </div>`;
      }).join("");

      list.querySelectorAll(".play-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
          const accountId = btn.dataset.id;
          const gameVal = el("launchGameInput").value.trim();
          if (!gameVal) {
            alert("Please enter a Place ID or Private Server Link in the Quick Launch box.");
            return;
          }
          btn.disabled = true;
          btn.textContent = "Launching…";
          let payload = { account_id: accountId };
          if (gameVal.includes("privateServerLinkCode") || gameVal.includes("linkCode")) {
            payload.private_server_link = gameVal;
          } else {
            payload.place_id = gameVal;
          }
          timeoutFetch(VYRE_URL + "/launch_game", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          }, 5000)
            .then((res) => {
              if (res.ok) {
                btn.textContent = "Launched!";
              } else {
                btn.textContent = "Failed";
              }
              setTimeout(() => { btn.disabled = false; btn.textContent = "▶ Launch"; }, 2000);
            })
            .catch(() => {
              btn.textContent = "Offline";
              setTimeout(() => { btn.disabled = false; btn.textContent = "▶ Launch"; }, 2000);
            });
        });
      });
    })
    .catch(() => {
      list.innerHTML = '<div class="empty">Could not connect to Vyre</div>';
      el("accBadge").textContent = "—";
    });
}

function save() {
  const btn = el("captureBtn");
  btn.disabled = true;
  showStatus("Reading session…", "info");
  getCookie().then((cookie) => {
    if (!cookie) {
      showStatus("No Roblox session found. Log in first.", "error");
      btn.disabled = false;
      return;
    }
    const name = el("accountName").value.trim() || "Roblox Account";
    const proxy = el("proxy").value.trim();
    const color = el("color").value;
    const private_server_link = el("privateLink").value.trim();
    chrome.storage.local.set({ proxy, color });
    showStatus("Saving to Vyre…", "info");
    timeoutFetch(VYRE_URL + "/add_account", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, cookie, proxy, color, private_server_link }),
    }, 4000)
      .then((res) => { if (!res.ok) throw new Error("status " + res.status); })
      .then(() => {
        showStatus("Saved " + name + " to Vyre.", "success");
        btn.disabled = false;
        el("privateLink").value = "";
        addHistory(name);
        loadVaultAccounts();
      })
      .catch(() => {
        showStatus("Could not reach Vyre. Is the app open?", "error");
        btn.disabled = false;
      });
  });
}

function copyCookie() {
  getCookie().then((cookie) => {
    if (!cookie) { showStatus("No session found.", "error"); return; }
    navigator.clipboard.writeText(cookie)
      .then(() => showStatus("Cookie copied to clipboard.", "success"))
      .catch(() => showStatus("Could not copy.", "error"));
  });
}

function checkHealth() {
  showStatus("Checking cookie…", "info");
  getCookie().then((cookie) => {
    if (!cookie) { showStatus("No session cookie found.", "error"); return; }
    fetch("https://users.roblox.com/v1/users/authenticated", { credentials: "include" })
      .then((res) => {
        if (res.ok) return res.json();
        throw new Error();
      })
      .then((me) => showStatus("Cookie valid — logged in as @" + me.name, "success"))
      .catch(() => showStatus("Cookie expired or invalid.", "error"));
  });
}

function addHistory(name) {
  chrome.storage.local.get(["captureHistory"], (result) => {
    const history = result.captureHistory || [];
    history.unshift({ name, time: Date.now() });
    if (history.length > 30) history.length = 30;
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
  list.innerHTML = history.slice(0, 15).map((h) =>
    `<div class="history-item"><span class="history-name">${h.name}</span><span class="history-time">${timeSince(h.time)}</span></div>`
  ).join("");
}

function loadHistory() {
  chrome.storage.local.get(["captureHistory"], (result) => renderHistory(result.captureHistory || []));
}

function initTabs() {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
      document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
      tab.classList.add("active");
      el("panel-" + tab.dataset.tab).classList.add("active");
      if (tab.dataset.tab === "accounts") loadVaultAccounts();
    });
  });
}

function initSettings() {
  chrome.storage.local.get(["autoCapture", "loginNotify"], (saved) => {
    if (saved.autoCapture !== undefined) el("autoCapture").checked = saved.autoCapture;
    if (saved.loginNotify !== undefined) el("loginNotify").checked = saved.loginNotify;
  });
  ["autoCapture", "loginNotify"].forEach((key) => {
    el(key).addEventListener("change", (e) => {
      chrome.storage.local.set({ [key]: e.target.checked });
      chrome.runtime.sendMessage({ type: "settingChanged", key, value: e.target.checked });
    });
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
  el("healthBtn").addEventListener("click", checkHealth);
  el("refreshAccounts").addEventListener("click", loadVaultAccounts);
  el("clearHistoryBtn").addEventListener("click", () => {
    chrome.storage.local.set({ captureHistory: [] });
    renderHistory([]);
  });
  el("clearAllBtn").addEventListener("click", () => {
    chrome.storage.local.clear();
    el("proxy").value = "";
    el("color").value = "#e5484d";
    el("colorText").textContent = "#e5484d";
    el("accountName").value = "";
    el("privateLink").value = "";
    el("launchGameInput").value = "";
    el("autoCapture").checked = false;
    el("loginNotify").checked = true;
    renderHistory([]);
    showStatus("Extension data cleared.", "info");
  });

  initTabs();
  initSettings();
  checkVyre();
  loadAccount();
  loadHistory();
  loadVaultAccounts();
});
