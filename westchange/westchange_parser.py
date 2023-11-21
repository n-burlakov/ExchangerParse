from datetime import datetime
import re
import time
from typing import List, Any, Dict
import logging

from base import BaseParser
import wutil as wu
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.service import Service
from selenium.common.exceptions import ElementClickInterceptedException, ElementNotInteractableException, \
    ElementClickInterceptedException, NoSuchElementException


class ParseRamon(BaseParser):
    def __init__(self, initial_data: dict = None):
        self.wu = wu.DataUtils()
        for key in initial_data:
            setattr(self, key, initial_data[key])

    def _timer_time(self, driver: Any = None) -> str:
        count = 0
        while count != 40:
            count += 1
            time.sleep(0.5)
            try:
                driver.find_element(By.ID, "transaction-number")
                return driver.find_element(By.ID, "time-left").text
            except NoSuchElementException:
                if 'E-mail не может быть пустым' in driver.find_element(By.ID, "exchange-form").text:
                    raise "E-mail не может быть пустым"
                pass
        else:
            raise TimeoutError

    def exchange_renew_task(self, driver: Any = None, task_url: str = None) -> Dict:
        if not driver:
            driver = self.wu.get_webdriver(self.host, self.port, self.usr, self.pwd)
            driver.get(task_url)
            close = True
        else:
            close = False
        try:
            timer_left = self._timer_time(driver)
            timer_time = time.time() + int(timer_left[0]) * 60 + int(timer_left[0])

            source_value = float(re.sub(r"([^.\d])", "",
                                        [i.find_element(By.TAG_NAME, "b").text for i in
                                         driver.find_elements(By.CLASS_NAME, "faq-q") if
                                         "будет получено" in i.text.lower()][0].split("(")[1]))

            target_wallet = driver.find_element(By.ID, "blurred-block").text.split(': ')[1]

            status = [i.find_element(By.TAG_NAME, "b").text for i in
                      driver.find_elements(By.CLASS_NAME, "faq-q") if
                      "Статус" in i.text][0]
            return {"status": status, "target_wallet": target_wallet, "source_value": source_value,
                    "task_url": task_url,
                    "timer_time": timer_time}
        except Exception as exc:
            logging.error(str(exc))
        finally:
            if close:
                driver.close()
                driver.quit()

    def approve_task(self, task_url: str = None) -> List:
        driver = self.wu.get_webdriver(self.host, self.port, self.usr, self.pwd)
        try:
            driver.get(task_url)
            self._click(driver, "id", "paid-submit")
            return {"status": "success", "text": "Button was clicked"}
        except Exception as exc:
            logging.error(str(exc))
        finally:
            driver.close()
            driver.quit()

    def get_currency_name(self, currency: str = None) -> str:
        coin_dict = {"USDT": "Tether ("}
        return [currency.replace(key, value).replace("20", "-20) USDT") for key, value in coin_dict.items() if key in currency][0]

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

    def click_trade(self, driver: Any = None, count: float = 0):
        driver = self._click(driver, "id", "transaction-submit-create-ajax")
        self._timer_time(driver)
        return driver

    def parse_page(self) -> Dict:
        driver = self.wu.get_webdriver(self.host, self.port, self.usr, self.pwd)
        try:
            driver.get(self.parse_url)
            self.get_click_currency(self.currency_from,
                                    driver.find_element(By.CLASS_NAME, "xtt_left_col_table_ins").find_elements(
                                        By.CLASS_NAME, "xtt_one_line_left")).click()
            self.get_click_currency(self.currency_to,
                                    driver.find_element(By.CLASS_NAME, "xtt_right_col_table_ins").find_elements(
                                        By.CLASS_NAME, "js_item_right")).click()

            while True:
                time.sleep(0.4)
                try:
                    exchange_form = driver.find_element(By.CLASS_NAME, "xchange_div")
                    break
                except IndexError as exc:
                    logging.error("Exchange form is not available \n" + str(exc))
                    pass

            input_tag = exchange_form.find_element(By.CLASS_NAME, "input-group").find_element(By.TAG_NAME, "input")
            input_tag.send_keys(str(self.value))

            for form_group in driver.find_elements(By.CLASS_NAME, "form-group"):
                if "e-mail" in form_group.text.lower() and self.email:
                    form_group.find_element(By.TAG_NAME, "input").send_keys(self.email)
                elif "кошелёк для получения" in form_group.text.lower() or "wallet" in form_group.text.lower() and self.wallet_to:
                    form_group.find_element(By.TAG_NAME, "input").send_keys(self.wallet_to)
            driver = self.click_trade(driver)

            task_url = driver.current_url
            return self.exchange_renew_task(driver, task_url=task_url)

        except Exception as exc:
            logging.error(str(exc))

        finally:
            driver.close()
            driver.quit()
