from report.pdfgen import generate_pdf
from api.get_data import get_report_data
import argparse

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Generate PDF reports from SonarQube data')
    parser.add_argument('-c', '--config', default='config.yaml',
                        help='Path to configuration file (default: config.yaml)')
    parser.add_argument('-o', '--output', help='Output PDF file path')
    parser.add_argument('-p', '--project', help='SonarQube project key', required=True)
    parser.add_argument('-u', '--url', help='SonarQube server URL', default="http://localhost:9000")
    parser.add_argument('-t', '--token', help='SonarQube authentication token', required=True)
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    return parser.parse_args()

args = parse_arguments()

if args.verbose:
    print(f"🚀 Starting ReflectSonar PDF Report Generation")
    print(f"📊 Project: {args.project}")
    print(f"🌐 SonarQube URL: {args.url}")
    print(f"📄 Output: {args.output or f'reflect_sonar_report_{args.project}_[timestamp].pdf'}")

report_data = get_report_data(args.url, args.token, args.project, verbose=args.verbose)

generate_pdf(report_data, args.output, args.project, verbose=args.verbose)

if args.verbose:
    print(f"✅ PDF report generation completed successfully!")
