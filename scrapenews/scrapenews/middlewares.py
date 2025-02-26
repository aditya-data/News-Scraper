# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
import logging
# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter


class ScrapenewsSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class ScrapenewsDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


# api_key_rotation_middleware.py
import threading
from scrapy import signals

class APIKeyRotationMiddleware:
    def __init__(self, api_key, search_engine_id, logger):
        self.api_keys = api_key.split(",")
        self.search_engine_id = search_engine_id
        self.current_index = 0
        self.logger = logger
        self.lock = threading.Lock()

    @classmethod
    def from_crawler(cls, crawler):
        # Expect API_KEYS and SEARCH_ENGINE_ID to be defined in settings.py
        api_key = crawler.settings.get("API_KEY")
        search_engine_id = crawler.settings.get("SEARCH_ENGINE_ID")
        logger = crawler.spider.logger if crawler.spider else logging.getLogger(__name__)
        return cls(api_key, search_engine_id, logger)

    def process_request(self, request, spider):
        # Intercept requests targeting the Google Custom Search API
        if "https://www.googleapis.com/customsearch/v1" in request.url:
            with self.lock:
                current_key = self.api_keys[self.current_index]
            # If the request URL doesn't already contain an API key, add it:
            if "key=" not in request.url:
                request.meta["api_key_used"] = current_key
                separator = "&" if "?" in request.url else "?"
                new_url = f"{request.url}{separator}key={current_key}&cx={self.search_engine_id}"
                return request.replace(url=new_url)
        return None  # Continue processing as usual

    def process_response(self, request, response, spider):
        # If this is a Google API request and a 429 (Too Many Requests) is received,
        # rotate the API key and reissue the request.
        if "https://www.googleapis.com/customsearch/v1" in request.url and response.status == 429:
            self.logger.warning("Received 429 response. Rotating API key.")
            with self.lock:
                self.current_index += 1
                if self.current_index >= len(self.api_keys):
                    self.logger.error("Exhausted all API keys!")
                    # You can either return the response to let the spider handle it,
                    # or raise an exception to stop further processing.
                    return response
                new_key = self.api_keys[self.current_index]

            # Replace the old key with the new one in the URL.
            old_key = request.meta.get("api_key_used")
            if old_key:
                new_url = request.url.replace(f"key={old_key}", f"key={new_key}")
            else:
                separator = "&" if "?" in request.url else "?"
                new_url = f"{request.url}{separator}key={new_key}&cx={self.search_engine_id}"

            self.logger.info(f"Retrying request with new API key: {new_key}")
            # Update meta to record the new API key used.
            request.meta["api_key_used"] = new_key
            # Reissue the request with the updated URL.
            return request.replace(url=new_url)

        return response  # Return the response if it's not a 429 or not an API request



import requests
from random import randint
from urllib.parse import urlencode

class ScrapeOpsFakeUserAgentMiddleware:

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def __init__(self, settings):
        self.scrapeops_api_key = settings.get("SCRAPEOPS_API_KEY")
        self.scrapeops_endpoint = settings.get("SCRAPEOPS_FAKE_USER_AGENT_ENDPOINT", "https://headers.scrapeops.io/v1/user-agents")
        self.scrapeops_fake_user_agents_active = settings.get("SCRAPEOPS_FAKE_USER_AGENT_ENABLED", False)
        self.scrapeops_num_results = settings.get("SCRAPEOPS_NUM_RESULTS")
        self.user_agents_list = []
        self._get_user_agents_list()
        self._scrapeops_fake_user_agents_enabled()

    def _get_user_agents_list(self):
        payload = {'api_key': self.scrapeops_api_key}
        if self.scrapeops_num_results is not None:
            payload['num_results'] = self.scrapeops_num_results
        response = requests.get(self.scrapeops_endpoint, params=urlencode(payload))
        if response.status_code == 200:  # Check for successful response
            json_response = response.json()
            self.user_agents_list = json_response.get('result', [])
        else:
            self.user_agents_list = []

    def _get_random_user_agent(self):
        if not self.user_agents_list:
            return "Default-User-Agent"  # Fallback user agent if list is empty
        random_index = randint(0, len(self.user_agents_list) - 1)
        return self.user_agents_list[random_index]

    def _scrapeops_fake_user_agents_enabled(self):
        if not self.scrapeops_api_key or not self.scrapeops_fake_user_agents_active:
            self.scrapeops_fake_user_agents_active = False
        else:
            self.scrapeops_fake_user_agents_active = True

    def process_request(self, request, spider):
        if self.scrapeops_fake_user_agents_active:
            random_user_agent = self._get_random_user_agent()
            request.headers['User-Agent'] = random_user_agent
            print("************ NEW HEADER ATTACHED *******")
            print(request.headers['User-Agent'])
