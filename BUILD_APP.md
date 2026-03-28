# Build KernelFinance Pro apps

This project currently includes:

- `Python desktop app` in `kernel_finance_pro.py`
- `Node/Electron desktop app` in `js-frontend`

## Python macOS build

### 1) Place logo
Put your company logo PNG here:

- `assets/logo.png`

The app uses this image for:
- login/dashboard logo
- app window icon

### 2) Install builder

```bash
python3 -m pip install pyinstaller
```

### 3) Build app

```bash
./build_macos_app.sh
```

This creates:
- `dist/KernelFinance Pro.app`

## Node/Electron run

Install dependencies:

```bash
cd js-frontend
npm install
```

Run:

```bash
npm start
```
