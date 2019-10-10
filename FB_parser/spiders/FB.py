# -*- coding: utf-8 -*-
import scrapy
import time
from scrapy.http import HtmlResponse, Request
from urllib.parse import urlencode, urljoin

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from FB_parser.items import FbParserItem


class FbSpider(scrapy.Spider):
    name = 'FB_shortcut'
    allowed_domains = ['facebook.com']
    auth_url = 'https://www.facebook.com'
    level_manager = {}
    # Михаил Шеремет    https://www.facebook.com/profile.php?id=100002724472881
    # Doug Smith        https://www.facebook.com/profile.php?id=100004082239392
    start_urls = ['https://www.facebook.com/profile.php?id=100002724472881', 'https://www.facebook.com/profile.php?id=100004082239392']

    def __init__(self, login, pswrd, *args, **kwargs):
        self.login = login
        self.pswrd = pswrd
        super().__init__(*args, *kwargs)
        
  
    def fc_login(self, local_driver):
        """ авторизуемся  """
        try:
            mail = local_driver.find_element_by_xpath('//input[@class="inputtext login_form_input_box"][@type ="email"][@name ="email"]')
            pswd = local_driver.find_element_by_xpath('//input[@class="inputtext login_form_input_box"][@type ="password"][@name ="pass"]')
            login_btn = local_driver.find_element_by_xpath('//label[@class="login_form_login_button uiButton uiButtonConfirm"]/input[@type ="submit"][@value ="Log In"]')
        except:
            mail = local_driver.find_element_by_xpath('//input[@type ="text"][@name ="email"]')
            pswd = local_driver.find_element_by_xpath('//input[@type ="password"][@name ="pass"]')
            login_btn = local_driver.find_element_by_xpath('//button[@name ="login"][@type ="submit"]')

        mail.send_keys(self.login)
        pswd.send_keys(self.pswrd)
        login_btn.click()
        #self.webdriver.get(self.first_profile)


    def parse(self, response: HtmlResponse):
        # при инициализации авторизуемся и передаем куки, после передаем управление на разбор страницы 
        tmp_driver = webdriver.Chrome()
        tmp_driver.get(self.auth_url)
        self.fc_login(tmp_driver)
        yield Request(response.url, cookies=tmp_driver.get_cookies(), callback=self.parse_manager, cb_kwargs={'w_driver': tmp_driver})
        #yield Request(response.url, cookies=tmp_driver.get_cookies(), callback=self.parse_page, cb_kwargs={'w_driver': tmp_driver, 'level':0})

        """    
        if '/login/' in response.url:
            tmp_driver.get(self.auth_url)
            self.fc_login(tmp_driver)
            yield Request(response.url, cookies=tmp_driver.get_cookies(),callback=self.parse_page, cb_kwargs={'w_driver': tmp_driver})
            #tmp_driver.close()
        else:
            yield response.follow(tmp_driver.current_url, callback=self.parse_page, cb_kwargs={'w_driver': tmp_driver})
        
       
        yield Request(response.url, cookies=self.webdriver.get_cookies(),callback=self.parse_page)

        if not self.is_init:
            self.fc_login()
            self.is_init = True
            yield Request(self.webdriver.current_url, cookies=self.webdriver.get_cookies(),callback=self.parse)
        else:
            yield response.follow(self.first_profile, callback=self.parse_page)
        """

    def parse_manager(self, response: HtmlResponse, w_driver):
        #yield Request(response.url, cookies=w_driver.get_cookies(), callback=self.parse_page, cb_kwargs={'w_driver': w_driver, 'level': 0})
        yield response.follow(self.make_friends_url(response.url), callback=self.parse_page, cb_kwargs={'w_driver': w_driver, 'level':0})
        #yield self.parse_list(w_driver, 0)
        #yield self.parse_page( response, w_driver, 0)
        pass


    def parse_list(self, w_driver, level):
        print('hello')
        pass

    def make_friends_url(self, baseurl):
        delim = 'next='
        next_url = baseurl.split(delim)[1] if delim in baseurl else baseurl
        url_friends =  (next_url + '&sk=friends') if '?' in next_url else (next_url + '?sk=friends')
        return url_friends


    def parse_page(self, response: HtmlResponse, w_driver, level):

        tmp_driver = w_driver      
        # переходим на персональную страницу
        url_friends =  self.make_friends_url(response.url)
        tmp_driver.get(url_friends)

        """
        Секция обработки персональных данных
        """
        item_id = tmp_driver.find_element_by_xpath('//meta[@property="al:ios:url"]').get_attribute('content')[5:].split('/')[1]

        """
        Секция обработки список друзей
        """
        # ссылка на списк друзей
        # friends_link  = tmp_driver.find_element_by_xpath('//a[@data-tab-key="friends"]').get_attribute('href')
        # переходим на список друзей
        # tmp_driver.get(friends_link)

        # прокручиваем список
        body = tmp_driver.find_element_by_tag_name('body')
        _friend_list_item = '//div[@data-testid="friend_list_item"]/a'
        friends_len = len(tmp_driver.find_elements_by_xpath(
            _friend_list_item ))
        while True:
            body.send_keys(Keys.PAGE_DOWN)
            time.sleep(1)
            body.send_keys(Keys.PAGE_DOWN)
            time.sleep(1)
            body.send_keys(Keys.PAGE_DOWN)
            time.sleep(1)
            tmp_len = len(tmp_driver.find_elements_by_xpath(
                _friend_list_item ))
            if friends_len == tmp_len:
                break
            friends_len = len(tmp_driver.find_elements_by_xpath(
                _friend_list_item ))
        # если открытых друзей нет - прекращаем обработку
        if friends_len == 0:
            return

        # получаем и обрабатываем список друзей
        friends_list = tmp_driver.find_elements_by_xpath(_friend_list_item )
        item_friends_href_list = list(map(lambda x: x.get_attribute('href'), friends_list))
        #print(f'Друзей у {full_name}= ', len(href_list))
        

        
        # сохраняем в базу
        yield FbParserItem(
                            id_person = item_id, 
                            level = level,
                            friends_count = friends_len,
                            friends = item_friends_href_list
                            )
        
        """
        # и далее запускаем паучка рекурсивно по списку!
        for url in item_friends_href_list:
            yield response.follow(url, callback=self.parse_page, cb_kwargs={'w_driver': tmp_driver})
        """
        
        
        