from nicegui import ui, app
from app.database import create_db_and_tables
from app.ui.dashboard import dashboard_page
from app.ui.owners import owners_page
from app.ui.accounts import accounts_page
from app.ui.lots import lots_page
from app.ui.operations import operations_page
from app.ui.reports import reports_page
from app.ui.login import login_page
from app.ui.logs import logs_page
from app.ui.categories import categories_page

# Auth Guard
def check_auth():
    if not app.storage.user.get('authenticated', False):
        ui.navigate.to('/login')
        return False
    return True

@ui.page('/login')
def login():
    login_page()

@ui.page('/')
def index():
    if check_auth():
        dashboard_page()

@ui.page('/owners')
def owners():
    if check_auth():
        owners_page()

@ui.page('/accounts')
def accounts():
    if check_auth():
        accounts_page()

@ui.page('/lots')
def lots():
    if check_auth():
        lots_page()

@ui.page('/operations')
def operations():
    if check_auth():
        operations_page()

@ui.page('/matrix')
def matrix():
    if check_auth():
        from app.ui.matrix import matrix_page
        matrix_page()

@ui.page('/reports')
def reports():
    if check_auth():
        reports_page()

@ui.page('/logs')
def logs():
    if check_auth():
        logs_page()

@ui.page('/categories')
def categories():
    if check_auth():
        categories_page()

import os
from app.services.bootstrap import bootstrap_data

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(PROJECT_ROOT, 'static')

def main():
    create_db_and_tables()
    bootstrap_data()
    
    storage_secret = os.getenv('VIGIE_STORAGE_SECRET', 'vigie_secure_key')
    port = int(os.getenv('VIGIE_PORT', 8080))
    
    # Serve static files (including favicon)
    app.add_static_files('/static', STATIC_DIR)
    
    ui.run(
        title="Vigie", 
        show=False, 
        port=port, 
        storage_secret=storage_secret,
        favicon=os.path.join(STATIC_DIR, 'favicon.png')
    )

if __name__ in {"__main__", "__mp_main__"}:
    main()
