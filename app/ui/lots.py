from nicegui import ui, app
from app.ui.theme import frame
from app.models.domain import Lot, QuotePart, Owner, UserRole
from app.database import get_session
from sqlmodel import select
from datetime import date
from typing import Optional
from app.services.accounting import resync_lot_allocations

def lots_page():
    # --- EDIT/ADD LOT DIALOG ---
    with ui.dialog() as dialog, ui.card().classes('w-full max-w-4xl h-[90vh]'):
        lot_id_ref = {'value': None} # Mutable to store ID
        qp_id_ref = {'value': None}  # Track if we are editing a fraction
        
        ui.label('Détail du Lot').classes('text-xl font-bold mb-4')
        
        with ui.tabs().classes('w-full') as tabs:
            tab_general = ui.tab('Général')
            tab_fractions = ui.tab('Quote-Parts (Fractions)')
        
        with ui.tab_panels(tabs, value=tab_general).classes('w-full flex-grow'):
            # --- TAB GENERAL ---
            with ui.tab_panel(tab_general):
                name = ui.input('Nom (ex: Appartement A1)')
                l_type = ui.input('Type (ex: Appartement, Cave)')
                desc = ui.textarea('Description')
                
                def save_general():
                    with next(get_session()) as session:
                        if lot_id_ref['value']:
                            lot = session.get(Lot, lot_id_ref['value'])
                            lot.name = name.value
                            lot.type = l_type.value
                            lot.description = desc.value
                        else:
                            lot = Lot(name=name.value, type=l_type.value, description=desc.value)
                            session.add(lot)
                        session.commit()
                        lot_id_ref['value'] = lot.id # Set ID for subsections
                        ui.notify('Lot enregistré')
                        refresh_main_table_func()
                        refresh_fractions_table() # Enable fractions tab content if needed

                def delete_lot():
                    if not lot_id_ref['value']: return
                    try:
                        with next(get_session()) as session:
                             lot = session.get(Lot, lot_id_ref['value'])
                             session.delete(lot)
                             session.commit()
                        ui.notify('Lot supprimé')
                        dialog.close()
                        refresh_main_table_func()
                    except Exception:
                        ui.notify("Impossible de supprimer (utilisé ailleurs ?)", type='negative')

                with ui.row().classes('w-full justify-between mt-4'):
                    del_lot_btn = ui.button('Supprimer', on_click=delete_lot).classes('bg-red-500 text-white')
                    del_lot_btn.visible = False
                    ui.button('Enregistrer Général', on_click=save_general)

            # --- TAB FRACTIONS ---
            with ui.tab_panel(tab_fractions):
                ui.label('Historique des propriétés').classes('text-lg font-bold')
                
                with ui.row().classes('items-end gap-2 mb-4 p-4 border rounded glass-panel'):
                    owners_map = {}
                    with next(get_session()) as session:
                        owners = session.exec(select(Owner)).all()
                        owners_map = {o.id: o.name for o in owners}
                    
                    if not owners_map:
                         ui.label("Créez d'abord des propriétaires !")
                    
                    owner_select = ui.select(owners_map, label='Propriétaire').classes('w-48')
                    num = ui.number('Numérateur', value=1, precision=0).classes('w-24')
                    ui.label('/')
                    den = ui.number('Dénominateur', value=1000, precision=0).classes('w-24')
                    
                    start_d = ui.input('Début (YYYY-MM-DD)', value=date.today().isoformat()).classes('w-32')
                    end_d = ui.input('Fin (Optional)', placeholder='YYYY-MM-DD').classes('w-32')
                    
                    def save_fraction():
                        if not lot_id_ref['value']:
                            ui.notify('Veuillez d\'abord enregistrer le lot (Onglet Général)', type='warning')
                            return
                        
                        try:
                            with next(get_session()) as session:
                                if qp_id_ref['value']:
                                    qp = session.get(QuotePart, qp_id_ref['value'])
                                    qp.owner_id = owner_select.value
                                    qp.numerator = int(num.value)
                                    qp.denominator = int(den.value)
                                    qp.start_date = date.fromisoformat(start_d.value)
                                    qp.end_date = date.fromisoformat(end_d.value) if end_d.value else None
                                else:
                                    qp = QuotePart(
                                        lot_id=lot_id_ref['value'],
                                        owner_id=owner_select.value,
                                        numerator=int(num.value),
                                        denominator=int(den.value),
                                        start_date=date.fromisoformat(start_d.value),
                                        end_date=date.fromisoformat(end_d.value) if end_d.value else None
                                    )
                                    session.add(qp)
                                session.commit()
                            
                            ui.notify('Fraction enregistrée')
                            cancel_edit_fraction()
                            refresh_fractions_table()
                        except Exception as e:
                            ui.notify(f"Erreur: {e}", type='negative')

                    def cancel_edit_fraction():
                        qp_id_ref['value'] = None
                        save_frac_btn.text = 'AJOUTER'
                        cancel_frac_btn.visible = False
                        num.value = 1
                        den.value = 1000
                        start_d.value = date.today().isoformat()
                        end_d.value = None

                    def open_edit_fraction(qp_id):
                        qp_id_ref['value'] = qp_id
                        with next(get_session()) as session:
                            qp = session.get(QuotePart, qp_id)
                            if qp:
                                owner_select.value = qp.owner_id
                                num.value = qp.numerator
                                den.value = qp.denominator
                                start_d.value = qp.start_date.isoformat()
                                end_d.value = qp.end_date.isoformat() if qp.end_date else ''
                                
                                save_frac_btn.text = 'ENREGISTRER'
                                cancel_frac_btn.visible = True

                    def sync_history_fraction():
                        if not lot_id_ref['value']: return
                        with next(get_session()) as session:
                            resync_lot_allocations(session, lot_id_ref['value'])
                        ui.notify('Historique synchronisé avec les nouvelles parts')

                    user_role = app.storage.user.get('role', UserRole.READ.value)
                    can_edit = user_role in [UserRole.WRITE.value, UserRole.ADMIN.value]

                    if can_edit:
                        with ui.row().classes('w-full items-center gap-2'):
                            save_frac_btn = ui.button('AJOUTER', on_click=save_fraction, icon='add').classes('bg-emerald-500 text-white')
                            cancel_frac_btn = ui.button('Annuler', on_click=cancel_edit_fraction).classes('bg-gray-400 text-white')
                            cancel_frac_btn.visible = False
                            ui.space()
                            ui.button('Synchroniser l\'historique', on_click=sync_history_fraction, icon='sync')\
                                .classes('bg-amber-600 text-white')\
                                .tooltip('Recalcule toutes les répartitions de ce lot selon les parts actuelles')

                columns_frac = [
                    {'name': 'owner', 'label': 'Propriétaire', 'field': 'owner_name', 'align': 'left'},
                    {'name': 'fraction', 'label': 'Part', 'field': 'fraction_str', 'align': 'left'},
                    {'name': 'dates', 'label': 'Période', 'field': 'dates_str', 'align': 'left'},
                    {'name': 'actions', 'label': 'Action', 'field': 'id'},
                ]
                
                if not can_edit:
                    columns_frac = [c for c in columns_frac if c['name'] != 'actions']

                table_frac = ui.table(columns=columns_frac, rows=[], pagination=5).classes('w-full')
                
                def delete_fraction(qp_id):
                    with next(get_session()) as session:
                        qp = session.get(QuotePart, qp_id)
                        if qp:
                            session.delete(qp)
                            session.commit()
                            refresh_fractions_table()
                            ui.notify('Supprimé')

                if can_edit:
                    table_frac.add_slot('body-cell-actions', '''
                        <q-td :props="props">
                            <q-btn size="sm" color="primary" round dense icon="edit" class="q-mr-xs" @click="$parent.$emit('edit', props.value)" />
                            <q-btn size="sm" color="negative" round dense icon="delete" @click="$parent.$emit('delete', props.value)" />
                        </q-td>
                    ''')
                    table_frac.on('edit', lambda e: open_edit_fraction(e.args))
                    table_frac.on('delete', lambda e: delete_fraction(e.args))

                def refresh_fractions_table():
                    if not lot_id_ref['value']: 
                        table_frac.rows = []
                        return
                    
                    with next(get_session()) as session:
                        parts = session.exec(select(QuotePart).where(QuotePart.lot_id == lot_id_ref['value'])).all()
                        rows = []
                        for p in parts:
                            o = session.get(Owner, p.owner_id)
                            o_name = o.name if o else "?"
                            rows.append({
                                'id': p.id,
                                'owner_name': o_name,
                                'fraction_str': f"{p.numerator} / {p.denominator}",
                                'dates_str': f"{p.start_date} -> {p.end_date or '...'}"
                            })
                        table_frac.rows = rows
                        table_frac.update()

    # --- MAIN PAGE CONTENT ---
    def content():
        user_role = app.storage.user.get('role', UserRole.READ.value)
        can_edit = user_role in [UserRole.WRITE.value, UserRole.ADMIN.value]

        def open_create():
            lot_id_ref['value'] = None
            name.value = ''
            l_type.value = ''
            desc.value = ''
            del_lot_btn.visible = False
            cancel_edit_fraction()
            refresh_fractions_table()
            dialog.open()
            
        def open_edit(l_id):
            lot_id_ref['value'] = l_id
            del_lot_btn.visible = True
            with next(get_session()) as session:
                l = session.get(Lot, l_id)
                name.value = l.name
                l_type.value = l.type
                desc.value = l.description
            cancel_edit_fraction()
            refresh_fractions_table()
            dialog.open()

        if can_edit:
            ui.button('Ajouter un Lot', on_click=open_create, icon='add').classes('mb-4 bg-emerald-500 text-white')
        
        columns = [
            {'name': 'name', 'label': 'Nom', 'field': 'name', 'align': 'left', 'sortable': True},
            {'name': 'type', 'label': 'Type', 'field': 'type', 'align': 'left'},
            {'name': 'description', 'label': 'Description', 'field': 'description', 'align': 'left'},
            {'name': 'actions', 'label': 'Action', 'field': 'id'},
        ]
        
        if not can_edit:
            columns = [c for c in columns if c['name'] != 'actions']

        table = ui.table(columns=columns, rows=[], pagination=10).classes('w-full glass-panel')
        
        if can_edit:
            table.add_slot('body-cell-actions', '''
                <q-td :props="props">
                    <q-btn size="sm" color="primary" round dense icon="edit" @click="$parent.$emit('edit', props.value)" />
                </q-td>
            ''')
            table.on('edit', lambda e: open_edit(e.args))
        
        def refresh_main_table_func():
            with next(get_session()) as session:
                lots = session.exec(select(Lot)).all()
                table.rows = [l.model_dump() for l in lots]
                table.update()
                
        refresh_main_table_func()
        global refresh_main_table_ref
        refresh_main_table_ref = refresh_main_table_func

    frame("Gestion des Lots", content)

refresh_main_table_ref = None
def refresh_main_table():
    if refresh_main_table_ref: refresh_main_table_ref()
