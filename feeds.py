from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import verify_token
from db import get_session, Feed
from messages import FeedResponse
from scrapper import scrape_feed

router = APIRouter()


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


@router.post("/", response_model=dict)
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
@router.put("/follow-feeds")
def follow_feed(feed_updates: List[FeedUpdate], user_id: int = Depends(verify_token)):
    db = get_session()
    for feed_update in feed_updates:
        feed = db.query(Feed).filter_by(id=feed_update.id, user_id=user_id).first()
        if not feed:
            raise HTTPException(status_code=404, detail=FeedResponse.feed_not_exist(feed_update.id))
        feed.follow = feed_update.follow
    db.commit()
    return FeedResponse.feed_updated_successfully()


@router.get("/", response_model=List[FeedData])
async def get_items_by_feed_id(user_id: int = Depends(verify_token)):
    db = get_session()
    user_feeds = db.query(Feed).filter_by(user_id=user_id).all()
    return [FeedData(id=feed.id, follow=feed.follow, url=feed.url, sync=feed.sync,
                     status=feed.status, failed_cnt=feed.failed_cnt) for feed in user_feeds]


@router.put("/{feed_id}/force-sync/", response_model=dict)
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

