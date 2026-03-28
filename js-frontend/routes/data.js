const { Router } = require('express');
const fs = require('fs');
const path = require('path');
const db = require('../db');

const router = Router();

router.get('/backup', (req, res) => {
  const d = db.getDb();
  d.pragma('wal_checkpoint(FULL)');
  const dbPath = db.DB_PATH;
  res.setHeader('Content-Type', 'application/octet-stream');
  res.setHeader('Content-Disposition', 'attachment; filename="kernel_finance_pro.db"');
  const stream = fs.createReadStream(dbPath);
  stream.pipe(res);
});

router.post('/restore', (req, res) => {
  const chunks = [];
  req.on('data', chunk => chunks.push(chunk));
  req.on('end', () => {
    const data = Buffer.concat(chunks);
    if (data.length === 0) return res.json({ ok: false, error: 'No file data received.' });
    try {
      db.closeDb();
      fs.writeFileSync(db.DB_PATH, data);
      db.openDb();
      res.json({ ok: true });
    } catch (err) {
      try { db.openDb(); } catch (_) { /* ignore */ }
      res.json({ ok: false, error: 'Restore failed: ' + err.message });
    }
  });
});

module.exports = router;
