"""
Data models for SonarQube entities
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class SonarQubeIssue:
    """Represents a SonarQube issue"""
    key: str
    component: str
    project: str
    rule: str
    severity: str
    status: str
    message: str
    type: str
    line: Optional[int] = None
    effort: Optional[str] = None
    author: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    creation_date: Optional[datetime] = None
    update_date: Optional[datetime] = None
    impacts: List[Dict[str, Any]] = field(default_factory=list)
    code_snippet: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SonarQubeIssue':
        """Create an issue object from a dictionary"""
        return cls(
            key=data.get('key', ''),
            component=data.get('component', ''),
            project=data.get('project', ''),
            rule=data.get('rule', ''),
            severity=data.get('severity', ''),
            status=data.get('status', ''),
            message=data.get('message', ''),
            type=data.get('type', ''),
            line=data.get('line'),
            effort=data.get('effort'),
            author=data.get('author'),
            tags=data.get('tags', []),
            creation_date=data.get('creationDate')
                if data.get('creationDate') else None,
            update_date=data.get('updateDate')
                if data.get('updateDate') else None,
            impacts=data.get('impacts', [])
        )


@dataclass
class SonarQubeMeasure:
    """Represents a SonarQube measure"""
    metric: str
    value: Any
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SonarQubeMeasure':
        """Create a measure object from a dictionary"""
        return cls(
            metric=data.get('metric', ''),
            value=data.get('value') or data.get('period', {}).get('value')
        )


@dataclass
class SonarQubeProject:
    """Represents a SonarQube project"""
    key: str
    name: str
    qualifier: str
    visibility: str
    last_analysis_date: Optional[datetime] = None
    revision: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SonarQubeProject':
        """Create a project object from a dictionary"""
        component = data.get('component', {})
        return cls(
            key=component.get('key', ''),
            name=component.get('name', ''),
            qualifier=component.get('qualifier', ''),
            visibility=component.get('visibility', ''),
            last_analysis_date=component.get('analysisDate')
                if component.get('analysisDate') else None,
            revision=component.get('revision')
        )


@dataclass
class SonarQubeHotspot:
    """Represents a SonarQube security hotspot"""
    key: str
    component: str
    project: str
    rule: str
    status: str
    message: str
    line: Optional[int] = None
    author: Optional[str] = None
    creation_date: Optional[datetime] = None
    update_date: Optional[datetime] = None
    vulnerability_probability: str = "MEDIUM"
    code_snippet: Optional[str] = None
    security_category: Optional[str] = None
    rule_name: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SonarQubeHotspot':
        """Create a hotspot object from a dictionary"""
        return cls(
            key=data.get('key', ''),
            component=data.get('component', ''),
            project=data.get('project', ''),
            rule=data.get('rule', ''),
            status=data.get('status', ''),
            message=data.get('message', ''),
            line=data.get('line'),
            author=data.get('author'),
            creation_date=data.get('creationDate')
                if data.get('creationDate') else None,
            update_date=data.get('updateDate')
                if data.get('updateDate') else None,
            vulnerability_probability=data.get('vulnerabilityProbability', 'MEDIUM'),
            security_category=data.get('securityCategory'),
            rule_name=data.get('ruleName')
        )


@dataclass
class ReportData:
    """Container for all data needed for the report"""
    project: SonarQubeProject
    issues: List[SonarQubeIssue]
    measures: Dict[str, SonarQubeMeasure]
    hotspots: List[SonarQubeHotspot]
    quality_gate: Dict[str, Any]
    quality_profiles: List[Dict[str, Any]]
    mode_setting: bool