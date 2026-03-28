const { Router } = require('express');
const db = require('../db');

const router = Router();

router.get('/:userId/stats/month-total', (req, res) => {
  res.json({ ok: true, value: db.monthTotal(Number(req.params.userId)) });
});

router.get('/:userId/stats/category-totals', (req, res) => {
  res.json({ ok: true, totals: db.monthlyCategoryTotals(Number(req.params.userId)) });
});

router.get('/:userId/stats/compare', (req, res) => {
  const data = db.compareData(Number(req.params.userId), req.query.mode, req.query.yearContext);
  res.json({ ok: true, ...data });
});

module.exports = router;
