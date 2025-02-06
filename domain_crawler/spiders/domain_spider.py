import scrapy
from urllib.parse import urlparse
from domain_crawler.items import DomainCrawlerItem
from scrapy.exceptions import CloseSpider
from datetime import datetime


class DomainSpiderSpider(scrapy.Spider):
    name = "domain_spider"
    def __init__(self, domain=None, company_id=None, company_name=None, *args, **kwargs):
        """
        domain, company_id, and company_name can be passed
        via arguments when we call `process.crawl(...)`
        """
        super().__init__(*args, **kwargs)
        self.domain = domain
        self.company_id = company_id
        self.company_name = company_name
        
        # Page counter
        self.crawled_pages = 0
        self.page_limit = 1000  # limit of 1000 pages
        
        # If domain is provided, set allowed_domains and start_urls
        if self.domain:
            self.allowed_domains = [f"www.{self.domain}", self.domain]
            self.start_urls = [f"https://{self.domain}/"]
        
        self.close_spider_raised = False
    
    def parse(self, response):
        """Parse the main page and follow internal links, up to 1,000 pages per domain."""
        if self.close_spider_raised:
            return
        
        # Check if we've already reached 1,000 pages for this domain
        if self.crawled_pages >= self.page_limit:
            self.logger.info(
                f"Reached {self.page_limit} pages for domain: {self.domain}, stopping further crawling."
            )
            self.close_spider_raised = True
            raise CloseSpider(reason="page_limit")

        # Increment page counter
        self.crawled_pages += 1
        
        item = DomainCrawlerItem()
        item['url'] = response.url
        item['html'] = response.text
        item["company_id"] = self.company_id
        item["company_name"] = self.company_name
        item["scrape_date"] = datetime.today().strftime('%m-%d-%Y')
        yield item

        if self.crawled_pages < self.page_limit:
            # Follow only links internal to this company's domain
            links = response.css("a::attr(href)").getall()
            for link in links:
                absolute_url = response.urljoin(link)
                parsed = urlparse(absolute_url)

                # Only follow links within the same domain
                if parsed.netloc == self.domain or parsed.netloc == f"www.{self.domain}":
                    yield scrapy.Request(
                        url=absolute_url,
                        callback=self.parse,
                    )
            
            
    # For single website only can use this
    # allowed_domains = [""]
    # start_urls = [""]            
    # def parse(self, response):
    #     # Create an item to pass to pipeline
    #     item = DomainCrawlerItem()
    #     item['url'] = response.url
    #     item['html'] = response.text
    #     yield item

    #     # 2) Now find all links and follow them
    #     links = response.css("a::attr(href)").getall()
    #     for link in links:
    #         absolute_url = response.urljoin(link)
    #         if self.is_same_domain(absolute_url):
    #             yield scrapy.Request(absolute_url, callback=self.parse)
                
    #             # if need to use render_js, switich to this
    #             # yield scrapy.Request(
    #             #     response.url,
    #             #     callback=self.parse,
    #             #     meta={"scrapeops": {"render_js": True}},
    #             # )
        
    # def is_same_domain(self, url):
    #     """Check if 'url' belongs to one of our allowed domains."""
    #     parsed = urlparse(url)
    #     return parsed.netloc in self.allowed_domains
    
