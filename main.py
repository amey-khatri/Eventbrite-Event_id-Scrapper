# import requests
# from bs4 import BeautifulSoup
# import time
# import random
#
#
# def get_venue_ids(city="Toronto"):
#     base_url = f"https://www.eventbrite.ca/d/canada--Toronto/all-events/?page=1"
#     venue_ids = set()  # Set to store unique venue_ids
#
#     # for page_num in range(1, 2):
#     url = base_url
#     response = requests.get(url)
#
#     if response.status_code != 200:
#         print(f"Failed to retrieve page")
#         # continue
#
#     soup = BeautifulSoup(response.text, 'html.parser')
#     print(soup.prettify())
#
#     # Find all event containers (adjust the selector as necessary based on the HTML structure)
#     events = soup.find_all(class_="search-results-panel-content__events")
#
#     for event in events:
#         # event_url = event['href']
#         # venue_id = extract_venue_id(event_url)
#         # if venue_id:
#         #     venue_ids.add(venue_id)
#         venue_ids.add(event)
#
#     # Throttling: Wait for a random amount of time to avoid hitting the server too quickly
#     time.sleep(random.uniform(1.5, 3))  # Sleep between 1.5 and 3 seconds
#
#     return list(venue_ids)
#
#
# def extract_venue_id(event_url):
#     # Here you would parse the URL or make another request to get the venue ID
#     # Example: The venue ID might be in the URL or metadata of the event page
#     # (This is a simplified assumption; you'd need to inspect the Eventbrite pages to find the correct pattern)
#
#     if "eventbrite.com" in event_url:
#         # Extract venue ID from the event URL or by scraping the event page
#         return event_url.split("/e/")[1].split("/")[0]  # Example: eventbrite.com/e/{venue_id}/
#     return None
#
#
# def main():
#     venue_ids = get_venue_ids(city="Toronto")
#     print(f"Found {len(venue_ids)} unique venue IDs.")
#     return venue_ids
#
#
# if __name__ == "__main__":
#     venue_ids = main()
#     print(venue_ids)  # Optionally print the list of IDs

from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import random

from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import random


def get_event_ids(city="Toronto", num_pages=2):
    base_url = f"https://www.eventbrite.ca/d/canada--{city}/all-events/?page="
    event_ids = []  # Set to store unique event IDs

    # Set up Chrome WebDriver (ensure you provide the correct path to your ChromeDriver)
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode (no UI)
    driver = webdriver.Chrome(options=options)

    try:
        for page_num in range(1, num_pages + 1):  # Loop through the set number of pages
            url = f"{base_url}{page_num}"
            driver.get(url)

            # Wait for the page to load
            time.sleep(random.uniform(3, 5))  # Adding a delay for loading content

            # Find the parent container with the list of events
            try:
                event_list = driver.find_element(By.CLASS_NAME,
                                                 "SearchResultPanelContentEventCardList-module__eventList___2wk-D")

                # Find all <li> elements inside the event list container
                event_items = event_list.find_elements(By.TAG_NAME, "li")

                for item in event_items:
                    # Find the <a> tag inside the <li> element and extract the 'data-event-id' attribute
                    event_link = item.find_element(By.TAG_NAME, "a")
                    event_id = event_link.get_attribute("data-event-id")
                    if event_id:
                        event_ids.append(event_id)

            except Exception as e:
                print(f"Error on page {page_num}: {e}")
                continue

            # Throttling: Wait for a random amount of time to avoid being rate-limited
            time.sleep(random.uniform(1.5, 3))  # Random sleep between 1.5 and 3 seconds

    finally:
        driver.quit()  # Ensure to close the driver

    return event_ids


def main():
    num_pages = 2  # Set the number of pages you want to scrape
    event_ids = get_event_ids(city="Toronto", num_pages=num_pages)
    print(f"Found {len(event_ids)} unique event IDs.")
    return event_ids


if __name__ == "__main__":
    event_ids = main()
    print(event_ids)  # Optionally print the list of IDs
