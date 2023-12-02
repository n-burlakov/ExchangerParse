import json
import re
import time
from datetime import datetime
from typing import List, Any, Dict
import logging
import pickle

from base import BaseParser
import wutil as wu
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC


class ParseCryptonex(BaseParser):
    def __init__(self, initial_data: dict = None):
        self.wu = wu.DataUtils()
        for key in initial_data:
            setattr(self, key, initial_data[key])

    def get_currency_name(self, currency: str = None) -> str:
        coin_dict = {"USDTTRC20": "USDT TRC20", "USDTTERC20": "USDT ERC20", "USDTBEP20": "USDT BEP20",
                     "BTC": "BTC BitCoin"}
        return [currency.replace(key, value) for key, value in coin_dict.items() if key in currency][0]

    def get_click_currency(self, currency: str, currency_list: list):
        current_currency = self.get_currency_name(currency)
        for row_item in currency_list:
            if current_currency in row_item.text:
                return row_item

    def _click(self, driver: Any = None, element_search: str = None, name: str = None) -> Any:
        counter = 0
        while counter != 10:
            counter += 1
            try:
                time.sleep(0.4)
                if element_search == "class_name":
                    driver.find_element(By.CLASS_NAME, name).click()
                elif element_search == "id":
                    driver.find_element(By.ID, name).click()
                break
            except Exception as exc:
                logging.error(str(exc))
                pass
        return driver

    def _timer_time(self, driver: Any = None) -> tuple:
        try:
            date_str = driver.find_elements(By.CLASS_NAME, "data-text")[0].text.split('\n')[1]
            timer_time = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S').timestamp() + 900
            if time.time() > timer_time:
                status = 'canceled'
            else:
                status = 'waiting for payment'
            return timer_time, status
        except NoSuchElementException:
            return None

    def auth(self, login: str, password: str, driver: Any = None) -> bool:
        try:
            driver.find_element(By.CLASS_NAME, "px-md-4").click()
            time.sleep(1)
            driver.find_element(By.ID, "ulogin").send_keys(login)
            driver.find_element(By.ID, "upass").send_keys(password)
            driver.find_element(By.ID, "btn-block").click()
            return True
        except:
            return False

    def exchange_renew_task(self, driver: Any = None, task_url: str = None) -> Dict:
        if not driver:
            task_url = self.task_url
            driver = self.wu.get_webdriver(self.host, self.port, self.usr, self.pwd)
            driver.get('https://cryptonex.top/')
            time.sleep(1)
            driver.delete_all_cookies()
            cookie = json.loads(self.task_url)
            driver.add_cookie(cookie)
            time.sleep(0.5)
            driver.refresh()

            # if not self.auth(login=self.usr, password=self.pwd, driver=driver):
            #     raise "Authentication was unsuccessful. Please check your login and password"
            #
            # driver.find_element(By.ID, "pills-2-tab").click()
            # driver.find_element(By.ID, "btn-oplati").click()
            # WebDriverWait(driver, 30).until(driver.find_element(By.CLASS_NAME, "form-control-lg"))

            close = True
        else:
            close = False

        try:
            WebDriverWait(driver, 100).until(EC.presence_of_element_located((By.ID, "iFindMoney")))

            timer_time, status = self._timer_time(driver)
            source_value = float(driver.find_elements(By.CLASS_NAME, "bg-control")[2].get_attribute("value").split()[0])

            while True:
                time.sleep(1)
                try:
                    target_wallet = driver.find_element(By.ID, "tocopy").get_attribute("value")
                    break
                except Exception as ex:
                    if "ожидан" in driver.find_elements(By.CLASS_NAME, "data-text")[1].text:
                        target_wallet = None
                        break
                    logging.error("Exchange form is not available \n" + str(ex))

            return {"status": status, "target_wallet": target_wallet, "source_value": source_value,
                    "task_url": task_url,
                    "timer_time": timer_time}
        except Exception as exc:
            logging.error(str(exc))
        finally:
            if close:
                driver.close()
                driver.quit()

    def approve_task(self, ) -> Dict:
        driver = self.wu.get_webdriver(self.host, self.port, self.usr, self.pwd)
        try:
            driver.get('https://cryptonex.top/')
            time.sleep(1)
            driver.delete_all_cookies()
            cookie = json.loads(self.task_url)
            driver.add_cookie(cookie)
            time.sleep(1)
            driver.refresh()

            WebDriverWait(driver, 100).until(EC.presence_of_element_located((By.ID, "iFindMoney")))

            if self._timer_time(driver)[1] != 'canceled':
                return {"status": "success", "text": "Button doesn't exist"}
            else:
                return {"status": "canceled", "text": "Button doesn't exist"}

        except Exception as exc:
            logging.error(str(exc))
        finally:
            driver.close()
            driver.quit()

    def parse_page(self) -> Dict:
        driver = self.wu.get_webdriver(self.host, self.port, self.usr, self.pwd)
        try:
            driver.get(self.parse_url)
            self.get_click_currency(self.currency_from,
                                    driver.find_element(By.ID, "InputCoin").find_elements(By.TAG_NAME,
                                                                                          "option")).click()
            time.sleep(1)
            self.get_click_currency(self.currency_to,
                                    driver.find_element(By.ID, "OutputCoin").find_elements(By.TAG_NAME,
                                                                                           "option")).click()
            time.sleep(1)

            count = 0
            while count != 10:
                time.sleep(0.5)
                count += 1
                self._click(driver, "class_name", "btn-success")
                try:
                    if driver.find_element(By.ID, "ss"):
                        break
                except:
                    pass

            input_value = driver.find_element(By.ID, "ss")
            # time.sleep(1)
            input_value.clear()
            time.sleep(0.5)
            input_value.send_keys(str(self.value))
            driver.find_element(By.ID, "toaddr").send_keys(self.wallet_to)
            driver.find_element(By.ID, "iemail").send_keys(self.email)

            try:
                self._click(driver, "id", "req000")
            except Exception as ex:
                logging.error(driver.find_element(By.ID, "opros").find_element(By.TAG_NAME, "div").text)
                logging.error(ex)

            self._click(driver, "class_name", "btn-lg")
            time.sleep(3)
            self._click(driver, "class_name", "btn-success")

            cookie_task_url = driver.get_cookie("UIN")

            return self.exchange_renew_task(driver, task_url=json.dumps(cookie_task_url))

        except Exception as exc:
            logging.error(str(exc))

        finally:
            driver.close()
            driver.quit()
