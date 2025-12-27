from nicegui import ui, app
from app.ui.theme import frame
from app.database import get_session
from app.models.domain import Category, Operation, OperationType
from sqlmodel import select, func
from app.audit import log_action

def categories_page():
    table = None # Reference for refresh
    
    def get_categories_with_usage():
        with next(get_session()) as session:
            # Join with operation to see usage count
            statement = select(
                Category, 
                func.count(Operation.id).label('usage_count')
            ).outerjoin(Operation).group_by(Category.id)
            results = session.exec(statement).all()
            return [
                {
                    **cat.dict(),
                    'usage_count': count
                }
                for cat, count in results
            ]

    def add_category():
        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.label('Ajouter une catégorie').classes('text-lg font-bold mb-2')
            name_input = ui.input('Nom').classes('w-full').props('autofocus')
            type_select = ui.select(
                {OperationType.ENTREE: 'Entrée (Revenu)', OperationType.SORTIE: 'Sortie (Dépense)'}, 
                label='Type par défaut', 
                value=OperationType.SORTIE
            ).classes('w-full')
            is_rev_checkbox = ui.checkbox('Reversement direct (sans lot)').classes('mb-2')
            desc_input = ui.input('Description').classes('w-full')
            
            with ui.row().classes('w-full justify-end mt-4'):
                ui.button('Annuler', on_click=dialog.close).props('flat')
                async def save():
                    if not name_input.value:
                        ui.notify('Le nom est requis', type='negative')
                        return
                    
                    with next(get_session()) as session:
                        new_cat = Category(
                            name=name_input.value,
                            type=type_select.value,
                            is_reversement=is_rev_checkbox.value,
                            description=desc_input.value
                        )
                        session.add(new_cat)
                        try:
                            session.commit()
                            log_action(app.storage.user.get('name', 'System'), 'CREATE_CATEGORY', f'Nom: {new_cat.name}')
                            ui.notify(f'Catégorie "{new_cat.name}" ajoutée')
                            dialog.close()
                            refresh_table()
                        except Exception as e:
                            session.rollback()
                            ui.notify(f'Erreur: {e}', type='negative')
                
                ui.button('Enregistrer', on_click=save).props('elevated color=primary')
        dialog.open()

    def edit_category(cat_data):
        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.label('Modifier la catégorie').classes('text-lg font-bold mb-2')
            name_input = ui.input('Nom', value=cat_data['name']).classes('w-full')
            type_select = ui.select(
                {OperationType.ENTREE: 'Entrée (Revenu)', OperationType.SORTIE: 'Sortie (Dépense)'}, 
                label='Type par défaut', 
                value=cat_data['type']
            ).classes('w-full')
            is_rev_checkbox = ui.checkbox('Reversement direct (sans lot)', value=cat_data.get('is_reversement', False)).classes('mb-2')
            desc_input = ui.input('Description', value=cat_data['description']).classes('w-full')
            
            with ui.row().classes('w-full justify-end mt-4'):
                ui.button('Annuler', on_click=dialog.close).props('flat')
                async def save():
                    with next(get_session()) as session:
                        cat = session.get(Category, cat_data['id'])
                        if cat:
                            cat.name = name_input.value
                            cat.type = type_select.value
                            cat.is_reversement = is_rev_checkbox.value
                            cat.description = desc_input.value
                            session.add(cat)
                            session.commit()
                            log_action(app.storage.user.get('name', 'System'), 'UPDATE_CATEGORY', f'ID: {cat.id}, Nom: {cat.name}')
                            ui.notify('Catégorie mise à jour')
                            dialog.close()
                            refresh_table()
                
                ui.button('Mettre à jour', on_click=save).props('elevated color=primary')
        dialog.open()

    async def delete_category(cat_data):
        if cat_data['usage_count'] > 0:
            ui.notify('Impossible de supprimer une catégorie utilisée par des opérations', type='warning')
            return
        
        async with ui.dialog() as dialog, ui.card():
            ui.label(f'Supprimer la catégorie "{cat_data["name"]}" ?').classes('text-lg font-bold')
            with ui.row().classes('w-full justify-end mt-4'):
                ui.button('Annuler', on_click=dialog.close).props('flat')
                async def confirm():
                    with next(get_session()) as session:
                        cat = session.get(Category, cat_data['id'])
                        if cat:
                            session.delete(cat)
                            session.commit()
                            log_action(app.storage.user.get('name', 'System'), 'DELETE_CATEGORY', f'Nom: {cat.name}')
                            ui.notify('Catégorie supprimée')
                            dialog.close()
                            refresh_table()
                ui.button('Supprimer', on_click=confirm).props('elevated color=negative')
        dialog.open()

    def refresh_table():
        table.rows[:] = get_categories_with_usage()
        table.update()

    def content():
        nonlocal table
        with ui.column().classes('w-full gap-4'):
            # Header Row
            with ui.row().classes('w-full justify-between items-center glass-panel p-4 rounded-xl shadow-sm'):
                with ui.row().classes('items-center gap-3'):
                    ui.icon('category', color='primary').classes('text-2xl')
                    with ui.column().classes('gap-0'):
                        ui.label('Gestion des Catégories').classes('text-lg font-bold text-slate-900 dark:text-slate-100')
                        ui.label('Configurez les types de revenus et dépenses').classes('text-xs text-slate-500 dark:text-slate-400')
                
                ui.button('Ajouter une catégorie', icon='add', on_click=add_category).props('elevated color=emerald').classes('rounded-lg')

            # Table
            columns = [
                {'name': 'name', 'label': 'Nom', 'field': 'name', 'required': True, 'align': 'left', 'sortable': True},
                {'name': 'type', 'label': 'Type par défaut', 'field': 'type', 'required': True, 'align': 'left', 'sortable': True},
                {'name': 'is_reversement', 'label': 'Rév. Direct', 'field': 'is_reversement', 'align': 'center'},
                {'name': 'description', 'label': 'Description', 'field': 'description', 'align': 'left', 'sortable': True},
                {'name': 'usage_count', 'label': 'Utilisations', 'field': 'usage_count', 'align': 'center', 'sortable': True},
                {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'align': 'right'}
            ]
            
            rows = get_categories_with_usage()
            
            with ui.card().classes('w-full shadow-lg border border-slate-200 dark:border-slate-700'):
                table = ui.table(columns=columns, rows=rows, row_key='id').classes('w-full')
                
                table.add_slot('body-cell-type', r'''
                    <q-td :props="props">
                        <q-badge :color="props.value === 'ENTREE' ? 'emerald' : 'orange'" outline>
                            {{ props.value === 'ENTREE' ? 'Entrée' : 'Sortie' }}
                        </q-badge>
                    </q-td>
                ''')

                table.add_slot('body-cell-is_reversement', r'''
                    <q-td :props="props" class="text-center">
                        <q-icon :name="props.value ? 'check_circle' : 'cancel'" 
                                :color="props.value ? 'emerald' : 'grey-4'" size="sm" />
                    </q-td>
                ''')

                table.add_slot('body-cell-actions', '''
                    <q-td :props="props" class="text-right">
                        <q-btn flat round size="sm" icon="edit" color="primary" @click="$parent.$emit('edit', props.row)" />
                        <q-btn flat round size="sm" icon="delete" :color="props.row.usage_count > 0 ? 'grey' : 'negative'" 
                               :disable="props.row.usage_count > 0" @click="$parent.$emit('delete', props.row)">
                            <q-tooltip v-if="props.row.usage_count > 0">Utilisée par des opérations</q-tooltip>
                        </q-btn>
                    </q-td>
                ''')
                
                table.on('edit', lambda e: edit_category(e.args))
                table.on('delete', lambda e: delete_category(e.args))

    frame('Catégories', content)
