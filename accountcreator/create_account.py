import os, sys
import subprocess
import zipfile
import atexit
import random
import hashlib
import string
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import Select
import requests


class WebScraper(webdriver.Chrome):

    _path = os.path.expandvars(r"C:/Users/${USERNAME}/chromedriver.exe")
    ENTER = webdriver.common.keys.Keys.RETURN

    def __init__(self, driver_path=None, visible=False):
        _pywin32 = self._import_pywin32()
        self.driver_path = driver_path or self._path
        self.visible = visible
        try:
            self._get_driver(visible=self.visible)
            self.get("https://google.com")
        except common.exceptions.WebDriverException as e:
            if not _pywin32:
                raise
            print("Chrome and Chromedriver versions do not match!")
            version = self._get_chrome_version()
            driver_path = self._path
            print("Currently using chrome version:", version)
            print("Installing correct Chromedriver version at:", driver_path)
            self._install_chromedriver(version.split(".")[0])
            self._get_driver(visible=self.visible)
        self.XPATH = lambda value: self.find_element(webdriver.common.by.By.XPATH, value)

    def _install_chromedriver(self, version):
        print("Installing executable driver for Chrome version:", version)
        url = "https://chromedriver.chromium.org/downloads"
        resp = requests.get(url)
        parser = BeautifulSoup(resp.text, "lxml")
        version = [elem.getText().strip().split()[-1] for elem in parser.findAll("strong") if ("ChromeDriver " + version) in elem.getText()][0]
        print("Located correct Chromedriver version:", version)
        new_url = f"https://chromedriver.storage.googleapis.com/{version}/chromedriver_win32.zip"

        resp = requests.get(new_url)
        with open(os.path.join(os.path.dirname(self.driver_path), "chromedriver.zip"), "wb") as f:
            f.write(resp.content)
        print("Downloaded zip archive")
        os.chdir(os.path.dirname(self.driver_path))
        with zipfile.ZipFile(os.path.join(os.path.dirname(self.driver_path), "chromedriver.zip"), 'r') as zip_file:
            zip_file.extractall()
        print("Successfully extracted zip archive to:", os.path.dirname(self.driver_path))
        print("Removed excess files")
        print("Chromedriver successfully installed at:", self.driver_path)

    def _import_pywin32(self):
        assert sys.platform == "win32", "this script can only be run on Windows"
        try:
            global Dispatch
            from win32com.client import Dispatch
        except ImportError:
            proc = subprocess.Popen([sys.executable, "-m", "pip", "install", "pywin32"], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if proc.stderr.read().decode():
                return False
            from win32com.client import Dispatch            
        return True

    def _get_driver(self, visible=False):
        options = webdriver.chrome.options.Options()
        if not visible:
            options.add_argument("--headless")
        options.add_argument("start-maximized")
        options.add_argument("--log-level=3")
        options.add_argument("--incognito")
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        service = webdriver.chrome.service.Service(executable_path=self.driver_path, log_path=os.devnull)
        super(WebScraper, self).__init__(service=service, options=options)

    def _get_chrome_version(self):
        parser = Dispatch("Scripting.FileSystemObject")
        try:
            path = "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
            if not os.path.exists(path):
                path = path.replace(" (x86)", "")
            version = parser.GetFileVersion(path)
        except Exception:
            return None
        return version
        
    def wait(self, fn, exc=Exception, maxtries=100): 
        """Wait for a web page to load or wait to locate dynamically rendered web elements"""
        assert "<lambda>" in repr(fn) and callable(fn), "expected a lambda expression!"
        # If `exc` is a `bool(False)` object then rethrow any exceptions that occur 
        noexcept = not bool(exc)
        if noexcept:
            exc = BaseException
        # Continuously try and execute the function until no exceptions are thrown
        tries = 0
        while True:
            try:
                return fn()
            except exc:
                if maxtries is not None and tries > maxtries:
                    raise TimeoutError(
                        f"exceeded number of tries, function failed"
                    ) from None
                if noexcept:
                    raise


randomhash = lambda: hashlib.sha256(str(random.randint(1, 0xffffffff)).encode()).hexdigest()

def randompwd(length=16):
    rand = random.SystemRandom()
    pwd = []
    pwd.append(rand.choice(string.ascii_uppercase))
    pwd.append(rand.choice(string.ascii_lowercase))
    pwd.append(rand.choice(string.digits))
    pwd.append(rand.choice(string.punctuation))
    for i in range(length - 4):
        pwd.append(rand.choice(rand.choice((string.ascii_letters, string.digits, string.punctuation))))
    random.shuffle(pwd)
    return "".join(pwd)

def get_email_address(driver: WebScraper, handle: str):
    driver.switch_to.window(handle)

    elem = driver.wait(lambda: driver.find_element("id", "mail"))
    while not "@" in elem.text:
        print(elem.text)
        elem = driver.wait(lambda: driver.find_element("id", "mail"))
    
    return "nasem23368@jrvps.com"

def create_account():
    # Set up driver
    driver = WebScraper(visible=True)
    atexit.register(driver.quit)
    driver.get("https://www.instagram.com/accounts/emailsignup/")
    handle1 = driver.current_window_handle
    driver.execute_script('window.open("https://www.temp-mail.org")')
    time.sleep(2)
    driver.delete_all_cookies()
    handle2 = [h for h in driver.window_handles if h != handle1][0]

    try:
        denied = driver.XPATH("/html/body/div[1]/section/main/div/div/div[1]/div/div[6]/button")
        if "please wait a few minutes" in denied.text.lower():
            raise TimeoutError(
                "couldn't create an account"
            )
    except NoSuchElementException:
        pass
    
    username = randomhash()[-10:]
    pwd = randompwd()
    email = get_email_address(driver, handle2)

    # Cookies
    driver.wait(lambda: driver.XPATH("/html/body/div[4]/div/div/button[1]")).click()
    # Email address
    driver.wait(lambda: driver.find_element("name", "emailOrPhone")).send_keys(email)
    # Username
    driver.wait(lambda: driver.find_element("name", "username")).send_keys(username)
    # Password
    driver.wait(lambda: driver.find_element("name", "password")).send_keys(pwd)
    # Next button
    driver.wait(lambda: driver.XPATH("/html/body/div[1]/section/main/div/div/div[1]/div[2]/form/div[7]/div/button")).click()
    # Year selector
    menu = Select(driver.wait(lambda: driver.XPATH("/html/body/div[1]/section/main/div/div/div[1]/div/div[4]/div/div/span/span[3]/select")))
    menu.select_by_visible_text("2000")
    # Next button
    driver.wait(lambda: driver.XPATH("/html/body/div[1]/section/main/div/div/div[1]/div/div[6]/button")).click()

    input("Continue...")
    return "", ""

if __name__ == "__main__":  
    creds = create_account()
    print(f"Username: {creds[0]}, password: {creds[1]}")