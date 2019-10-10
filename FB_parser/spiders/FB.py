# -*- coding: utf-8 -*-
import scrapy
import time
from scrapy.http import HtmlResponse, Request
from urllib.parse import urlencode, urljoin

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

#from jobparser.items import FacebookItem


class FbSpider(scrapy.Spider):
    name = 'FB_shortcut'
    allowed_domains = ['facebook.com']
    auth_url = 'https://www.facebook.com'
    # <meta property="al:ios:url" content="fb://profile/100002724472881">
    # Михаил Шеремет    https://www.facebook.com/profile.php?id=100002724472881
    # Doug Smith        https://www.facebook.com/profile.php?id=100004082239392
    start_urls = ['https://www.facebook.com/profile.php?id=100002724472881', 'https://www.facebook.com/profile.php?id=100004082239392']

    def __init__(self, user_link, login, pswrd, *args, **kwargs):
        #self.webdriver = webdriver.Chrome()
        
        self.login = login
        self.pswrd = pswrd
        self.first_profile = user_link
        #self.is_init = False
        #self.fc_login()
        #self.is_init = True
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
        # при инициализации авторизуемся и передаем куки, после подгружаем себя же 
        tmp_driver = webdriver.Chrome()
        tmp_driver.get(self.auth_url)
        self.fc_login(tmp_driver)
        yield Request(response.url, cookies=tmp_driver.get_cookies(),callback=self.parse_page, cb_kwargs={'w_driver': tmp_driver})

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

    def parse_page(self, response: HtmlResponse, w_driver, level):

        tmp_driver = w_driver      
        # переходим на персональную страницу

        _url = response.url
        delim = 'next='
        next_url = _url.split(delim)[1] if delim in _url else _url
        url_friends =  (next_url + '&sk=friends') if '?' in next_url else (next_url + '?sk=friends')
        
 
        #url_friends = urljoin(response.url, 'sk=friends')
        tmp_driver.get(url_friends)

        """
        Секция обработки персональных данных
        """


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
            body.send_keys(Keys.END)
            body.send_keys(Keys.PAGE_DOWN)
            time.sleep(1)
            body.send_keys(Keys.END)
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
        

        """
        # сохраняем в базу
        yield FacebookItem(
                            name = item_full_name, 
                            birthdate = item_birthdate,
                            photos = item_photo_list,
                            friends_count = friends_len,
                            friends = item_friends_href_list
                            )
        """
        # и далее запускаем паучка рекурсивно по списку!
        for url in item_friends_href_list:
            yield response.follow(url, callback=self.parse_page, cb_kwargs={'w_driver': tmp_driver})
        
        