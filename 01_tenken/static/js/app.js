/**
 * 日常点検アプリ メインロジック
 * - IndexedDB への結果保存（即時）
 * - サーバーへのリアルタイム保存（オンライン時）
 * - オフライン時のキュー管理と復帰後の自動同期
 */

import {
  saveResult, getResult, getAllResultsForDate,
  getPendingResults, markSynced
} from "./db.js";

/* ─── 状態 ──────────────────────────────────── */
let isOnline   = navigator.onLine;
let syncTimer  = null;
const _now     = new Date();
const TODAY    = `${_now.getFullYear()}-${String(_now.getMonth()+1).padStart(2,"0")}-${String(_now.getDate()).padStart(2,"0")}`; // ローカル日付 YYYY-MM-DD

/* ─── ユーティリティ ────────────────────────── */
function getWeekNumber(date = new Date()) {
  const day  = date.getDate();
  return Math.ceil(day / 7);          // 1〜5（第1〜5週）
}

function getDayOfWeek(date = new Date()) {
  const d = date.getDay();            // 0=日, 1=月, ..., 6=土
  return d === 0 ? 7 : d;            // 1=月 〜 7=日
}

function formatDateJP(dateStr) {
  const d = new Date(dateStr + "T00:00:00");
  const dow = "日月火水木金土"[d.getDay()];
  return `${d.getFullYear()}年${d.getMonth()+1}月${d.getDate()}日（${dow}）`;
}

/* ─── オフライン検知 ────────────────────────── */
function updateOnlineStatus() {
  isOnline = navigator.onLine;
  document.body.classList.toggle("offline", !isOnline);
  updateSyncStatus();
  if (isOnline) syncToServer();
}

window.addEventListener("online",  updateOnlineStatus);
window.addEventListener("offline", updateOnlineStatus);

/* ─── 同期ステータスUI ──────────────────────── */
let syncEl = null;

function getSyncEl() {
  if (!syncEl) {
    syncEl = document.getElementById("sync-status");
  }
  return syncEl;
}

async function updateSyncStatus() {
  const el = getSyncEl();
  if (!el) return;
  const dot = el.querySelector(".sync-dot");
  const lbl = el.querySelector(".sync-label");

  if (!isOnline) {
    dot.className = "sync-dot pending";
    lbl.textContent = "オフライン（未同期あり）";
    el.classList.add("show");
    return;
  }

  const pending = await getPendingResults();
  if (pending.length > 0) {
    dot.className = "sync-dot pending";
    lbl.textContent = `未同期 ${pending.length} 件`;
    el.classList.add("show");
  } else {
    dot.className = "sync-dot synced";
    lbl.textContent = "同期済み";
    el.classList.add("show");
    clearTimeout(syncTimer);
    syncTimer = setTimeout(() => el.classList.remove("show"), 2500);
  }
}

/* ─── サーバー同期 ──────────────────────────── */
async function syncToServer() {
  if (!isOnline) return;
  const pending = await getPendingResults();
  if (!pending.length) return;

  try {
    const res = await fetch("/api/results/batch", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(pending.map(r => ({
        item_id:         r.item_id,
        inspection_date: r.inspection_date,
        result:          r.result,
        memo:            r.memo || ""
      })))
    });
    if (res.ok) {
      await markSynced(pending.map(r => r.id));
      updateSyncStatus();
    }
  } catch (e) {
    // サーバー未応答 → 次回再試行
  }
}

/* サーバー死活確認（30秒ごと）*/
async function checkHealth() {
  try {
    const res = await fetch("/api/health", { signal: AbortSignal.timeout(3000) });
    isOnline = res.ok;
  } catch {
    isOnline = false;
  }
  document.body.classList.toggle("offline", !isOnline);
  if (isOnline) syncToServer();
}
setInterval(checkHealth, 30000);

/* ════════════════════════════════════════════
   トップページ (index.html) 用関数
   ════════════════════════════════════════════ */

export function initIndexPage() {
  const today   = new Date();
  const todayDow = getDayOfWeek(today);

  // 今日の曜日カードをハイライト
  document.querySelectorAll(".day-card").forEach(card => {
    if (parseInt(card.dataset.day) === todayDow) {
      card.classList.add("today");
    }
  });

  // 週番号を表示
  const wn = getWeekNumber(today);
  const el = document.getElementById("week-number");
  if (el) el.textContent = `第${wn}週`;

  updateOnlineStatus();
};

/* ════════════════════════════════════════════
   点検入力ページ (inspect.html) 用関数
   ════════════════════════════════════════════ */

// 週選択で共有する状態
let _currentDay  = null;
let _currentWeek = null;
let _currentDate = TODAY;
const _todayWeek = getWeekNumber(new Date());

// 先発グループキャッシュ: group_name -> [machine_obj, ...]
let _senpatuGroups = {};

export function initInspectPage(dayOfWeek, dateStr = TODAY) {
  const date    = new Date(dateStr + "T00:00:00");
  const weekNum = getWeekNumber(date);

  _currentDay  = dayOfWeek;
  _currentWeek = weekNum;
  _currentDate = dateStr;

  // 日付・週表示
  const dateEl = document.getElementById("current-date");
  const weekEl = document.getElementById("week-badge");
  if (dateEl) dateEl.textContent = formatDateJP(dateStr);
  if (weekEl) weekEl.textContent = `第${weekNum}週`;

  // 週選択ボタンの初期状態を設定（水曜日のみ存在）
  _updateWeekSelector(weekNum);

  loadInspectItems(dayOfWeek, weekNum, dateStr);
  updateOnlineStatus();
}

/** 週選択ボタンのアクティブ状態を更新 */
function _updateWeekSelector(selectedWeek) {
  document.querySelectorAll(".week-sel-btn").forEach(btn => {
    const w = parseInt(btn.dataset.week);
    btn.classList.toggle("active", w === selectedWeek);
    // 現在の実際の週に★マークを付ける
    btn.classList.toggle("today-week", w === _todayWeek);
  });
  // ヘッダーの週バッジも更新
  const weekEl = document.getElementById("week-badge");
  if (weekEl) weekEl.textContent = `第${selectedWeek}週`;
}

/** 週を切り替えて項目を再ロード（水曜日用） */
export function switchWeek(week) {
  if (_currentDay === null) return;
  _currentWeek = week;
  _updateWeekSelector(week);
  loadInspectItems(_currentDay, week, _currentDate);
};

/* 点検項目を取得して画面に描画 */
async function loadInspectItems(day, week, dateStr) {
  const container = document.getElementById("inspect-container");
  container.innerHTML = `<div class="loading"><div class="spinner"></div>読み込み中…</div>`;

  let items = [];
  try {
    const res = await fetch(`/api/items?day=${day}&week=${week}`);
    if (res.ok) items = await res.json();
  } catch (e) {
    container.innerHTML = `<p style="padding:1rem;color:red">点検項目の取得に失敗しました。</p>`;
    return;
  }

  if (!items.length) {
    container.innerHTML = `<p style="padding:1rem;color:#666">本日（第${week}週）の点検項目はありません。</p>`;
    return;
  }

  // 既存の点検結果・先発グループをサーバーとIndexedDBから取得して統合
  const [serverResults, localResults, senpatuList] = await Promise.all([
    fetchServerResults(dateStr),
    getAllResultsForDate(dateStr),
    fetchSenpatuGroups(day)
  ]);
  const resultMap = buildResultMap(serverResults, localResults);

  // 先発グループをキャッシュ
  _senpatuGroups = {};
  for (const g of senpatuList) {
    if (!_senpatuGroups[g.group_name]) _senpatuGroups[g.group_name] = [];
    _senpatuGroups[g.group_name].push(g);
  }

  // 建物ごとにグループ化
  const groups = groupByBuilding(items);

  // DOM構築
  container.innerHTML = "";
  for (const [building, bItems] of Object.entries(groups)) {
    container.appendChild(buildBuildingSection(building, bItems, resultMap, dateStr));
  }

  // 進捗バー更新
  updateProgress(items, resultMap);
}

async function fetchServerResults(dateStr) {
  try {
    const res = await fetch(`/api/results?date=${dateStr}`);
    if (res.ok) return await res.json();
  } catch {}
  return [];
}

async function fetchSenpatuGroups(day) {
  try {
    const res = await fetch(`/api/senpatu?day=${day}`);
    if (res.ok) return await res.json();
  } catch {}
  return [];
}

/** サーバー結果とローカル(IndexedDB)結果をマージ（ローカルが最新として優先） */
function buildResultMap(serverList, localList) {
  const map = {};
  for (const r of serverList) {
    map[r.item_id] = { result: r.result, memo: r.memo || "" };
  }
  for (const r of localList) {
    map[r.item_id] = { result: r.result, memo: r.memo || "" };
  }
  return map;
}

function groupByBuilding(items) {
  const groups = {};
  for (const item of items) {
    if (!groups[item.building]) groups[item.building] = [];
    groups[item.building].push(item);
  }
  return groups;
}

/** 建物セクションのDOM生成 */
function buildBuildingSection(building, items, resultMap, dateStr) {
  const section = document.createElement("div");
  section.className = "building-section";

  const header = document.createElement("div");
  header.className = "building-header";
  header.innerHTML = `
    <span>${building}</span>
    <span class="bldg-count" id="bcount-${CSS.escape(building)}">0/${items.length} 件完了</span>
  `;
  section.appendChild(header);

  for (const item of items) {
    section.appendChild(buildItemRow(item, resultMap[item.id] || {}, dateStr));
  }

  updateBuildingCount(building, items, resultMap);
  return section;
}

/** 点検行1行のDOM生成 */
function buildItemRow(item, current, dateStr) {
  const row = document.createElement("div");
  row.className = "item-row";
  row.id = `row-${item.id}`;
  row.dataset.resultHint = item.result_hint || "";

  const descHTML = item.description
    ? `<div class="item-description">${item.description}</div>` : "";

  // Excelから読み込んだ参照メモ（F/M列）
  const baseMemoHTML = item.base_memo
    ? `<div class="base-memo">${item.base_memo}</div>` : "";

  // 故障リストからの故障内容
  const faultHTML = item.fault_memo
    ? `<div class="fault-memo">⚠ 故障: ${item.fault_memo}</div>` : "";

  // 先発バッジ（G/N列）
  const senpatuHTML = buildSenpatuBadge(item.senpatu, item.location);

  // ユーザーメモの状態
  const hasUserMemo = !!current.memo;
  const hasBaseMemo = !!item.base_memo;
  const memoBtnClass = hasUserMemo ? "has-memo" : (hasBaseMemo ? "has-base-memo" : "");
  const memoBtnLabel = hasUserMemo ? "✏️ メモあり" : (hasBaseMemo ? "📋 参照あり" : "✏️ メモ");

  const resultHintHTML = (() => {
    const h = item.result_hint;
    if (!h) return "";
    const cls = h === "〇" ? "hint-ok" : (h === "×" ? "hint-ng" : (h === "△" || h === "▲" ? "hint-tri" : ""));
    return `<span class="result-hint-badge ${cls}">${h}</span>`;
  })();

  row.innerHTML = `
    <div class="item-code">${item.code}</div>
    <div class="item-info">
      <div class="item-location">${item.location}${resultHintHTML}</div>
      ${descHTML}
      ${faultHTML}
      ${senpatuHTML}
      ${baseMemoHTML}
    </div>
    <div class="item-controls">
      <div class="result-btns">
        ${["〇","△","×"].map(r => `
          <button class="result-btn ${current.result === r ? "active" : ""}"
                  data-item="${item.id}"
                  data-date="${dateStr}"
                  data-building="${item.building}"
                  data-result="${r}"
                  aria-label="結果: ${r}">
            ${r}
          </button>`).join("")}
      </div>
      <button class="memo-btn ${memoBtnClass}"
              data-item="${item.id}"
              aria-label="メモ">
        ${memoBtnLabel}
      </button>
    </div>
    <div class="memo-area ${hasUserMemo ? "open" : ""}" id="memo-area-${item.id}">
      <textarea class="memo-textarea"
                id="memo-${item.id}"
                placeholder="追記メモを入力">${current.memo || ""}</textarea>
      <button class="memo-save-btn" data-item="${item.id}" data-date="${dateStr}">
        保存
      </button>
    </div>
  `;

  // 〇/×/△ ボタン イベント
  row.querySelectorAll(".result-btn").forEach(btn => {
    btn.addEventListener("click", () => onResultClick(btn));
  });

  // メモボタン イベント
  row.querySelector(".memo-btn").addEventListener("click", (e) => {
    const area = document.getElementById(`memo-area-${item.id}`);
    area.classList.toggle("open");
    if (area.classList.contains("open")) {
      area.querySelector("textarea").focus();
    }
  });

  // メモ保存ボタン イベント
  row.querySelector(".memo-save-btn").addEventListener("click", async (e) => {
    const id   = parseInt(e.target.dataset.item);
    const date = e.target.dataset.date;
    const memo = document.getElementById(`memo-${id}`).value;
    await onMemoSave(id, date, memo, item.building);
    const memoBtn = row.querySelector(".memo-btn");
    const hasBase = !!item.base_memo;
    memoBtn.classList.remove("has-memo", "has-base-memo");
    if (memo) {
      memoBtn.classList.add("has-memo");
      memoBtn.textContent = "✏️ メモあり";
    } else if (hasBase) {
      memoBtn.classList.add("has-base-memo");
      memoBtn.textContent = "📋 参照あり";
    } else {
      memoBtn.textContent = "✏️ メモ";
    }
  });

  return row;
}

/**
 * 先発バッジHTMLを生成する。
 * @param {string} senpatu  item.senpatu の値
 * @returns {string} HTML文字列（先発なしの場合は ""）
 */
function buildSenpatuBadge(senpatu, location = "") {
  if (!senpatu) return "";
  const sen = senpatu.trim();
  if (!sen) return "";

  const currentMonth = new Date().getMonth() + 1;  // 1〜12

  // A/B/C → 先発グループ参照
  if (sen === "A" || sen === "B" || sen === "C") {
    const machines = _senpatuGroups[sen] || [];
    if (!machines.length) return "";

    // 場所名と部分一致する機器があればその行のみ表示
    // 完全部分一致 → 先頭6〜3文字プレフィックス一致 の順に試みる
    const loc = location.trim();
    let matched = [];
    if (loc) {
      // 1. 完全部分一致（既存ロジック）
      matched = machines.filter(m => m.machine_name.includes(loc) || loc.includes(m.machine_name));
      // 2. プレフィックス一致（6〜3文字）
      if (!matched.length) {
        for (let n = 6; n >= 3; n--) {
          const locPre = loc.slice(0, n);
          if (locPre.length < n) continue; // loc が n 文字未満なら短縮してもしかたない
          const found = machines.filter(m => m.machine_name.slice(0, n) === locPre);
          if (found.length) { matched = found; break; }
        }
      }
    }
    const displayMachines = matched.length > 0 ? matched : machines;

    const parts = displayMachines.map(m => {
      let nums = [];
      try { nums = JSON.parse(m.monthly_numbers); } catch {}
      const num = nums[currentMonth - 1] || "";
      return num
        ? `<strong>${m.machine_name}</strong>${num}号`
        : `<strong>${m.machine_name}</strong>`;
    });
    return `<div class="senpatu-badge">先発${sen}: ${parts.join(" / ")}</div>`;
  }

  // JSON配列（12か月分の値）
  if (sen.startsWith("[")) {
    try {
      const arr = JSON.parse(sen);
      const val = arr[currentMonth - 1] || "";
      return val ? `<div class="senpatu-badge">先発: ${val}号</div>` : "";
    } catch {}
  }

  // 直値（数字文字列など）
  return `<div class="senpatu-badge">先発: ${sen}</div>`;
}

/* ─── 結果ボタン クリックハンドラ ────────────── */
async function onResultClick(btn) {
  const itemId  = parseInt(btn.dataset.item);
  const dateStr = btn.dataset.date;
  const result  = btn.dataset.result;
  const building = btn.dataset.building;

  // 同じボタンを再タップ → クリア
  const isActive = btn.classList.contains("active");
  const newResult = isActive ? "" : result;

  // ボタンUIを即時更新
  const row = btn.closest(".item-row");
  row.querySelectorAll(".result-btn").forEach(b => b.classList.remove("active"));
  if (newResult) btn.classList.add("active");

  // IndexedDBに保存
  const current = await getResult(itemId, dateStr);
  const memo = current ? (current.memo || "") : "";
  const record = { item_id: itemId, inspection_date: dateStr, result: newResult, memo };
  await saveResult(record);

  // サーバーにリアルタイム保存（オンライン時）
  if (isOnline) {
    try {
      await fetch("/api/results", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(record)
      });
      await markSynced((await getPendingResults())
        .filter(r => r.item_id === itemId && r.inspection_date === dateStr)
        .map(r => r.id));
    } catch {}
  }

  // 進捗・件数カウントを更新
  updateProgressFromDOM();
  updateBuildingCountFromDOM(building);
  updateSyncStatus();
}

/* ─── メモ保存ハンドラ ──────────────────────── */
async function onMemoSave(itemId, dateStr, memo, building) {
  const current = await getResult(itemId, dateStr);
  const existingResult = current ? (current.result || "") : "";
  const record = { item_id: itemId, inspection_date: dateStr, result: existingResult, memo };
  await saveResult(record);

  if (isOnline) {
    try {
      await fetch("/api/results", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(record)
      });
    } catch {}
  }
  updateSyncStatus();
}

/* ─── 進捗バー ──────────────────────────────── */
function updateProgressFromDOM() {
  const allRows    = document.querySelectorAll(".item-row");
  const doneRows   = document.querySelectorAll(".item-row .result-btn.active");
  const total      = allRows.length;
  const done       = new Set([...doneRows].map(b => b.dataset.item)).size;
  const pct        = total ? Math.round(done / total * 100) : 0;

  const fill = document.getElementById("progress-fill");
  const lbl  = document.getElementById("progress-label");
  if (fill) fill.style.width = pct + "%";
  if (lbl)  lbl.textContent  = `${done} / ${total} 件完了 (${pct}%)`;
}

function updateProgress(items, resultMap) {
  const total = items.length;
  const done  = items.filter(i => resultMap[i.id]?.result).length;
  const pct   = total ? Math.round(done / total * 100) : 0;

  const fill = document.getElementById("progress-fill");
  const lbl  = document.getElementById("progress-label");
  if (fill) fill.style.width = pct + "%";
  if (lbl)  lbl.textContent  = `${done} / ${total} 件完了 (${pct}%)`;
}

function updateBuildingCount(building, items, resultMap) {
  const done  = items.filter(i => resultMap[i.id]?.result).length;
  const total = items.length;
  const el = document.getElementById(`bcount-${CSS.escape(building)}`);
  if (el) el.textContent = `${done}/${total} 件完了`;
}

function updateBuildingCountFromDOM(building) {
  const escaped = CSS.escape(building);
  const el = document.getElementById(`bcount-${escaped}`);
  if (!el) return;
  const section = el.closest(".building-section");
  const total = section.querySelectorAll(".item-row").length;
  const done  = new Set(
    [...section.querySelectorAll(".result-btn.active")].map(b => b.dataset.item)
  ).size;
  el.textContent = `${done}/${total} 件完了`;
}
