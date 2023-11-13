from os import path, getcwd
import json
from datetime import datetime

from seleniumwire import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from fake_useragent import UserAgent
from typing import Dict, Any

from ramon import ramon_parser


class DataUtils:
    """
        Utils class for some general methods.
    """

    def __init__(self):
        """
            There is need add to self.parser_dict new exchange modules,
            key of dict should be same as name of directory running exchanger.
        """
        self.parser_dict = {"ramon": ramon_parser.ParseRamon}

    @staticmethod
    def __parse_config_file(config_filepath: str) -> Dict[str, str]:
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
        param = settings_data[name]

        return param

    def choose_package_name(self, name: str) -> Any:
        """
            Get package name from self.parser_dict dictionary

        :param name: name of exchanger;
        :return: object of exchanger parser class
        """
        conf = "package"
        package = self.get_params(name, conf)
        return self.parser_dict[package]

    def get_url_by_name(self, name: str) -> str:
        """
            Get url exchanger by name

        :param name: name of exchanger;
        :return: exchange url
        """
        conf = "urls"
        exchange_url = self.get_params(name, conf)
        return exchange_url

    @staticmethod
    def get_webdriver(host: str, port: str, usr: str, pwd: str) -> Any:
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
        # options.add_argument('--headless=new')  # turn off opening browser window
        options.add_argument(f"user-agent={useragent.random}")
        if usr and pwd:
            proxy_options = {
                "proxy": {"https": f"https://{usr}:{pwd}@{host}:{port}"},
            }
        else:
            proxy_options = dict()

        return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()),
                                options=options,
                                seleniumwire_options=proxy_options)
