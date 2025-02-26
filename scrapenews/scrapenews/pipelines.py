# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import json
import os

class NewsAggregationPipeline:
    def __init__(self):
        self.aggregated_data = {}

    def recursive_convert(self, obj):
    # If the object has a 'load_item' method, convert it first
        if isinstance(obj, dict):
            # Recursively process dictionary values
            return {self.recursive_convert(k): self.recursive_convert(v) for k, v in obj.items()}
        else:
            # For other types (e.g., str, int, etc.), return as is
            return str(obj)



    def process_item(self, item, spider):
        for category, headline_data in item.items():
            for original_headline, source_data in headline_data.items():
                for source, details in source_data.items():
                    if category not in self.aggregated_data:
                        self.aggregated_data[category] = []  # Initialize category list
                    details = dict(details)
                    # print(" "*100)
                    # print(" "*100)
                    # print(" "*100)
                    # print(" "*100)
                    # for key, value in details.items():
                    #     print(f"Key: {key}, Type of key: {type(key)}, Value: {value}, Type of value: {type(value)}")
                    # print(" "*100)
                    # print(" "*100)
                    # print(" "*100)
                    # print(" "*100)

                    # details = self.recursive_convert(details)
                    # Find existing headline entry
                    headline_entry = next((entry for entry in self.aggregated_data[category] if original_headline in entry), None)

                    if not headline_entry:
                        # If headline does not exist, create a new entry
                        self.aggregated_data[category].append({original_headline: [{source: details}]})
                    else:
                        # If headline exists, append new source data
                        headline_entry[original_headline].append({source: details})

        return item  # Returning item allows other pipelines (if any) to process it

    def close_spider(self, spider):
        """Save aggregated data when the spider closes"""
        filename = "aggregated_data.json"
        
        # Load existing data if file exists
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                try:
                    existing_data = json.load(f)
                    if not isinstance(existing_data, dict):  # Ensure it's a dict
                        existing_data = {}
                except json.JSONDecodeError:
                    existing_data = {}
        else:
            existing_data = {}

        # Merge the new data with existing data
        for category, headlines in self.aggregated_data.items():
            if category in existing_data:
                # Append new headlines if they don't already exist
                for headline_entry in headlines:
                    headline_text = list(headline_entry.keys())[0]  # Get the headline key
                    existing_headline_entry = next(
                        (entry for entry in existing_data[category] if headline_text in entry),
                        None
                    )

                    if existing_headline_entry:
                        # Append new sources if they don't already exist
                        existing_headline_entry[headline_text].extend(headline_entry[headline_text])
                    else:
                        existing_data[category].append(headline_entry)
            else:
                # If category doesn't exist, add it
                existing_data[category] = headlines
        print(" "*1000)
        print(" "*1000)
        print(" "*1000)
        print(" "*1000)
        print(existing_data)
        

        # Write merged data back to the file
        with open(filename, "w", encoding="utf-8") as f:
            try:
                json.dump(existing_data, f ,indent=2, ensure_ascii=False)
            except TypeError as e:
                print("Serialization error:", e)


