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
