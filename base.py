from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Any


class BaseParser(ABC):
    """
        Abstract base class for future exchangers
    """
    @abstractmethod
    def parse_page(self) -> Dict:
        """
            Parse exchanger with selenium.

        :return: task url with information about transaction
        """
        pass

    @abstractmethod
    def click_trade(self, driver: Any = None) -> None:
        """
            Click button 'Ready to trade', confirm that button clicked.

        :param driver: webdriver object;
        :return: driver
        """
        pass

    def auth(self, login: str, password: str) -> bool:
        """
            Authenticate method

        :param login: user login;
        :param password: user password;
        :return: auth status
        """
        pass

    def _click(self, driver: Any = None, element_search: str = None, name: str = None) -> Any:
        """
            Press click any webdriver element, until that will be done in 4 second or raise Exception
            that it couldn't be done.

        :param driver: webdriver selenium current object;
        :param element_search: name of search attribute, could be: "id", "class_name" and etc.;
        :param name: name of this attribute;
        :return: webdriver selenium current object.
        """
        pass

    @abstractmethod
    def get_currency_name(self, currency: str = None) -> str:
        """
            Get name of currency on web page.
            Override class with key in dictionary for this exchanger example:
                coin_dict = {"USDT": "Tether ", "BTC": "Bitcoin"}

        :param currency: name of currency which we want choose;
        :return: name of currency how it looks on web page.
        """
        pass

    @abstractmethod
    def _timer_time(self, driver: Any = None) -> str:
        """
            Get time which are need for approve exchange.

        :param driver: webdriver selenium current object;
        :return: time with format like '5 min 43 sec', string format.
        """
        pass

    @abstractmethod
    def exchange_renew_task(self, driver: Any = None, task_url: str = None) -> Dict:
        """
            Update information after getting task url for exchange.

        :param driver: webdriver selenium current object;
        :param task_url: url which we get after clicked 'Exchange';
        :return: List of variables - [status, target_wallet, source_value, task_url, timer_time]
        """
        pass

    @abstractmethod
    def approve_task(self, task_url: str = None) -> Dict:
        """
            Click button approve exchange task in task url.

        :param task_url: url which we get after clicked 'Exchange';
        :return: List of variables - [status, text_of_result]
        """
        pass
