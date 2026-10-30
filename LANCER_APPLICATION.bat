@echo off
title Hello Pizza - Tableau de bord
cd /d "%~dp0"
echo Lancement de l application Hello Pizza...
python -m streamlit run app.py
pause
