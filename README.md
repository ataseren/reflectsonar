# ReflectSonar

**PDF Report Generator for SonarQube Analysis**

ReflectSonar is a simple Python tool for generating a PDF report of a project scan conducted by a SonarQube instance. It reads the data via API and generates a PDF report for general metrics, issues and security hotspots.

SonarQube Community and Developer Editions do not have report generationn feature. The purpose of this tool is adding this functionality to these editions.

This tool is not affiliated with Sonar. The report is generated based on SonarQube instance that its information is provided. All data is fetched from
SonarQube API. ReflectSonar just provides a way to generate the report.



##= Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/ataseren/reflectsonar.git
cd reflectsonar

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```bash
# Generate a report for your project
python src/main.py -p "your-project-key" -t "your-sonarqube-token" -u "http://your-sonarqube-server:9000"

# With custom output path
python src/main.py -p "my-app" -t "squ_abc123..." -o "reports/my-app-quality-report.pdf"

# With verbose logging
python src/main.py -p "my-app" -t "squ_abc123..." --verbose
```

## Command Line Options

| Option | Short | Description | Required | Default |
|--------|-------|-------------|----------|---------|
| `--project` | `-p` | SonarQube project key | ✅ Yes | - |
| `--token` | `-t` | SonarQube authentication token | ✅ Yes | - |
| `--url` | `-u` | SonarQube server URL | ❌ No | `http://localhost:9000` |
| `--output` | `-o` | Output PDF file path | ❌ No | Auto-generated |
| `--config` | `-c` | Configuration file path | ❌ No | `config.yaml` |
| `--verbose` | `-v` | Enable detailed logging | ❌ No | `False` |

## Configuration

### SonarQube Token Setup

1. **Generate Token**: Go to SonarQube → My Account → Security → Generate Tokens
2. **Token Format**: `squ_1a2b3c4d5e6f7g8h9i0j...` (User Token)
3. **Permissions**: Ensure token has "Browse" permission on your project


## Report Structure

### 1. **Cover Page**
- Project overview and summary statistics
- Quality metrics and ratings
- Generation timestamp and SonarQube mode

### 2. **Security Issues**
- Vulnerabilities sorted by severity
- Security hotspots with risk assessment
- Code snippets showing problematic areas

### 3. **Reliability Issues**  
- Bugs and reliability concerns
- Impact analysis and severity breakdown
- Complete file paths for easy navigation

### 4. **Maintainability Issues**
- Code smells and technical debt
- Maintainability ratings and trends
- Actionable improvement recommendations

### 5. **Security Hotspots**
- Detailed security hotspot analysis
- Risk categories and remediation guidance
- Code context and security implications


## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

Have an idea for improvement? We'd love to hear it!
-  Enhanced visualizations and charts
-  Multi-project portfolio reports  
-  Web interface for report generation
-  Integration with Jira/Slack/Teams
-  Historical trend analysis

[Open an issue](https://github.com/ataseren/reflectsonar/issues) to discuss your ideas!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
