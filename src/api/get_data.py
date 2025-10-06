# Module to fetch data from SonarQube API
from typing import Dict, List
from data.models import SonarQubeProject, SonarQubeIssue, SonarQubeMeasure, SonarQubeHotspot, ReportData, SonarQubeRule
import requests
import traceback
from report.utils import log

# Helpers
def get_json(url: str, token: str) -> Dict:
    response = requests.get(url, auth=(token, ""))
    response.raise_for_status()
    return response.json()

def fetch(name: str, url: str, token: str, verbose: bool) -> Dict:
    log(verbose, f"Fetching {name}...")
    return get_json(url, token)

# Function to fetch rule descriptions for given rule keys
def get_rules(base_url: str, token: str, rule_keys: List[str], verbose: bool = False) -> Dict[str, 'SonarQubeRule']:
    if not rule_keys:
        return {}

    try:
        # SonarQube API: /api/rules/show?key=rule_key
        rules = {}
        
        for rule_key in rule_keys:
            if verbose:
                print(f"   📋 Fetching rule description: {rule_key}")
                
            rule_url = f"{base_url}/api/rules/show?key={rule_key}"
            response = fetch("rule description...", rule_url, token, verbose)
            
            if 'rule' in response:
                rule = SonarQubeRule.from_dict(response['rule'])
                rules[rule_key] = rule
                
        log(verbose, f"   ✅ Fetched {len(rules)} rule descriptions")
        return rules
        
    except Exception as e:
        print(f"ERROR: Error fetching rules: {e}")
        return {}

# Function to fetch code snippet for a specific issue or hotspot
def get_code_snippet(base_url: str, token: str, component: str, line: int, context_lines: int = 3) -> str:
    try:
        # Calculate line range (line ± context_lines)
        from_line = max(1, line - context_lines)
        to_line = line + context_lines
        
        sources_url = f"{base_url}/api/sources/show?key={component}&from={from_line}&to={to_line}"
        
        try:
            response = fetch("code snippets...", sources_url, token, False)
        except Exception as api_error:
            print(f"ERROR: API call failed: {api_error}")
            return ""
        
        sources = response.get("sources", [])
        
        if not sources:
            print(f"ERROR: No sources found for {component}:{line}")
            print(f"ERROR: Full API response: {response}")
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
    except Exception as e:
        print(f"ERROR: Error fetching code snippet for {component}:{line}: {e}")  # Debug log
        traceback.print_exc()
        return ""

# Function to fetch all hotspots with pagination
def fetch_all_hotspots(base_url: str, token: str, project_key: str) -> Dict:
    all_hotspots = []
    page = 1
    page_size = 500  # Maximum page size
        
    while True:
        hotspots_url = f"{base_url}/api/hotspots/search?projectKey={project_key}&ps={page_size}&p={page}"
        
        try:
            page_data = fetch("hotspots...", hotspots_url, token, False)
            page_hotspots = page_data.get("hotspots", [])
            
            all_hotspots.extend(page_hotspots)
            
            # Check if we have more pages
            paging = page_data.get("paging", {})
            total = paging.get("total", 0)
            current_total = len(all_hotspots)
            
            if current_total >= total:
                break
                
            page += 1
            
        except Exception as e:
            print(f"ERROR: Failed to fetch hotspots page {page}: {e}")
            break
    
    # Return in the same format as the original API response
    return {
        "hotspots": all_hotspots,
        "paging": {
            "pageIndex": 1,
            "pageSize": len(all_hotspots),
            "total": len(all_hotspots)
        }
    }

# Main function to get all report data
def get_report_data(base_url: str, token: str, project_key: str, verbose: bool = False) -> ReportData:

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
    issues_url = f"{base_url}/api/issues/search?componentKeys={project_key}&ps=500"
    measures_url = f"{base_url}/api/measures/component?component={project_key}&metricKeys={metrics_param}"
    settings_url = f"{base_url}/api/settings/values?keys=sonar.multi-quality-mode.enabled"

    component_data = fetch("project component data...", component_url, token, verbose)
    
    issues_data = fetch("issues data...", issues_url, token, verbose)

    measures_data = fetch("measures data...", measures_url, token, verbose)

    settings_data = fetch("SonarQube settings...", settings_url, token, verbose)

    hotspots_data = fetch_all_hotspots(base_url, token, project_key)

    project = SonarQubeProject.from_dict(component_data)
    
    # Process issues and fetch code snippets
    issues: List[SonarQubeIssue] = []
    total_issues = len(issues_data.get("issues", []))
    
    log(verbose, f"Processing {total_issues} issues and fetching code snippets...")
    
    for i, issue_data in enumerate(issues_data.get("issues", [])):
        issue = SonarQubeIssue.from_dict(issue_data)
        
        if (i + 1) % 10 == 0:  # Progress every 10 issues
            log(verbose, f"   Processed {i + 1}/{total_issues} issues...")
        
        # Fetch code snippet if the issue has a line number
        if issue.line:
            if verbose and total_issues <= 20:  # Show detail for small datasets
                log(verbose, f"      Fetching code snippet for {issue.key} at line {issue.line}")
            code_snippet = get_code_snippet(base_url, token, issue.component, issue.line, 3)

            if not code_snippet.strip():
                code_snippet = "No code snippet available for this issue."
            
            issue.code_snippet = code_snippet
        else:
            print(f"ERROR: Issue {issue.key} has no line number, skipping code snippet")
            
        issues.append(issue)

    measures: Dict[str, SonarQubeMeasure] = {
        m["metric"]: SonarQubeMeasure.from_dict(m)
        for m in measures_data.get("component", {}).get("measures", [])
    }

    # Process hotspots and fetch code snippets
    hotspots: List[SonarQubeHotspot] = []
    total_hotspots = len(hotspots_data.get("hotspots", []))

    log(verbose, f"Processing {total_hotspots} security hotspots and fetching code snippets...")

    for i, hotspot_data in enumerate(hotspots_data.get("hotspots", [])):
        hotspot = SonarQubeHotspot.from_dict(hotspot_data)

        if (i + 1) % 5 == 0:  # Progress every 5 hotspots
            log(verbose, f"   Processed {i + 1}/{total_hotspots} hotspots...")
        
        # Fetch code snippet if the hotspot has a line number
        if hotspot.line:
            if verbose and total_hotspots <= 10:  # Show detail for small datasets
                log(f"      Fetching code snippet for hotspot {hotspot.key} at line {hotspot.line}")
            code_snippet = get_code_snippet(base_url, token, hotspot.component, hotspot.line, 3)
            
            # If no code snippet was fetched, create a security-focused fallback
            if not code_snippet.strip():
                code_snippet = "No code snippet available for this hotspot."
            
            hotspot.code_snippet = code_snippet
        else:
            log(verbose, f"Hotspot {hotspot.key} has no line number, skipping code snippet")

        hotspots.append(hotspot)

    # Collect unique rule keys from issues and hotspots
    rule_keys = set()
    for issue in issues:
        if issue.rule:
            rule_keys.add(issue.rule)
    for hotspot in hotspots:
        if hotspot.rule_key:
            rule_keys.add(hotspot.rule_key)

    log(verbose, f"📋 Fetching descriptions for {len(rule_keys)} unique rules...")
    
    # Fetch rule descriptions
    rules = get_rules(base_url, token, list(rule_keys), verbose)

    settings: bool = settings_data.get("sonar.multi-quality-mode.enabled", {}).get("value", "true").lower() == "true"

    log(verbose, "Data collection summary:")
    log(verbose, f"   • Project: {project.name}")
    log(verbose, f"   • Issues collected: {len(issues)}")
    log(verbose, f"   • Hotspots collected: {len(hotspots)}")
    log(verbose, f"   • Measures collected: {len(measures)}")
    log(verbose, f"   • MQR mode enabled: {settings}")
    log(verbose, f"   • Issues with code snippets: {sum(1 for i in issues if i.code_snippet and i.code_snippet.strip())}")
    log(verbose, f"   • Hotspots with code snippets: {sum(1 for h in hotspots if h.code_snippet and h.code_snippet.strip())}")
    log(verbose, f"   • Rules descriptions fetched: {len(rules)}")

    return ReportData(
        project=project,
        issues=issues,
        measures=measures,
        hotspots=hotspots,
        quality_gate={},
        quality_profiles=[],
        mode_setting=settings,
        rules=rules
    )