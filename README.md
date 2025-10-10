# ReflectSonar

<p align="center">
  <img src="https://raw.githubusercontent.com/ataseren/reflectsonar/refs/heads/main/rs-logo.png" width="400" alt="reflectsonar-logo">
</p>

**PDF Report Generator for SonarQube Analysis**

ReflectSonar is a simple Python tool for generating a PDF report of a project scan conducted by a SonarQube instance. It reads the data via API and generates a PDF report for general metrics, issues and security hotspots.

SonarQube Community and Developer Editions do not have report generationn feature. The purpose of this tool is adding this functionality to these editions.

This tool is not affiliated with Sonar. The report is generated based on SonarQube instance that its information is provided. All data is fetched from
SonarQube API. ReflectSonar just provides a way to generate the report.

## Quick Start

### Installation

#### Option 1: Install from PyPI

```bash
# Install ReflectSonar
pip install reflectsonar

# Run directly
reflectsonar -p "your-project-key" -t "your-token" -u "http://your-sonarqube:9000"
```

#### Option 2: Download Pre-built Binary

Download the latest binary release for your platform from the [Releases page](https://github.com/ataseren/reflectsonar/releases):

**Linux:**
```bash
# Download and extract
wget https://github.com/ataseren/reflectsonar/releases/latest/download/reflectsonar-linux-x64.tar.gz
tar -xzf reflectsonar-linux-x64.tar.gz

# Make executable and run
chmod +x reflectsonar
./reflectsonar --help
```

**Windows:**
```powershell
# Download reflectsonar-windows-x64.zip from releases page
# Extract and run reflectsonar.exe
.\reflectsonar.exe --help
```

**macOS:**
```bash
# Download and extract
wget https://github.com/ataseren/reflectsonar/releases/latest/download/reflectsonar-macos-x64.tar.gz
tar -xzf reflectsonar-macos-x64.tar.gz

# Make executable and run  
chmod +x reflectsonar
./reflectsonar --help
```

#### Option 3: Install from Source

```bash
# Clone the repository
git clone https://github.com/ataseren/reflectsonar.git
cd reflectsonar

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

#### Using the Binary (Recommended)

```bash
# Generate a report for your project
./reflectsonar -p "your-project-key" -t "your-sonarqube-token" -u "http://your-sonarqube-server:9000"

# With custom output path
./reflectsonar -p "my-app" -t "squ_abc123..." -o "reports/my-app-quality-report.pdf"

# With verbose logging
./reflectsonar -p "my-app" -t "squ_abc123..." --verbose

# Using a configuration file
./reflectsonar -c config.yaml
```

#### Using Python Source

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

- **Generate Token**: Go to SonarQube → My Account → Security → Generate Tokens (It must be a User Token)
- **Token Format**: `squ_1a2b3c4d5e6f7g8h9i0j...` 
- **Permissions**: Ensure token has enough permission on your project

## Report Structure

### 1. **Cover Page**
- Project overview and summary statistics
- Quality metrics and ratings
- Generation timestamp and SonarQube mode

### 2. **Issues**
- Security, reliability and maintainability issues
- Affected code snippets and triggered rules

### 3. **Security Hotspots**
- Detailed security hotspot analysis
- Risk categories and remediation guidance
- Code context and security implications

### 4. Rules
- Rules triggered by the issues in a project
- Mitigation and detailed description for the issue
- Extra resources

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

[Open an issue](https://github.com/ataseren/reflectsonar/issues) to discuss your ideas! Submit a PR in any way you want.

I am trying to make life easier for peoples' that need the functionality of this tool. Therefore, I don't want to bother you with strict contribution rules. Just open an issue or PR and I will be happy to review it. 

Also, feel free to reach out to me via email or LinkedIn.

## License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.
