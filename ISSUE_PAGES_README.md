# ReflectSonar - Enhanced PDF Report Features

## New Issue Pages with Dual SonarQube Mode Support

The ReflectSonar PDF report now includes detailed issue pages organized by software quality impact categories with automatic detection and support for both SonarQube modes:

### 📋 Issue Sections

1. **Security Issues** - Contains vulnerabilities and security-related issues
2. **Reliability Issues** - Contains bugs and reliability problems  
3. **Maintainability Issues** - Contains code smells and maintainability concerns

### 🎯 Features

#### Issue Categorization
- Issues are automatically categorized based on SonarQube's issue types:
  - **Security**: `VULNERABILITY` type + security-tagged issues
  - **Reliability**: `BUG` type issues
  - **Maintainability**: `CODE_SMELL` type issues

#### SonarQube Mode Detection
The report automatically detects and adapts to your SonarQube instance mode:

**Standard Mode** (Classic SonarQube):
- Uses traditional severity levels: BLOCKER, CRITICAL, MAJOR, MINOR, INFO
- Categorizes issues by type: VULNERABILITY, BUG, CODE_SMELL

**MQR Mode** (Multi-Quality Rule):
- Uses impact-based severity: HIGH, MEDIUM, LOW  
- Categorizes issues by software quality impacts
- Displays both classic and impact severities

#### Severity Sorting
Issues within each section are sorted by severity (most critical first):

**Standard Mode:**
1. BLOCKER (highest priority)
2. CRITICAL
3. MAJOR
4. MINOR
5. INFO (lowest priority)

**MQR Mode:**
1. HIGH (highest priority)
2. MEDIUM
3. LOW (lowest priority)

#### Visual Elements
- **Colored severity badges** - Each issue has a color-coded severity indicator
- **Issue count summaries** - Shows total count and breakdown by severity
- **Structured tables** - Clean tabular format with file, rule, and message info

### 📊 Report Structure

```
Page Layout:
├── Logo (Top Left Corner - all pages)
├── Page Number (Bottom Right - all pages)

Page 1: Cover Page
├── SonarQube SAST Report (Centered Title)
├── Project overview
├── Quality metrics dashboard
└── Summary statistics

Page 2+: Issue Details
├── SonarQube Mode Detection
├── Security Issues
│   ├── Summary (count by severity)
│   └── Detailed issue table
├── Reliability Issues  
│   ├── Summary (count by severity)
│   └── Detailed issue table
└── Maintainability Issues
    ├── Summary (count by severity)
    └── Detailed issue table
```

### 🎨 Table Format

Each issue table includes:
- **Severity Badge**: Color-coded circular badge with severity level
- **File Location**: Filename and line number (when available)
- **Rule & Message**: SonarQube rule name and detailed issue description

### 🔧 Technical Implementation

#### New Functions Added:
- `detect_sonarqube_mode()` - Auto-detects Standard vs MQR mode
- `get_issues_by_impact_category()` - Categorizes issues by quality impact (mode-aware)
- `get_severity_order()` - Provides sorting order for both severity systems
- `get_severity_color()` - Returns color mapping for both severity systems
- `get_severity_list()` - Returns appropriate severity list for mode
- `severity_badge()` - Creates colored severity indicators (mode-aware)
- `create_issue_table()` - Generates formatted issue tables (mode-aware)
- `create_issue_section()` - Creates complete sections with summaries (mode-aware)

#### Color Scheme:

**Standard Mode:**
- **BLOCKER**: Red (#D50000)
- **CRITICAL**: Deep Orange (#FF5722)  
- **MAJOR**: Orange (#FF9800)
- **MINOR**: Amber (#FFC107)
- **INFO**: Blue (#2196F3)

**MQR Mode:**
- **HIGH**: Red (#D50000)
- **MEDIUM**: Orange (#FF9800)
- **LOW**: Blue (#2196F3)

### 📝 Usage

The enhanced report is generated automatically when running:
```bash
python src/main.py -u <sonarqube_url> -t <token> -p <project_key>
```

### 🧪 Testing

Use the test script to validate functionality:
```bash
python test_report.py
```

This will test issue categorization and severity ordering without requiring a SonarQube connection.