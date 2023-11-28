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


class ParseWestchange(BaseParser):
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
                driver.find_element(By.CLASS_NAME, "breadcrumb_title")
                return time.time() + int(driver.find_element(By.CLASS_NAME, "time_span").get_attribute("end-time"))
            except NoSuchElementException:
                pass
        else:
            raise TimeoutError

    def exchange_renew_task(self, driver: Any = None, task_url: str = None) -> Dict:
        if not driver:
            driver = self.wu.cloudflare_challenge_solve_captcha(self.task_url, self.host, self.port, self.usr, self.pwd)
            close = True
        else:
            close = False
        try:
            timer_time = self._timer_time(driver)

            source_value = float([i.find_element(By.TAG_NAME, "p").text for i in
                                  driver.find_elements(By.CLASS_NAME, "block_payinfo_line") if
                                  "Сумма к получению: " in i.text][0].split(": ")[1].split(' ')[0])

            status = driver.find_element(By.CLASS_NAME, "block_status_bids").text

            driver.find_element(By.CLASS_NAME, "success_paybutton").click()
            time.sleep(1)
            # get current window handle
            p = driver.current_window_handle

            # get first child window
            chwd = driver.window_handles

            for w in chwd:
                # switch focus to child window
                if (w != p):
                    driver.switch_to.window(w)
            target_wallet = driver.find_element(By.CLASS_NAME, "zone_table").find_elements(By.CLASS_NAME, "zone_text")[
                1].text

            return {"status": status, "target_wallet": target_wallet, "source_value": source_value,
                    "task_url": task_url,
                    "timer_time": timer_time}
        except Exception as exc:
            logging.error(str(exc))
        finally:
            if close:
                driver.close()
                driver.quit()

    def approve_task(self,) -> List:
        return {"status": "success", "text": "Exchange was approved, but the button 'Paid' wasn't find."}

    def get_currency_name(self, currency: str = None) -> str:
        coin_dict = {"USDT": "Tether ("}
        return \
            [currency.replace(key, value).replace("20", "-20) USDT") if key in currency else currency for key, value in
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
        driver.find_element(By.CLASS_NAME, "xchange_submit").click()
        time.sleep(1)
        driver.find_element(By.CLASS_NAME, "standart_window_submit").find_element(By.TAG_NAME, "input").click()
        self._timer_time(driver)
        return driver

    def parse_page(self) -> Dict:
        driver = self.wu.cloudflare_challenge_solve_captcha(self.parse_url, self.host, self.port, self.usr,
                                                            self.pwd)
        try:
            time.sleep(5)
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

            if self.email:
                driver.find_element(By.CLASS_NAME, "xchange_pers_input").find_element(By.TAG_NAME, "input").send_keys(
                    self.email)

            for form_group in exchange_form.find_elements(By.CLASS_NAME, "xchange_curs_line"):
                if "на счет" in form_group.text.lower() and self.wallet_to:
                    form_group.find_element(By.TAG_NAME, "input").send_keys(self.wallet_to)

            form_group.find_element(By.CLASS_NAME, "select_js_title").click()
            time.sleep(1)
            form_group.find_elements(By.CLASS_NAME, "select_js_ulli")[1].click()

            input_tag = exchange_form.find_element(By.CLASS_NAME, "xchange_sum_input").find_element(By.TAG_NAME,
                                                                                                    "input")
            input_tag.clear()
            time.sleep(1)
            input_tag.send_keys(str(self.value))
            time.sleep(1)

            for checkbox in exchange_form.find_elements(By.CLASS_NAME, "checkbox"):
                checkbox.find_element(By.TAG_NAME, "label").click()
                time.sleep(1)

            driver = self.click_trade(driver)

            task_url = driver.current_url
            return self.exchange_renew_task(driver, task_url=task_url)

        except Exception as exc:
            logging.error(str(exc))

        finally:
            driver.close()
            driver.quit()
