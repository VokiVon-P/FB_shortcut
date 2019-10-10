import os
from os.path import join, dirname
from dotenv import load_dotenv
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from FB_parser import settings
from FB_parser.spiders.FB import FbSpider

do_env = join(dirname(__file__), '.env')
load_dotenv(do_env)

INST_LOGIN = os.getenv('INST_LOGIN')
INST_PWD = os.getenv('INST_PASSWORD')
FC_START_PROFILE = os.getenv('FC_START_PROFILE')

if __name__ == '__main__':
    crawler_settings = Settings()
    crawler_settings.setmodule(settings)
    process = CrawlerProcess(settings=crawler_settings)
    process.crawl(FbSpider, FC_START_PROFILE, INST_LOGIN, INST_PWD)
    
    process.start()
