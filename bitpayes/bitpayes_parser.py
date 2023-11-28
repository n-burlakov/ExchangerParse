import re
import time
from typing import List, Any, Dict
import logging

from base import BaseParser
import wutil as wu
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


class ParseBitpayes(BaseParser):
    def __init__(self, initial_data: dict = None):
        self.wu = wu.DataUtils()
        for key in initial_data:
            setattr(self, key, initial_data[key])

    def _timer_time(self, driver: Any = None) -> float:
        try:
            script = driver.find_element(By.ID, "TimerLinetemp").find_elements(By.TAG_NAME, "script")[0]
            innerHTML = script.get_property('innerHTML')
            time_step = re.search('var StepCount = (.*);', innerHTML).group(1)
            return time.time() + int(time_step) * 100
        except NoSuchElementException:
            return None

    def accept_cookie(self, driver: Any = None) -> Any:
        try:
            cookie = driver.find_element(By.ID, "bot1-Msg1")
            cookie.click()
        except NoSuchElementException:
            pass
        return driver

    def auth(self, login: str, password: str, driver: Any = None) -> bool:
        try:
            [item for item in driver.find_elements(By.CLASS_NAME, "nav-link") if "Авторизация" in item.text][0].click()
            time.sleep(1)
            driver.find_element(By.ID, "UserEmailAuth").send_keys(login)
            driver.find_element(By.ID, "UserPasswordAuth").send_keys(password)
            driver.find_element(By.ID, "btnReAuth").click()
            return True
        except:
            return False

    def exchange_renew_task(self, driver: Any = None, task_url: str = None) -> Dict:
        if not driver:
            driver = self.wu.get_webdriver(self.host, self.port, self.usr, self.pwd)
            driver.get(self.task_url)
            driver = self.accept_cookie(driver)
            task_url = self.task_url
            if self.auth(login=self.usr, password=self.pwd, driver=driver):
                driver.refresh()
            else:
                raise "Authentication was unsuccessful. Please check your login and password"
            close = True
        else:
            close = False
        try:
            status = driver.find_element(By.ID, "OperationLabel").text
            if "ожида" in status.lower():
                timer_time = self._timer_time(driver)
            else:
                timer_time = None
            while True:
                time.sleep(1)
                try:
                    target_wallet = driver.find_element(By.ID, "CryptoWallet").text
                    break
                except Exception as ex:
                    if "Не завершена" in status:
                        target_wallet = None
                        break
                    logging.error("Exchange form is not available \n" + str(ex))

            source_value = float(re.sub(r"[^.\d]", "",
                                        driver.find_element(By.ID, "InfoBlock").find_elements(By.TAG_NAME, "strong")[
                                            1].text))

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
            driver.get(self.task_url)
            driver = self.accept_cookie(driver)
            if self.auth(self.usr, self.pwd, driver):
                driver.refresh()
            else:
                raise "Authentication was unsuccessful. Please check your login and password"
            driver.execute_script("arguments[0].setAttribute('value',arguments[1])",
                                  driver.find_element(By.ID, "payment_USDT_TRANID"), self.hash_code)
            self._click(driver, "class_name", "btn-success")
            return {"status": "success", "text": "Button was clicked"}
        except Exception as exc:
            logging.error(str(exc))
        finally:
            driver.close()
            driver.quit()

    def get_currency_name(self, currency: str = None) -> str:
        coin_dict = {"USDT": "Tether USD (", "BTC": "Bitcoin"}
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

    def check_alert(self, driver):
        try:
            error = driver.find_element(By.CLASS_NAME, "openPosition").find_element(By.CLASS_NAME, "alert-danger")
            logging.error(error.text)
            raise error.text
        except NoSuchElementException:
            pass

    def parse_page(self) -> Dict:
        driver = self.wu.get_webdriver(self.host, self.port, self.usr, self.pwd)
        try:
            driver.get(self.parse_url)
            driver = self.accept_cookie(driver)
            self.get_click_currency(self.currency_from,
                                    driver.find_elements(By.CLASS_NAME, "col-md-6")[0].find_elements(By.CLASS_NAME,
                                                                                                     "inmetka")).click()
            time.sleep(1)
            group_currency_list = driver.find_elements(By.CLASS_NAME, "col-md-6")[1].find_elements(By.CLASS_NAME,
                                                                                                   "hidden_content")
            for group_currency in group_currency_list:
                if group_currency.get_attribute("style") == 'display: block;':
                    self.get_click_currency(self.currency_to,
                                            driver.find_elements(By.CLASS_NAME, "col-md-6")[1].find_elements(
                                                By.CLASS_NAME, "list-group-item")).click()
                    break

            while True:
                time.sleep(0.4)
                try:
                    exchange_form = driver.find_element(By.CLASS_NAME, "card-body")
                    break
                except IndexError as exc:
                    logging.error("Exchange form is not available \n" + str(exc))
                    pass

            input_tag = exchange_form.find_element(By.CLASS_NAME, "input-group").find_element(By.TAG_NAME, "input")
            input_tag.send_keys(str(self.value))
            self.check_alert(driver)  # check right value input

            driver = self._click(driver, 'id', "btnAddAllForm")
            time.sleep(1)

            for item in driver.find_elements(By.CLASS_NAME, "addReqForApplic"):
                for elem in item.find_elements(By.TAG_NAME, "input"):
                    if elem.get_attribute("name") == "UserEmailAuthForm":
                        elem.send_keys(self.email)
                    else:
                        elem.send_keys(self.wallet_to)

            for tag in driver.find_elements(By.TAG_NAME, "option"):
                if tag.get_attribute("value") == "dec_fastestFee":
                    tag.click()
                    break

            driver.find_element(By.ID, "btnSendNext").click()

            try:
                driver.find_element(By.ID, "bot1-Msg1").click()
                time.sleep(0.5)
            except NoSuchElementException:
                pass

            time.sleep(5)

            self.check_alert(driver)  # check right exchange

            driver = self.accept_cookie(driver)

            for tag in driver.find_elements(By.CLASS_NAME, "custom-control-label"):
                if tag.get_attribute("for") == "rulesConfirmOperation":
                    tag.click()
                    time.sleep(1)

            driver = self._click(driver, "id", "ButtonPayment")

            task_url = driver.current_url
            return self.exchange_renew_task(driver, task_url=task_url)

        except Exception as exc:
            logging.error(str(exc))

        finally:
            driver.close()
            driver.quit()
