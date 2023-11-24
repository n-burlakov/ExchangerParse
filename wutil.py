from os import path, getcwd
import json
from datetime import datetime
from typing import Dict, Any
import time

# from seleniumwire import webdriver as webdriver_wire
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from fake_useragent import UserAgent

from twocaptcha import TwoCaptcha
from twocaptcha.solver import NetworkException

from ramon import ramon_parser
from westchange import westchange_parser


class DataUtils:
    """
        Utils class for some general methods.
    """

    def __init__(self):
        """
            There is need add to self.parser_dict new exchange modules,
            key of dict should be same as name of directory running exchanger.
        """
        self.parser_dict = {"ramon": ramon_parser.ParseRamon,
                            "westchange": westchange_parser.ParseWestchange}

    @classmethod
    def __parse_config_file(cls, config_filepath: str) -> Dict[str, str]:
        """
            Get config dictionary from 'config' directory

            :param config_filepath (string): filepath to config file.
            :return dictionary with config info.
        """
        settings_dict = dict()

        if path.exists(config_filepath):
            with open(config_filepath) as f:
                settings_dict = json.load(f)

        return settings_dict

    def get_params(self, name: str = "ramon", conf: str = "package") -> str:
        """
            Get params from config file

            :param name: name of exchanger;
            :param conf: config file addition, could be 'package' and 'urls'.
            :return name of run module name
        """
        settings_data = self.__parse_config_file(path.join(getcwd(), f"config/name_{conf}_config.json"))

        return settings_data[name]

    def get_object_of_exchanger(self, name: str = None, attribute_dict: Dict = None) -> Any:
        """
            Get package name from self.parser_dict dictionary

        :param attribute_dict: dictionary with arguments for next function;
        :param name: name of exchanger;
        :return: object of exchanger parser class
        """
        conf = "package"
        package = self.get_params(name, conf)
        return self.parser_dict[package](attribute_dict)

    def get_url_by_name(self, name: str) -> str:
        """
            Get url exchanger by name

        :param name: name of exchanger;
        :return: exchange url
        """
        conf = "urls"
        return self.get_params(name, conf)

    def cloudflare_challenge_solve_captcha(self, exchange_url: str = None, host: str = None, port: str = None,
                                           usr: str = None, pwd: str = None) -> Any:
        """
            Solve Cloudflare Challenge captcha

        :param host: proxy host name;
        :param port: proxy port;
        :param usr: user name;
        :param pwd: proxy password;
        :param exchange_url: exсhanger url;
        :return: solved driver with captcha.
        """
        api_key = self.get_params("key", "captcha")
        callback = self.get_params("callback", "captcha")

        config = {
            'server': 'rucaptcha.com',
            'apiKey': api_key,
            'softId': 123,
            'callback': callback,
            'defaultTimeout': 150,
            'recaptchaTimeout': 600,
            'pollingInterval': 20,
        }

        solver = TwoCaptcha(**config)

        with open('jquery.js', 'r') as f:
            jquery_js = f.read()

        options = webdriver.ChromeOptions()
        if usr and pwd:
            options.add_argument(f"--proxy-server=https://{usr}:{pwd}@{host}:{port}")
        # options.add_argument('--headless=new')  # turn off opening browser window
        options.set_capability("goog:loggingPrefs", {'browser': 'ALL'})
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

        # launch URL
        driver.get(exchange_url)
        # set JS script for stopping captcha
        driver.execute_script(jquery_js)
        time.sleep(2)
        main_count = 5
        while main_count != 0:
            try:
                count = 0
                try:
                    while count != 5:
                        # get js data
                        time.sleep(3)
                        for e in driver.get_log('browser'):
                            resp = e['message']
                            if "sitekey" in resp:
                                resp = json.loads(json.loads(resp.split(' ')[2]))
                                count = 5
                                break
                        else:
                            count += 1
                            driver.execute_script(jquery_js)
                except Exception as exc:
                    raise exc
                result = solver.turnstile(
                    sitekey=resp['sitekey'], url=exchange_url, data=resp['data'], pagedata=resp['pagedata'],
                    action=resp['action'],
                    useragent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36')
                break
            except Exception as exc:
                driver.refresh()
                driver.execute_script(jquery_js)
                time.sleep(2)
                main_count -= 1

        for tick in range(16, 30, 2):
            try:
                time.sleep(tick)
                token = solver.get_result(result['captchaId'])
                break
            except NetworkException as exc:
                if 'CAPCHA_NOT_READY' in str(exc) or 'NETWORK' in str(exc):
                    continue
            except Exception as exc:
                raise exc
        driver.execute_script("window.tsCallback(arguments[0]);", (str(token)))
        return driver

    @classmethod
    def get_webdriver(cls, host: str, port: str, usr: str, pwd: str) -> Any:
        """
            Create webdriver object with options and proxy secure

        :param host: proxy host name;
        :param port: proxy port;
        :param usr: user name;
        :param pwd: proxy password;
        :return: webdriver object.
        """
        useragent = UserAgent()

        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        if usr and pwd:
            options.add_argument(f"--proxy-server=https://{usr}:{pwd}@{host}:{port}")
        # options.add_argument('--headless=new')  # turn off opening browser window
        options.add_argument(f"user-agent={useragent.random}")
        options.set_capability("goog:loggingPrefs", {'browser': 'ALL'})

        return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
