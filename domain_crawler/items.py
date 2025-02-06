# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class DomainCrawlerItem(scrapy.Item):
    # define the fields for your item here like:
    url = scrapy.Field()
    html = scrapy.Field()
    openai_result = scrapy.Field()  
    company_name = scrapy.Field()
    company_id = scrapy.Field()
    scrape_date = scrapy.Field()