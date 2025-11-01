@echo off
echo ========================================
echo Installing Dissertation Dependencies
echo ========================================

echo.
echo Installing core packages...
pip install pandas numpy scipy matplotlib seaborn plotly statsmodels openpyxl

echo.
echo Installing Jupyter...
pip install jupyter notebook ipykernel

echo.
echo Installing Streamlit...
pip install streamlit

echo.
echo Installing web scraping tools...
pip install requests beautifulsoup4

echo.
echo Installing WRDS (optional)...
pip install wrds sqlalchemy psycopg2-binary

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo To start Jupyter: jupyter notebook
echo To start Dashboard: streamlit run dashboard/app.py
echo.
pause