import json

from locus.capture.window import WindowTracker


def test_window_tracker_uses_app_mapping(tmp_path):
    config_path = tmp_path / "app_mapping.json"
    config_path.write_text(
        json.dumps({
            "editor": ["code.exe", "cursor.exe"],
            "browser": ["chrome.exe"],
        }),
        encoding="utf-8",
    )

    tracker = WindowTracker(callback_action=lambda payload: payload, config_path=str(config_path))

    assert tracker._determine_category("code.exe") == "editor"
    assert tracker._determine_category("chrome.exe") == "browser"
    assert tracker._determine_category("unknown.exe") == "uncategorized"
