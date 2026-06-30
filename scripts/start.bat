@echo off
cd /d %~dp0..
call .\venv\Scripts\activate
start "" python main.py