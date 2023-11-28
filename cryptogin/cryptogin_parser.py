import time
from typing import Any, Dict, Union
import logging

from base import BaseParser
import wutil as wu
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException, \
    ElementNotInteractableException


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

    def auth(self, login: str, password: str, driver: Any = None) -> bool:
        try:
            time.sleep(1)
            driver.find_element(By.ID, "loginFormEmail").send_keys(login)
            driver.find_element(By.ID, "loginFormPassword").send_keys(password)
            driver.find_element(By.ID, "dynamicLoginForm").find_element(By.CLASS_NAME, "button-primary").click()
            return True
        except:
            return False

    def exchange_renew_task(self, driver: Any = None, task_url: str = None) -> Dict:
        if not driver:
            task_url = self.task_url
            driver = self.wu.get_webdriver(self.host, self.port, self.usr, self.pwd)
            driver.get(task_url)
            if self.auth(login=self.usr, password=self.pwd, driver=driver):
                driver.refresh()
            else:
                raise "Authentication was unsuccessful. Please check your information"
            close = True
        else:
            close = False

        try:
            cur_time = self._timer_time(driver).split(':')
            timer_time = time.time() + int(cur_time[0]) * 60 + int(cur_time[1])

            source_value = float(
                driver.find_element(By.CLASS_NAME, "exchange-check-step-1").find_elements(By.CLASS_NAME,
                                                      "data-output-control")[1].text.split(" ")[0].replace(',', '.'))

            target_wallet = driver.find_element(By.CLASS_NAME,
                                    "exchange-check-step-2").find_elements(By.CLASS_NAME, "data-output-control")[1].text

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

    def approve_task(self, ) -> dict[str, Union[str, Any]]:
        driver = self.wu.get_webdriver(self.host, self.port, self.usr, self.pwd)
        try:
            driver.get(self.task_url)
            if self.auth(login=self.usr, password=self.pwd, driver=driver):
                driver.refresh()
            else:
                raise "Authentication was unsuccessful. Please check your information"
            self._click(driver, "class_name", "button-confirm-exchange")

            status = driver.find_element(By.ID, "statusTicketStep").find_elements(By.TAG_NAME, "h3")[1].text.split(
                "Статус | ")[1]
            return {"status": status, "text": "Button was clicked"}
        except Exception as exc:
            logging.error(str(exc))
        finally:
            driver.close()
            driver.quit()

    def get_currency_name(self, currency: str = None) -> str:
        coin_dict = {"USDT": "Tether ", "BTC": "Bitcoin"}
        for key, value in coin_dict.items():
            if key in currency:
                return currency.replace(key, value).replace("2", "-2")
        return currency

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
            except ElementClickInterceptedException:
                self.close_adds(driver)
            except Exception as exc:
                logging.error(str(exc))
                pass
        return driver

    def click_trade(self, driver: Any = None, count: float = 0):

        driver = self._click(driver, "class_name", "send-exchange-request-button")
        time.sleep(1)
        self.close_adds(driver)
        time.sleep(1)
        self._timer_time(driver)
        return driver

    def close_adds(self, driver):
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "closeIcon_e567"))
        )
        try:
            element.click()
        except ElementNotInteractableException:
            pass

    def parse_page(self) -> Dict:
        driver = self.wu.get_webdriver(self.host, self.port, self.usr, self.pwd)
        try:
            driver.get(self.parse_url)
            time.sleep(2)
            WebDriverWait(driver, 40).until(
                EC.element_to_be_clickable(driver.find_elements(By.CLASS_NAME, "custom-dropdown")[0])).click()

            WebDriverWait(driver, 30).until(EC.element_to_be_clickable(
                driver.find_elements(By.CLASS_NAME, "custom-dropdown")[0].find_element(By.CLASS_NAME,
                            "custom-dropdown-search").find_element(By.TAG_NAME, "input"))).send_keys(self.currency_from)

            WebDriverWait(driver, 30).until(EC.element_to_be_clickable(self.get_click_currency(self.currency_from,
                                    driver.find_elements(By.CLASS_NAME, "custom-dropdown-items")[0].find_elements(
                                        By.CLASS_NAME, "custom-dropdown-item")))).click()
            self.close_adds(driver)
            WebDriverWait(driver, 30).until(EC.element_to_be_clickable(driver.find_elements(By.CLASS_NAME,
                                                                                        "custom-dropdown")[1])).click()
            time.sleep(0.4)

            driver.find_elements(By.CLASS_NAME, "custom-dropdown")[1].find_element(By.CLASS_NAME,
                            "custom-dropdown-search").find_element(By.TAG_NAME, "input").send_keys(self.currency_to)

            WebDriverWait(driver, 30).until(EC.element_to_be_clickable(self.get_click_currency(self.currency_to,
                                    driver.find_elements(By.CLASS_NAME, "custom-dropdown-items")[1].find_elements(
                                        By.CLASS_NAME, "custom-dropdown-item")))).click()

            first_input = driver.find_elements(By.CLASS_NAME, "input-amount-wrapper")[0].find_element(By.TAG_NAME,
                                                                                                      "input")
            time.sleep(0.5)
            first_input.clear()
            time.sleep(1)
            first_input.send_keys(str(self.value))

            time.sleep(0.3)

            driver.find_elements(By.CLASS_NAME, "dynamic-content-panel")[1].find_element(By.TAG_NAME, "button").click()
            time.sleep(0.4)

            exchange_form = driver.find_element(By.ID, "exchangeFormRequisitesPart")
            for form_group in exchange_form.find_elements(By.CLASS_NAME, "form-row-control"):
                if "Введите адрес получения" in form_group.get_attribute("placeholder") and self.wallet_to:
                    form_group.send_keys(self.wallet_to)
                elif "Введите ваш Email" in form_group.get_attribute("placeholder") and self.email:
                    form_group.send_keys(self.email)

            # accept rules
            try:
                WebDriverWait(driver, 30).until(
                    EC.element_to_be_clickable(driver.find_element(By.ID, "ruleAgree-block"))).find_element(By.TAG_NAME,
                                                                                                            "label").click()
            except ElementClickInterceptedException:
                time.sleep(0.2)
                WebDriverWait(driver, 30).until(
                    EC.element_to_be_clickable(driver.find_element(By.ID, "ruleAgree-block"))).find_element(By.TAG_NAME,
                                                                                                        "label").click()
            self.click_trade(driver)

            task_url = driver.current_url
            return self.exchange_renew_task(driver, task_url=task_url)

        except Exception as exc:
            logging.error(str(exc))

        finally:
            driver.close()
            driver.quit()
