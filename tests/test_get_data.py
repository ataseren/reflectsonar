"""Tests for SonarQube API response handling."""

import pytest
import requests

from reflectsonar.api import get_data


def test_get_mode_setting_reads_official_settings_shape():
    payload = {"settings": [{"key": "sonar.multi-quality-mode.enabled", "value": "false"}]}

    assert get_data.get_mode_setting(payload, default=True) is False


def test_get_mode_setting_defaults_to_standard_for_old_servers():
    assert get_data.get_mode_setting({}, default=False) is False


def test_metric_keys_follow_active_mode():
    assert "software_quality_security_rating" in get_data.get_metric_keys(True)
    assert "security_rating" not in get_data.get_metric_keys(True)
    assert "security_rating" in get_data.get_metric_keys(False)
    assert "software_quality_security_rating" not in get_data.get_metric_keys(False)


def test_build_api_url_encodes_query_values():
    url = get_data.build_api_url(
        "https://sonar.example/", "/api/components/show", {"component": "a&b c"}
    )

    assert url == "https://sonar.example/api/components/show?component=a%26b+c"


def test_paginated_fetch_raises_instead_of_returning_partial_data(monkeypatch):
    def fail_fetch(*_args, **_kwargs):
        raise requests.RequestException("network down")

    monkeypatch.setattr(get_data, "fetch", fail_fetch)

    with pytest.raises(RuntimeError, match="Failed to fetch issues page 1"):
        get_data.fetch_paginated_items(
            "issues", "issues", "https://sonar/api/issues?ps={page_size}&p={page}", "token"
        )


def test_paginated_fetch_rejects_api_limit_truncation(monkeypatch):
    monkeypatch.setattr(get_data, "API_RESULT_LIMIT", 2)

    def limited_fetch(*_args, **_kwargs):
        return {"issues": [{"key": "1"}, {"key": "2"}], "paging": {"total": 3}}

    monkeypatch.setattr(get_data, "fetch", limited_fetch)

    with pytest.raises(RuntimeError, match="refusing to generate an incomplete report"):
        get_data.fetch_paginated_items(
            "issues", "issues", "https://sonar/api/issues?ps={page_size}&p={page}", "token"
        )


def test_standard_issue_query_does_not_require_mqr_parameters(monkeypatch):
    captured = {}

    def capture_fetch(name, item_key, url_template, *_args, **_kwargs):
        captured.update(name=name, item_key=item_key, url_template=url_template)
        return {"issues": [], "paging": {"total": 0}}

    monkeypatch.setattr(get_data, "fetch_paginated_items", capture_fetch)

    get_data.fetch_all_issues("https://sonar.example", "token", "project&branch", mqr_mode=False)

    assert "impactSoftwareQualities" not in captured["url_template"]
    assert "componentKeys=project%26branch" in captured["url_template"]


def test_mqr_issue_queries_are_deduplicated_and_merge_impacts(monkeypatch):
    def category_fetch(name, *_args, **_kwargs):
        category = name[len("issues data (") : -1]
        return {
            "issues": [
                {
                    "key": "shared",
                    "impacts": [{"softwareQuality": category, "severity": "HIGH"}],
                }
            ]
        }

    monkeypatch.setattr(get_data, "fetch_paginated_items", category_fetch)

    result = get_data.fetch_all_issues("https://sonar.example", "token", "project", mqr_mode=True)

    assert len(result["issues"]) == 1
    assert {impact["softwareQuality"] for impact in result["issues"][0]["impacts"]} == {
        "SECURITY",
        "RELIABILITY",
        "MAINTAINABILITY",
    }
