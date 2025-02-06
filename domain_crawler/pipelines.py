# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class DomainCrawlerPipeline:
    def process_item(self, item, spider):
        return item

import json
from bs4 import BeautifulSoup
from openai import OpenAI
from typing_extensions import override
from openai import AssistantEventHandler
from collections import defaultdict

# Headers to mimic a browser visit
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
}

# First, we create a EventHandler class to define
# how we want to handle the events in the response stream.
class EventHandler(AssistantEventHandler):    
  @override
  def on_text_created(self, text) -> None:
    print(f"\nassistant > ", end="", flush=True)
      
  @override
  def on_text_delta(self, delta, snapshot):
    print(delta.value, end="", flush=True)
      
  def on_tool_call_created(self, tool_call):
    print(f"\nassistant > {tool_call.type}\n", flush=True)
  
  def on_tool_call_delta(self, delta, snapshot):
    if delta.type == 'code_interpreter':
      if delta.code_interpreter.input:
        print(delta.code_interpreter.input, end="", flush=True)
      if delta.code_interpreter.outputs:
        print(f"\n\noutput >", flush=True)
        for output in delta.code_interpreter.outputs:
          if output.type == "logs":
            print(f"\n{output.logs}", flush=True)

class OpenAIPipeline:
    def __init__(self):
        # Initialize OpenAI client here
        self.client = OpenAI(api_key="")
        self.items_collected = defaultdict(list)

    def open_spider(self, spider):
        """Called when the spider opens."""
        pass
        
    def process_item(self, item, spider):
        """
        1) Perform your OpenAI logic on item["html"].
        2) Append the result to self.items_collected.
        """
        
        soup = BeautifulSoup(item["html"], 'html.parser')
        prod = str(soup.get_text(separator=' ', strip=True))
        thread = self.client.beta.threads.create()
        message = self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"Please follow the instruction to check if the following content is product information or not and summarize the information into a JSON format with attributes (product_name, product_detail, and product_application) if it is a product information page: {prod}"
        )
        # Then, we use the `stream` SDK helper with the `EventHandler` class to create the Run and stream the response.

        with self.client.beta.threads.runs.stream(
                    thread_id=thread.id,
                    assistant_id="",
                    event_handler=EventHandler(),
            ) as stream:
                stream.until_done()
        # Retrieve the final message
        messages = self.client.beta.threads.messages.list(
            thread_id=thread.id
        )
        final_message = messages.data[0].content[0].text.value 
        
        # Store the result in the item
        item['openai_result'] = final_message
        runs = self.client.beta.threads.runs.list(
            thread_id=thread.id
        )
        final_tokens={"completion_tokens": runs.data[0].usage.completion_tokens, 
        "prompt_tokens": runs.data[0].usage.prompt_tokens, 
        "total_tokens": runs.data[0].usage.total_tokens}

        spider_key = item["company_id"]  
        
        # Optionally store in self.results if you want to save everything on close
        self.items_collected[spider_key].append({
            "url": item["url"],
            "company_name": item["company_name"],
            "openai_result": json.loads(final_message),
            "final_tokens": final_tokens,
            "company_id": item["company_id"],
            "scrape_date": item["scrape_date"],
        })

        return item

    def close_spider(self, spider):
        """
        Called after the spider finishes crawling that domain.
        Write all items to <company_id>.json.
        """
        
        company_id = getattr(spider, 'company_id', None)
        results = self.items_collected.get(company_id, [])
        if not results:
            return
        
        file_name = f"{company_id}.json"
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        spider.logger.info(f"Saved {len(results)} items to {file_name}")
        del self.items_collected[company_id]
        