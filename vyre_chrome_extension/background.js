const VYRE_URL = "http://localhost:59124";

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "vyre-add",
    title: "Save this Roblox session to Vyre",
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
  if (!changeInfo.cookie.domain.includes("roblox.com")) return;

  if (changeInfo.removed) {
    lastCookieValue = null;
    chrome.storage.local.get(["loginNotify"], (s) => {
      if (s.loginNotify !== false) notify("Vyre", "Roblox session ended.");
    });
    return;
  }

  const newVal = changeInfo.cookie.value;
  if (newVal === lastCookieValue) return;
  lastCookieValue = newVal;

  chrome.storage.local.get(["autoCapture", "loginNotify"], (settings) => {
    if (settings.loginNotify !== false) {
      getAuthUser().then((me) => {
        notify("Vyre", "Roblox login detected" + (me ? ": " + me.name : ""));
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
          .then((res) => { if (res.ok) notify("Vyre", "Auto-captured " + name); })
          .catch(() => {});
      });
    }
  });
});
