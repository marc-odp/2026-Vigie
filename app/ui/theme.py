from nicegui import ui, app
from typing import Callable
from app.database import get_session
from app.models.domain import Owner

def menu_link(text: str, target: str, icon: str):
    # Dynamic text color: slate-500 in light, slate-400 in dark
    with ui.link(target=target).classes('w-full no-underline text-slate-600 dark:text-slate-400 hover:text-emerald-600 dark:hover:text-white transition-colors duration-200'):
        with ui.row().classes('items-center py-1.5 px-2 gap-2 hover:bg-slate-100 dark:hover:bg-white/5 rounded-lg cursor-pointer'):
            ui.icon(icon).classes('text-lg')
            ui.label(text).classes('text-sm font-medium')

def frame(page_title: str, content_func: Callable):
    """
    Main layout for the application (Dark/Light Mode).
    """
    
    # 1. Initialize Theme (from Session/DB)
    user_id = app.storage.user.get('id')
    initial_value = True # Default Dark
    
    if user_id:
        with next(get_session()) as session:
            me = session.get(Owner, user_id)
            if me and me.theme == "LIGHT":
                initial_value = False
    
    # Create the dark mode manager for this page
    dm = ui.dark_mode(value=initial_value)

    # 2. Global Styles
    ui.add_head_html('''
        <style>
            /* BASE VARS */
            :root {
                --bg-grad-dark: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
                --bg-grad-light: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
                --glass-dark: rgba(255, 255, 255, 0.05);
                --glass-light: rgba(255, 255, 255, 0.7);
                --border-dark: rgba(255, 255, 255, 0.1);
                --border-light: rgba(0, 0, 0, 0.1);
            }

            body { 
                font-family: 'Inter', sans-serif;
                margin: 0;
                background: var(--bg-grad-light); /* Default Light */
                color: #0f172a;
                transition: background 0.3s ease;
            }
            
            body.body--dark {
                 background: var(--bg-grad-dark);
                 color: #f8fafc;
            }

            .glass-panel {
                background: var(--glass-light);
                backdrop-filter: blur(10px);
                border: 1px solid var(--border-light);
            }
            body.body--dark .glass-panel {
                background: var(--glass-dark);
                border: 1px solid var(--border-dark);
            }

            /* Quasar overrides for better contrast */
            .q-field--standard .q-field__label { color: #475569 !important; font-weight: 500; }
            body.body--dark .q-field--standard .q-field__label { color: #94a3b8 !important; }
            
            .q-field__native { color: #1e293b !important; }
            body.body--dark .q-field__native { color: #f1f5f9 !important; }

            /* Table Header */
            .q-table th { font-weight: 700; color: #1e293b; font-size: 0.875rem; }
            body.body--dark .q-table th { color: #e2e8f0; }
            
            /* Table Body */
            .q-table tbody td { border-bottom: 1px solid rgba(0,0,0,0.1) !important; color: #1e293b; }
            body.body--dark .q-table tbody td { border-bottom: 1px solid rgba(255,255,255,0.05) !important; color: #f1f5f9; }
            
            /* Table Footer/Pagination */
            .q-table__bottom { color: #1e293b !important; border-top: 1px solid rgba(0,0,0,0.1) !important; }
            body.body--dark .q-table__bottom { color: #e2e8f0 !important; border-top: 1px solid rgba(255,255,255,0.05) !important; }
            
            .q-table__bottom .q-btn, .q-table__bottom .q-select, .q-table__bottom .q-select .q-select__dropdown-icon {
                 color: inherit !important;
            }
            
            .q-field__native, .q-field__label { color: inherit !important; }
            
            .page-container {
                max-width: 1200px;
                margin: 0 auto;
                width: 100%;
            }

            /* Robust Sidebar & Avatar */
            .app-sidebar {
                background-color: #ffffff !important;
            }
            body.body--dark .app-sidebar {
                background-color: #0f172a !important;
            }

            .app-user-avatar {
                background-color: #f1f5f9 !important;
                color: #475569 !important;
            }
            body.body--dark .app-user-avatar {
                background-color: #1e293b !important;
                color: #f8fafc !important;
            }
            
            /* Hide drawer top padding/border if needed */
            .q-drawer-container .q-drawer {
                top: 0 !important;
                padding-top: 56px;
            }
        </style>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    ''')

    # Toggle Handler
    def toggle_theme(e):
        # Update UI state
        new_val = e.value
        dm.value = new_val
        
        # Sync Tailwind dark class
        ui.run_javascript(f'document.body.classList.toggle("dark", {str(new_val).lower()})')
        
        # Persist to DB
        if user_id:
            with next(get_session()) as session:
                me = session.get(Owner, user_id)
                if me:
                    me.theme = "DARK" if new_val else "LIGHT"
                    session.add(me)
                    session.commit()

    # Initial sync on load
    ui.run_javascript(f'document.body.classList.toggle("dark", {str(initial_value).lower()})')

    # HEADER
    with ui.header(elevated=False).classes('bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-gray-200 dark:border-slate-700 h-14 px-4 sm:px-6 flex items-center justify-between'):
        with ui.row().classes('items-center gap-2 sm:gap-4'):
            # Sidebar Toggle
            ui.button(on_click=lambda: drawer.toggle(), icon='menu').props('flat round color=primary').classes('lg:hidden')
            
            with ui.row().classes('items-center gap-2'):
                ui.icon('apartment', color='emerald-500').classes('text-2xl sm:text-3xl')
                ui.label('Vigie').classes('text-xl sm:text-2xl font-bold tracking-tight text-gray-900 dark:text-white')
                ui.label('Indivision Manager').classes('text-xs sm:text-sm text-gray-500 dark:text-slate-400 mt-1 hidden sm:block')

        # Right Side: Year + Theme
        with ui.row().classes('items-center gap-2 sm:gap-4'):
            # Year
            with ui.row().classes('items-center gap-2 hidden xs:flex'):
                ui.icon('calendar_today').classes('text-gray-400')
                ui.select([2024, 2025, 2026], value=2026).classes('w-20 sm:w-24').props('dense options-dense outlined')

            # Theme Switch
            ui.switch(value=dm.value, on_change=toggle_theme).props('checked-icon=dark_mode unchecked-icon=light_mode color=indigo')

    # SIDEBAR (LEFT DRAWER)
    with ui.left_drawer(value=True).classes('app-sidebar border-r border-gray-200 dark:border-slate-800 p-4 gap-2 flex flex-col') as drawer:
        drawer.props('width=280 breakpoint=1024') # Collapses at 1024px
        
        ui.label('NAVIGATION').classes('text-[10px] font-bold text-slate-400 dark:text-slate-500 mb-0.5 px-3 uppercase tracking-tighter')
        menu_link('Tableau de bord', '/', 'dashboard')
        
        ui.label('GESTION').classes('text-[10px] font-bold text-slate-400 dark:text-slate-500 mt-2 mb-0.5 px-3 uppercase tracking-tighter')
        menu_link('Opérations', '/operations', 'receipt_long')
        menu_link('Propriétaires', '/owners', 'group')
        menu_link('Lots & Fractions', '/lots', 'home_work')
        menu_link('Répartition', '/matrix', 'pivot_table_chart')
        
        ui.label('CONFIGURATION').classes('text-[10px] font-bold text-slate-400 dark:text-slate-500 mt-2 mb-0.5 px-3 uppercase tracking-tighter')
        menu_link('Comptes Bancaires', '/accounts', 'account_balance')
        menu_link('Catégories', '/categories', 'category')
        menu_link('Historique', '/logs', 'history')
        menu_link('Exports', '/reports', 'download')

        ui.separator().classes('mt-auto my-2 opacity-50 dark:opacity-20 bg-gray-300 dark:bg-gray-500')
        
        # User Info
        with ui.row().classes('items-center px-4 gap-3 mb-2'):
            ui.avatar(icon='person').classes('app-user-avatar').props('size=sm')
            with ui.column().classes('gap-0'):
                ui.label(app.storage.user.get('name', 'Utilisateur')).classes('text-sm font-bold text-slate-900 dark:text-white')
                ui.label(app.storage.user.get('role', 'Unknown')).classes('text-xs text-slate-400')

        # Logout
        def logout():
            app.storage.user.clear()
            ui.navigate.to('/login')
        
        with ui.item(on_click=logout).classes('text-rose-400 hover:bg-rose-500/10 rounded-lg mx-2 mb-4 cursor-pointer'):
            with ui.item_section().props('avatar'):
                ui.icon('logout')
            with ui.item_section():
                ui.label('Déconnexion')

    # MAIN AREA
    with ui.column().classes('w-full transition-colors duration-300 bg-gray-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100 min-h-screen pt-14'): 
        with ui.column().classes('px-4 pb-4 pt-1 sm:px-6 sm:pb-6 sm:pt-2 overflow-y-auto page-container'):
            ui.label(page_title).classes('text-xl sm:text-2xl font-bold mb-4 bg-gradient-to-r from-emerald-500 to-cyan-500 text-transparent bg-clip-text')
            content_func()
