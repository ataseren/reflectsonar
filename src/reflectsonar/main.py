"""
Main entry point for the ReflectSonar PDF report generator.
Handles command-line arguments, configuration loading, 
and orchestrates the report generation process.
"""
import argparse
import sys
import signal
import yaml

from .report.pdfgen import generate_pdf
from .report.utils import log, handle_exception
from .api.get_data import get_report_data

def load_config(config_path):
    """Loads configuration from a YAML file"""
    if not config_path:
        return {}
    try:
        with open(config_path, 'r',  encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e: # pylint: disable=broad-exception-caught
        print(f"Warning: Could not load config file {config_path}: {e}")
        return {}

def parse_arguments():
    """Parses command-line arguments and loads configuration from a YAML file if provided"""
    parser = argparse.ArgumentParser(description='Generate PDF reports from SonarQube data')
    parser.add_argument('-c', '--config', default=None,
            help='Path to YAML configuration file, overrides arguments if provided in the file')
    parser.add_argument('-o', '--output', help='Output PDF file path')
    parser.add_argument('-p', '--project', help='SonarQube project key')
    parser.add_argument('-u', '--url', help='SonarQube server URL', default="http://localhost:9000")
    parser.add_argument('-t', '--token', help='SonarQube authentication token')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    # Load config file and override args if config values exist
    if args.config:
        config = load_config(args.config)
        if 'project' in config:
            args.project = config['project']
        if 'token' in config:
            args.token = config['token']
        if 'url' in config:
            args.url = config['url']
        if 'output' in config:
            args.output = config['output']
        if 'verbose' in config:
            args.verbose = config['verbose']

    # Validate required fields
    if not args.project:
        parser.error('Project key is required (use -p or set in config file)')
    if not args.token:
        parser.error('SonarQube token is required (use -t or set in config file)')

    return args

def handle_interrupt(signum, frame): # pylint: disable=unused-argument
    """Handles keyboard interrupt (Ctrl+C)"""
    print("\n")
    print("🛑 Report generation interrupted by user")
    print("✨ Thanks for using ReflectSonar!")
    sys.exit(0)

# Main function to generate the PDF report
def main():
    """Main function to generate the PDF report"""
    signal.signal(signal.SIGINT, handle_interrupt)

    try:
        args = parse_arguments()

        log(args.verbose, "🚀 Starting ReflectSonar PDF Report Generation")
        log(args.verbose, f"📊 Project: {args.project}")
        log(args.verbose, f"🌐 SonarQube URL: {args.url}")
        log(args.verbose, f"📄 Output: {args.output or f'reflect_sonar_report_{args.project}_[timestamp].pdf'}") # pylint: disable=line-too-long

        # Fetch data from SonarQube
        log(args.verbose, "📡 Connecting to SonarQube and fetching data...")
        print("📡 Fetching data from SonarQube... (Press Ctrl+C to cancel)")

        report_data = get_report_data(args.url, args.token, args.project, verbose=args.verbose)

        print("📄 Generating PDF report... (Press Ctrl+C to cancel)")

        output_file = generate_pdf(report_data, args.output, args.project, verbose=args.verbose)

        # Success message
        print("✅ PDF report generated successfully!")
        print(f"📁 Saved to: {output_file}")

        return 0

    except Exception as e:  # pylint: disable=broad-exception-caught
        return handle_exception(e, args.verbose)

if __name__ == "__main__":
    sys.exit(main())
