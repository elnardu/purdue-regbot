import base64
import json
import os
import sys

import requests
import pyotp

from loguru import logger

CONFIG_PATH = 'boilerkey_config.json'
COUNTER_PATH = 'boilerkey_counter.json'

# DO NOT LOSE YOUR WAAAAAAY!

__license__ = "WTFPL"
__author__ = "Russian election hackers"
__credits__ = ['ITaP', 'Mitch Daniels']


def getActivationData(code):
    print("Requesting activation data...")

    HEADERS = {
        "User-Agent": "okhttp/3.11.0",
    }

    PARAMS = {
        "app_id": "com.duosecurity.duomobile.app.DMApplication",
        "app_version": "2.3.3",
        "app_build_number": "323206",
        "full_disk_encryption": False,
        "manufacturer": "Google",
        "model": "Pixel",
        "platform": "Android",
        "jailbroken": False,
        "version": "6.0",
        "language": "EN",
        "customer_protocol": 1
    }

    ENDPOINT = "https://api-1b9bef70.duosecurity.com/push/v2/activation/{}"

    res = requests.post(
        ENDPOINT.format(code),
        headers=HEADERS,
        params=PARAMS
    )

    if res.json().get('code') == 40403:
        print("Invalid activation code."
              "Please request a new link in BoilerKey settings.")
        sys.exit(1)

    if not res.json()['response']:
        print("Unknown error")
        print(res.json())
        sys.exit(1)

    return res.json()['response']


def validateLink(link):
    try:
        assert "m-1b9bef70.duosecurity.com" in link
        code = link.split('/')[-1]
        assert len(code) == 20
        return True, code
    except Exception:
        return False, None


class BoilerKey:
    def __init__(self, config_path, counter_path):
        self.config_path = config_path
        self.counter_path = counter_path

        if not os.path.isfile(config_path) or not os.path.isfile(counter_path):
            logger.error(
                "Failed to locate boilerkey configs. Running setup...")
            self.askForInfo()
            logger.info("Reload the script to continue")

    def askForInfo(self):
        print("""Hello there.
1. Please go to the BoilerKey settings (https://purdue.edu/boilerkey)
and click on 'Set up a new Duo Mobile BoilerKey'
2. Follow the process until you see the qr code
3. Paste the link (https://m-1b9bef70.duosecurity.com/activate/XXXXXXXXXXX)
under the qr code right here and press Enter""")

        valid = False
        while not valid:
            link = input()
            valid, activationCode = validateLink(link)

            if not valid:
                print("Invalid link. Please try again")

        print("""4. In order to generate full password (pin,XXXXXX),
script needs your pin. You can leave this empty. THIS IS NOT OPTIONAL""")

        valid = False
        while not valid:
            pin = input()
            if len(pin) != 4:
                pin = ""
                print("Invalid pin")

        activationData = getActivationData(activationCode)
        activationData['pin'] = pin
        self.set_config(activationData)
        self.set_counter(0)
        print("Setup successful!")

        print("Here is your password: ", self.generate_password())
        print("Use it to finish the registration")

    def set_config(self, activation_data):
        with open(self.config_path, 'w') as f:
            json.dump(activation_data, f, indent=2)
        print("Activation data saved!")

    def get_config(self):
        with open(self.config_path, 'r') as f:
            return json.load(f)

    def set_counter(self, number):
        with open(self.counter_path, 'w') as f:
            json.dump({
                "counter": number
            }, f, indent=2)

    def get_counter(self):
        with open(self.counter_path, 'r') as f:
            return json.load(f)['counter']

    def generate_password(self):
        config = self.get_config()
        counter = self.get_counter()

        hotp = pyotp.HOTP(base64.b32encode(config['hotp_secret'].encode()))

        hotpPassword = hotp.at(counter)

        if config.get('pin'):
            password = "{},{}".format(config.get('pin'), hotpPassword)
        else:
            password = hotpPassword

        self.set_counter(counter + 1)
        return password
