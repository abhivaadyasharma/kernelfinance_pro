const { Router } = require('express');
const db = require('../db');

const router = Router();

router.get('/:id', (req, res) => {
  const user = db.userById(Number(req.params.id));
  if (!user) return res.json({ ok: false, error: 'User not found.' });
  res.json({ ok: true, user: db.safeUser(user) });
});

router.put('/:id/currency', (req, res) => {
  db.getDb().prepare('UPDATE users SET currency = ? WHERE id = ?').run(req.body.currency, Number(req.params.id));
  const user = db.userById(Number(req.params.id));
  res.json({ ok: true, user: db.safeUser(user), monthTotal: db.monthTotal(Number(req.params.id)) });
});

router.put('/:id/theme', (req, res) => {
  db.getDb().prepare('UPDATE users SET theme = ? WHERE id = ?').run(req.body.theme, Number(req.params.id));
  const user = db.userById(Number(req.params.id));
  res.json({ ok: true, user: db.safeUser(user) });
});

router.put('/:id/profile', (req, res) => {
  const userId = Number(req.params.id);
  const usernameDisplay = String(req.body.username || '').trim();
  const usernameNorm = db.normUsername(req.body.username);
  if (!usernameDisplay || !usernameNorm) return res.json({ ok: false, error: 'Username cannot be empty.' });

  const existing = db.getDb().prepare('SELECT id FROM users WHERE username_norm = ?').get(usernameNorm);
  if (existing && existing.id !== userId) return res.json({ ok: false, error: 'Username taken' });

  db.getDb().prepare('UPDATE users SET username_display = ?, username_norm = ? WHERE id = ?').run(usernameDisplay, usernameNorm, userId);
  if (String(req.body.newPassword || '').trim()) {
    db.getDb().prepare('UPDATE users SET password_hash = ? WHERE id = ?').run(db.hashText(req.body.newPassword), userId);
  }
  if (String(req.body.securityAnswer || '').trim()) {
    db.getDb().prepare('UPDATE users SET security_answer_hash = ? WHERE id = ?').run(db.hashText(db.normAnswer(req.body.securityAnswer)), userId);
  }
  res.json({ ok: true, user: db.safeUser(db.userById(userId)) });
});

module.exports = router;
