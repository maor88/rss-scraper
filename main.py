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
from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional
import threading
import uvicorn
from sqlalchemy import desc

from auth import verify_token
from db import Feed, Item, get_session, get_user_by_email

from messages import FeedResponse, AuthResponse, ItemResponse
from scrapper import scrape_feeds, scrape_feed

app = FastAPI()


class FeedCreate(BaseModel):
    url: str


class FeedUpdate(BaseModel):
    id: int
    follow: bool


class FeedData(BaseModel):
    id: int
    url: str
    follow: bool
    status: str
    failed_cnt: int
    sync: bool


class ItemData(BaseModel):
    id: int
    unread: bool = True
    created_time: str
    url: str
    title: str
    description: str
    feed_id: int


class UserLogin(BaseModel):
    email: str


# API endpoints
@app.post("/login/", response_model=dict)
async def login(user_login: UserLogin):
    user = get_user_by_email(user_login.email)
    if user is None:
        raise HTTPException(status_code=404, detail=AuthResponse.user_not_exist(user_login.email))
    else:
        response_model = dict()
        response_model["access_token"] = user.token
        response_model["token_type"] = "bearer"
        return response_model


@app.post("/feeds/", response_model=dict)
async def create_feed(feed: FeedCreate, user_id: int = Depends(verify_token)):
    db = get_session()
    user_feeds = db.query(Feed).filter_by(url=feed.url, user_id=user_id).all()
    if user_feeds is None or len(user_feeds) == 0:
        new_feed = Feed(url=feed.url, user_id=user_id)
        db.add(new_feed)
        db.commit()
        db.refresh(new_feed)
        return FeedResponse.subscribed_successfully(feed.url)
    else:
        return FeedResponse.already_subscribed(feed.url)


# Update the follow/unfollow field for a list of feeds
@app.put("/follow-feeds")
def follow_feed(feed_updates: List[FeedUpdate], user_id: int = Depends(verify_token)):
    db = get_session()
    for feed_update in feed_updates:
        feed = db.query(Feed).filter_by(id=feed_update.id, user_id=user_id).first()
        if not feed:
            raise HTTPException(status_code=404, detail=FeedResponse.feed_not_exist(feed_update.id))
        feed.follow = feed_update.follow
    db.commit()
    return FeedResponse.feed_updated_successfully()


@app.get("/feeds/", response_model=List[FeedData])
async def get_items_by_feed_id(user_id: int = Depends(verify_token)):
    db = get_session()
    user_feeds = db.query(Feed).filter_by(user_id=user_id).all()
    return [FeedData(id=feed.id, follow=feed.follow, url=feed.url, sync=feed.sync,
                     status=feed.status, failed_cnt=feed.failed_cnt) for feed in user_feeds]


@app.put("/{feed_id}/force-sync/", response_model=dict)
async def force_feed_sync(feed_id: int, user_id: int = Depends(verify_token)):
    db = get_session()
    try:
        feed = db.query(Feed).filter_by(user_id=user_id, id=feed_id).first()
        if feed is None:
            return FeedResponse.feed_not_exist(feed_id)
        else:
            cnt = scrape_feed(feed, db)
            return FeedResponse.feed_force_sync_success(cnt)
    except Exception as e:
        raise HTTPException(status_code=400, detail=FeedResponse.feed_force_sync_failed(feed_id, str(e)))


"""
/{feed_id}/items api - getting all feed items with 3 different states using query param:
1. no query param added - get all items of feed
2. unread_only - getting only items that marked as unread
3. read_only - getting only items that marked as read
"""


@app.get("/{feed_id}/items", response_model=List[ItemData])
async def get_items_by_feed_id(feed_id: int, user_id: int = Depends(verify_token),
                               unread_only: Optional[bool] = Query(None, description="Retrieve only unread items"),
                               read_only: Optional[bool] = Query(None, description="Retrieve only read items")):
    db = get_session()
    feed = db.query(Feed).filter_by(user_id=user_id, id=feed_id).first()

    if feed is None:
        raise HTTPException(status_code=404, detail=FeedResponse.feed_not_exist(feed_id))

    else:
        if unread_only is True:
            items = db.query(Item).filter_by(feed_id=feed_id, unread=True).order_by(desc(Item.created_time)).all()
        elif read_only is True:
            items = db.query(Item).filter_by(feed_id=feed_id, unread=False).order_by(desc(Item.created_time)).all()
        else:
            items = db.query(Item).filter_by(feed_id=feed_id).order_by(desc(Item.created_time)).all()
        if len(items) == 0:
            raise HTTPException(status_code=404, detail=ItemResponse.no_items_for_this_feed(feed_id))
        return [ItemData(id=item.id, unread=item.unread, url=item.url,
                         created_time=item.created_time.strftime("%Y-%m-%d %H:%M:%S"), feed_id=item.feed_id,
                         description=item.description, title=item.title) for item in items]


@app.put("/read-item/{item_id}",  response_model=dict)
async def set_item_read_unread(item_id: int, user_id: int = Depends(verify_token)):
    db = get_session()
    item = db.query(Item).filter_by(id=item_id).first()
    if item is None:
        return ItemResponse.item_not_exist(item_id)

    else:
        if item.feed.user_id != user_id:
            return ItemResponse.no_permissions(user_id)
        else:
            item.unread = False
            db.commit()
            return ItemResponse.item_updated_successfully()

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
