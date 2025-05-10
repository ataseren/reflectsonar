import requests
from data.models import SonarQubeProject, SonarQubeIssue, SonarQubeMeasure, SonarQubeHotspot, ReportData
from datetime import datetime
from typing import Dict, List

def get_json(url: str, token: str) -> Dict:
    response = requests.get(url, auth=(token, ""))
    response.raise_for_status()
    return response.json()

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

    component_data = get_json(component_url, token)
    issues_data = get_json(issues_url, token)
    measures_data = get_json(measures_url, token)
    hotspots_data = get_json(hotspots_url, token)

    project = SonarQubeProject.from_dict(component_data)

    issues: List[SonarQubeIssue] = [
        SonarQubeIssue.from_dict(i) for i in issues_data.get("issues", [])
    ]

    measures: Dict[str, SonarQubeMeasure] = {
        m["metric"]: SonarQubeMeasure.from_dict(m)
        for m in measures_data.get("component", {}).get("measures", [])
    }

    hotspots: List[SonarQubeHotspot] = [
        SonarQubeHotspot.from_dict(h) for h in hotspots_data.get("hotspots", [])
    ]

    return ReportData(
        project=project,
        issues=issues,
        measures=measures,
        hotspots=hotspots,
        quality_gate={},
        quality_profiles=[]
    )


#######################
#### Add rules list to the report, maybe at the end
#######################