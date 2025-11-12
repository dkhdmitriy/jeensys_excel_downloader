## Repo snapshot

- Single-file Python utility: `main.py`.
- Purpose: use Selenium (Chrome) to log into https://mon.jeensys.com and export devices to Excel.
- Key libs: `selenium`, `webdriver-manager`.

## What an AI assistant should know up-front

- This is a small, procedural script (no package layout). All behavior is implemented in `main.py`.
- Credentials are currently hard-coded in `read_credentials()` (lines near the top of `main.py`). Treat those as secrets: do not commit changes that include real credentials. Prefer using environment variables `JEENSYS_LOGIN` and `JEENSYS_PASSWORD` (the code already hints at env vars in the error message).
- The script writes downloads into the repository root (the Chrome prefs set `download.default_directory` to the script directory). If modifying download behavior, update that preference in `build_driver()`.

## Assistant language

- The assistant MUST respond only in Russian for all messages, comments, and code explanations when working on this repository. Use clear, idiomatic Russian in prose and in-line comments. Keep any example commands or code unchanged except for necessary translation of human-facing text/comments.

## How to run and test locally (Windows PowerShell)

- Install requirements (if not present):

  ```powershell
  python -m pip install selenium webdriver-manager
  ```

- Run headful (shows browser):

  ```powershell
  python .\main.py
  ```

- Run headless (CI or background):

  ```powershell
  python .\main.py --headless
  ```

- Keep browser open for inspection (adds 15s pause):

  ```powershell
  python .\main.py --keep-open
  ```

## Important code-patterns and conventions to follow

- wait helpers: The file defines `wait_for()` and `wait_clickable()` wrappers around `WebDriverWait`. Prefer using these helpers when adding new page interactions so timing is consistent with the current approach.
- Flow functions: high-level steps are factored into small functions: `perform_login()`, `open_devices_page()`, `select_all_devices()`, `ensure_settings_panel_open()`, `start_excel_download()`, and `export_devices_excel()`. When modifying behavior, update or add similarly-named helper functions rather than adding long inline logic in `main()`.
- Minimal side-effects: the script uses `driver.quit()` in `finally` to ensure cleanup. Keep that pattern when adding error handling or early returns.

## Integration and external dependencies

- External webapp: https://mon.jeensys.com — many locators use CSS class names (e.g., `button.table__select`, `.settings.panel-box-blur`). Changes to the site will likely break locators; prefer robust locators (text-based XPaths or stable attributes) if you must make locators more resilient.
- ChromeDriver is installed at runtime via `webdriver-manager` (`ChromeDriverManager().install()`). Tests or CI must allow downloads or provide a cached driver.

## Security and secrets guidance (critical)

- Do NOT add real credentials to the repo. If you add credential handling, read from environment variables (e.g., `os.getenv('JEENSYS_LOGIN')`) and document the required variables in `README` or a new `env.example` file.
- If you replace hard-coded values, open a PR that strips secrets and documents how to set credentials locally.

## Small examples / quick edits an AI might make

- Replace hard-coded credentials in `read_credentials()` with `os.getenv()` and a helpful error message referencing `JEENSYS_LOGIN` and `JEENSYS_PASSWORD`.
- If adding new page steps, create a small helper function and call it from `export_devices_excel()` to keep `main()` concise.

## Tests / CI / Debugging notes

- There are no tests or CI config in the repo. For quick syntax checks, run:

  ```powershell
  python -m py_compile .\main.py
  ```

- For debugging, run without `--headless` so you can visually confirm interactions.

## Files to inspect when making changes

- `main.py` — single source of truth for behavior.

---
If any of these assumptions are wrong or you want me to open a PR that: (1) removes hardcoded secrets, (2) reads credentials from env, and (3) adds a minimal `README.md` / `requirements.txt`, tell me and I will implement those changes next.
