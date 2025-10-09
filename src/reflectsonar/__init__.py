"""
ReflectSonar - PDF Report Generator for SonarQube Analysis

ReflectSonar is a Python tool for generating PDF reports from SonarQube analysis data.
It reads data via the SonarQube API and generates comprehensive PDF reports for 
general metrics, issues, and security hotspots.

Author: Ata Seren
License: MIT
"""

__version__ = "1.0.0"
__author__ = "Ata Seren"
__email__ = "ata.seren@hotmail.com"
__license__ = "GPL-3.0"

from .main import main

__all__ = ["main"]