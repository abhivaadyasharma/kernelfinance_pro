# KernelFinance Pro

KernelFinance Pro currently runs as a hybrid desktop app:

- `Python frontend`
  - Main file: `kernel_finance_pro.py`
  - Uses Tkinter for the desktop UI
- `Node.js backend`
  - Folder: `js-frontend`
  - Uses Express and SQLite for the local API server

The Python app talks to the Node.js backend over HTTP on `127.0.0.1`.

## Run The App

Use the unified startup script:

```bash
./start.sh
```

This script:

- installs Node dependencies if needed
- starts the Node.js backend server
- waits for the backend health check to pass
- launches the Python desktop frontend

## Run Pieces Separately

If you want to start each part manually:

Start the Python frontend:

```bash
./run_python_app.sh
```

Start the Node.js backend:

```bash
./run_node_app.sh
```

## Notes

- The recommended way to run the app is `./start.sh`.
- The shared database path defaults to `kernel_finance_pro.db`.
- Logo assets are shared from `assets/logo.png`.
