"""
RSS scraper app - sendCloud

Messages module retrieve static messages to the client base on the situation

Author: Maor Avitan
"""

class FeedResponse:
    @staticmethod
    def subscribed_successfully(feed_url):
        return {"message": f"Subscribed to feed '{feed_url}' successfully."}

    @staticmethod
    def already_subscribed(feed_url):
        return {"message": f"The feed '{feed_url}' is already subscribed."}

    @staticmethod
    def feed_not_exist(feed_id):
        return {"message": f"Feed with ID {feed_id} not found."}

    @staticmethod
    def feed_force_sync_success(cnt):
        return {"message": f"{cnt} items added to the feed"}

    @staticmethod
    def feed_updated_successfully():
        return {"message": "Feed updated successfully"}

    @staticmethod
    def feed_force_sync_failed(feed_id, err):
        return {"message": f"Scrapping feed ID {feed_id} Failed. {err}"}


class ItemResponse:
    @staticmethod
    def no_items_for_this_feed(feed_id):
        return {"message": f"No items found for feed {feed_id}."}

    @staticmethod
    def item_not_exist(item_id):
        return {"message": f"Item ID {item_id} not found."}

    @staticmethod
    def no_permissions(user_id):
        return {"message": f"User {user_id} does not have permission."}

    @staticmethod
    def item_updated_successfully():
        return {"message": "Item updated successfully"}


class AuthResponse:
    @staticmethod
    def user_authenticated(email, token):
        return {"message": f"User '{email}' authenticated successfully.", "token": token}

    @staticmethod
    def user_not_exist(email):
        return {"message": f"User '{email}' not found."}
