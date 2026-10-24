import dlt
import requests
import time
from datetime import datetime, timedelta, timezone

WINDOW_DAYS = 7       # size of each date window; shrink if you see WARNING lines
HORIZON_DAYS = 365    # how far ahead to look for events
PAGE_SIZE = 200
MAX_PAGES = 5         # API deep-paging limit: page * size must stay under 1000


def fetch_page(url, params, retries=4):
    """GET with backoff on rate limits (429), server errors (5xx) and network timeouts.
    Returns the response, or None if every attempt failed."""
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, timeout=60)
        except requests.exceptions.RequestException as e:
            # Print only the error type: the full message can include the URL, and the URL contains the API key
            print(f"  Network error ({type(e).__name__}), retry {attempt + 1}/{retries}...")
            time.sleep(2 ** (attempt + 1))
            continue
        
        time.sleep(0.3)
        if response.status_code == 429 or response.status_code >= 500:
            time.sleep(2 ** (attempt + 1))
            continue
        return response
    return None


@dlt.resource(write_disposition="replace")
def ticketmaster_events(api_key=dlt.secrets.value):
    url = "https://app.ticketmaster.com/discovery/v2/events.json"
    
    cities = ["New York", "Los Angeles", "Chicago"]
    segments = ["Music", "Sports", "Arts & Theatre"]

    # Build non-overlapping date windows covering today -> today + HORIZON_DAYS
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    horizon_end = today + timedelta(days=HORIZON_DAYS)
    windows = []
    start = today
    while start < horizon_end:
        end = start + timedelta(days=WINDOW_DAYS) - timedelta(seconds=1)
        windows.append((start.strftime(fmt), end.strftime(fmt)))
        start += timedelta(days=WINDOW_DAYS)
    
    for city in cities:
        for segment in segments:
            print(f"--- Fetching {segment} events for {city} ---")
            seen = set()  # guards against the same event appearing in two windows
            incomplete_windows = 0
            
            for window_start, window_end in windows:
                page_number = 0
                
                while page_number < MAX_PAGES:
                    params = {
                        "apikey": api_key,
                        "city": city,
                        "segmentName": segment,
                        "startDateTime": window_start,
                        "endDateTime": window_end,
                        "size": PAGE_SIZE,
                        "page": page_number,
                    }
                    
                    response = fetch_page(url, params)
                    
                    if response is None or response.status_code != 200:
                        status = "no response" if response is None else response.status_code
                        print(
                            f"API problem ({status}) for {city} - {segment}, "
                            f"window {window_start}, page {page_number}. Skipping rest of this window."
                        )
                        incomplete_windows += 1
                        break
                    
                    data = response.json()
                    page_info = data.get("page", {})
                    
                    # Make truncation visible instead of silent
                    total = page_info.get("totalElements", 0)
                    if page_number == 0 and total > PAGE_SIZE * MAX_PAGES:
                        print(
                            f"WARNING: {city} - {segment}, window {window_start} has {total} events; "
                            f"only the first {PAGE_SIZE * MAX_PAGES} can be fetched. Reduce WINDOW_DAYS."
                        )
                    
                    events = data.get("_embedded", {}).get("events", [])
                    for event in events:
                        if event["id"] in seen:
                            continue
                        seen.add(event["id"])
                        event["target_city"] = city
                        event["target_segment"] = segment
                        yield event
                    
                    page_number += 1
                    # Stop as soon as the API says there are no more pages for this window
                    if page_number >= page_info.get("totalPages", 0):
                        break
            
            note = f" ({incomplete_windows} window(s) incomplete - re-run)" if incomplete_windows else ""
            print(f"Done: {len(seen)} unique {segment} events for {city}.{note}")


if __name__ == "__main__":
    pipeline = dlt.pipeline(
        pipeline_name="ticketmaster",
        destination="motherduck",
        dataset_name="raw",
    )
    
    load_info = pipeline.run(ticketmaster_events(), refresh="drop_resources")
    print(load_info)