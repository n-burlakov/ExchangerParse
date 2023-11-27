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
from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException


class ParseCryptogin(BaseParser):
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
                driver.find_element(By.ID, "exchangeFormPaymentStep")
                return driver.find_element(By.CLASS_NAME, "exchange-payment_timer").text.split("Время на оплату ")[1]
            except NoSuchElementException:
                pass
        else:
            raise TimeoutError

    def exchange_renew_task(self, driver: Any = None, task_url: str = None) -> Dict:
        if not driver:
            driver = self.wu.cloudflare_challenge_solve_captcha(task_url, self.host, self.port, self.usr, self.pwd)
            close = True
        else:
            close = False
        try:

            cur_time = self._timer_time(driver).split(':')
            timer_time = time.time() + int(cur_time[0]) * 60 + int(cur_time[1])

            exchange_check_step = driver.find_element(By.CLASS_NAME, "exchange-check-step-2")
            for item in exchange_check_step.find_elements(By.CLASS_NAME, "data-output-control"):
                if "Сумма к оплате" in item.text:
                    source_value = float(
                        item.find_element(By.CLASS_NAME, "data-output-control-value").split(" ")[1].replace(',', '.'))
                elif "Адрес получения" in item.text:
                    target_wallet = item.find_element(By.CLASS_NAME, "data-output-control-value").text
            status = "success"

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
            self._click(driver, "class_name", "button-confirm-exchange")
            return {"status": "success", "text": "Button was clicked"}
        except Exception as exc:
            logging.error(str(exc))
        finally:
            driver.close()
            driver.quit()

    def get_currency_name(self, currency: str = None) -> str:
        coin_dict = {"USDT": "Tether ", "BTC": "Bitcoin"}
        return \
            [currency.replace(key, value).replace("2", "-2") if key in currency else currency for key, value in
             coin_dict.items()][0]

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
                elif element_search == "tag":
                    driver.find_element(By.TAG_NAME, name).click()
                break
            except Exception as exc:
                logging.error(str(exc))
                pass
        return driver

    def click_trade(self, driver: Any = None, count: float = 0):
        driver.find_element(By.CLASS_NAME, "send-exchange-request-button").click()
        time.sleep(1)
        self._timer_time(driver)
        return driver

    def parse_page(self) -> Dict:
        driver = self.wu.get_webdriver(self.host, self.port, self.usr, self.pwd)
        try:
            driver.get(self.parse_url)

            self.get_click_currency(self.currency_from,
                                    driver.find_elements(By.CLASS_NAME, "custom-dropdown-items")[0].find_elements(
                                        By.CLASS_NAME, "custom-dropdown-item")).click()
            first_input = driver.find_elements(By.CLASS_NAME, "input-amount-wrapper")[0]
            first_input.clear()
            time.sleep(1)
            first_input.send_keys(str(self.value))
            self.get_click_currency(self.currency_to,
                                    driver.find_elements(By.CLASS_NAME, "custom-dropdown-items")[1].find_elements(
                                        By.CLASS_NAME, "custom-dropdown-item")).click()

            driver.find_elements(By.CLASS_NAME, "dynamic-content-panel")[1].find_element(By.TAG_NAME, "button").click()
            time.sleep(0.4)
            exchange_form = driver.find_element(By.ID, "exchangeFormRequisitesPart")

            for form_group in exchange_form.find_elements(By.CLASS_NAME, "form-row-control"):
                if "Введите адрес получения" in form_group.get_attribute("placeholder") and self.wallet_to:
                    form_group.send_keys(self.wallet_to)
                elif "Введите ваш Email" in form_group.get_attribute("placeholder") and self.email:
                    form_group.send_keys(self.wallet_to)

            # accept rules
            exchange_form.find_elements(By.CLASS_NAME, "ruleAgree-block").find_element(By.TAG_NAME, "label").click()
            time.sleep(0.5)

            driver = self.click_trade(driver)

            task_url = driver.current_url
            return self.exchange_renew_task(driver, task_url=task_url)

        except Exception as exc:
            logging.error(str(exc))

        finally:
            driver.close()
            driver.quit()