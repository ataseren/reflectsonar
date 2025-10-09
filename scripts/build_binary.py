#!/usr/bin/env python3
"""
Build script to create a standalone binary of ReflectSonar using PyInstaller.
This script handles the proper configuration for creating a distributable executable.
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

def clean_build_artifacts():
    """Clean up previous build artifacts"""
    artifacts = ['build', 'dist', '__pycache__', '*.spec']
    for artifact in artifacts:
        if artifact.endswith('*'):
            # Handle glob patterns
            for path in Path('.').glob(artifact):
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    shutil.rmtree(path)
        else:
            if os.path.exists(artifact):
                if os.path.isfile(artifact):
                    os.remove(artifact)
                else:
                    shutil.rmtree(artifact)
    print("Cleaned build artifacts")

def create_entry_point():
    """Create entry point script for PyInstaller"""
    entry_content = '''#!/usr/bin/env python3
"""
Entry point script for ReflectSonar binary build.
This script handles the package imports and calls the main function.
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

# Import and run the main function
if __name__ == "__main__":
    from reflectsonar.main import main
    sys.exit(main())
'''
    
    with open('reflectsonar_entry.py', 'w', encoding='utf-8') as f:
        f.write(entry_content)
    print("Created entry point script")

def create_pyinstaller_spec():
    """Create PyInstaller spec file with proper configuration"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['reflectsonar_entry.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/reflectsonar/report/reflect-sonar.png', 'reflectsonar/report'),
    ],
    hiddenimports=[
        'yaml',
        'reportlab.pdfbase',
        'reportlab.pdfbase.pdfmetrics',
        'reportlab.pdfbase._fontdata',
        'reportlab.platypus',
        'reportlab.lib',
        'reportlab.graphics',
        'PIL._tkinter_finder',
        'reflectsonar',
        'reflectsonar.main',
        'reflectsonar.api',
        'reflectsonar.api.get_data',
        'reflectsonar.data',
        'reflectsonar.data.models',
        'reflectsonar.report',
        'reflectsonar.report.pdfgen',
        'reflectsonar.report.utils',
        'reflectsonar.report.cover_page',
        'reflectsonar.report.issues',
        'reflectsonar.report.hotspots',
        'reflectsonar.report.rules',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='reflectsonar',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
    
    with open('reflectsonar.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    print("Created PyInstaller spec file")

def build_binary():
    """Build the binary using PyInstaller"""
    print("Building binary with PyInstaller...")
    
    try:
        # Use the virtual environment's pyinstaller
        venv_pyinstaller = Path('venv/bin/pyinstaller')
        if venv_pyinstaller.exists():
            cmd = [str(venv_pyinstaller), 'reflectsonar.spec']
        else:
            cmd = ['pyinstaller', 'reflectsonar.spec']
        
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Binary built successfully!")
        
        # Check if binary was created (platform-specific)
        if platform.system() == 'Windows':
            binary_path = Path('dist/reflectsonar.exe')
        else:
            binary_path = Path('dist/reflectsonar')
            
        if binary_path.exists():
            print(f"Binary location: {binary_path.absolute()}")
            print(f"Binary size: {binary_path.stat().st_size / (1024*1024):.1f} MB")
        else:
            # Try both possible locations to debug
            exe_path = Path('dist/reflectsonar.exe')
            unix_path = Path('dist/reflectsonar')
            print(f"Error: Binary not found in expected location: {binary_path}")
            print(f"Checked for .exe: {exe_path.exists()} at {exe_path}")
            print(f"Checked for unix: {unix_path.exists()} at {unix_path}")
            # List all files in dist directory for debugging
            dist_dir = Path('dist')
            if dist_dir.exists():
                print(f"Files in dist/: {list(dist_dir.iterdir())}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Error: Build failed: {e}")
        print(f"Error output: {e.stderr}")
        return False
    except FileNotFoundError:
        print("Error: PyInstaller not found. Please install it with: pip install pyinstaller")
        return False
    
    return True

def create_release_info():
    """Create release information file"""
    release_info = """# ReflectSonar Binary Release

This is a standalone binary version of ReflectSonar that doesn't require Python to be installed.

## Usage

```bash
./reflectsonar -p PROJECT_KEY -t SONARQUBE_TOKEN -u SONARQUBE_URL -o output.pdf
```

## Arguments

- `-p, --project`: SonarQube project key (required)
- `-t, --token`: SonarQube authentication token (required) 
- `-u, --url`: SonarQube server URL (default: http://localhost:9000)
- `-o, --output`: Output PDF file path
- `-c, --config`: Path to YAML configuration file
- `-v, --verbose`: Enable verbose logging

## Configuration File

You can use a YAML configuration file instead of command line arguments:

```yaml
project: "your-project-key"
token: "your-sonarqube-token"
url: "http://your-sonarqube-server:9000"
output: "report.pdf"
verbose: true
```

Then run: `./reflectsonar -c config.yaml`

## System Requirements

- Linux x86_64
- No Python installation required
"""
    
    with open('dist/README.txt', 'w', encoding='utf-8') as f:
        f.write(release_info)
    print("Created release information file")

def main():
    """Main build process"""
    print("Starting ReflectSonar binary build process...")
    
    # Change to project root directory (parent of scripts/)
    os.chdir(Path(__file__).parent.parent)
    
    # Clean previous builds
    clean_build_artifacts()
    
    # Create entry point and spec file
    create_entry_point()
    create_pyinstaller_spec()
    
    # Build binary
    if build_binary():
        create_release_info()
        print("\nBuild completed successfully!")
        print("Your binary is ready in the 'dist' directory")
        print("You can distribute the entire 'dist' directory or just the 'reflectsonar' binary")
    else:
        print("\nBuild failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()