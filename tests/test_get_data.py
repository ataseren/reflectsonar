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


def test_standard_issue_query_includes_branch_when_provided(monkeypatch):
    captured = {}

    def capture_fetch(name, item_key, url_template, *_args, **_kwargs):
        captured.update(name=name, item_key=item_key, url_template=url_template)
        return {"issues": [], "paging": {"total": 0}}

    monkeypatch.setattr(get_data, "fetch_paginated_items", capture_fetch)

    get_data.fetch_all_issues(
        "https://sonar.example", "token", "my-project", mqr_mode=False, branch="develop"
    )

    assert "branch=develop" in captured["url_template"]
    assert "componentKeys=my-project" in captured["url_template"]


def test_mqr_issue_query_includes_branch_when_provided(monkeypatch):
    captured_urls = []

    def capture_fetch(name, item_key, url_template, *_args, **_kwargs):
        captured_urls.append(url_template)
        return {"issues": [], "paging": {"total": 0}}

    monkeypatch.setattr(get_data, "fetch_paginated_items", capture_fetch)

    get_data.fetch_all_issues(
        "https://sonar.example", "token", "my-project", mqr_mode=True, branch="feature/auth"
    )

    assert len(captured_urls) == 3
    for url in captured_urls:
        assert "branch=feature%2Fauth" in url
        assert "componentKeys=my-project" in url


def test_hotspot_query_includes_branch_when_provided(monkeypatch):
    captured = {}

    def capture_fetch(name, item_key, url_template, *_args, **_kwargs):
        captured.update(name=name, item_key=item_key, url_template=url_template)
        return {"hotspots": [], "paging": {"total": 0}}

    monkeypatch.setattr(get_data, "fetch_paginated_items", capture_fetch)

    get_data.fetch_all_hotspots(
        "https://sonar.example", "token", "my-project", branch="release/1.0"
    )

    assert "projectKey=my-project" in captured["url_template"]
    assert "branch=release%2F1.0" in captured["url_template"]


def test_hotspot_query_omits_branch_when_none(monkeypatch):
    captured = {}

    def capture_fetch(name, item_key, url_template, *_args, **_kwargs):
        captured.update(name=name, item_key=item_key, url_template=url_template)
        return {"hotspots": [], "paging": {"total": 0}}

    monkeypatch.setattr(get_data, "fetch_paginated_items", capture_fetch)

    get_data.fetch_all_hotspots("https://sonar.example", "token", "my-project", branch=None)

    assert "projectKey=my-project" in captured["url_template"]
    assert "branch=" not in captured["url_template"]


def test_get_code_snippet_includes_branch_when_provided(monkeypatch):
    captured_url = None

    def capture_fetch(name, url, *_args, **_kwargs):
        nonlocal captured_url
        captured_url = url
        return {"sources": [[10, "line 10 content"]]}

    monkeypatch.setattr(get_data, "fetch", capture_fetch)

    snippet = get_data.get_code_snippet(
        "https://sonar.example", "token", "my-project:src/main.py", 10, branch="feature/patch"
    )

    assert "branch=feature%2Fpatch" in captured_url
    assert "key=my-project%3Asrc%2Fmain.py" in captured_url
    assert "line 10 content" in snippet


def test_get_code_snippet_omits_branch_when_none(monkeypatch):
    captured_url = None

    def capture_fetch(name, url, *_args, **_kwargs):
        nonlocal captured_url
        captured_url = url
        return {"sources": [[10, "line 10 content"]]}

    monkeypatch.setattr(get_data, "fetch", capture_fetch)

    get_data.get_code_snippet(
        "https://sonar.example", "token", "my-project:src/main.py", 10, branch=None
    )

    assert "branch=" not in captured_url


def test_branch_with_special_characters_is_safely_encoded(monkeypatch):
    captured = {}

    def capture_fetch(name, item_key, url_template, *_args, **_kwargs):
        captured.update(name=name, item_key=item_key, url_template=url_template)
        return {"issues": [], "paging": {"total": 0}}

    monkeypatch.setattr(get_data, "fetch_paginated_items", capture_fetch)

    get_data.fetch_all_issues(
        "https://sonar.example",
        "token",
        "project",
        mqr_mode=False,
        branch="feature/ticket-123&v=2#tag",
    )

    # Characters / & = # must all be percent-encoded
    assert "branch=feature%2Fticket-123%26v%3D2%23tag" in captured["url_template"]


def test_get_report_data_propagates_branch(monkeypatch):
    fetched_urls = []

    def mock_fetch(name, url, *_args, **_kwargs):
        fetched_urls.append(url)
        if "/api/settings/values" in url:
            return {"settings": [{"key": "sonar.multi-quality-mode.enabled", "value": "false"}]}
        if "/api/components/show" in url:
            return {"component": {"key": "my-project", "name": "My Project", "qualifier": "TRK"}}
        if "/api/measures/component" in url:
            return {"component": {"measures": []}}
        return {}

    monkeypatch.setattr(get_data, "fetch", mock_fetch)
    monkeypatch.setattr(
        get_data,
        "fetch_all_issues",
        lambda *args, **kwargs: {"issues": [], "paging": {"total": 0}},
    )
    monkeypatch.setattr(
        get_data,
        "fetch_all_hotspots",
        lambda *args, **kwargs: {"hotspots": [], "paging": {"total": 0}},
    )

    report_data = get_data.get_report_data(
        "https://sonar.example",
        "token",
        "my-project",
        include_snippets=False,
        include_rules=False,
        branch="develop",
    )

    assert report_data.branch == "develop"
    component_urls = [u for u in fetched_urls if "/api/components/show" in u]
    measures_urls = [u for u in fetched_urls if "/api/measures/component" in u]

    assert len(component_urls) == 1
    assert "branch=develop" in component_urls[0]

    assert len(measures_urls) == 1
    assert "branch=develop" in measures_urls[0]
