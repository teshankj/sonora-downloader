from sonora.models import DownloadItem


def test_new_item_strips_url():
    item = DownloadItem.new("  https://example.com/audio  ")
    assert item.url == "https://example.com/audio"
    assert item.status == "PENDING"
