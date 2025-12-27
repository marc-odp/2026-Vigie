from nicegui import ui, app
from app.ui.theme import frame
from app.models.domain import BankAccount, UserRole
from app.database import get_session
from sqlmodel import select
from decimal import Decimal
from app.utils.formatters import format_currency

def accounts_page():
    # State
    acc_id_ref = {'value': None}

    with ui.dialog() as dialog, ui.card():
        title_label = ui.label('Nouveau Compte Bancaire').classes('text-xl font-bold')
        name = ui.input('Nom (ex: Compte Courant)')
        iban = ui.input('IBAN')
        initial = ui.number('Solde Initial', value=0.0, format='%.2f')
        
        def save():
            with next(get_session()) as session:
                if acc_id_ref['value']:
                    # UPDATE
                    acc = session.get(BankAccount, acc_id_ref['value'])
                    acc.name = name.value
                    acc.iban = iban.value
                    acc.initial_balance = Decimal(str(initial.value))
                else:
                    # INSERT
                    acc = BankAccount(
                        name=name.value, 
                        iban=iban.value, 
                        initial_balance=Decimal(str(initial.value))
                    )
                    session.add(acc)
                
                session.commit()
                ui.notify('Compte enregistré')
                dialog.close()
                refresh_table_func()

        def delete_acc():
            if not acc_id_ref['value']: return
            try:
                with next(get_session()) as session:
                    acc = session.get(BankAccount, acc_id_ref['value'])
                    session.delete(acc)
                    session.commit()
                ui.notify('Compte supprimé')
                dialog.close()
                refresh_table_func()
            except Exception:
                # Likely IntegrityError
                ui.notify("Impossible de supprimer ce compte (probablement utilisé dans des opérations).", type='negative')

        with ui.row().classes('w-full justify-between mt-4'):
            delete_btn = ui.button('Supprimer', on_click=delete_acc).classes('bg-red-500 text-white')
            ui.button('Enregistrer', on_click=save)

    def content():
        # Check Permissions
        user_role = app.storage.user.get('role', UserRole.READ.value)
        can_edit = user_role in [UserRole.WRITE.value, UserRole.ADMIN.value]

        def open_create():
            acc_id_ref['value'] = None
            title_label.text = 'Nouveau Compte'
            name.value = ''
            iban.value = ''
            initial.value = 0.0
            delete_btn.visible = False
            dialog.open()
            
        def open_edit(row_id):
            acc_id_ref['value'] = row_id
            title_label.text = 'Modifier Compte'
            delete_btn.visible = True
            with next(get_session()) as session:
                acc = session.get(BankAccount, row_id)
                if acc:
                    name.value = acc.name
                    iban.value = acc.iban
                    initial.value = float(acc.initial_balance)
                    dialog.open()

        if can_edit:
            ui.button('Ajouter un Compte', on_click=open_create, icon='add').classes('mb-4 bg-emerald-500 text-white')
        
        columns = [
            {'name': 'name', 'label': 'Nom', 'field': 'name', 'align': 'left', 'sortable': True},
            {'name': 'iban', 'label': 'IBAN', 'field': 'iban', 'align': 'left'},
            {'name': 'initial_balance', 'label': 'Solde Initial', 'field': 'initial_balance', 'align': 'right'},
            {'name': 'actions', 'label': 'Actions', 'field': 'id'},
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
        
        def refresh_table_func():
            with next(get_session()) as session:
                accounts = session.exec(select(BankAccount)).all()
                # Convert Decimal to float/str for UI table
                rows = []
                for a in accounts:
                    d = a.model_dump()
                    d['initial_balance'] = format_currency(a.initial_balance)
                    rows.append(d)
                table.rows = rows
                table.update()
                
        refresh_table_func()
        global refresh_table_account_ref
        refresh_table_account_ref = refresh_table_func

    frame("Comptes Bancaires", content)

refresh_table_account_ref = None
def refresh_account_ui():
    if refresh_table_account_ref: refresh_table_account_ref()
