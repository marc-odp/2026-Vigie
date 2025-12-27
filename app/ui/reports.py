from nicegui import ui
from app.ui.theme import frame
from app.database import get_session
from app.models.domain import Operation, Allocation
from app.services.export import generate_operations_csv, generate_allocations_csv
from sqlmodel import select

def reports_page():
    def download_ops():
        with next(get_session()) as session:
            # Eager load refs for CSV
            ops = session.exec(select(Operation)).all()
            content = generate_operations_csv(ops)
            ui.download(content.encode('utf-8'), 'operations.csv')

    def download_allocs():
        with next(get_session()) as session:
            allocs = session.exec(select(Allocation)).all()
            content = generate_allocations_csv(allocs)
            ui.download(content.encode('utf-8'), 'allocations.csv')

    def content():
        ui.label('Exports & Rapports').classes('text-xl font-bold mb-4')
        
        with ui.grid(columns=2).classes('w-full gap-4'):
            with ui.card().classes('glass-panel hover:bg-white/5 cursor-pointer'):
                ui.icon('table_view').classes('text-4xl text-emerald-400 mb-2')
                ui.label('Journal des Opérations').classes('text-lg font-bold')
                ui.label('Export CSV de toutes les opérations brutes.').classes('text-sm text-slate-400')
                ui.button('Télécharger CSV', on_click=download_ops).classes('mt-4 bg-emerald-500 w-full')

            with ui.card().classes('glass-panel hover:bg-white/5 cursor-pointer'):
                ui.icon('pie_chart').classes('text-4xl text-cyan-400 mb-2')
                ui.label('Détail des Répartitions').classes('text-lg font-bold')
                ui.label('Export CSV détaille: qui paie quoi pour chaque opération.').classes('text-sm text-slate-400')
                ui.button('Télécharger CSV', on_click=download_allocs).classes('mt-4 bg-cyan-500 w-full')

    frame("Rapports", content)
