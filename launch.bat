@echo off
title von-triage - defect severity scorer
cd /d "%~dp0"
python launch.py
if errorlevel 1 pause
