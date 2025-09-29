# Module to fetch data from SonarQube API
from typing import Dict, List
from data.models import SonarQubeProject, SonarQubeIssue, SonarQubeMeasure, SonarQubeHotspot, ReportData
import requests
import traceback

# Helper function to make authenticated GET requests
def get_json(url: str, token: str) -> Dict:
    response = requests.get(url, auth=(token, ""))
    response.raise_for_status()
    return response.json()

# Function to fetch code snippet for a specific issue or hotspot
def get_code_snippet(base_url: str, token: str, component: str, line: int, context_lines: int = 3) -> str:
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
            page_data = get_json(hotspots_url, token)
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

    if verbose:
        print("Fetching project component data...")
    component_data = get_json(component_url, token)
    
    if verbose:
        print("Fetching issues data...")
    issues_data = get_json(issues_url, token)
    
    if verbose:
        print("Fetching measures data...")
    measures_data = get_json(measures_url, token)
    
    if verbose:
        print("Fetching SonarQube settings...")
    settings_data = get_json(settings_url, token)
    
    if verbose:
        print("Fetching security hotspots (with pagination)...")
    hotspots_data = fetch_all_hotspots(base_url, token, project_key)

    project = SonarQubeProject.from_dict(component_data)

    # Process issues and fetch code snippets
    issues: List[SonarQubeIssue] = []
    total_issues = len(issues_data.get("issues", []))
    
    if verbose:
        print(f"Processing {total_issues} issues and fetching code snippets...")
    
    for i, issue_data in enumerate(issues_data.get("issues", [])):
        issue = SonarQubeIssue.from_dict(issue_data)
        
        if verbose and (i + 1) % 10 == 0:  # Progress every 10 issues
            print(f"   Processed {i + 1}/{total_issues} issues...")
        
        # Fetch code snippet if the issue has a line number
        if issue.line:
            if verbose and total_issues <= 20:  # Show detail for small datasets
                print(f"      Fetching code snippet for {issue.key} at line {issue.line}")
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
    
    if verbose:
        print(f"Processing {total_hotspots} security hotspots and fetching code snippets...")
    
    for i, hotspot_data in enumerate(hotspots_data.get("hotspots", [])):
        hotspot = SonarQubeHotspot.from_dict(hotspot_data)
        
        if verbose and (i + 1) % 5 == 0:  # Progress every 5 hotspots
            print(f"   Processed {i + 1}/{total_hotspots} hotspots...")
        
        # Fetch code snippet if the hotspot has a line number
        if hotspot.line:
            if verbose and total_hotspots <= 10:  # Show detail for small datasets
                print(f"      Fetching code snippet for hotspot {hotspot.key} at line {hotspot.line}")
            code_snippet = get_code_snippet(base_url, token, hotspot.component, hotspot.line, 3)
            
            # If no code snippet was fetched, create a security-focused fallback
            if not code_snippet.strip():
                code_snippet = "No code snippet available for this hotspot."
            
            hotspot.code_snippet = code_snippet
        else:
            if verbose:
                print(f"Hotspot {hotspot.key} has no line number, skipping code snippet")

        hotspots.append(hotspot)

    settings: bool = settings_data.get("sonar.multi-quality-mode.enabled", {}).get("value", "true").lower() == "true"

    if verbose:
        print("Data collection summary:")
        print(f"   • Project: {project.name}")
        print(f"   • Issues collected: {len(issues)}")
        print(f"   • Hotspots collected: {len(hotspots)}")
        print(f"   • Measures collected: {len(measures)}")
        print(f"   • MQR mode enabled: {settings}")
        print(f"   • Issues with code snippets: {sum(1 for i in issues if i.code_snippet and i.code_snippet.strip())}")
        print(f"   • Hotspots with code snippets: {sum(1 for h in hotspots if h.code_snippet and h.code_snippet.strip())}")

    return ReportData(
        project=project,
        issues=issues,
        measures=measures,
        hotspots=hotspots,
        quality_gate={},
        quality_profiles=[],
        mode_setting=settings
    )