const path = require('path');
const crypto = require('crypto');
const Database = require('better-sqlite3');

const DB_PATH = process.env.KF_DB_PATH || path.join(__dirname, '..', 'kernel_finance_pro.db');

const CATEGORIES = [
  'Food', 'Transport', 'Monthly Bills', 'Stationary', 'Party', 'Shopping', 'Others'
];

let db;

function hashText(value) {
  return crypto.createHash('sha256').update(String(value || ''), 'utf8').digest('hex');
}

function normUsername(username) {
  return String(username || '').trim().toLowerCase();
}

function normAnswer(answer) {
  return String(answer || '').trim().toLowerCase();
}

function nowIso() {
  const d = new Date();
  const pad = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

function openDb() {
  db = new Database(DB_PATH);
  db.pragma('journal_mode = WAL');
  db.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username_display TEXT NOT NULL,
      username_norm TEXT NOT NULL UNIQUE,
      password_hash TEXT NOT NULL,
      security_answer_hash TEXT NOT NULL,
      currency TEXT NOT NULL DEFAULT 'INR',
      real_name TEXT NOT NULL DEFAULT '',
      theme TEXT NOT NULL DEFAULT 'dark',
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS transactions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      amount REAL NOT NULL,
      category TEXT NOT NULL,
      remark TEXT,
      created_at TEXT NOT NULL,
      FOREIGN KEY(user_id) REFERENCES users(id)
    );
  `);
  const cols = db.prepare("PRAGMA table_info(users)").all().map(r => r.name);
  if (!cols.includes('currency')) db.exec("ALTER TABLE users ADD COLUMN currency TEXT NOT NULL DEFAULT 'INR'");
  if (!cols.includes('real_name')) db.exec("ALTER TABLE users ADD COLUMN real_name TEXT NOT NULL DEFAULT ''");
  if (!cols.includes('theme')) db.exec("ALTER TABLE users ADD COLUMN theme TEXT NOT NULL DEFAULT 'dark'");
}

function closeDb() {
  if (db) {
    try { db.close(); } catch (_) { /* ignore */ }
    db = null;
  }
}

function getDb() { return db; }

function userById(id) {
  return db.prepare('SELECT * FROM users WHERE id = ?').get(id);
}

function userByUsername(username) {
  return db.prepare('SELECT * FROM users WHERE username_norm = ?').get(normUsername(username));
}

function safeUser(user) {
  if (!user) return null;
  return {
    id: user.id,
    username_display: user.username_display,
    currency: user.currency || 'INR',
    theme: user.theme || 'dark',
    real_name: user.real_name || '',
  };
}

function monthTotal(userId) {
  const now = new Date();
  const y = now.getFullYear();
  const m = now.getMonth() + 1;
  const rows = db.prepare('SELECT amount, created_at FROM transactions WHERE user_id = ?').all(userId);
  return rows.reduce((acc, r) => {
    const d = new Date(r.created_at);
    if (d.getFullYear() === y && d.getMonth() + 1 === m) return acc + Number(r.amount || 0);
    return acc;
  }, 0);
}

function monthlyCategoryTotals(userId) {
  const now = new Date();
  const y = now.getFullYear();
  const m = now.getMonth() + 1;
  const rows = db.prepare('SELECT amount, category, created_at FROM transactions WHERE user_id = ?').all(userId);
  const out = {};
  for (const c of CATEGORIES) out[c] = 0;
  for (const r of rows) {
    const d = new Date(r.created_at);
    if (d.getFullYear() === y && d.getMonth() + 1 === m) {
      if (!Object.prototype.hasOwnProperty.call(out, r.category)) out[r.category] = 0;
      out[r.category] += Number(r.amount || 0);
    }
  }
  return out;
}

function compareData(userId, mode, yearContext) {
  const rows = db.prepare('SELECT amount, created_at FROM transactions WHERE user_id = ?').all(userId);
  const now = new Date();

  if (mode === 'weekly') {
    const labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const values = [0, 0, 0, 0, 0, 0, 0];
    const day = now.getDay();
    const monday = new Date(now);
    monday.setDate(now.getDate() - ((day + 6) % 7));
    monday.setHours(0, 0, 0, 0);
    for (const r of rows) {
      const d = new Date(r.created_at);
      const delta = Math.floor((d - monday) / 86400000);
      if (delta >= 0 && delta <= 6) values[delta] += Number(r.amount || 0);
    }
    return { labels, values };
  }

  if (mode === 'monthly') {
    const labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const values = new Array(12).fill(0);
    for (const r of rows) {
      const d = new Date(r.created_at);
      if (d.getFullYear() === now.getFullYear()) values[d.getMonth()] += Number(r.amount || 0);
    }
    return { labels, values };
  }

  if (mode === 'yearly') {
    const map = new Map();
    for (const r of rows) {
      const y = new Date(r.created_at).getFullYear();
      map.set(y, (map.get(y) || 0) + Number(r.amount || 0));
    }
    const years = [...map.keys()].sort((a, b) => a - b);
    return { labels: years.map(String), values: years.map(y => map.get(y)) };
  }

  if (mode === 'year-month') {
    const labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const values = new Array(12).fill(0);
    const yr = Number(yearContext);
    for (const r of rows) {
      const d = new Date(r.created_at);
      if (d.getFullYear() === yr) values[d.getMonth()] += Number(r.amount || 0);
    }
    return { labels, values };
  }

  return { labels: [], values: [] };
}

function filteredTransactions(userId, filters = {}) {
  const rows = db.prepare('SELECT id, amount, category, remark, created_at FROM transactions WHERE user_id = ? ORDER BY datetime(created_at) DESC').all(userId);
  return rows;
}

function transactionById(userId, txId) {
  return db.prepare('SELECT id, amount, category, remark, created_at FROM transactions WHERE id = ? AND user_id = ?').get(txId, userId);
}

module.exports = {
  CATEGORIES, openDb, closeDb, getDb, hashText, normUsername, normAnswer, nowIso,
  userById, userByUsername, safeUser, monthTotal, monthlyCategoryTotals,
  compareData, filteredTransactions, transactionById, DB_PATH,
};
