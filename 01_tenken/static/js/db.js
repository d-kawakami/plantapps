/**
 * IndexedDB ラッパー
 * オフライン時の点検結果を一時保存し、オンライン復帰時にサーバーへ同期する
 */

const IDB_NAME    = "tenken-offline";
const IDB_VERSION = 1;
const STORE_NAME  = "pending_results";

let _db = null;

/** DBを開く（初回のみ作成） */
function openDB() {
  if (_db) return Promise.resolve(_db);
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(IDB_NAME, IDB_VERSION);
    req.onupgradeneeded = (e) => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        const store = db.createObjectStore(STORE_NAME, { keyPath: "id", autoIncrement: true });
        store.createIndex("by_item_date", ["item_id", "inspection_date"], { unique: true });
        store.createIndex("by_synced", "synced");
      }
    };
    req.onsuccess = (e) => { _db = e.target.result; resolve(_db); };
    req.onerror   = (e) => reject(e.target.error);
  });
}

/** 点検結果を保存（存在すれば上書き） */
async function saveResult(record) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx   = db.transaction(STORE_NAME, "readwrite");
    const store = tx.objectStore(STORE_NAME);
    const idx   = store.index("by_item_date");

    // 既存レコードを検索して上書き or 新規挿入
    const key = [record.item_id, record.inspection_date];
    const getReq = idx.getKey(key);
    getReq.onsuccess = () => {
      const existingId = getReq.result;
      const data = { ...record, synced: false };
      if (existingId !== undefined) {
        data.id = existingId;
        store.put(data);
      } else {
        store.add(data);
      }
      tx.oncomplete = () => resolve(data);
      tx.onerror    = (e) => reject(e.target.error);
    };
    getReq.onerror = (e) => reject(e.target.error);
  });
}

/** 指定日・指定item_idの結果を取得 */
async function getResult(itemId, date) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx    = db.transaction(STORE_NAME, "readonly");
    const store = tx.objectStore(STORE_NAME);
    const idx   = store.index("by_item_date");
    const req   = idx.get([itemId, date]);
    req.onsuccess = () => resolve(req.result || null);
    req.onerror   = (e) => reject(e.target.error);
  });
}

/** 指定日の全結果を取得 */
async function getAllResultsForDate(date) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx    = db.transaction(STORE_NAME, "readonly");
    const store = tx.objectStore(STORE_NAME);
    const req   = store.getAll();
    req.onsuccess = () => {
      const all = req.result.filter(r => r.inspection_date === date);
      resolve(all);
    };
    req.onerror = (e) => reject(e.target.error);
  });
}

/** 未同期レコードを全件取得 */
async function getPendingResults() {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx    = db.transaction(STORE_NAME, "readonly");
    const store = tx.objectStore(STORE_NAME);
    const idx   = store.index("by_synced");
    const req   = idx.getAll(IDBKeyRange.only(false));
    req.onsuccess = () => resolve(req.result);
    req.onerror   = (e) => reject(e.target.error);
  });
}

/** IDを指定してsynced=trueに更新 */
async function markSynced(ids) {
  if (!ids.length) return;
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx    = db.transaction(STORE_NAME, "readwrite");
    const store = tx.objectStore(STORE_NAME);
    ids.forEach(id => {
      const getReq = store.get(id);
      getReq.onsuccess = () => {
        if (getReq.result) {
          store.put({ ...getReq.result, synced: true });
        }
      };
    });
    tx.oncomplete = () => resolve();
    tx.onerror    = (e) => reject(e.target.error);
  });
}

/** 指定日の全結果をIndexedDBから削除 */
async function clearResultsForDate(date) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx    = db.transaction(STORE_NAME, "readwrite");
    const store = tx.objectStore(STORE_NAME);
    const req   = store.getAll();
    req.onsuccess = () => {
      const toDelete = req.result.filter(r => r.inspection_date === date);
      toDelete.forEach(r => store.delete(r.id));
      tx.oncomplete = () => resolve(toDelete.length);
      tx.onerror    = (e) => reject(e.target.error);
    };
    req.onerror = (e) => reject(e.target.error);
  });
}

export { saveResult, getResult, getAllResultsForDate, getPendingResults, markSynced, clearResultsForDate };
