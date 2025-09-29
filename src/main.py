from report.pdfgen import generate_pdf
from api.get_data import get_report_data
import argparse
import sys
import signal
import yaml
import traceback


# Load configuration from YAML file
def load_config(config_path):
    if not config_path:
        return {}
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Warning: Could not load config file {config_path}: {e}")
        return {}

# Parse command-line arguments
def parse_arguments():
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

# Handle Ctrl+C interrupt gracefully
def handle_interrupt(signum, frame):
    print("\n")
    print("🛑 Report generation interrupted by user")
    print("✨ Thanks for using ReflectSonar!")
    sys.exit(0)

# Main function to generate the PDF report
def main():
    signal.signal(signal.SIGINT, handle_interrupt)
    
    try:
        args = parse_arguments()

        if args.config is not None:
            with open(args.config, 'r') as file:
                config = yaml.safe_load(file)

        if args.verbose:
            print("🚀 Starting ReflectSonar PDF Report Generation")
            print(f"📊 Project: {args.project}")
            print(f"🌐 SonarQube URL: {args.url}")
            print(f"📄 Output: {args.output or f'reflect_sonar_report_{args.project}_[timestamp].pdf'}")

        # Fetch data from SonarQube
        if args.verbose:
            print("\n📡 Connecting to SonarQube and fetching data...")
        else:
            print("📡 Fetching data from SonarQube... (Press Ctrl+C to cancel)")
        
        report_data = get_report_data(args.url, args.token, args.project, verbose=args.verbose)

        # Generate PDF report
        if args.verbose:
            print("\n📄 Generating PDF report...")
        else:
            print("📄 Generating PDF report... (Press Ctrl+C to cancel)")
            
        output_file = generate_pdf(report_data, args.output, args.project, verbose=args.verbose)

        # Success message
        print("✅ PDF report generated successfully!")
        print(f"📁 Saved to: {output_file}")
        
        return 0

    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("\n")
        print("🛑 Report generation interrupted by user")
        print("✨ Thanks for using ReflectSonar!")
        return 1
    except ConnectionError as e:
        print("\n🌐 Connection Error: Unable to connect to SonarQube server")
        print(f"❌ {str(e)}")
        print("\n💡 Check your SonarQube URL and network connection")
        return 1
    except PermissionError as e:
        print("\n🔒 Permission Error: Cannot write to output location")
        print(f"❌ {str(e)}")
        print("\n💡 Check file permissions or choose a different output path")
        return 1
    except FileNotFoundError as e:
        print("\n📁 File Not Found: Missing required file")
        print(f"❌ {str(e)}")
        print("\n💡 Ensure all required files (like logo) are in place")
        return 1
    except Exception as e:
        # Handle other errors gracefully
        error_msg = str(e)
        if "401" in error_msg or "Unauthorized" in error_msg:
            print("\n🔐 Authentication Error: Invalid SonarQube token")
            print("💡 Check your token and permissions")
        elif "404" in error_msg or "Not Found" in error_msg:
            print("\n🔍 Project Not Found: Cannot find the specified project")
            print("💡 Verify your project key is correct")
        else:
            print(f"\n❌ Error generating report: {error_msg}")
            
        if args.verbose if 'args' in locals() else False:
            print("\n🔍 Detailed error information:")
            traceback.print_exc()
        else:
            print("\n💡 Run with --verbose for detailed error information")
        return 1


if __name__ == "__main__":
    sys.exit(main())
