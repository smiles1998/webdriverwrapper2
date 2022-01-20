import logging
from urllib.parse import urlparse, urlunparse, urlencode

from selenium.webdriver import *
import selenium.common.exceptions as selenium_exc
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s : %(message)s')


class _WebdriverBaseWrapper:
    default_wait_timeout = 10
    """
    Default timeout in seconds for wait* methods(such as wait_for_element).
    """

    def click(self, *args, **kwargs):
        """
        When you not pass any argument, it clicks on current element. If you
        pass some arguments, it works as following snippet. For more info what
        you can pass check out method :py:meth `~._WebdriverBaseWrapper.get_elm`.

        ... code-block:: python

            driver.get_elm(id='someid').click()
        """
        if args or kwargs:
            elm = self.get_elm(*args, **kwargs)
            elm.click()
        else:
            super().click()

    def get_elm(self,
                id_=None, class_name=None, name=None, tag_name=None,
                parent_id=None, parent_class_name=None, parent_name=None, parent_tag_name=None,
                xpath=None, css_selector=None):
        """
        Returns first found element. This method uses
        :py:meth: `~._WebdriverBaseWrapper.get_elms`.
        """
        elms = self.get_elms(
            id_, class_name, name, tag_name,
            parent_id, parent_class_name, parent_name, parent_tag_name,
            xpath, css_selector
        )
        if not elms:
            raise selenium_exc.NoSuchElementException()
        return elms[0]

    def get_elms(self,
                 id_=None, class_name=None, name=None, tag_name=None,
                 parent_id=None, parent_class_name=None, parent_name=None, parent_tag_name=None,
                 xpath=None, css_selector=None):
        """
        Shortcut for :py:meth: `find_element* <selenium.webdriver.remote.webelement.WebElement.find_element>`
        methods. It's shorter, and you can quickly find element in element.

        ... code-block:: python

            elm = driver.find_element_by_id('someid')
            elm.find_elements_by_class_name('someclass')

            # vs.

            elm = driver.get_elms(parent_id='someid', class_name='someclass')
        """
        if parent_id or parent_class_name or parent_name or parent_tag_name:
            parent = self.get_elm(parent_id, parent_class_name, parent_name, parent_tag_name)
        else:
            parent = self

        if len([x for x in (id_, class_name, name, tag_name, xpath, css_selector) if x is not None]) > 1:
            raise Exception('You can find element only by one param.')

        if id_ is not None:
            return parent.find_elements(by=By.ID, value=id_)
        if class_name is not None:
            return parent.find_elements(by=By.CLASS_NAME, value=class_name)
        if name is not None:
            return parent.find_elements(by=By.NAME, value=name)
        if tag_name is not None:
            return parent.find_elements(by=By.TAG_NAME, value=tag_name)
        if xpath is not None:
            return parent.find_elements(by=By.XPATH, value=xpath)
        if css_selector is not None:
            return parent.find_elements(by=By.CSS_SELECTOR, value=css_selector)
        raise Exception('You must specify id or name of element on which you want to click.')

    def wait_for_element(self, timeout=None, message='', *args, **kwargs):
        """
        Shortcut for waiting for element. If it not ends with exception, it
        returns that element. Default timeout is `~.default_wait_timeout`.
        Same as following:

        ... code-block:: python
            selenium.webdriver.support.wait.WebDriverWait(driver, timeout).until(lambda driver: driver.get_elm(...))
        """
        if not timeout:
            timeout = self.default_wait_timeout
        self.wait(timeout).until(lambda driver: driver.get_elm(*args, **kwargs), message=message)

        elm = self.get_elm(*args, **kwargs)
        return elm

    def wait_for_element_show(self, timeout=None, message='', *args, **kwargs):
        """
        Shortcut for waiting for visible element. If it not ends with exception, it
        returns that element. Default timeout is `~.default_wait_timeout`.
        Some as following:

        ... code-block:: python
            selenium.webdriver.support.wait.WebDriverWait(driver, timeout).until(lambda driver: driver.get_elm(...))
        """
        if not timeout:
            timeout = self.default_wait_timeout
        def callback(driver):
            elms = self.get_elms(*args, **kwargs)
            if not elms:
                return False
            try:
                if all(not elm.is_displayed() for elm in elms):
                    return False
            except selenium_exc.StaleElementReferenceException:
                return False
            return True
        self.wait(timeout).until(callback, message=message)
        elm = self.get_elm(*args, **kwargs)
        return elm

    def wait_for_element_hide(self, timeout=None, message='', *args, **kwargs):
        """
        Shortcut for waiting for hiding of element. Detault timeout is `~.default_wait_timeout`.
        Same as following:

        ... code-block:: python
            selenium.webdriver.support.wait.WebDriverWait(driver, timeout).until(lambda driver: not driver.get_elm(...))
        """
        if not timeout:
            timeout = self.default_wait_timeout
        def callback(driver):
            elms = self.get_elms(*args, **kwargs)
            if not elms:
                return True
            try:
                if all(not elm.is_displayed() for elm in elms):
                    return True
            except selenium_exc.StaleElementReferenceException:
                return False
            return False
        self.wait(timeout).until(callback, message=message)

    def wait(self, timeout=None):
        """
        Call following snippet, so you don't have to remember what import. See
        :py:obj:`WebDriverWait <selenium.webdriver.support.wait.WebDriverWait>` for more
        information. Detault timeout is `~.default_wait_timeout`.

        ... code-block:: python
            selenium.webdriver.support.wait.WebDriverWait(driver, timeout)

        Example:

        ... code-block:: python
            driver.wait().until(lambda driver: len(driver.find_element_by_id('elm')) > 10)

        """
        if not timeout:
            timeout = self.default_wait_timeout
        return WebDriverWait(self, timeout)


class _WebdriverWrapper(_WebdriverBaseWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def _driver(self):
        """
        Returns always driver, not element. Use it when you need driver
        and variable can be driver or element.
        """
        return self

    @property
    def html(self):
        """
        Returns ``innerHTML`` of whole page. On page have to be tag ``body``.
        """
        try:
            body = self.get_elm(tag_name='body')
        except selenium_exc.NoSuchElementException:
            return None
        else:
            return body.get_attribute('innerHTML')

    def break_point(self):
        """
        Stops testing and wait for pressing enter to continue.

        Useful when you need check Chrome console for some info for example.
        """
        logging.info('Break point. Type enter to continue.')
        input()

    def get_url(self, path=None, query=None):
        if urlparse(path).netloc:
            return path

        if isinstance(query, dict):
            query = urlencode(query)

        url_parts = urlparse(self.current_url)
        new_url_parts = (
            url_parts.scheme,
            url_parts.netloc,
            path or url_parts.path,
            None, # params
            query,
            None # fragment
        )
        url = urlunparse(new_url_parts)

        return url

    def switch_to_window(self, window_name=None, title=None, url=None):
        """
        WebDriver implements switching to other window only by it's name. With
        wrapper there is also option to switch by title of window or URL. URL
        can be also relative path.
        """
        if window_name:
            self.switch_to.window(window_name)
            return

        if url:
            url = self.get_url(path=url)

        for window_handle in self.window_handles:
            self.switch_to.window(window_handle)
            if title and self.title == title:
                return
            if url and self.current_url == url:
                return
        raise selenium_exc.NoSuchWindowException('Window (title=%s, url=%s) not found.' % (title, url))

    def close_window(self, window_name=None, title=None, url=None):
        """
        WebDriver implements only closing current window. If you want to close
        some window without having to switch to it, use this method.
        """
        main_window_handle = self.current_window_handle
        self.switch_to_window(window_name, title, url)
        self.close()
        self.switch_to_window(main_window_handle)

    def close_other_windows(self):
        """
        Closes all not current windows. Useful for tests - after each test you
        can automatically close all windows.
        """
        main_window_handle = self.current_window_handle
        for window_handle in self.window_handles:
            if window_handle == main_window_handle:
                continue
            self.switch_to_window(window_handle)
            self.close()
        self.switch_to_window(main_window_handle)

    def close_alert(self, ignore_exception=False):
        """
        JS alerts all blocking. This method closes it. If there is no alert,
        method raises exception. In tests is good to call this method with
        ``ignore_exception`` setted to ``True`` which will ignore any exception.
        """
        try:
            alert = self.get_alert()
            alert.accept()
        except:
            if not ignore_exception:
                raise

    def get_alert(self):
        """
        Returns instance of :py:obj:`~selenium.webdriver.common.alert.Alert`.
        """
        return Alert(self)

    def wait_for_alert(self, timeout=None):
        """
        Shortcut for waiting for alert. If it not ends with exception, it
        returns that alert. Detault timeout is `~.default_wait_timeout`.
        """
        if not timeout:
            timeout = self.default_wait_timeout

        alert = Alert(self)

        def alert_shown(driver):
            try:
                alert.text
                return True
            except selenium_exc.NoAlertPresentException:
                return False

        self.wait(timeout).until(alert_shown)

        return alert


class Chrome(_WebdriverWrapper, Chrome):
    pass