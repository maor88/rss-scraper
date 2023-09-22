"""
RSS scraper app - sendCloud

Tests using pytests, test the core logic for the server -scrapping rss
this test file includes two main tests
1. rss scrape for invalid url
2. rss scrape for valid rss url

validate db rollback in case of failed, results, and error handling

Author: Maor Avitan
"""

from datetime import datetime
from unittest.mock import Mock, patch
import pytest
from scrapper import scrape_feed


@pytest.fixture
def mock_db():
    return Mock()


@pytest.fixture
def mock_feed_success():
    feed = Mock()
    feed.url = "https://www.nu.nl/rss/Algemeen"
    feed.bozo = False
    feed.bozo_exception = None
    feed.failed_cnt = 0
    feed.status = ""
    feed.id = 1
    return feed


@pytest.fixture
def mock_feed_failure():
    feed = Mock()
    feed.url = "https://www.not-real-rss-url.com"
    feed.bozo = True
    feed.bozo_exception = Exception("Simulated Bozo Exception")
    feed.failed_cnt = 0
    feed.status = ""
    feed.id = 2
    return feed


@pytest.fixture
def mock_parsed_feed_success():
    parsed_feed = Mock()
    parsed_feed.bozo = False
    parsed_feed.entries = [
        {
            "link": "https://example.com/post1",
            "published_parsed": datetime.now().timetuple(),
            "title": "Post 1",
            "summary": "Summary of post 1",
        },
    ]
    return parsed_feed


@patch("scrapper.feedparser.parse")
def test_scrape_feed_success(mock_parse, mock_db, mock_feed_success, mock_parsed_feed_success):
    mock_parse.return_value = mock_parsed_feed_success
    result = scrape_feed(mock_feed_success, mock_db, False)

    assert result == len(mock_parsed_feed_success.entries)
    assert mock_feed_success.failed_cnt == 0
    assert mock_feed_success.status == ""
    mock_db.commit.assert_called()
    mock_db.add.assert_called()
    assert mock_db.rollback.call_count == 0


@patch("scrapper.feedparser.parse")
def test_scrape_feed_failure(mock_db, mock_feed_failure):
    added = scrape_feed(mock_feed_failure, mock_db)

    assert mock_feed_failure.failed_cnt == 1
    assert added == 0
    mock_db.rollback.assert_called()
    mock_db.add.assert_not_called()
