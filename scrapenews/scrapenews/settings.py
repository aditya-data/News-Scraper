from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("API_KEYS")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")
BOT_NAME = "scrapenews"
SPIDER_MODULES = ["scrapenews.spiders"]
NEWSPIDER_MODULE = "scrapenews.spiders"
ROBOTSTXT_OBEY = False
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
DUPEFILTER_DEBUG = True
DOWNLOAD_DELAY = 2  # Wait 2 seconds between requests
SCRAPEOPS_FAKE_USER_AGENT_ENDPOINT = "https://headers.scrapeops.io/v1/user-agents"
SCRAPEOPS_FAKE_USER_AGENT_ENABLED = True
SCRAPEOPS_NUM_RESULTS = 50
DOWNLOADER_MIDDLEWARES = {
   "scrapenews.middlewares.APIKeyRotationMiddleware": 300,
   "scrapenews.middlewares.ScrapeOpsFakeUserAgentMiddleware": 400,
}
# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1
REDIRECT_ENABLED = True
ITEM_PIPELINES = {
   "scrapenews.pipelines.NewsAggregationPipeline": 300,
}
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 5
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
LOG_LEVEL = "INFO"  # or "DEBUG"
HTTPERROR_ALLOWED_CODES = [429]
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 30000

API_KEYS = ""
