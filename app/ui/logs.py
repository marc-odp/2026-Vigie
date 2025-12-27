import os
import re
from datetime import datetime
from nicegui import ui
from app.ui.theme import frame

def parse_log_line(line: str):
    """
    Parses a log line in the format:
    YYYY-MM-DD HH:MM:SS - USER: user_name | ACTION: action | DETAILS: details
    """
    pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - USER: (.*?) \| ACTION: (.*?) \| DETAILS: (.*)$'
    match = re.match(pattern, line.strip())
    if match:
        return {
            'timestamp': match.group(1),
            'user': match.group(2),
            'action': match.group(3),
            'details': match.group(4)
        }
    return None

def logs_page():
    def get_logs():
        log_file = "logs/audit.log"
        if not os.path.exists(log_file):
            return []
        
        try:
            with open(log_file, "r", encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            
            # Parse lines and reverse to show latest first
            parsed_logs = []
            for line in lines:
                parsed = parse_log_line(line)
                if parsed:
                    parsed_logs.append(parsed)
            
            return parsed_logs[::-1]
        except Exception as e:
            ui.notify(f"Erreur lors de la lecture des logs: {e}", type='negative')
            return []

    def content():
        with ui.column().classes('w-full gap-4'):
            # Stats / Info Row - Using 'glass-panel' for better dark mode support
            with ui.row().classes('w-full justify-between items-center glass-panel p-4 rounded-xl shadow-sm'):
                with ui.row().classes('items-center gap-3'):
                    ui.icon('history', color='primary').classes('text-2xl')
                    with ui.column().classes('gap-0'):
                        ui.label('Historique des Actions').classes('text-lg font-bold text-slate-900 dark:text-slate-100')
                        ui.label('Suivi des modifications effectuées dans l\'application').classes('text-xs text-slate-500 dark:text-slate-400')
                
                ui.button('Rafraîchir', icon='refresh', on_click=lambda: table.update_rows(get_logs())).props('flat color=primary')

            # Table
            columns = [
                {'name': 'timestamp', 'label': 'Date', 'field': 'timestamp', 'required': True, 'align': 'left', 'sortable': True},
                {'name': 'user', 'label': 'Utilisateur', 'field': 'user', 'required': True, 'align': 'left', 'sortable': True},
                {'name': 'action', 'label': 'Action', 'field': 'action', 'required': True, 'align': 'left', 'sortable': True},
                {'name': 'details', 'label': 'Détails', 'field': 'details', 'required': True, 'align': 'left'}
            ]
            
            rows = get_logs()
            
            with ui.card().classes('w-full shadow-lg border border-slate-200 dark:border-slate-700'):
                table = ui.table(columns=columns, rows=rows, row_key='timestamp').classes('w-full')
                table.add_slot('header', r'''
                    <q-tr :props="props">
                        <q-th v-for="col in props.cols" :key="col.name" :props="props">
                            {{ col.label }}
                        </q-th>
                    </q-tr>
                ''')
                
                # Custom cell rendering for better look
                table.add_slot('body-cell-user', r'''
                    <q-td :props="props">
                        <q-badge color="indigo-5" outline>
                            {{ props.value }}
                        </q-badge>
                    </q-td>
                ''')
                
                table.add_slot('body-cell-action', r'''
                    <q-td :props="props">
                        <span class="font-bold">{{ props.value }}</span>
                    </q-td>
                ''')

    frame('Historique', content)
