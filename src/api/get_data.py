import requests
from data.models import SonarQubeProject, SonarQubeIssue, SonarQubeMeasure, SonarQubeHotspot, ReportData
from datetime import datetime
from typing import Dict, List

def get_json(url: str, token: str) -> Dict:
    response = requests.get(url, auth=(token, ""))
    response.raise_for_status()
    return response.json()

def get_code_snippet(base_url: str, token: str, component: str, line: int, context_lines: int = 3) -> str:
    """Fetch code snippet for a specific component and line"""
    try:
        # Calculate line range (line ± context_lines)
        from_line = max(1, line - context_lines)
        to_line = line + context_lines
        
        sources_url = f"{base_url}/api/sources/show?key={component}&from={from_line}&to={to_line}"
        
        try:
            response = get_json(sources_url, token)
        except Exception as api_error:
            print(f"ERROR: API call failed: {api_error}")
            return ""
        
        sources = response.get("sources", [])
        
        if not sources:
            print(f"ERROR: No sources found for {component}:{line}")  # Debug log
            print(f"ERROR: Full API response: {response}")  # Show what we actually got
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
        import traceback
        traceback.print_exc()
        return ""



def fetch_all_hotspots(base_url: str, token: str, project_key: str) -> Dict:
    """Fetch all hotspots from SonarQube with pagination support"""
    all_hotspots = []
    page = 1
    page_size = 500  # Maximum page size
    
    print(f"DEBUG: Starting to fetch all hotspots for project {project_key}")
    
    while True:
        hotspots_url = f"{base_url}/api/hotspots/search?projectKey={project_key}&ps={page_size}&p={page}"
        print(f"DEBUG: Fetching hotspots page {page} with page size {page_size}")
        
        try:
            page_data = get_json(hotspots_url, token)
            page_hotspots = page_data.get("hotspots", [])
            
            print(f"DEBUG: Page {page} returned {len(page_hotspots)} hotspots")
            all_hotspots.extend(page_hotspots)
            
            # Check if we have more pages
            paging = page_data.get("paging", {})
            total = paging.get("total", 0)
            current_total = len(all_hotspots)
            
            print(f"DEBUG: Current total: {current_total}, API total: {total}")
            
            if current_total >= total:
                print(f"DEBUG: Fetched all {current_total} hotspots")
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


def get_report_data(base_url: str, token: str, project_key: str) -> ReportData:

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

    component_data = get_json(component_url, token)
    issues_data = get_json(issues_url, token)
    measures_data = get_json(measures_url, token)
    settings_data = get_json(settings_url, token)
    
    # Fetch ALL hotspots with pagination
    hotspots_data = fetch_all_hotspots(base_url, token, project_key)

    project = SonarQubeProject.from_dict(component_data)

    # Process issues and fetch code snippets
    issues: List[SonarQubeIssue] = []
    total_issues = len(issues_data.get("issues", []))
    print(f"DEBUG: Processing {total_issues} issues...")
    
    for i, issue_data in enumerate(issues_data.get("issues", [])):
        issue = SonarQubeIssue.from_dict(issue_data)
        print(f"DEBUG: Issue {i+1}/{total_issues}: {issue.key}, component: {issue.component}, line: {issue.line}")
        
        # Fetch code snippet if the issue has a line number
        if issue.line:
            print(f"DEBUG: Fetching code snippet for issue {issue.key}")
            code_snippet = get_code_snippet(base_url, token, issue.component, issue.line)
            
            # If no code snippet was fetched, create a more realistic fallback
            if not code_snippet.strip():
                code_snippet = "No code snippet available for this issue."
            
            issue.code_snippet = code_snippet
            print(f"DEBUG: Code snippet result: {'Found' if code_snippet else 'Empty'} ({len(code_snippet)} chars)")
        else:
            print(f"DEBUG: Issue {issue.key} has no line number, skipping code snippet")
            
        issues.append(issue)

    measures: Dict[str, SonarQubeMeasure] = {
        m["metric"]: SonarQubeMeasure.from_dict(m)
        for m in measures_data.get("component", {}).get("measures", [])
    }

    # Process hotspots and fetch code snippets
    hotspots: List[SonarQubeHotspot] = []
    total_hotspots = len(hotspots_data.get("hotspots", []))
    print(f"DEBUG: Processing {total_hotspots} hotspots...")
    
    for i, hotspot_data in enumerate(hotspots_data.get("hotspots", [])):
        hotspot = SonarQubeHotspot.from_dict(hotspot_data)
        print(f"DEBUG: Hotspot {i+1}/{total_hotspots}: {hotspot.key}, component: {hotspot.component}, line: {hotspot.line}")
        
        # Fetch code snippet if the hotspot has a line number
        if hotspot.line:
            print(f"DEBUG: Fetching code snippet for hotspot {hotspot.key}")
            code_snippet = get_code_snippet(base_url, token, hotspot.component, hotspot.line)
            
            # If no code snippet was fetched, create a security-focused fallback
            if not code_snippet.strip():
                code_snippet = "No code snippet available for this hotspot."
            
            hotspot.code_snippet = code_snippet
            print(f"DEBUG: Code snippet result: {'Found' if code_snippet else 'Empty'} ({len(code_snippet)} chars)")
        else:
            print(f"DEBUG: Hotspot {hotspot.key} has no line number, skipping code snippet")
            
        hotspots.append(hotspot)

    settings: bool = settings_data.get("sonar.multi-quality-mode.enabled", {}).get("value", "true").lower() == "true"

    return ReportData(
        project=project,
        issues=issues,
        measures=measures,
        hotspots=hotspots,
        quality_gate={},
        quality_profiles=[],
        mode_setting=settings
    )


#######################
#### Add rules list to the report, maybe at the end
#######################