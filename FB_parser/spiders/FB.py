# -*- coding: utf-8 -*-
import scrapy
import time
from scrapy.http import HtmlResponse, Request
from urllib.parse import urlencode, urljoin

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from FB_parser.items import FbParserItem

from collections import deque 

class FbSpider(scrapy.Spider):
    name = 'FB_shortcut'
    allowed_domains = ['facebook.com']
    auth_url = 'https://www.facebook.com'
    
    BINGO = False
    # Михаил Шеремет    https://www.facebook.com/profile.php?id=100002724472881
    # Doug Smith        https://www.facebook.com/profile.php?id=100004082239392
    start_urls = ['https://www.facebook.com/profile.php?id=100002724472881', 'https://www.facebook.com/profile.php?id=100004082239392']

    def __init__(self, login, pswrd, *args, **kwargs):
        self.login = login
        self.pswrd = pswrd
        self.level_manager = deque()
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

    def make_friends_url(self, baseurl):
        # delim = 'next='
        # next_url = baseurl.split(delim)[1] if delim in baseurl else baseurl
        if baseurl.count('sk=friends'):
            return baseurl

        next_url = baseurl
        add = 'sk=friends&source_ref=pb_friends_tl'
        url_friends =  (next_url + '&' + add ) if '?' in next_url else (next_url + '?' + add)
        return url_friends

    def get_clear_url(self, base_url):
        tmp_url = base_url.split('&')[0]   
        
        if not tmp_url.count('profile.php'):
            tmp_url = tmp_url.split('?')[0]   
            
        print(tmp_url)
        return tmp_url

    def parse(self, response: HtmlResponse):
        # при инициализации авторизуемся и передаем куки, после передаем управление на разбор страницы 
        tmp_driver = webdriver.Chrome()
        #tmp_driver.get(self.auth_url)
        tmp_driver.get(response.url)
        self.fc_login(tmp_driver)
        yield Request(response.url, cookies=tmp_driver.get_cookies(), callback=self.parse_page, cb_kwargs={'w_driver': tmp_driver, 'level' : 0})

  
    def parse_page(self, response: HtmlResponse, w_driver, level):

        tmp_driver = w_driver      
        # переходим на персональную страницу c друзьями
        url_friends =  self.make_friends_url(self.get_clear_url(response.url))
        tmp_driver.get(url_friends)
        time.sleep(1)

        """
        Секция обработки персональных данных
        """
        item_id = tmp_driver.find_element_by_xpath('//meta[@property="al:ios:url"]').get_attribute('content')[5:].split('/')[1]
        
        # TODO - реализовать проверку по item_id в базе
        # Если есть в базе и level > 0
        # То остановить обработку
        # И сложить два левела - из базы и из этой функции 
        # Это и будет результат 


        """
        Секция обработки список друзей
        """
        # прокручиваем список
        body = tmp_driver.find_element_by_tag_name('body')
        _friend_list_item = '//div[@data-testid="friend_list_item"]/a'
        friends_len = len(tmp_driver.find_elements_by_xpath(
            _friend_list_item ))
        while True:
            body.send_keys(Keys.PAGE_DOWN)
            body.send_keys(Keys.PAGE_DOWN)
            body.send_keys(Keys.PAGE_DOWN)
            time.sleep(1)
            tmp_len = len(tmp_driver.find_elements_by_xpath(
                _friend_list_item ))
            if friends_len == tmp_len:
                break
            friends_len = len(tmp_driver.find_elements_by_xpath(
                _friend_list_item ))

        # если открытых друзей нет - прекращаем обработку
        if friends_len != 0:
            # получаем и обрабатываем список друзей
            friends_list = tmp_driver.find_elements_by_xpath(_friend_list_item )
            friends_list = list(map(lambda x: x.get_attribute('href'), friends_list))
            item_friends_href_list = list(map(self.get_clear_url, friends_list))

            # подготавливаем список кортежей и добавляем его в очередь обработки            
            level_urls = [ (level+1, href) for href in friends_list]
            self.level_manager.extend(level_urls)
            print(len(self.level_manager))
            
            # сохраняем в базу
            yield FbParserItem(
                                id_person = item_id, 
                                level = level,
                                friends_count = friends_len,
                                friends = item_friends_href_list
                                )

        # продолжаем дальше ходить по нашему списку
        # вынимаем первый элемент из очереди и запускаем страницу в обработку
        level = -1
        page_url = None
        if len(self.level_manager):
            try:
                level, page_url = self.level_manager.popleft()
            except:
                pass
        #если все ок - идем дальше
        if page_url is not None and level >= 0 :
            page_url = page_url
            #yield response.follow(page_url, callback=self.parse_page, cb_kwargs={'w_driver': w_driver, 'level': level})
        
        
        
        