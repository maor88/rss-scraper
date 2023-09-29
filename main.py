"""
RSS scraper app - sendCloud

starting point for running the fast api server
including:
7 api: login, add-feed, follow-feed, get-feeds, get-feed-items, mark-item-read
authentication - each request (except login) depends on verify_token
scheduler running rss scrapper for all feeds

for api docs using Swagger: http://localhost:8080/docs#/
Author: Maor Avitan
"""

import time

import schedule
from fastapi import FastAPI
import threading
import uvicorn

from scrapper import scrape_feeds

from api import users, feeds, items

app = FastAPI()


app.include_router(users.router, prefix="/login", tags=["login"])
app.include_router(feeds.router, prefix="/feeds", tags=["feeds"])
app.include_router(items.router, prefix="/items", tags=["items"])


# Running rss scrapping every 1 hour in the app background
schedule.every(1).hour.do(scrape_feeds)


# Function to run the scheduled task
def run_scheduled_task():
    while True:
        schedule.run_pending()
        time.sleep(1)  # Sleep for 1 second to avoid excessive CPU usage


# Create a separate thread to run the scheduler
scheduler_thread = threading.Thread(target=run_scheduled_task, daemon=True)
scheduler_thread.start()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
