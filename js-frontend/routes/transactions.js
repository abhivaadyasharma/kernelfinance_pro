const { Router } = require('express');
const db = require('../db');

const router = Router();

router.post('/:userId/transactions', (req, res) => {
  const userId = Number(req.params.userId);
  const amount = Number(req.body.amount);
  if (!Number.isFinite(amount) || amount <= 0) return res.json({ ok: false, error: 'Invalid amount.' });
  db.getDb().prepare('INSERT INTO transactions (user_id, amount, category, remark, created_at) VALUES (?, ?, ?, ?, ?)')
    .run(userId, amount, req.body.category, String(req.body.remark || '').trim(), db.nowIso());
  res.json({ ok: true, monthTotal: db.monthTotal(userId) });
});

router.get('/:userId/transactions', (req, res) => {
  const userId = Number(req.params.userId);
  const rows = db.filteredTransactions(userId);
  res.json({ ok: true, rows });
});

router.get('/:userId/transactions/:txId', (req, res) => {
  const row = db.transactionById(Number(req.params.userId), Number(req.params.txId));
  if (!row) return res.json({ ok: false, error: 'Transaction not found.' });
  res.json({ ok: true, row });
});

router.put('/:userId/transactions/:txId', (req, res) => {
  const userId = Number(req.params.userId);
  const txId = Number(req.params.txId);
  const amount = Number(req.body.amount);
  if (!Number.isFinite(amount) || amount <= 0) return res.json({ ok: false, error: 'Invalid amount.' });
  db.getDb().prepare('UPDATE transactions SET amount = ?, category = ?, remark = ? WHERE id = ? AND user_id = ?')
    .run(amount, req.body.category, String(req.body.remark || '').trim(), txId, userId);
  res.json({ ok: true, monthTotal: db.monthTotal(userId) });
});

router.delete('/:userId/transactions/:txId', (req, res) => {
  const userId = Number(req.params.userId);
  const txId = Number(req.params.txId);
  db.getDb().prepare('DELETE FROM transactions WHERE id = ? AND user_id = ?').run(txId, userId);
  res.json({ ok: true, monthTotal: db.monthTotal(userId) });
});

module.exports = router;
