from nicegui import ui, app
from app.ui.theme import frame
from app.models.domain import Owner, UserRole
from app.database import get_session
from app.services.auth import get_password_hash
from sqlmodel import select

def owners_page():
    # Check Permissions
    user_role = app.storage.user.get('role', UserRole.READ.value)
    can_edit = user_role in [UserRole.WRITE.value, UserRole.ADMIN.value]

    # State for editing
    owner_id_ref = {'value': None}

    with ui.dialog() as dialog, ui.card():
        ui.label('Propriétaire').classes('text-xl font-bold')
        name = ui.input('Nom')
        email = ui.input('Email').classes('w-full')
        
        # New Fields
        role_select = ui.select([r.value for r in UserRole], label='Rôle', value=UserRole.READ.value).classes('w-full')
        password_input = ui.input('Mot de passe (Laisser vide pour ne pas changer)', password=True, password_toggle_button=True).classes('w-full')
        
        def save():
            if not can_edit: return
            with next(get_session()) as session:
                if owner_id_ref['value']:
                    # Update
                    owner = session.get(Owner, owner_id_ref['value'])
                    owner.name = name.value
                    owner.email = email.value
                    owner.role = UserRole(role_select.value)
                    if password_input.value:
                        owner.password_hash = get_password_hash(password_input.value)
                else:
                    # Insert
                    pwd = get_password_hash(password_input.value) if password_input.value else None
                    owner = Owner(
                        name=name.value, 
                        email=email.value, 
                        role=UserRole(role_select.value),
                        password_hash=pwd
                    )
                    session.add(owner)
                
                session.commit()
                ui.notify('Propriétaire enregistré')
                dialog.close()
                refresh_table()
        
        def delete_owner():
            if not owner_id_ref['value']: return
            try:
                with next(get_session()) as session:
                    o = session.get(Owner, owner_id_ref['value'])
                    session.delete(o)
                    session.commit()
                ui.notify('Propriétaire supprimé')
                dialog.close()
                refresh_table()
            except Exception:
                ui.notify("Impossible de supprimer (utilisé ailleurs ?)", type='negative')
        
        def cancel():
            dialog.close()

        with ui.row().classes('w-full justify-between'):
            del_btn = ui.button('Supprimer', on_click=delete_owner).classes('bg-red-500 text-white')
            del_btn.visible = False
            
            with ui.row():
                ui.button('Annuler', on_click=cancel).props('flat')
                if can_edit:
                    ui.button('Enregistrer', on_click=save)

    def content():
        def open_create():
            owner_id_ref['value'] = None
            name.value = ''
            email.value = ''
            role_select.value = UserRole.READ.value
            password_input.value = ''
            del_btn.visible = False
            dialog.open()
        
        def open_edit(owner_id):
            owner_id_ref['value'] = owner_id
            del_btn.visible = True
            with next(get_session()) as session:
                o = session.get(Owner, owner_id)
                if o:
                    name.value = o.name
                    email.value = o.email
                    role_select.value = o.role.value
                    password_input.value = '' # Reset
                    dialog.open()

        if can_edit:
            ui.button('Ajouter un Propriétaire', on_click=open_create, icon='add').classes('mb-4 bg-emerald-500 text-white')
        
        columns = [
            {'name': 'name', 'label': 'Nom', 'field': 'name', 'align': 'left', 'sortable': True},
            {'name': 'email', 'label': 'Email', 'field': 'email', 'align': 'left'},
            {'name': 'role', 'label': 'Rôle', 'field': 'role', 'align': 'left'},
            {'name': 'actions', 'label': 'Actions', 'field': 'id'},
        ]
        
        table = ui.table(columns=columns, rows=[], pagination=10).classes('w-full glass-panel')
        
        if can_edit:
            # Add Edit Button Slot
            table.add_slot('body-cell-actions', '''
                <q-td :props="props">
                    <q-btn size="sm" color="primary" round dense icon="edit" @click="$parent.$emit('edit', props.value)" />
                </q-td>
            ''')
            table.on('edit', lambda e: open_edit(e.args))

        def refresh_table_func():
            with next(get_session()) as session:
                owners = session.exec(select(Owner)).all()
                table.rows = [o.model_dump() for o in owners]
                table.update()
                
        refresh_table_func()
        global refresh_table_ref
        refresh_table_ref = refresh_table_func

    frame("Gestion des Propriétaires", content)

refresh_table_ref = None
def refresh_table():
    if refresh_table_ref: refresh_table_ref()
