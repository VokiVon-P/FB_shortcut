# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class FbParserItem(scrapy.Item):
    _id = scrapy.Field()
    id_person = scrapy.Field()
    level = scrapy.Field()
    friends_count = scrapy.Field()
    friends = scrapy.Field()
