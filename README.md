# KernelFinance Pro

KernelFinance Pro is now set up with two app versions in the same project:

- `Python desktop app`:
  - Main file: `kernel_finance_pro.py`
  - Uses Tkinter
- `Node.js desktop app`:
  - Folder: `js-frontend`
  - Uses Electron + JavaScript

## Run The Python App

```bash
./run_python_app.sh
```

## Run The Node.js App

Install dependencies first:

```bash
cd js-frontend
npm install
```

Then run:

```bash
../run_node_app.sh
```

## Notes

- Both versions can exist side by side.
- The Python app and Node app currently use separate database files.
- Logo assets are shared from `assets/logo.png`.
