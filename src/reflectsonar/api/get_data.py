"""
This module is used to fetch data from SonarQube API
"""
import traceback
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional
import requests

from ..data.models import (SonarQubeProject, SonarQubeIssue, SonarQubeMeasure, # pylint: disable=import-error
                         SonarQubeHotspot, ReportData, SonarQubeRule)  # pylint: disable=import-error

from ..report.utils import log, log_progress, finish_progress, print_message

PAGE_SIZE = 500
API_RESULT_LIMIT = 10000
ISSUE_IMPACT_QUALITIES = ("SECURITY", "RELIABILITY", "MAINTAINABILITY")
SNIPPET_FETCH_WORKERS = 8 # Tune for server load vs speed - SonarQube can handle around 8 concurrent requests without significant performance degradation in our testing

# Helpers
def create_session(token: str) -> requests.Session:
    """Create a requests session configured for SonarQube authentication."""
    session = requests.Session()
    session.auth = (token, "")
    return session

def get_json(url: str, token: str, session: requests.Session = None) -> Dict:
    """Helper function to perform GET request and return JSON response"""
    created_session = None
    client = session
    if client is None:
        created_session = create_session(token)
        client = created_session

    try:
        response = client.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    finally:
        if created_session is not None:
            created_session.close()

def fetch(name: str, url: str, token: str, verbose: bool,
          inline: bool = False, session: requests.Session = None) -> Dict:
    """Fetches data from SonarQube API by using get_json and utils.log"""
    if inline:
        log_progress(verbose, f"Fetching {name}...")
    else:
        log(verbose, f"Fetching {name}...")
    return get_json(url, token, session=session)

def fetch_paginated_items(name: str, item_key: str, url_template: str,
                          token: str, verbose: bool = False,
                          session: requests.Session = None) -> Dict:
    """Fetch every page for a paginated SonarQube API endpoint."""
    all_items = []
    page = 1
    total = 0
    hit_api_limit = False

    while True:
        page_url = url_template.format(page_size=PAGE_SIZE, page=page)

        try:
            page_data = fetch(
                f"{name} page {page}...",
                page_url,
                token,
                verbose,
                inline=True,
                session=session,
            )
        except requests.RequestException as e:
            print_message(f"ERROR: Failed to fetch {name} page {page}: {e}")
            break

        page_items = page_data.get(item_key, [])
        all_items.extend(page_items)

        paging = page_data.get("paging", {})
        total = paging.get("total", len(all_items))

        if len(all_items) >= API_RESULT_LIMIT:
            hit_api_limit = True
            break

        if not page_items or len(all_items) >= total:
            break

        page += 1

    finish_progress()
    if hit_api_limit:
        log(verbose, f"Reached SonarQube API result limit ({API_RESULT_LIMIT}) for {name}; stopping pagination early.") # pylint: disable=line-too-long

    return {
        item_key: all_items,
        "paging": {
            "pageIndex": 1,
            "pageSize": len(all_items),
            "total": max(total, len(all_items)),
        }
    }

# Getters
def get_rules(base_url: str, token: str, rule_keys: List[str],
              verbose: bool = False,
              session: requests.Session = None) -> Dict[str, 'SonarQubeRule']:
    """Fetches rule descriptions from SonarQube API for given rule keys"""
    if not rule_keys:
        return {}

    try:
        # SonarQube API: /api/rules/show?key=rule_key
        rules = {}
        total_rules = len(rule_keys)

        for index, rule_key in enumerate(rule_keys, start=1):
            rule_url = f"{base_url}/api/rules/show?key={rule_key}"
            response = fetch(
                f"rule description {index}/{total_rules}: {rule_key}",
                rule_url,
                token,
                verbose,
                inline=True,
                session=session,
            )

            if 'rule' in response:
                rules[rule_key] = SonarQubeRule.from_dict(response['rule'])

        finish_progress()
        log(verbose, f"   ✅ Fetched {len(rules)} rule descriptions")
        return rules

    except requests.RequestException as e:
        finish_progress()
        print_message(f"ERROR: Error fetching rules: {e}")
        return {}

# Function to fetch code snippet for a specific issue or hotspot
def get_code_snippet(base_url: str, token: str, component: str, line: int,
                     session: requests.Session = None) -> str:
    """Fetches code snippet for a specific issue or hotspot from SonarQube API"""
    try:
        # Calculate line range (line ± context_lines)
        from_line = max(1, line - 3)
        to_line = line + 3

        sources_url = f"{base_url}/api/sources/show?key={component}&from={from_line}&to={to_line}"

        try:
            response = fetch("code snippets...", sources_url, token, False, session=session)
        except requests.RequestException as api_error:
            print_message(f"ERROR: API call failed: {api_error}")
            return ""

        sources = response.get("sources", [])

        if not sources:
            print_message(f"ERROR: No sources found for {component}:{line}")
            print_message(f"ERROR: Full API response: {response}")
            return ""

        # Format the code snippet with line numbers
        snippet_lines = []
        for source in sources:
            line_num = source[0]
            code = source[1]
            # Mark the problematic line with >>>
            marker = ">>> " if line_num == line else "    "
            snippet_lines.append(f"{marker}{line_num:3d}: {code}")

        result = "\n".join(snippet_lines)
        return result
    except requests.RequestException as e:
        print_message(f"ERROR: Error fetching code snippet for {component}:{line}: {e}")  # Debug log
        traceback.print_exc()
        return ""

def populate_code_snippets(items, base_url: str, token: str,
                           item_type: str, verbose: bool = False):
    """Fetch code snippets concurrently for issues or hotspots with line numbers."""
    items_with_lines = []

    for item in items:
        if item.line:
            items_with_lines.append(item)
            continue

        if item_type == "issue":
            print_message(f"ERROR: Issue {item.key} has no line number, skipping code snippet")
        else:
            log(verbose, f"Hotspot {item.key} has no line number, skipping code snippet")

    total_items = len(items_with_lines)
    if not total_items:
        return

    plural = f"{item_type}s"
    log(verbose, f"Fetching code snippets for {total_items} {plural}...")

    worker_count = min(SNIPPET_FETCH_WORKERS, total_items)
    thread_local = threading.local()
    created_sessions = []
    sessions_lock = threading.Lock()

    def get_worker_session():
        if not hasattr(thread_local, "session"):
            thread_local.session = create_session(token)
            with sessions_lock:
                created_sessions.append(thread_local.session)
        return thread_local.session

    def fetch_item_snippet(item):
        snippet = get_code_snippet(
            base_url,
            token,
            item.component,
            item.line,
            session=get_worker_session(),
        )
        if not snippet.strip():
            if item_type == "issue":
                snippet = "No code snippet available for this issue."
            else:
                snippet = "No code snippet available for this hotspot."
        return item, snippet

    try:
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            future_map = {
                executor.submit(fetch_item_snippet, item): item
                for item in items_with_lines
            }

            completed = 0
            for future in as_completed(future_map):
                item, snippet = future.result()
                item.code_snippet = snippet
                completed += 1

                if completed % 10 == 0 or completed == total_items:
                    log_progress(verbose, f"   Processed {completed}/{total_items} {plural}...")
    finally:
        finish_progress()
        for created_session in created_sessions:
            created_session.close()

def fetch_all_issues(base_url: str, token: str, project_key: str,
                     verbose: bool = False,
                     session: requests.Session = None) -> Dict:
    """Fetches all issues from a project by impact category."""
    issues_by_key = {}

    for impact_quality in ISSUE_IMPACT_QUALITIES:
        issues_url_template = (
            f"{base_url}/api/issues/search?componentKeys={project_key}"
            f"&impactSoftwareQualities={impact_quality}"
            "&ps={page_size}&p={page}"
        )
        issues_data = fetch_paginated_items(
            f"issues data ({impact_quality})",
            "issues",
            issues_url_template,
            token,
            verbose,
            session=session,
        )

        for issue in issues_data.get("issues", []):
            issue_key = issue.get("key")
            if not issue_key:
                continue

            if issue_key not in issues_by_key:
                issues_by_key[issue_key] = issue
                continue

            existing_issue = issues_by_key[issue_key]
            existing_impacts = existing_issue.setdefault("impacts", [])
            for impact in issue.get("impacts", []):
                if impact not in existing_impacts:
                    existing_impacts.append(impact)

    unique_issues = list(issues_by_key.values())
    return {
        "issues": unique_issues,
        "paging": {
            "pageIndex": 1,
            "pageSize": len(unique_issues),
            "total": len(unique_issues),
        }
    }

def fetch_all_hotspots(base_url: str, token: str, project_key: str,
                       verbose: bool = False,
                       session: requests.Session = None) -> Dict:
    """Fetches all security hotspots from a project"""
    hotspots_url_template = (
        f"{base_url}/api/hotspots/search?projectKey={project_key}"
        "&ps={page_size}&p={page}"
    )
    return fetch_paginated_items(
        "hotspots",
        "hotspots",
        hotspots_url_template,
        token,
        verbose,
        session=session,
    )

def issue_matches_top_severity(issue: SonarQubeIssue, mqr_mode: bool) -> bool:  # pylint: disable=unused-argument
    """Return whether an issue is BLOCKER or has at least one HIGH impact."""
    high_impacts = [
        impact for impact in issue.impacts
        if impact.get("severity", "").upper() == "HIGH"
    ]
    if high_impacts:
        issue.impacts = high_impacts
        return True

    if issue.severity.upper() == "BLOCKER":
        # Drop lower-severity impacts so MQR rendering falls back to BLOCKER.
        issue.impacts = []
        return True

    return False

def hotspot_matches_top_severity(hotspot: SonarQubeHotspot) -> bool:
    """Return whether a hotspot matches the highest-severity filter."""
    return hotspot.vulnerability_probability.upper() == "HIGH"

def filter_findings_by_priority(issues: List[SonarQubeIssue],
                                hotspots: List[SonarQubeHotspot],
                                mqr_mode: bool):
    """Keep only BLOCKER or HIGH-severity issues and HIGH-risk hotspots."""
    filtered_issues = [
        issue for issue in issues
        if issue_matches_top_severity(issue, mqr_mode)
    ]
    filtered_hotspots = [
        hotspot for hotspot in hotspots
        if hotspot_matches_top_severity(hotspot)
    ]
    return filtered_issues, filtered_hotspots

def format_exclusions_note(include_snippets: bool,
                           high_severity_only: bool,
                           include_rules: bool) -> Optional[str]:
    """Build a human-readable cover-page note describing excluded content."""
    excluded_parts = []

    if not include_snippets:
        excluded_parts.append("code snippets")
    if high_severity_only:
        excluded_parts.append("non-BLOCKER/non-HIGH issues and non-HIGH-probability hotspots")
    if not include_rules:
        excluded_parts.append("the Rules Reference section")

    if not excluded_parts:
        return None

    if len(excluded_parts) == 1:
        excluded_summary = excluded_parts[0]
    elif len(excluded_parts) == 2:
        excluded_summary = f"{excluded_parts[0]} and {excluded_parts[1]}"
    else:
        excluded_summary = f"{', '.join(excluded_parts[:-1])}, and {excluded_parts[-1]}"

    return f"This report excludes {excluded_summary}."

# Main function to get all report data
def get_report_data(base_url: str, token: str,
                    project_key: str, verbose: bool = False,
                    include_snippets: bool = True,
                    high_severity_only: bool = False,
                    include_rules: bool = True) -> ReportData:
    """Main function that fetches all necessary data from SonarQube API"""
    metric_keys = [
    "software_quality_security_rating",
    "software_quality_reliability_rating",
    "software_quality_maintainability_rating",
    "lines_to_cover",
    "software_quality_maintainability_issues",
    "software_quality_security_issues",
    "software_quality_reliability_issues",
    "accepted_issues",
    "coverage",
    "duplicated_lines_density",
    "lines",
    "security_hotspots",
    ]
    metrics_param = ",".join(metric_keys)

    component_url = f"{base_url}/api/components/show?component={project_key}"
    measures_url = f"{base_url}/api/measures/component?component={project_key}&metricKeys={metrics_param}" # pylint: disable=line-too-long
    settings_url = f"{base_url}/api/settings/values?keys=sonar.multi-quality-mode.enabled"

    session = create_session(token)
    try:
        component_data = fetch("project component data...", component_url, token, verbose,
                               session=session)
        issues_data = fetch_all_issues(base_url, token, project_key, verbose, session=session)
        measures_data = fetch("measures data...", measures_url, token, verbose, session=session)
        settings_data = fetch("SonarQube settings...", settings_url, token, verbose,
                              session=session)
        hotspots_data = fetch_all_hotspots(base_url, token, project_key, verbose, session=session)

        project = SonarQubeProject.from_dict(component_data)

        issues = [SonarQubeIssue.from_dict(issue_data) for issue_data in issues_data.get("issues", [])]
        hotspots = [
            SonarQubeHotspot.from_dict(hotspot_data)
            for hotspot_data in hotspots_data.get("hotspots", [])
        ]

        settings: bool = settings_data.get("sonar.multi-quality-mode.enabled",
                                           {}).get("value", "true").lower() == "true"

        if high_severity_only:
            issues, hotspots = filter_findings_by_priority(issues, hotspots, settings)
            log(verbose, "Filtering findings to top severity only (BLOCKER or HIGH-severity issues / HIGH hotspots)...") # pylint: disable=line-too-long

        if include_snippets:
            log(verbose, f"Processing {len(issues)} issues and fetching code snippets...")
            populate_code_snippets(issues, base_url, token, "issue", verbose)
        else:
            log(verbose, "Skipping issue code snippets (--no-snippets enabled)")

        measures: Dict[str, SonarQubeMeasure] = {
            m["metric"]: SonarQubeMeasure.from_dict(m)
            for m in measures_data.get("component", {}).get("measures", [])
        }

        if include_snippets:
            log(verbose, f"Processing {len(hotspots)} security hotspots and fetching code snippets...")
            populate_code_snippets(hotspots, base_url, token, "hotspot", verbose)
        else:
            log(verbose, "Skipping hotspot code snippets (--no-snippets enabled)")

        # Collect unique rule keys from issues and hotspots
        if include_rules:
            rule_keys = set()
            for issue in issues:
                if issue.rule:
                    rule_keys.add(issue.rule)
            for hotspot in hotspots:
                if hotspot.rule_key:
                    rule_keys.add(hotspot.rule_key)

            log(verbose, f"📋 Fetching descriptions for {len(rule_keys)} unique rules...")

            # Fetch rule descriptions
            rules = get_rules(base_url, token, list(rule_keys), verbose, session=session)
        else:
            log(verbose, "Skipping rule descriptions and Rules Reference section (--no-rules enabled)")
            rules = {}

        log(verbose, "Data collection summary:")
        log(verbose, f"   • Project: {project.name}")
        log(verbose, f"   • Issues collected: {len(issues)}")
        log(verbose, f"   • Hotspots collected: {len(hotspots)}")
        log(verbose, f"   • Measures collected: {len(measures)}")
        log(verbose, f"   • MQR mode enabled: {settings}")
        log(verbose, f"   • Code snippets enabled: {include_snippets}")
        log(verbose, f"   • Top severity only: {high_severity_only}")
        log(verbose, f"   • Rules section enabled: {include_rules}")
        log(verbose, f"   • Issues with code snippets: {sum(1 for i in issues if i.code_snippet and i.code_snippet.strip())}") # pylint: disable=line-too-long
        log(verbose, f"   • Hotspots with code snippets: {sum(1 for h in hotspots if h.code_snippet and h.code_snippet.strip())}") # pylint: disable=line-too-long
        log(verbose, f"   • Rules descriptions fetched: {len(rules)}")

        return ReportData(
            project=project,
            issues=issues,
            measures=measures,
            hotspots=hotspots,
            quality_gate={},
            quality_profiles=[],
            mode_setting=settings,
            rules=rules,
            exclusions_note=format_exclusions_note(
                include_snippets,
                high_severity_only,
                include_rules,
            ),
        )
    finally:
        session.close()
