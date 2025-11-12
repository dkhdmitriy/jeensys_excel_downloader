# jeensys_parser

Small helper script that uses Selenium to log into https://mon.jeensys.com and export devices to Excel.


Quick start (Windows PowerShell):

1. Create and activate a virtual environment (recommended):

```powershell
# create a venv in the project folder
python -m venv .venv

# activate the venv in PowerShell
.\.venv\Scripts\Activate.ps1

# (You should now see '(.venv)' in your prompt)
```

2. Install Python dependencies into the active venv:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

3. Provide credentials via environment variables or a local `.env` file.

Create a `.env` (copy from `.env.example`) or set in PowerShell and run:

```powershell
$env:JEENSYS_LOGIN = 'your_login'
$env:JEENSYS_PASSWORD = 'your_password'
python .\main.py
```

Run headless:

```powershell
python .\main.py --headless
```

Keep the browser open for inspection (adds 15s pause):

```powershell
python .\main.py --keep-open
```

Notes:
- Do NOT commit real credentials. Use `.env.example` as a template.
- Downloads are written to the repository root; change `prefs['download.default_directory']` in `build_driver()` to change this location.