/**
 * 音声入力モジュール (Web Speech API)
 *
 * 対応コマンド:
 *   結果入力: 「異常なし」「正常」「まる」→ 〇
 *             「要注意」「注意」「さんかく」→ △
 *             「異常あり」「異常」「ばつ」  → ×
 *   ナビ:     「次」「次へ」「つぎ」        → 次の未入力項目へ
 *             「前」「戻る」「まえ」        → 前の項目へ
 *   メモ:     「メモ」                     → メモ欄を開く
 *             「メモ ○○」                 → メモ欄を開いてテキスト入力
 *             「保存」                     → メモを保存
 */

// ─── コマンドテーブル ────────────────────────
const RESULT_MAP = [
  { words: ["異常なし", "正常", "良好", "まる", "オッケー", "オーケー"], result: "〇" },
  { words: ["要注意", "注意", "警告", "さんかく", "三角"],               result: "△" },
  { words: ["異常あり", "異常", "不良", "ばつ", "バツ"],                 result: "×" },
];

// ─── フォーカス状態 ──────────────────────────
let _focusIdx = -1;

function getRows() {
  return [...document.querySelectorAll("#inspect-container .item-row")];
}

function isReadonly() {
  return document.getElementById("inspect-container")?.classList.contains("readonly") ?? false;
}

function setFocus(idx) {
  const rows = getRows();
  if (!rows.length) return;
  _focusIdx = Math.max(0, Math.min(idx, rows.length - 1));
  rows.forEach((r, i) => r.classList.toggle("voice-focus", i === _focusIdx));
  rows[_focusIdx].scrollIntoView({ behavior: "smooth", block: "center" });
}

export function focusFirst() {
  const rows = getRows();
  for (let i = 0; i < rows.length; i++) {
    if (!rows[i].querySelector(".result-btn.active")) { setFocus(i); return; }
  }
  if (rows.length) setFocus(0);
}

function advanceFocus() {
  const rows = getRows();
  for (let i = _focusIdx + 1; i < rows.length; i++) {
    if (!rows[i].querySelector(".result-btn.active")) { setFocus(i); return; }
  }
  if (_focusIdx < rows.length - 1) setFocus(_focusIdx + 1);
}

function applyResult(resultStr) {
  if (isReadonly()) return false;
  const rows = getRows();
  if (!rows.length || _focusIdx < 0) return false;
  const btn = rows[_focusIdx].querySelector(`.result-btn[data-result="${resultStr}"]`);
  if (!btn) return false;
  btn.click();
  return true;
}

function openMemoArea(textToSet = null) {
  if (isReadonly()) return;
  const rows = getRows();
  if (!rows.length || _focusIdx < 0) return;
  const row = rows[_focusIdx];
  const itemId = row.querySelector(".result-btn")?.dataset.item;
  if (!itemId) return;
  const area = document.getElementById(`memo-area-${itemId}`);
  if (area && !area.classList.contains("open")) row.querySelector(".memo-btn")?.click();
  if (textToSet !== null) {
    const ta = document.getElementById(`memo-${itemId}`);
    if (ta) { ta.value = textToSet; ta.focus(); }
  }
}

function saveMemo() {
  if (isReadonly()) return;
  const rows = getRows();
  if (!rows.length || _focusIdx < 0) return;
  rows[_focusIdx].querySelector(".memo-save-btn")?.click();
}

// ─── コマンド解析 ────────────────────────────
function parseCommand(transcript) {
  const t = transcript.trim();

  if (/^(保存|ほぞん)$/.test(t))       return { type: "memo-save" };
  const memoText = t.match(/^メモ\s*(.+)$/);
  if (memoText)                          return { type: "memo-text", text: memoText[1] };
  if (/^(メモ|めも)$/.test(t))          return { type: "memo-open" };
  if (/^(次|次へ|つぎ|次の項目)$/.test(t)) return { type: "nav-next" };
  if (/^(前|戻る|まえ|前の項目)$/.test(t)) return { type: "nav-prev" };

  for (const { words, result } of RESULT_MAP) {
    if (words.some(w => t.includes(w))) return { type: "result", result };
  }
  return null;
}

function executeCommand(cmd) {
  if (!cmd) return false;
  switch (cmd.type) {
    case "result":
      if (applyResult(cmd.result)) { setTimeout(advanceFocus, 400); return true; }
      return false;
    case "nav-next":  advanceFocus(); return true;
    case "nav-prev":  if (_focusIdx > 0) setFocus(_focusIdx - 1); return true;
    case "memo-open": openMemoArea(); return true;
    case "memo-text": openMemoArea(cmd.text); return true;
    case "memo-save": saveMemo(); return true;
  }
  return false;
}

// ─── 現在項目の読み上げ ──────────────────────
function speakCurrentItem(onDone) {
  if (!window.speechSynthesis) { onDone?.(); return; }
  const rows = getRows();
  if (!rows.length || _focusIdx < 0) { onDone?.(); return; }
  const row = rows[_focusIdx];
  const code     = row.querySelector(".item-code")?.textContent?.trim() || "";
  const location = row.querySelector(".item-location")?.textContent?.trim() || "";
  if (!code && !location) { onDone?.(); return; }
  window.speechSynthesis.cancel();

  if (code && location) {
    // 番号を読み上げ → 0.5秒待機 → 機器名を読み上げ → 完了コールバック
    const utt1 = new SpeechSynthesisUtterance(code);
    utt1.lang = "ja-JP";
    utt1.rate = 1.0;
    utt1.onend = () => {
      setTimeout(() => {
        const utt2 = new SpeechSynthesisUtterance(location);
        utt2.lang = "ja-JP";
        utt2.rate = 1.0;
        utt2.onend = () => onDone?.();
        window.speechSynthesis.speak(utt2);
      }, 500);
    };
    window.speechSynthesis.speak(utt1);
  } else {
    const utt = new SpeechSynthesisUtterance(`${code}${location}`);
    utt.lang = "ja-JP";
    utt.rate = 1.0;
    utt.onend = () => onDone?.();
    window.speechSynthesis.speak(utt);
  }
}

// ─── 音声認識エンジン ────────────────────────
/**
 * @param {object} callbacks
 * @param {function} callbacks.onStateChange  - "listening" | "idle"
 * @param {function} callbacks.onTranscript   - { transcript, matched }
 * @returns {{ toggle, focusFirst, isListening }} | null
 */
export function initVoiceInput({ onStateChange, onTranscript } = {}) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return null;

  const recog = new SpeechRecognition();
  recog.lang            = "ja-JP";
  recog.continuous      = false;
  recog.interimResults  = false;
  recog.maxAlternatives = 3;

  let _listening = false;
  let _autoStop  = null;

  recog.onstart = () => {
    _listening = true;
    onStateChange?.("listening");
    _autoStop = setTimeout(() => { try { recog.stop(); } catch {} }, 10000);
  };

  recog.onresult = (e) => {
    clearTimeout(_autoStop);
    // 複数の認識候補からコマンドに合致するものを優先採用
    let matched = null;
    let usedTranscript = e.results[0][0].transcript;
    for (let i = 0; i < e.results[0].length; i++) {
      const t   = e.results[0][i].transcript;
      const cmd = parseCommand(t);
      if (cmd) { matched = cmd; usedTranscript = t; break; }
    }
    executeCommand(matched);
    onTranscript?.({ transcript: usedTranscript, matched: !!matched });
  };

  recog.onerror = (e) => {
    clearTimeout(_autoStop);
    _listening = false;
    if (e.error !== "no-speech") {
      onTranscript?.({ transcript: `エラー: ${e.error}`, matched: false });
    }
    onStateChange?.("idle");
  };

  recog.onend = () => {
    clearTimeout(_autoStop);
    _listening = false;
    onStateChange?.("idle");
  };

  return {
    toggle() {
      if (_listening) { try { recog.stop(); } catch {} }
      else {
        if (_focusIdx < 0) focusFirst();
        speakCurrentItem(() => {
          try { recog.start(); } catch {}
        });
      }
    },
    focusFirst,
    isListening() { return _listening; },
  };
}
