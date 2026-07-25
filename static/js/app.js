/* Dashboard frontend logic.
 * Polls the Flask backend (see app.py) on a timer and renders the results.
 * No build step, no framework -- kept intentionally simple so it's easy to
 * hand off and modify later. */

const STATUS_INTERVAL_MS = 15000;
const GAMES_INTERVAL_MS = 20000;
const TOPKILLS_INTERVAL_MS = 60000;

const avatarUrl = (username) => `https://mc-heads.net/avatar/${encodeURIComponent(username)}/64`;

/* Minimal line-icon glyphs (stroke = currentColor) for the game cards.
 * Add a case here if a new game in services/site_games.py needs a new icon. */
const ICONS = {
  sword: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 3.5 20.5 9.5 12 18 6 20 4 18 6 12 14.5 3.5Z"/><path d="M6 12 12 18"/><path d="M3 21 6 18"/></svg>`,
  house: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 11 12 4l8 7"/><path d="M6 10v9h12v-9"/><path d="M10 19v-5h4v5"/></svg>`,
  dice: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="3"/><circle cx="8.5" cy="8.5" r="1" fill="currentColor" stroke="none"/><circle cx="15.5" cy="8.5" r="1" fill="currentColor" stroke="none"/><circle cx="8.5" cy="15.5" r="1" fill="currentColor" stroke="none"/><circle cx="15.5" cy="15.5" r="1" fill="currentColor" stroke="none"/><circle cx="12" cy="12" r="1" fill="currentColor" stroke="none"/></svg>`,
  cube: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3 20 7.5v9L12 21 4 16.5v-9L12 3Z"/><path d="M4 7.5 12 12l8-4.5"/><path d="M12 21v-9"/></svg>`,
};

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function renderPulseBar() {
  const bar = document.getElementById("pulse-bar");
  bar.innerHTML = "";
  for (let i = 0; i < 14; i++) {
    const span = document.createElement("span");
    span.style.animationDelay = `${(i * 0.09).toFixed(2)}s`;
    bar.appendChild(span);
  }
}

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || `${res.status} ${res.statusText}`);
  }
  return res.json();
}

/* ---------------- Status / hero ---------------- */
async function refreshStatus() {
  const dot = document.getElementById("live-dot");
  const connChip = document.getElementById("server-online");
  try {
    const data = await fetchJSON("/api/status");
    const ping = data.ping || {};

    document.getElementById("server-name").textContent = ping.address || "السيرفر";
    document.getElementById("server-motd").textContent = ping.online
      ? (ping.motd || "—")
      : "تعذّر الوصول للسيرفر حالياً";
    document.getElementById("server-version").textContent = ping.version || "—";
    document.getElementById("server-latency").textContent = ping.online ? `${ping.latency_ms} ms` : "—";

    dot.classList.toggle("is-online", !!ping.online);
    dot.classList.toggle("is-offline", !ping.online);
    connChip.textContent = ping.online ? "متصل" : "غير متصل";

    const headline = data.network_total ?? ping.players_online;
    document.getElementById("online-count").textContent =
      headline != null ? headline.toLocaleString("en-US") : "—";

    document.getElementById("hero-source").textContent = data.network_total != null
      ? `  `
      : `مصدر البيانات: قياس مباشر عبر ${ping.address || "السيرفر"}`;
  } catch (err) {
    connChip.textContent = "خطأ";
    dot.classList.remove("is-online");
    dot.classList.add("is-offline");
    console.error("status refresh failed:", err);
  }
}

/* ---------------- Games grid (also the leaderboard selector) ---------------- */
let currentGames = [];

function renderGameCard(game) {
  const card = el("div", "game-card");
  card.dataset.key = game.key;

  const icon = el("div", "game-icon");
  icon.innerHTML = ICONS[game.icon] || ICONS.cube;
  card.appendChild(icon);

  card.appendChild(el("div", "game-name", game.name));
  if (game.subtitle) card.appendChild(el("div", "game-subtitle", game.subtitle));

  if (game.has_live_data) {
    card.appendChild(el("div", "game-players", (game.players ?? 0).toLocaleString("en-US")));
    card.appendChild(el("div", "game-players-label", "لاعب متصل"));
  } else {
    card.appendChild(el("div", "soon-badge", "قريباً"));
  }

  card.addEventListener("click", () => selectGame(game.key));
  return card;
}

async function refreshGames() {
  const grid = document.getElementById("games-grid");
  try {
    const games = await fetchJSON("/api/games");
    currentGames = games;
    grid.innerHTML = "";
    if (!games.length) {
      grid.appendChild(el("div", "empty-state", "لا توجد ألعاب مُعرّفة بعد"));
      return;
    }
    games.forEach((g) => grid.appendChild(renderGameCard(g)));
    highlightActiveCard();

    // First load: auto-select a game so the leaderboard panel isn't empty.
    if (activeGameKey === null) {
      const first = games.find((g) => g.has_live_data) || games[0];
      selectGame(first.key);
    }
  } catch (err) {
    grid.innerHTML = "";
    grid.appendChild(el("div", "empty-state", `تعذّر تحميل الألعاب: ${err.message}`));
  }
}

function highlightActiveCard() {
  document.querySelectorAll(".game-card").forEach((card) => {
    card.classList.toggle("is-active", card.dataset.key === activeGameKey);
  });
}

/* ---------------- Leader row (shared by top-kills + per-game boards) ---------------- */
function renderLeaderRow(entry) {
  const row = el("li", "leader-row");
  row.appendChild(el("span", "leader-rank", `#${entry.rank}`));

  const avatar = document.createElement("img");
  avatar.className = "leader-avatar";
  avatar.src = avatarUrl(entry.username);
  avatar.alt = entry.username;
  avatar.loading = "lazy";
  row.appendChild(avatar);

  row.appendChild(el("span", "leader-name", entry.username));
  return row;
}

function renderLeaderList(listEl, entries, emptyMessage) {
  listEl.innerHTML = "";
  if (!entries || !entries.length) {
    listEl.appendChild(el("li", "empty-state", emptyMessage));
    return;
  }
  entries.forEach((e) => listEl.appendChild(renderLeaderRow(e)));
}

/* ---------------- Top kills panel ---------------- */
async function refreshTopKills() {
  const list = document.getElementById("topkills-list");
  const source = document.getElementById("topkills-source");
  try {
    const board = await fetchJSON("/api/leaderboards/top-kills");
    source.textContent = `${board.game} · ${board.title}`;
    renderLeaderList(list, board.entries, "لا توجد بيانات كيلز متاحة حالياً");
  } catch (err) {
    source.textContent = "—";
    renderLeaderList(list, [], `تعذّر تحميل الترتيب: ${err.message}`);
  }
}

/* ---------------- Per-game leaderboard (driven by card selection) ---------------- */
let activeGameKey = null;
let activeBoards = [];

function renderBoardTabs() {
  const container = document.getElementById("board-tabs");
  const list = document.getElementById("board-list");
  const hint = document.getElementById("board-hint");
  container.innerHTML = "";

  const game = currentGames.find((g) => g.key === activeGameKey);

  if (game && !game.has_live_data) {
    hint.textContent = "غير متاح بعد";
    list.innerHTML = "";
    list.appendChild(el("li", "empty-state", "سيتم عرض الترتيب هنا بعد ربط الموقع بسيرفركم الخاص"));
    return;
  }

  if (!activeBoards.length) {
    hint.textContent = "—";
    list.innerHTML = "";
    list.appendChild(el("li", "empty-state", "لا توجد فئات ترتيب لهذه اللعبة"));
    return;
  }

  hint.textContent = `${activeBoards.length} فئة ترتيب`;
  activeBoards.forEach((board, idx) => {
    const btn = el("button", "tab-btn", board.title);
    btn.type = "button";
    if (idx === 0) btn.classList.add("is-active");
    btn.addEventListener("click", () => {
      container.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("is-active"));
      btn.classList.add("is-active");
      renderLeaderList(list, board.entries, "لا توجد بيانات لهذه الفئة");
    });
    container.appendChild(btn);
  });

  renderLeaderList(list, activeBoards[0].entries, "لا توجد بيانات لهذه الفئة");
}

async function selectGame(key) {
  activeGameKey = key;
  highlightActiveCard();

  const game = currentGames.find((g) => g.key === key);
  document.getElementById("selected-game-name").textContent = game ? game.name : key;

  if (game && !game.has_live_data) {
    activeBoards = [];
    renderBoardTabs();
    return;
  }

  const list = document.getElementById("board-list");
  list.innerHTML = "";
  list.appendChild(el("li", "empty-state", "جارِ التحميل…"));
  try {
    activeBoards = await fetchJSON(`/api/leaderboards/${encodeURIComponent(key)}`);
    renderBoardTabs();
  } catch (err) {
    activeBoards = [];
    list.innerHTML = "";
    list.appendChild(el("li", "empty-state", `تعذّر تحميل الترتيب: ${err.message}`));
  }
}

/* ---------------- Boot ---------------- */
renderPulseBar();
refreshStatus();
refreshGames();
refreshTopKills();

setInterval(refreshStatus, STATUS_INTERVAL_MS);
setInterval(refreshGames, GAMES_INTERVAL_MS);
setInterval(refreshTopKills, TOPKILLS_INTERVAL_MS);
