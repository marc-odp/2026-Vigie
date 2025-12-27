from nicegui import ui, app
from app.ui.theme import frame
from app.models.domain import Operation, Owner
from app.database import get_session
from sqlmodel import select
from collections import defaultdict
from decimal import Decimal
from app.utils.formatters import format_currency, short_name

def matrix_page():
    """
    Displays a global matrix table (Pivot).
    """
    def content():
        with next(get_session()) as session:
            # Load Data
            ops = session.exec(select(Operation).order_by(Operation.date.desc())).all()
            owners = session.exec(select(Owner).order_by(Owner.name)).all()
            
            # 1. Base Columns
            columns = [
                {'name': 'date', 'label': 'Date', 'field': 'date', 'sortable': True, 'align': 'left', 'classes': 'min-w-[100px]'},
                {'name': 'label', 'label': 'Libellé', 'field': 'label', 'align': 'left', 'classes': 'truncate max-w-[200px]'},
                {'name': 'lot', 'label': 'Lot', 'field': 'lot', 'align': 'left', 'classes': 'text-slate-400'},
                {'name': 'total', 'label': 'Total', 'field': 'total_fmt', 'sortable': True, 'align': 'right', 'classes': 'font-bold'},
            ]
            
            rows = []
            totals = defaultdict(Decimal)
            grand_total = Decimal(0)
            
            # 2. Calculate Rows & Totals
            for op in ops:
                sign = -1 if op.type == "SORTIE" else 1
                amount = op.amount * sign
                grand_total += amount
                
                row = {
                    'date': op.date.isoformat(),
                    'label': op.label,
                    'lot': op.lot.name if op.lot else "-",
                    'total_fmt': format_currency(amount, show_sign=True),
                }
                
                for o in owners:
                    # Find alloc for this owner
                    alloc = next((a for a in op.allocations if a.owner_id == o.id), None)
                    val = Decimal(0)
                    if alloc:
                        val = alloc.amount * sign
                    
                    totals[o.id] += val
                    # row[f'owner_{o.id}_fmt'] = f"{val:+,.2f}" if val != 0 else ""
                    row[f'owner_{o.id}_fmt'] = format_currency(val, show_sign=True, include_symbol=False) if val != 0 else ""
                
                rows.append(row)

            # 3. Filter Active Owners (Total != 0)
            # Use abs(total) > 0 to capture positive/negative balances, ignore strict 0.
            active_owners = [o for o in owners if totals[o.id] != 0]

            # 4. Add Columns for Active Owners
            for o in active_owners:
                columns.append({
                    'name': f'owner_{o.id}',
                    'label': short_name(o.name),
                    'field': f'owner_{o.id}_fmt',
                    'align': 'right',
                    'headerClasses': 'text-indigo-700 dark:text-indigo-200 bg-indigo-50 dark:bg-slate-800',
                    'classes': 'bg-slate-100 dark:bg-slate-800/20 font-mono text-xs'
                })
                
            # 5. Density-Optimized Summary Bar
            with ui.row().classes('w-full items-center gap-4 mb-3 p-3 glass-panel rounded-xl border-emerald-500/20 shadow-sm'):
                # Global Balance (Prominent but thin)
                with ui.column().classes('gap-0 border-r border-slate-200 dark:border-slate-800 pr-4'):
                    ui.label('SOLDE GLOBAL').classes('text-[9px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest')
                    ui.label(format_currency(grand_total, show_sign=True)).classes('text-2xl font-black text-slate-900 dark:text-white leading-none')
                
                # Owner Balances (Horizontal scrolling or wrapping badges)
                with ui.row().classes('flex-grow gap-3 items-center overflow-x-auto no-scrollbar'):
                    for o in active_owners:
                        val = totals[o.id]
                        color = 'text-emerald-500' if val >= 0 else 'text-rose-500'
                        bg_color = 'bg-emerald-500/5' if val >= 0 else 'bg-rose-500/5'
                        with ui.row().classes(f'items-center gap-2 px-3 py-1 rounded-full {bg_color} border border-current opacity-80'):
                            ui.label(short_name(o.name)).classes('text-[10px] font-bold text-slate-600 dark:text-slate-300 uppercase')
                            ui.label(format_currency(val, show_sign=True)).classes(f'text-xs font-bold {color}')

            # Main Table
            ui.table(columns=columns, rows=rows, pagination=50).classes('w-full glass-panel').props('dense flat separator=cell')

    frame("Matrice de Répartition", content)
