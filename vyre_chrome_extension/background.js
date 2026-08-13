const VYRE_URL = "http://localhost:59124";

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "vyre-add",
    title: "Add this Roblox account to Vyre",
    contexts: ["page"],
    documentUrlPatterns: ["*://*.roblox.com/*"],
  });
  chrome.contextMenus.create({
    id: "vyre-copy",
    title: "Copy Roblox cookie",
    contexts: ["page"],
    documentUrlPatterns: ["*://*.roblox.com/*"],
  });
});

function notify(title, message) {
  chrome.notifications.create({
    type: "basic",
    iconUrl: "icon.png",
    title,
    message,
  });
}

function getCookie() {
  return new Promise((resolve) => {
    chrome.cookies.getAll({ domain: "roblox.com", name: ".ROBLOSECURITY" }, (cookies) => {
      resolve(cookies && cookies.length ? cookies[0].value : "");
    });
  });
}

function getAuthUser() {
  return fetch("https://users.roblox.com/v1/users/authenticated", { credentials: "include" })
    .then((res) => (res.ok ? res.json() : null))
    .catch(() => null);
}

chrome.contextMenus.onClicked.addListener((info) => {
  if (info.menuItemId === "vyre-add") {
    getCookie().then((cookie) => {
      if (!cookie) { notify("Vyre", "No Roblox session found. Log in first."); return; }
      getAuthUser().then((me) => {
        const name = (me && me.name) || "Roblox Account";
        return fetch(VYRE_URL + "/add_account", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name, cookie, proxy: "", color: "#e5484d" }),
        }).then((res) => {
          if (!res.ok) throw new Error();
          notify("Vyre", "Saved " + name + " to Vyre.");
        });
      }).catch(() => notify("Vyre", "Could not reach Vyre. Is the app open?"));
    });
  }

  if (info.menuItemId === "vyre-copy") {
    getCookie().then((cookie) => {
      if (!cookie) { notify("Vyre", "No session found."); return; }
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs[0]) {
          chrome.scripting.executeScript({
            target: { tabId: tabs[0].id },
            func: (text) => navigator.clipboard.writeText(text),
            args: [cookie],
          });
          notify("Vyre", "Cookie copied to clipboard.");
        }
      });
    });
  }
});

function updateBadge(tabId, url) {
  const onRoblox = url && url.includes("roblox.com");
  chrome.action.setBadgeText({ tabId, text: onRoblox ? "●" : "" });
  chrome.action.setBadgeBackgroundColor({ color: "#e5484d" });
}

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === "complete") updateBadge(tabId, tab.url || "");
});

chrome.tabs.onActivated.addListener(({ tabId }) => {
  chrome.tabs.get(tabId, (tab) => updateBadge(tabId, tab.url || ""));
});

let lastCookieValue = null;

chrome.cookies.onChanged.addListener((changeInfo) => {
  if (changeInfo.cookie.name !== ".ROBLOSECURITY") return;
  if (changeInfo.cookie.domain.includes("roblox.com") === false) return;

  if (changeInfo.removed) {
    lastCookieValue = null;
    chrome.storage.local.get(["loginNotify"], (s) => {
      if (s.loginNotify !== false) notify("Vyre", "Roblox session ended — cookie removed.");
    });
    return;
  }

  const newVal = changeInfo.cookie.value;
  if (newVal === lastCookieValue) return;
  lastCookieValue = newVal;

  chrome.storage.local.get(["autoCapture", "loginNotify"], (settings) => {
    if (settings.loginNotify !== false) {
      getAuthUser().then((me) => {
        const who = me ? me.name : "Unknown";
        notify("Vyre", "Roblox login detected: " + who);
      });
    }

    if (settings.autoCapture) {
      getAuthUser().then((me) => {
        const name = (me && me.name) || "Roblox Account";
        fetch(VYRE_URL + "/add_account", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name, cookie: newVal, proxy: "", color: "#e5484d" }),
        })
          .then((res) => { if (res.ok) notify("Vyre", "Auto-captured session for " + name); })
          .catch(() => {});
      });
    }
  });
});

chrome.alarms.create("friendCheck", { periodInMinutes: 5 });

let previousOnlineFriends = new Set();

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name !== "friendCheck") return;
  chrome.storage.local.get(["friendAlerts"], (s) => {
    if (!s.friendAlerts) return;
    getAuthUser().then((me) => {
      if (!me) return;
      fetch(`https://friends.roblox.com/v1/users/${me.id}/friends`)
        .then((res) => res.json())
        .then((data) => {
          const friendIds = (data.data || []).map((f) => f.id);
          if (!friendIds.length) return;
          return fetch("https://presence.roblox.com/v1/presence/users", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ userIds: friendIds }),
            credentials: "include",
          }).then((res) => res.json());
        })
        .then((presenceData) => {
          if (!presenceData) return;
          const currentOnline = new Set();
          const nameMap = {};
          (presenceData.userPresences || []).forEach((p) => {
            if (p.userPresenceType === 2) {
              currentOnline.add(p.userId);
              nameMap[p.userId] = p.lastLocation || "a game";
            }
          });
          currentOnline.forEach((uid) => {
            if (!previousOnlineFriends.has(uid)) {
              fetch(`https://users.roblox.com/v1/users/${uid}`)
                .then((res) => res.json())
                .then((user) => {
                  notify("Friend Activity", user.displayName + " joined " + (nameMap[uid] || "a game"));
                })
                .catch(() => {});
            }
          });
          previousOnlineFriends = currentOnline;
        })
        .catch(() => {});
    });
  });
});

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === "settingChanged") {
    if (msg.key === "friendAlerts" && msg.value) {
      previousOnlineFriends = new Set();
    }
  }
});
