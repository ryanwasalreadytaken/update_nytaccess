"""
Activates 24 hours of New York Times digital provided by the Multnomah County Library
"""
import os
import sys
import urllib
import http.client
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import FirefoxOptions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M",
    handlers=[RotatingFileHandler('logs/update.log', maxBytes=10240000, backupCount=3),
              logging.StreamHandler(sys.stdout)],
    )

# Pull in config values from .env
load_dotenv()


def pushover(title, message):
    """
    Receives title & message variables and generates a pushover alert.
    Disabled in default env.env file. Set ALERTS=true in .env file to enable. 
    """
    alerts = os.getenv('ALERTS')
    priority = os.getenv('ALERT_PRIORITY')
    userkey = os.getenv('USERKEY')
    token = os.getenv('TOKEN')
    conn = http.client.HTTPSConnection("api.pushover.net:443")

    if alerts:
        conn.request("POST", "/1/messages.json",
                     urllib.parse.urlencode({
                         "token": token,
                         "user": userkey,
                         "title": title,
                         "message": message,
                         "priority": priority,
                     }), {"Content-type": "application/x-www-form-urlencoded"})
        response = conn.getresponse()

        if response.status == 200:
            logging.info('Pushover alert sent successfully')
        else:
            logging.error('Pushover alert failed to send')
            logging.error("Server response: %s, %s", {response.status}, {response.reason})

    else:
        logging.warning('Pushover alerts are disabled. Set ALERT=true in .env to enable')


def update_nyt():
    """
    Uses selenium to browse to MCL renewal website, fill in form values, and submit.
    Will generate an error message for pushover in the event of an exception.
    """
    try:
        cardnum = os.getenv('CARDNUM')
        cardpin = os.getenv('CARDPIN')
        url = os.getenv('URL')

        options = FirefoxOptions()
        options.add_argument("-headless")
        driver = webdriver.Firefox(options=options)
        driver.get(url)

        logging.debug('Headless Firefox Initialized')

        username = driver.find_element(By.NAME, value='user')
        password = driver.find_element(By.NAME, value='pass')

        username.send_keys(cardnum)
        password.send_keys(cardpin, Keys.RETURN)
        driver.close()
        driver.quit()

        logging.info('NYT access renewal was successful!')

    except Exception as e:
        title = "NYT Access Renewal Failure"
        message = f' An error occurred when reactivating on cloud.nerdtime.org:\n \n {e} '

        logging.error(message, exc_info=True)
        pushover(title, message)


if __name__ == '__main__':
    logging.info('Initializing NYT renewal script...')

    update_nyt()
