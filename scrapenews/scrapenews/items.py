import scrapy
import scrapy.item
from itemloaders.processors import TakeFirst , MapCompose, Join, Compose
import re
from w3lib.html import remove_tags

def clean_article(text):
    # Ensure text is handled in UTF-8
    text = text.encode('utf8', errors='ignore').decode('utf8')
    
    # Remove any HTML tags
    text = remove_tags(text)
    
    # Normalize whitespace (collapsing multiple spaces/newlines into a single space)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Define patterns for different markers
    published_pattern = r"Published\s*-\s*\w+\s+\d{1,2},\s+\d{4}\s+\d{1,2}:\d{2}\s*(?:am|pm)?\s*IST?\s*Read Comments"
    mps_pattern = r"More\s+Premium\s+Stories"
    sudbn_pattern = r"Stay\s+updated\s+with\s+breaking\s+news\s*,"
    
    # Find the starting index of each pattern (if present)
    indices = []
    
    pub_match = re.search(published_pattern, text, re.IGNORECASE)
    if pub_match:
        indices.append(pub_match.start())
    
    mps_match = re.search(mps_pattern, text, re.IGNORECASE)
    if mps_match:
        indices.append(mps_match.start())
    
    sudbn_match = re.search(sudbn_pattern, text, re.IGNORECASE)
    if sudbn_match:
        indices.append(sudbn_match.start())
    
    # If any marker is found, trim the text up to the earliest occurrence
    if indices:
        cut_index = min(indices)
        text = text[:cut_index].strip()
    
    return text




class ScrapenewsItem(scrapy.Item):
    url = scrapy.Field()
    headline = scrapy.Field(
        input_processor=MapCompose(remove_tags, str.strip),
        # output_processor = TakeFirst
    )
    article_text = scrapy.Field(
        input_processor=MapCompose(str.strip),
        output_processor=Compose(Join(" "), clean_article)
    )
    description = scrapy.Field(
        input_processor=MapCompose(remove_tags, str.strip),
        # output_processor = TakeFirst
    )
    # datetime = scrapy.Field(
    #     input_processor=MapCompose(str.strip),
    #     # output_processor = TakeFirst
    # )
