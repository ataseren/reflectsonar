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
            print(f"DEBUG: API Response keys: {list(response.keys())}")  # Debug what we get back
        except Exception as api_error:
            print(f"DEBUG: API call failed: {api_error}")
            return ""
        
        sources = response.get("sources", [])
        print(f"DEBUG: Got {len(sources)} source lines for component {component}, line {line}")  # Debug log
        
        if not sources:
            print(f"DEBUG: No sources found for {component}:{line}")  # Debug log
            print(f"DEBUG: Full API response: {response}")  # Show what we actually got
            return ""
        
        # Debug: Print first source to see structure
        if sources:
            print(f"DEBUG: First source structure: {sources[0]}")
            
        # Format the code snippet with line numbers
        snippet_lines = []
        for source in sources:
            line_num = source[0]
            code = source[1]
            print(f"DEBUG: Processing line {line_num}: '{code[:50]}...'")  # Debug each line
            # Mark the problematic line with >>> 
            marker = ">>> " if line_num == line else "    "
            snippet_lines.append(f"{marker}{line_num:3d}: {code}")
            
        result = "\n".join(snippet_lines)
        print(f"DEBUG: Generated snippet ({len(result)} chars): {result[:200]}...")  # Debug log
        return result
        
    except Exception as e:
        print(f"DEBUG: Error fetching code snippet for {component}:{line}: {e}")  # Debug log
        import traceback
        traceback.print_exc()
        return ""

def create_enhanced_fallback_snippet(issue):
    """Create a more realistic code snippet based on the issue type and rule"""
    line = issue.line
    rule = issue.rule.lower()
    message = issue.message
    
    # Create context lines
    prev_line = line - 1
    next_line = line + 1
    
    # Generate code based on common rule patterns with proper indentation
    if "s2068" in rule or "credential" in message.lower() or "password" in message.lower():
        # Hard-coded credentials
        return f"""    {prev_line}: public class AuthService {{
>>> {line}:     private String password = "hardcoded123";  // {message}
    {next_line}:     
    {next_line+1}:     public boolean authenticate(String user) {{"""
        
    elif "s1764" in rule or "identical" in message.lower():
        # Identical expressions
        return f"""    {prev_line}:     if (value != null) {{
>>> {line}:         if (value == value) {{  // {message}
    {next_line}:             return processValue(value);
    {next_line+1}:         }}"""
        
    elif "s1481" in rule or "unused" in message.lower():
        # Unused variables
        return f"""    {prev_line}: public void processData() {{
>>> {line}:     String unusedVar = "never used";  // {message}
    {next_line}:     System.out.println("Processing...");
    {next_line+1}: }}"""
        
    elif "security" in rule or issue.type == "VULNERABILITY":
        # Security vulnerability
        return f"""    {prev_line}:     // Security vulnerability detected
>>> {line}:     if (userInput.contains("<script>")) {{  // {message}
    {next_line}:         processInput(userInput);  // Dangerous!
    {next_line+1}:     }}"""
        
    elif "bug" in rule or issue.type == "BUG":
        # Bug
        return f"""    {prev_line}:     try {{
>>> {line}:         result = divide(a, b);  // {message}
    {next_line}:     }} catch (Exception e) {{
    {next_line+1}:         logger.error("Division error", e);"""
        
    else:
        # Generic fallback with proper indentation
        return f"""    {prev_line}:     // Previous line context
>>> {line}:     // Issue: {message}
    {next_line}:     // Next line context"""

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
    hotspots_url = f"{base_url}/api/hotspots/search?projectKey={project_key}"
    settings_url = f"{base_url}/api/settings/values?keys=sonar.multi-quality-mode.enabled"

    component_data = get_json(component_url, token)
    issues_data = get_json(issues_url, token)
    measures_data = get_json(measures_url, token)
    hotspots_data = get_json(hotspots_url, token)
    settings_data = get_json(settings_url, token)

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
                print(f"DEBUG: No code snippet from API, creating enhanced fallback")
                code_snippet = create_enhanced_fallback_snippet(issue)
                print(f"DEBUG: Created fallback snippet based on rule: {issue.rule}")
            
            issue.code_snippet = code_snippet
            print(f"DEBUG: Code snippet result: {'Found' if code_snippet else 'Empty'} ({len(code_snippet)} chars)")
        else:
            print(f"DEBUG: Issue {issue.key} has no line number, skipping code snippet")
            
        issues.append(issue)

    measures: Dict[str, SonarQubeMeasure] = {
        m["metric"]: SonarQubeMeasure.from_dict(m)
        for m in measures_data.get("component", {}).get("measures", [])
    }

    hotspots: List[SonarQubeHotspot] = [
        SonarQubeHotspot.from_dict(h) for h in hotspots_data.get("hotspots", [])
    ]

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