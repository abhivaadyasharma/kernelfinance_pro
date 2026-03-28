const express = require('express');
const cors = require('cors');
const path = require('path');
const db = require('./db');

const authRoutes = require('./routes/auth');
const usersRoutes = require('./routes/users');
const transactionsRoutes = require('./routes/transactions');
const statsRoutes = require('./routes/stats');
const dataRoutes = require('./routes/data');

const PORT = Number(process.env.KF_PORT) || 3721;
const HOST = '127.0.0.1';

const app = express();
app.use(cors());
app.use(express.json());

app.get('/api/health', (_req, res) => res.json({ ok: true }));

app.use('/api/auth', authRoutes);
app.use('/api/users', usersRoutes);
app.use('/api/transactions', transactionsRoutes);
app.use('/api/stats', statsRoutes);
app.use('/api/data', dataRoutes);

db.openDb();

const server = app.listen(PORT, HOST, () => {
  console.log(`KernelFinance server listening on http://${HOST}:${PORT}`);
});

function shutdown() {
  console.log('Shutting down...');
  db.closeDb();
  server.close(() => process.exit(0));
  setTimeout(() => process.exit(0), 2000);
}

process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
