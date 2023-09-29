"""
RSS scraper app - sendCloud

Tasks module running RSS Scraper task using dramatiq for queueing tasks
for scrapping using feedparser library in order to extract structured data from web feeds and insert into Items table

Author: Maor Avitan
"""
from datetime import datetime
from time import mktime

import dramatiq
import feedparser
from dramatiq.brokers.redis import RedisBroker

# Initialize the Redis broker for Dramatiq
broker = RedisBroker(url="redis://localhost:6379/0")
dramatiq.set_broker(broker)


from db import Feed, Item, get_session

MAX_FAILED_ALLOWED = 3


@dramatiq.actor
def scrape_feeds():
    session = get_session()
    feeds = session.query(Feed).filter_by(sync=True).all()

    try:
        for feed in feeds:
            added = scrape_feed(feed, session)
            print(f"{added}: Items added in total")
    except Exception as e:
        print(f"Error scraping feeds: {str(e)}")


def scrape_feed(feed, db, prevent_duplication: bool = True):
    feed_url = feed.url
    try:
        parsed_feed = feedparser.parse(feed_url)
        if parsed_feed.bozo:
            feed.status = "Failed to get feed items"
            feed.failed_cnt += 1
            if feed.failed_cnt > MAX_FAILED_ALLOWED:
                feed.sync = False
                print(f"Feed {feed_url} reached the max failures allowed, it will be no longer synced")
            db.commit()
            raise Exception(parsed_feed.bozo_exception)

        cnt = 0
        for entry in parsed_feed.entries:
            existing_item = db.query(Item).filter(Item.url == entry['link']).first()
            if existing_item is None or prevent_duplication is not True:
                item = Item(
                    feed_id=feed.id,
                    created_time=datetime.fromtimestamp(mktime(entry['published_parsed'])),
                    url=entry['link'],
                    title=entry['title'],
                    description=entry['summary'],
                    unread=True,
                )
                cnt += 1
                db.add(item)
        feed.failed_cnt = 0
        feed.sync = True
        feed.status = ""
        db.commit()
        return cnt
    except Exception as e:
        db.rollback()
        print(f"Error scraping feed: {feed_url}, {str(e)}")
        return 0
