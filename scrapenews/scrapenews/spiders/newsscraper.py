import scrapy
from scrapy_playwright.page import PageMethod
from scrapenews.items import ScrapenewsItem
from scrapy.loader import ItemLoader
from dotenv import load_dotenv
import os
from scrapy.selector import Selector

load_dotenv()

ALLOWED_CATS = ["India", "World"]
NEWS_SOURCES = [
    "timesofindia.indiatimes.com",
    "hindustantimes.com",
    "thehindu.com",
    "indianexpress.com",
]

class NewsscraperSpider(scrapy.Spider):
    name = "newsscraper"
    allowed_domains = ["news.google.com"]
    start_urls = ["https://news.google.com"]

    def start_requests(self):
        yield scrapy.Request(
            self.start_urls[0],
            meta=dict(
                playwright=True,
                playwright_page_methods=[
                    PageMethod("wait_for_load_state", "domcontentloaded")
                ],
            ),
            callback=self.parse_categories,
        )

    def parse_categories(self, response):
        categories = response.xpath("//div[contains(@data-url, '/topics')]/a")
        for category in categories:
            category_name = category.xpath("./text()").get().strip()
            self.logger.info(f"Extracted category: '{category_name}'")
            category_url = category.xpath("./@href").get()
            if category_name in ALLOWED_CATS:
                yield scrapy.Request(
                    response.urljoin(category_url),
                    meta=dict(
                        category=category_name,
                        playwright=True,
                        playwright_page_methods=[
                            PageMethod("wait_for_load_state", "domcontentloaded"),
                            PageMethod("evaluate", "window.scrollTo(0, document.body.scrollHeight)"),
                            PageMethod("wait_for_timeout", 3000),
                        ],
                    ),
                    callback=self.parse_box,
                )

    def parse_box(self, response):
        """Extracts headlines and searches for each across all sources."""
        boxes = response.xpath("//c-wiz[div/article]")
        for box in boxes:
            headline = box.xpath("./div/article//a/text()").get()
            self.logger.info(f"Found headline: {headline}")
            category = response.meta.get("category")
            if not headline:
                continue  # Skip if no headline
            print(headline)
            for source in NEWS_SOURCES:
                search_query = f"{headline} site:{source}"
                # Note: We now only include the query. The middleware will add key and cx.
                api_url = f"https://www.googleapis.com/customsearch/v1?q={search_query}"
                yield scrapy.Request(
                    url=api_url,
                    callback=self.parse_api_response,
                    meta={
                        "headline": headline,
                        "category": category,
                        "source": source,
                        "dont_retry": True
                    },
                    dont_filter=True,
                )

    def parse_api_response(self, response):
        """Extracts title and URL from Google API response."""
        if response.status != 200:
            self.logger.error(f"Non-200 response: {response.status} for headline: {response.meta['headline']}")
            return

        items = response.json()
        total_results = items.get("searchInformation", {}).get("totalResults", "0")
        if int(total_results):
            first_item = items["items"][0]  # Expect first item to be best SEO match
            target_url = first_item["link"]
            self.logger.info(f"Dispatching request to: {target_url}")
            yield scrapy.Request(
                url=target_url,
                meta=dict(
                    source=response.meta["source"],
                    category=response.meta["category"],
                    headline=response.meta["headline"],
                    url=target_url,
                ),
                callback=self.parse_article,
                errback=self.handle_error,
                dont_filter=True,
            )
        else:
            self.logger.info(f"No search results for: {response.meta['headline']} on {response.meta['source']}")

    def parse_article(self, response):
        source = response.meta["source"]
        category = response.meta["category"]
        original_headline = response.meta["headline"]

        item = ItemLoader(item=ScrapenewsItem(), selector=Selector(text=response.text))
        if source == "hindustantimes.com":
            item.add_value("url", response.meta["url"])
            item.add_xpath("headline", "//h1/text()")
            item.add_xpath("article_text", "//div[@class='detail ']//text()")
            item.add_xpath("description", "//h2[@class='sortDec']/text()")
        elif source == "timesofindia.indiatimes.com":
            item.add_value("url", response.meta["url"])
            item.add_xpath("headline", "//h1//text()")
            item.add_xpath("article_text", "//div[@data-articlebody]//text()")
            item.add_xpath("description", "//div[@class='art_synopsis']//text()")
        elif source == "thehindu.com":
            item.add_value("url", response.meta["url"])
            item.add_xpath("headline", "//h1[@class='title']//text()")
            item.add_xpath("article_text", "//div[@itemprop='articleBody']//text()")
            item.add_xpath("description", "//h2[@class='sub-title']//text()")
        elif source == "indianexpress.com":
            item.add_value("url", response.meta["url"])
            item.add_xpath("headline", "//h1[@itemprop='headline']//text()")
            item.add_xpath("article_text", "//div[@class='blog-content' or @class='story_details']//text()")
            item.add_xpath("description", "//h2[@itemprop='description']//text()")

        if item.get_output_value("headline") and item.get_output_value("article_text"):
            yield {
                category: {
                    original_headline: {
                        source: item.load_item()
                    }
                }
            }
        else:
            self.logger.info(f"The URL was not a news article: {response.meta['url']}")

    def handle_error(self, failure):
        self.logger.error(f"Request failed: {failure}")
        if failure.value.response:
            self.logger.error(f"FAILED URL: {failure.request.url} - STATUS CODE: {failure.value.response.status}")
