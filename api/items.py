from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc

from auth import verify_token
from db import get_session, Item, Feed
from messages import ItemResponse, FeedResponse

router = APIRouter()


class ItemData(BaseModel):
    id: int
    unread: bool = True
    created_time: str
    url: str
    title: str
    description: str
    feed_id: int



"""
/{feed_id}/items api - getting all feed items with 3 different states using query param:
1. no query param added - get all items of feed
2. unread_only - getting only items that marked as unread
3. read_only - getting only items that marked as read
"""


@router.get("/{feed_id}/", response_model=List[ItemData])
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


@router.put("/read-item/{item_id}",  response_model=dict)
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