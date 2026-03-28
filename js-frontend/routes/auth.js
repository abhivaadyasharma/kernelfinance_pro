const { Router } = require('express');
const db = require('../db');

const router = Router();

router.post('/create-account', (req, res) => {
  const { username, password, securityAnswer } = req.body;
  const usernameDisplay = String(username || '').trim();
  const usernameNorm = db.normUsername(username);
  const pwd = String(password || '');
  const answer = String(securityAnswer || '').trim();

  if (!usernameDisplay || !usernameNorm) return res.json({ ok: false, error: 'Username cannot be empty.' });
  if (!pwd) return res.json({ ok: false, error: 'Password cannot be empty.' });
  if (!answer) return res.json({ ok: false, error: 'Security answer cannot be empty.' });

  try {
    db.getDb().prepare(
      `INSERT INTO users (username_display, username_norm, password_hash, security_answer_hash, currency, theme, created_at)
       VALUES (?, ?, ?, ?, 'INR', 'dark', ?)`
    ).run(usernameDisplay, usernameNorm, db.hashText(pwd), db.hashText(db.normAnswer(answer)), db.nowIso());
    res.json({ ok: true });
  } catch (err) {
    if (String(err.message || '').toLowerCase().includes('unique')) return res.json({ ok: false, error: 'Username taken' });
    res.json({ ok: false, error: 'Failed to create account.' });
  }
});

router.post('/login', (req, res) => {
  const user = db.userByUsername(req.body.username);
  if (!user) return res.json({ ok: false, error: 'Invalid username or password.' });
  if (user.password_hash !== db.hashText(req.body.password || '')) return res.json({ ok: false, error: 'Invalid username or password.' });
  res.json({ ok: true, user: db.safeUser(user), monthTotal: db.monthTotal(user.id) });
});

router.post('/reset-password', (req, res) => {
  const user = db.userByUsername(req.body.username);
  if (!user) return res.json({ ok: false, error: 'Username or security answer is incorrect.' });
  if (user.security_answer_hash !== db.hashText(db.normAnswer(req.body.securityAnswer || ''))) {
    return res.json({ ok: false, error: 'Username or security answer is incorrect.' });
  }
  if (!String(req.body.newPassword || '')) return res.json({ ok: false, error: 'Password cannot be empty.' });
  db.getDb().prepare('UPDATE users SET password_hash = ? WHERE id = ?').run(db.hashText(req.body.newPassword), user.id);
  res.json({ ok: true });
});

router.post('/verify-security', (req, res) => {
  const user = db.userByUsername(req.body.username);
  if (!user) return res.json({ ok: false, error: 'Username or security answer is incorrect.' });
  if (user.security_answer_hash !== db.hashText(db.normAnswer(req.body.securityAnswer || ''))) {
    return res.json({ ok: false, error: 'Username or security answer is incorrect.' });
  }
  res.json({ ok: true, user: db.safeUser(user) });
});

module.exports = router;
