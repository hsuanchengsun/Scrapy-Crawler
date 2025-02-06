import pandas as pd
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from domain_crawler.spiders.domain_spider import DomainSpiderSpider


def run_all_domains(csv_path):
    df = pd.read_csv(csv_path, dtype={'Company ID': object})  # Expect columns: Company ID, Company name, Company Domain Name

    process = CrawlerProcess(get_project_settings())

    for _, row in df.iterrows():
        company_id = str(row["Company ID"]).strip()
        company_name = str(row["Company name"]).strip()
        company_domain = str(row["Company Domain Name"]).strip()

        # Crawl once per domain
        process.crawl(
            DomainSpiderSpider,
            domain=company_domain,
            company_id=company_id,
            company_name=company_name
        )

    # Run all crawls sequentially
    process.start()

if __name__ == "__main__":
    run_all_domains("company_info.csv")