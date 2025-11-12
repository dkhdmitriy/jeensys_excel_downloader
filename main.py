import os
import sys
import time
from typing import Tuple

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# Optionally load environment variables from a local `.env` file if
# `python-dotenv` is installed. This makes local development easier while
# keeping secrets out of source control.
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # Ignore if python-dotenv isn't installed; environment variables can
    # still be provided by the shell or CI environment.
    pass

SIGNIN_URL = "https://mon.jeensys.com/signin"
DEVICES_URL = "https://mon.jeensys.com/devices"
DEFAULT_TIMEOUT = 30


def read_credentials() -> Tuple[str, str]:
    # Read credentials from environment variables to avoid committing secrets.
    # Preferred variables: JEENSYS_LOGIN and JEENSYS_PASSWORD
    login = os.getenv("JEENSYS_LOGIN")
    password = os.getenv("JEENSYS_PASSWORD")

    if not login or not password:
        raise RuntimeError(
            "Credentials not found. Set environment variables JEENSYS_LOGIN and JEENSYS_PASSWORD "
            "or create a local `.env` file and load it before running. See `.env.example`."
        )

    return login, password


def build_driver(headless: bool = False) -> webdriver.Chrome:
    path = os.path.dirname(os.path.abspath(__file__))
    prefs = {'download.default_directory' : path}
    options = Options()
    options.add_experimental_option('prefs', prefs)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
    )
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(60)
    return driver


def wait_for(driver: webdriver.Chrome, locator, timeout: int = DEFAULT_TIMEOUT):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located(locator))


def wait_clickable(driver: webdriver.Chrome, locator, timeout: int = DEFAULT_TIMEOUT):
    return WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(locator))


def perform_login(driver: webdriver.Chrome, login: str, password: str) -> None:
    driver.get(SIGNIN_URL)

    email_input = wait_for(driver, (By.NAME, "username"))
    password_input = wait_for(driver, (By.NAME, "password"))

    email_input.clear()
    email_input.send_keys(login)

    password_input.clear()
    password_input.send_keys(password)

    submit_button = wait_for(driver, (By.CSS_SELECTOR, "button.authform__btn"))
    WebDriverWait(driver, 30).until(lambda d: submit_button.is_enabled())
    submit_button.click()

    WebDriverWait(driver, DEFAULT_TIMEOUT).until(
        EC.any_of(
            EC.url_contains("/dashboard"),
            EC.presence_of_element_located((By.CLASS_NAME, "ant-alert-error")),
        )
    )

    if driver.find_elements(By.CLASS_NAME, "ant-alert-error"):
        raise RuntimeError("Не удалось авторизоваться: проверьте логин и пароль.")


def open_devices_page(driver: webdriver.Chrome) -> None:
    driver.get(DEVICES_URL)
    wait_for(driver, (By.CSS_SELECTOR, "button.table__select"))


def select_all_devices(driver: webdriver.Chrome) -> None:
    select_locator = (By.CSS_SELECTOR, "button.table__select")
    wait_clickable(driver, select_locator).click()

    WebDriverWait(driver, DEFAULT_TIMEOUT).until(
        lambda d: "table__select-active"
        in d.find_element(*select_locator).get_attribute("class")
    )


def ensure_settings_panel_open(driver: webdriver.Chrome) -> None:
    panel_locator = (By.CSS_SELECTOR, ".settings.panel-box-blur")
    if driver.find_elements(*panel_locator):
        return

    toggle_locator = (By.CSS_SELECTOR, ".slot__buttons button:nth-child(2)")
    wait_clickable(driver, toggle_locator).click()
    wait_for(driver, panel_locator)


def start_excel_download(driver: webdriver.Chrome) -> None:
    export_button_locator = (
        By.XPATH,
        "//button[contains(@class,'settings__button') and .//span[text()='Скачать Excel']]",
    )
    wait_clickable(driver, export_button_locator).click()

    download_button_locator = (By.CSS_SELECTOR, "button.download__download")
    wait_clickable(driver, download_button_locator).click()

    confirm_button_locator = (By.CSS_SELECTOR, "button.confirmer__accept")
    wait_clickable(driver, confirm_button_locator).click()

    WebDriverWait(driver, DEFAULT_TIMEOUT).until(
        lambda d: not d.find_elements(*confirm_button_locator)
    )

    time.sleep(15)


def export_devices_excel(driver: webdriver.Chrome) -> None:
    open_devices_page(driver)
    select_all_devices(driver)
    ensure_settings_panel_open(driver)
    start_excel_download(driver)


def main():
    headless = "--headless" in sys.argv
    driver = build_driver(headless=headless)

    try:
        login, password = read_credentials()
        perform_login(driver, login, password)
        print("Авторизация завершена. Ожидайте экспорт устройств в Excel.")
        export_devices_excel(driver)
        print("Запрос на скачивание Excel отправлен.")
    except Exception as exc:
        print(f"Ошибка: {exc}")
    finally:
        if "--keep-open" in sys.argv:
            print("Оставляю браузер открытым на 15 секунд.")
            time.sleep(15)
        driver.quit()


if __name__ == "__main__":
    main()

