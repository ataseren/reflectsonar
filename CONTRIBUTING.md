# Contributing to ReflectSonar

Welcome to ReflectSonar! We appreciate your interest in contributing to this PDF report generator for SonarQube analysis. This document provides a comprehensive guide to the codebase architecture, development setup, and contribution guidelines.

## Table of Contents

- [Project Overview](#project-overview)
- [Code Hierarchy](#code-hierarchy)
- [Development Setup](#development-setup)
- [Contribution Workflow](#contribution-workflow)
- [Code Guidelines](#code-guidelines)
- [Testing](#testing)
- [Documentation](#documentation)

## Project Overview

ReflectSonar is a Python-based PDF report generator that connects to SonarQube instances via API to extract analysis data and generate comprehensive PDF reports. The tool is designed to provide reporting functionality for SonarQube Community and Developer Editions, which lack built-in report generation features.

## Code Hierarchy

### Root Directory Structure
```
reflectsonar/
├── src/                     # Main source code
├── config.yaml.example     # Configuration template
├── requirements.txt         # Python dependencies
├── README.md               # Project documentation
├── LICENSE                 # License information
├── rs-logo.png            # Project logo
└── example_api.json       # Sample API response structure
```

### Source Code Structure (`src/`)
```
src/
├── main.py                 # Application entry point
├── api/                    # SonarQube API interaction layer
│   └── get_data.py        # API client and data fetching logic
├── data/                   # Data models and structures
│   └── models.py          # SonarQube entity models
└── report/                 # PDF report generation
    ├── pdfgen.py          # Main PDF generation orchestrator
    ├── utils.py           # Utility functions and custom flowables
    ├── cover_page.py      # Cover page generation
    ├── issues.py          # Issues section generation
    ├── hotspots.py        # Security hotspots section generation
    └── reflect-sonar.png  # Report logo
```

## File Definitions and Responsibilities

### `/src/main.py`
**Purpose**: Application entry point and command-line interface
**Key Functions**:
- `parse_arguments()`: Command-line argument parsing with YAML config support
- `load_config(config_path)`: YAML configuration file loading
- `main()`: Application orchestration and error handling
- Signal handling for graceful interruption

**Dependencies**: 
- `argparse` for CLI parsing
- `yaml` for configuration management
- `report.pdfgen` for PDF generation
- `api.get_data` for SonarQube data fetching

---

### `/src/api/get_data.py`
**Purpose**: SonarQube API client and data transformation layer
**Key Functions**:
- `get_json(url, token)`: Authenticated HTTP requests to SonarQube API
- `get_code_snippet()`: Fetches source code context for issues/hotspots
- `get_report_data()`: Main orchestrator for fetching all required data
- `get_project_component()`: Project metadata retrieval
- `get_issues()`: Issues data with pagination support
- `get_measures()`: Quality metrics and measures
- `get_hotspots()`: Security hotspots with pagination

**Data Processing**:
- Handles both Standard and MQR mode detection
- Implements pagination for large datasets
- Processes code snippets with syntax highlighting markers
- Transforms API responses into internal data models

---

### `/src/data/models.py`
**Purpose**: Data models and structures for SonarQube entities
**Key Classes**:

#### `SonarQubeIssue`
```python
@dataclass
class SonarQubeIssue:
    key: str                    # Unique issue identifier
    component: str              # File/component path
    project: str                # Project key
    rule: str                   # SonarQube rule identifier
    severity: str               # Issue severity (BLOCKER, CRITICAL, etc.)
    status: str                 # Issue status (OPEN, CLOSED, etc.)
    message: str                # Issue description
    type: str                   # Issue type (BUG, VULNERABILITY, CODE_SMELL)
    line: Optional[int]         # Source code line number
    effort: Optional[str]       # Estimated fix effort
    author: Optional[str]       # Issue author
    tags: List[str]             # Associated tags
    creation_date: Optional[datetime]
    update_date: Optional[datetime]
    impacts: List[Dict[str, Any]]  # MQR mode impact information
    code_snippet: Optional[str]   # Source code context
```

#### `SonarQubeHotspot`
```python
@dataclass  
class SonarQubeHotspot:
    key: str                    # Unique hotspot identifier
    component: str              # File/component path
    project: str                # Project key
    security_category: str      # Security category
    vulnerability_probability: str  # Risk probability (HIGH, MEDIUM, LOW)
    status: str                 # Review status
    line: Optional[int]         # Source code line number
    message: str                # Hotspot description
    rule: str                   # Security rule identifier
    code_snippet: Optional[str] # Source code context
```

#### `SonarQubeMeasure`
```python
@dataclass
class SonarQubeMeasure:
    metric: str                 # Metric key (e.g., 'lines', 'bugs')
    value: str                  # Metric value
    component: str              # Associated component
```

#### `ReportData`
```python
@dataclass
class ReportData:
    project: SonarQubeProject   # Project information
    issues: List[SonarQubeIssue]  # All issues
    hotspots: List[SonarQubeHotspot]  # Security hotspots
    measures: Dict[str, SonarQubeMeasure]  # Quality measures
    mode_setting: bool          # MQR mode flag
```

---

### `/src/report/pdfgen.py`
**Purpose**: Main PDF generation orchestrator
**Key Functions**:
- `generate_pdf()`: Primary PDF generation function
- `add_header_footer()`: Page header/footer callback function

**Report Structure**:
1. Cover page with project overview and quality metrics
2. Security issues section with categorized issues
3. Reliability issues section
4. Maintainability issues section  
5. Security hotspots section

---

### `/src/report/utils.py`
**Purpose**: Utility functions, custom flowables, and shared styling
**Key Classes**:

#### `BookmarkFlowable`
Creates PDF bookmarks in the document outline
```python
class BookmarkFlowable(Flowable):
    def __init__(self, title, level=0):
        # Creates bookmark at current location
```

#### `SeverityBookmarkFlowable`
Creates severity-specific bookmarks linking to anchors
```python
class SeverityBookmarkFlowable(Flowable):
    def __init__(self, title, anchor_id, level=1):
        # Links bookmarks to specific severity locations
```

#### `ParagraphWithAnchor`
Extended Paragraph class that embeds bookmark anchors
```python
class ParagraphWithAnchor(Paragraph):
    def __init__(self, text, style, anchor_id=None):
        # Embeds anchors at precise table cell locations
```

#### `CircleBadge`
Custom flowable for colored severity/grade badges
```python
class CircleBadge(Flowable):
    def __init__(self, letter, radius=12, color=HexColor("#D50000")):
        # Creates circular badges for visual indicators
```

**Utility Functions**:
- `get_severity_order()`: Severity sorting logic for both Standard and MQR modes
- `get_severity_color()`: Color mapping for severity levels
- `severity_badge()`: Creates severity badges for tables
- `badge()`: Creates quality grade badges
- `score_to_grade()`: Converts numeric scores to letter grades
- `draw_logo()`: Logo rendering with transparency support

**Style Definitions**:
- Pre-configured paragraph styles for consistent formatting
- Color schemes for different severity levels
- Typography settings for headers, body text, and metadata

---

### `/src/report/cover_page.py`
**Purpose**: Cover page generation with project overview
**Key Functions**:
- `generate_cover_page()`: Main cover page generation
- Quality metrics display with grade badges
- Project information layout
- SonarQube mode detection and display

**Content Sections**:
1. Project title and metadata
2. Quality gate status
3. Key metrics (bugs, vulnerabilities, code smells)
4. Lines of code and technical debt
5. Mode indicator (Standard/MQR)

---

### `/src/report/issues.py`
**Purpose**: Issues section generation with advanced bookmark functionality
**Key Functions**:

#### `get_issues_by_impact_category()`
Filters issues by impact category (Security, Reliability, Maintainability)
- Supports both legacy type-based and MQR impact-based categorization
- Handles graceful fallback for older SonarQube versions

#### `create_issue_table()`
Generates formatted issue tables with embedded anchors
- **Smart Path Formatting**: Breaks long file paths for readability
- **Code Snippet Integration**: Embeds syntax-highlighted code context
- **Anchor Embedding**: Places invisible anchors at first occurrence of each severity
- **Severity Sorting**: Orders issues by severity priority
- **HTML Sanitization**: Cleans message content to prevent parsing conflicts

#### `create_issue_section()`  
Orchestrates complete issue sections
- **Summary Generation**: Creates severity count summaries
- **Bookmark Management**: Places severity-specific bookmarks with anchor linking
- **Layout Management**: Handles spacing and section structure

---

### `/src/report/hotspots.py`
**Purpose**: Security hotspots section generation  
**Key Functions**:
- `create_hotspot_table()`: Generates security hotspot tables
- `generate_security_hotspots_page()`: Complete hotspots section orchestration

## Development Setup

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)
- Access to a SonarQube instance

### Installation
```bash
# Clone the repository
git clone https://github.com/ataseren/reflectsonar.git
cd reflectsonar

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration
1. Copy `config.yaml.example` to `config.yaml`
2. Update configuration with your SonarQube details:
```yaml
project: "your-project-key"
token: "your-sonarqube-token"
url: "http://your-sonarqube-instance:9000"
output: "report.pdf"
verbose: true
```

## Contribution Workflow

### 1. Fork and Branch
```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/your-username/reflectsonar.git
cd reflectsonar

# Create feature branch
git checkout -b feature/your-feature-name
```

### 2. Development
- Follow the existing code structure and naming conventions
- Add appropriate documentation for new functions/classes
- Include type hints for function parameters and return values
- Update this CONTRIBUTION.md if you add new modules or significantly change architecture

### 3. Testing
```bash
# Activate virtual environment
source venv/bin/activate

# Test with real SonarQube data
python src/main.py -p your-project -t your-token -o test-report.pdf --verbose

# Verify PDF generation and bookmark functionality
```

### 4. Submit Pull Request
- Ensure code follows existing style conventions
- Include description of changes and rationale
- Reference any related issues
- Ensure all tests pass

## Code Guidelines

### Style Conventions
- **PEP 8 Compliance**: Follow Python style guidelines
- **Type Hints**: Use type annotations for function signatures
- **Docstrings**: Document all public functions and classes
- **Comments**: Use inline comments for complex logic
- **Naming**: Use descriptive variable and function names

### Error Handling
- Use try-catch blocks for external API calls
- Provide meaningful error messages
- Implement graceful degradation when possible
- Log errors appropriately with context

### Performance Considerations
- Use pagination for large datasets
- Implement caching where appropriate
- Optimize PDF generation for large reports
- Monitor memory usage with large code snippet collections

## Testing

### Manual Testing Checklist
- [ ] PDF generation completes without errors
- [ ] All sections render correctly
- [ ] Bookmarks navigate to correct locations
- [ ] Severity-level bookmarks point to first occurrences
- [ ] Code snippets display properly
- [ ] Logo and styling appear correctly
- [ ] Both Standard and MQR modes work
- [ ] Configuration file loading works
- [ ] Command-line arguments override config properly

### Test Data
- Use projects with diverse issue types and severities
- Test with both small and large projects
- Verify with different SonarQube versions
- Test both authenticated and unauthenticated scenarios

## Documentation

### Code Documentation
- All public functions must have docstrings
- Include parameter descriptions and return value types  
- Document complex algorithms or business logic
- Update this CONTRIBUTION.md for architectural changes

### User Documentation
- Update README.md for user-facing changes
- Include examples for new configuration options
- Document any new command-line arguments
- Provide troubleshooting guidance for common issues

## Questions and Support

For questions about contributing or the codebase:
1. Check existing GitHub issues
2. Create a new issue with the "question" label
3. Provide context and relevant code snippets
4. Follow up on discussions promptly

Thank you for contributing to ReflectSonar! Your contributions help improve PDF reporting for the SonarQube community.