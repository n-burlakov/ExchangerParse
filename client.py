import time

import wutil as wu
from typing import List, Dict
import logging

logging.basicConfig(filename="exchange_log.log", format='%(asctime)s - %(message)s', level=logging.INFO)


class ParseClient:
    """
        Main client class with methods for running exchange task.
    """

    def __init__(self):
        self.wu = wu.DataUtils()

    def prepare_exchange(self, name: str = None, host: str = None, port: str = None, usr: str = None, pwd: str = None,
                         email: str = None, user_pwd: str = None, currency_from: str = None, currency_to: str = None,
                         wallet_from: str = None, wallet_to: str = None, value: str = None) -> Dict:
        """
            Prepare exchanger for next exchange action.

        :param name: name of exchanger
        :param host: proxy host;
        :param port: proxy port;
        :param usr: proxy user name;
        :param pwd: proxy user password;
        :param email: target email for getting notification, and for auth;
        :param user_pwd: user password if authorization is required;
        :param currency_from: name of currencies which are give away. Can take values BTC, USDTTRC20, USDTERC20,
            USDTBEP20. In some exchangers, the names may differ and contain spaces or underscores. But the function
            input will always receive one of these particular options; for such exchangers you need to take this
            into account and select the right currencies;
        :param currency_to: name of currencies which are receive. (same as currency_from)
        :param wallet_from: wallet from which funds will be sent. wallet_from will be empty in most cases.
                            If there is a field for entering a wallet, and it is required, but the input received
                            an empty value, an error is returned. If it’s the other way around – there is no field,
                            but there is a wallet – it’s not an error;
        :param wallet_to: wallet to which funds will be sent;
        :param value: the amount of currency we give.
        :return: Dictionary of variables - {"status": "success", "target_wallet": "RJ42NK3J2R23RN",
                                "source_value": 34343.33, "task_url": https://example.urls/342342,
                                "timer_time": 1699873224.805435]
        """
        logging.info(f"{'#'*30} Run prepare exchange method for '{name.title()}' {'#'*30}")
        var_list = ["parse_url", "host", "port", "usr", "pwd", "email", "user_pwd", "currency_from", "currency_to",
                    "wallet_from", "wallet_to", "value"]
        parse_url = self.wu.get_url_by_name(name)
        logging.info(f"{'#'*30} Parse url is {parse_url} {'#'*30}")
        attribute_dict = dict(zip(var_list, [parse_url, host, port, usr, pwd, email, user_pwd, currency_from,
                                             currency_to, wallet_from, wallet_to, value]))
        parse_obj = self.wu.get_object_of_exchanger(name, attribute_dict)

        output_vars = parse_obj.parse_page()
        logging.info(f"{'#'*30} Task done! {'#'*30}")
        return output_vars

    def renew_task(self, name: str = None, task_url: str = None, host: str = None, port: str = None, usr: str = None,
                   pwd: str = None, ) -> Dict:
        """
            Information update.

        :param name: name of exchanger
        :param task_url: url which we get after clicked 'Exchange';
        :param host: proxy host;
        :param port: proxy port;
        :param usr: proxy user name;
        :param pwd: proxy user password;
        :return: Dictionary of variables - {"status": "success", "target_wallet": "RJ42NK3J2R23RN",
                                "source_value": 34343.33, "task_url": https://example.urls/342342,
                                "timer_time": 1699870733.443]
        """
        logging.info(f"{'#'*30} Run renew task for '{name.title()}' {'#'*30}")
        attribute_dict = dict(zip(["task_url", "host", "port", "usr", "pwd"], [task_url, host, port, usr, pwd]))
        parse_obj = self.wu.get_object_of_exchanger(name, attribute_dict)
        output_vars = parse_obj.exchange_renew_task()
        logging.info(f"{'#'*30} Renew has been done! {'#'*30}")
        return output_vars

    def approve_task(self, name: str = None, task_url: str = None, host: str = None, port: str = None, usr: str = None,
                     pwd: str = None, hash_code: str = None, ) -> Dict:
        """
            Click the “I paid” button or something similar.

        :param name: name of exchanger
        :param task_url: url which we get after clicked 'Exchange';
        :param host: proxy host;
        :param port: proxy port;
        :param usr: proxy user name;
        :param pwd: proxy user password;
        :param hash_code: hash code or transaction number
        :return: Dictionary of variables - {'status': 'success', 'text': 'complete'}
        """
        logging.info(f"{'#'*30} Run approve task for '{name.title()}' {'#'*30}")
        attribute_dict = dict(zip(["task_url", "host", "port", "usr", "pwd", "hash_code"],
                                  [task_url, host, port, usr, pwd, hash_code]))
        parse_obj = self.wu.get_object_of_exchanger(name, attribute_dict)
        logging.info(f"{'#'*30} Approve task has been done! {'#'*30}")
        return parse_obj.approve_task()


if __name__ == "__main__":
    ############################
    # Example execution methods
    temp = ParseClient()
    # temp_dict1 = temp.prepare_exchange(name="bitpayes", email="lala.liza@mail.ru", currency_to="BTC",
    #                                    currency_from="USDTTRC20",
    #                                    wallet_to="16mPRz23tVR4n1e4mJTEH2n82wTMWdnSE2", value=21)
    temp_dict1 = temp.prepare_exchange(name="cryptonex", email="lovesach4@gmail.com", currency_to="USDTTRC20",
                                       currency_from="BTC",
                                       # wallet_to="16mPRz23tVR4n1e4mJTEH2n82wTMWdnSE2", value=1)
                                       wallet_to="TAN47nJdDUPEAReQWgpEemtBiep6nusLgM", value=0.008)
    # print(temp_dict1)
    # temp_dict1 = {'status': 'waiting for payment', 'target_wallet': '3DnAW9EhwZkMjPJFrzFJDtqZy1HjRUuNZT', 'source_value': 305.534234, 'task_url': '{"domain": "cryptonex.top", "httpOnly": false, "name": "UIN", "path": "/", "sameSite": "Lax", "secure": false, "value": "100107664507ecbe"}', 'timer_time': 1701529495.0}
    # time.sleep(5)
    # print(temp.renew_task(name="cryptonex", task_url=temp_dict1['task_url']))
    # time.sleep(5)
    # print(temp.approve_task(name="cryptonex", task_url=temp_dict1['task_url']))
    # print(temp.renew_task(name="bitpayes", task_url=temp_dict1['task_url'], usr="ilovesach4@gmail.com", pwd='12345678qwe'))
    # print(temp.approve_task(name="cryptogin", task_url=temp_dict1['task_url'], usr="ilovesach4@gmail.com", pwd='12345678qwe',
    #                         hash_code="None"))

    ###########################