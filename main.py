import flet as ft
from borrar_duplicados import find_duplicates, delete_file
from app import organize_folder
from cambiar_tamaño import resize_single_image
import os

def main(page: ft.Page):
    # 1. Configuración de página
    page.title = "Automatización de Tareas"
    page.window.width = 1000
    page.window.height = 700
    page.padding = 0
    page.bgcolor = ft.Colors.BLACK
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(
        color_scheme_seed=ft.Colors.BLUE,
        visual_density=ft.VisualDensity.COMFORTABLE,
    )

    # 2. Estado
    state = {
        "current_duplicates": [],
        "current_view": "duplicates",
        "selected_folder": "",
        "organize_input_folder": "",
        "resize_input_folder": "",
        "resize_output_folder": "",
    }

    # 3. Definición de controles UI (declaración temprana para ser usados en funciones)
    selected_dir_text = ft.Text("No se ha seleccionado ninguna carpeta", size=14, color=ft.Colors.BLUE_200)
    organize_selected_text = ft.Text("No se ha seleccionado ninguna carpeta", color=ft.Colors.BLUE_200)
    
    result_text = ft.Text("", color=ft.Colors.BLUE_200)
    organize_result_text = ft.Text("", color=ft.Colors.BLUE_200)

    # Listas
    duplicates_list = ft.ListView(expand=True, spacing=8, padding=0, auto_scroll=False)

    # Botones
    delete_all_btn = ft.ElevatedButton(
        "Eliminar todos",
        icon=ft.Icons.DELETE_SWEEP,
        bgcolor=ft.Colors.RED_900,
        color=ft.Colors.WHITE,
        visible=False,
        disabled=True,
    )

    # 4. Funciones Manejadoras (Lógica)
    
    # --- Lógica de Duplicados ---
    def scan_and_show_duplicates(e=None):
        folder = state["selected_folder"]
        if not folder or not os.path.isdir(folder):
            result_text.value = "Selecciona una carpeta válida."
            result_text.color = ft.Colors.RED_400
            result_text.update()
            delete_all_btn.visible = False
            delete_all_btn.disabled = True
            delete_all_btn.update()
            return

        duplicates = find_duplicates(folder)
        state["current_duplicates"] = duplicates

        duplicates_list.controls.clear()
        if not duplicates:
            result_text.value = "No se encontraron archivos duplicados."
            result_text.color = ft.Colors.GREEN_400
            delete_all_btn.visible = False
            delete_all_btn.disabled = True
        else:
            result_text.value = f"Se encontraron {len(duplicates)} archivos duplicados."
            result_text.color = ft.Colors.ORANGE_400
            delete_all_btn.visible = True
            delete_all_btn.disabled = False
            
            for dup, orig in duplicates:
                def make_delete_fn(dup_file):
                    return lambda _ev: delete_and_refresh(dup_file)
                
                item = ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.COPY, color=ft.Colors.BLUE_200, size=18),
                            ft.Text(f"Duplicado: {dup}\nOriginal: {orig}", color=ft.Colors.BLUE_200, expand=True, no_wrap=False),
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                tooltip="Eliminar este duplicado",
                                icon_color=ft.Colors.WHITE,
                                bgcolor=ft.Colors.RED_900,
                                on_click=make_delete_fn(dup),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                    padding=8, 
                    border_radius=6,
                    bgcolor=ft.Colors.with_opacity(0.10, ft.Colors.WHITE),
                )
                duplicates_list.controls.append(item)

        duplicates_list.update()
        result_text.update()
        delete_all_btn.update()

    def delete_and_refresh(dup_file):
        if delete_file(dup_file):
            state["current_duplicates"] = [item for item in state["current_duplicates"] if item[0] != dup_file]
            scan_and_show_duplicates()
        else:
            result_text.value = f"Error al eliminar: {dup_file}"
            result_text.color = ft.Colors.RED_400
            result_text.update()

    def perform_delete_all(e=None):
        if not state["current_duplicates"]: return
        
        delete_all_btn.disabled = True
        delete_all_btn.text = "Eliminando..."
        delete_all_btn.update()

        to_delete = [dup for dup, _ in state["current_duplicates"]]
        ok = fail = 0
        for dup in to_delete:
            try:
                if delete_file(dup): ok += 1
                else: fail += 1
            except: fail += 1

        scan_and_show_duplicates()
        if fail == 0:
            result_text.value = f"Eliminados {ok} duplicados correctamente."
            result_text.color = ft.Colors.GREEN_400
        else:
            result_text.value = f"Eliminados {ok}. Fallaron {fail}."
            result_text.color = ft.Colors.ORANGE_400
        
        delete_all_btn.text = "Eliminar todos"
        result_text.update()

    delete_all_btn.on_click = perform_delete_all

    # --- Lógica de FilePickers ---
    def handle_folder_picker_result(e: ft.FilePickerResultEvent):
        if e.path:
            state["selected_folder"] = e.path
            selected_dir_text.value = f"Carpeta seleccionada: {e.path}"
            selected_dir_text.update()
            scan_and_show_duplicates()

    def handle_organize_picker_result(e: ft.FilePickerResultEvent):
        if e.path:
            state["organize_input_folder"] = e.path
            organize_selected_text.value = f"Carpeta a organizar: {e.path}"
            organize_selected_text.update()

    # --- Lógica de Organizar ---
    def run_organize(_ev=None):
        folder = state.get("organize_input_folder") or ""
        if not folder or not os.path.isdir(folder):
            organize_result_text.value = "Selecciona una carpeta válida."
            organize_result_text.color = ft.Colors.RED_400
            organize_result_text.update()
            return
        try:
            organize_folder(folder)
            organize_result_text.value = "Organización completada."
            organize_result_text.color = ft.Colors.GREEN_400
        except Exception as ex:
            organize_result_text.value = f"Error: {ex}"
            organize_result_text.color = ft.Colors.RED_400
        organize_result_text.update()
        page.snack_bar = ft.SnackBar(ft.Text(organize_result_text.value), open=True)
        page.update()

    # 5. Inicialización de FilePickers (AHORA que las funciones existen)
    # IMPORTANTE: No pasar on_result en el constructor si da error, asignarlo después.
    # Pero lo más importante es añadirlos al overlay ANTES de usarlos.
    folder_picker = ft.FilePicker()
    folder_picker.on_result = handle_folder_picker_result
    
    organize_picker = ft.FilePicker()
    organize_picker.on_result = handle_organize_picker_result
    
    # Añadir al inicio del árbol de controles (aunque son invisibles)
    # page.overlay.extend([folder_picker, organize_picker]) <- Eliminado por causar error visual "Unknown control"
    # Se añadirán al final junto con el layout principal



    # 6. Construcción de Vistas
    
    # Vista Duplicados
    duplicate_files_view = ft.Container(
        content=ft.Column([
            ft.Text("Eliminar Archivos Duplicados", color=ft.Colors.BLUE_200, size=24),
            ft.Row([
                ft.ElevatedButton(
                    "Seleccionar carpeta",
                    icon=ft.Icons.FOLDER_OPEN,
                    on_click=lambda _: folder_picker.get_directory_path()
                ),
                selected_dir_text,
                delete_all_btn,
            ], spacing=10),
            result_text,
            ft.Divider(),
            duplicates_list
        ], expand=True),
        expand=True,
        bgcolor=ft.Colors.with_opacity(0.25, ft.Colors.BLACK),
        padding=20, 
        border_radius=8
    )

    # Vista Organizar
    organize_files_view = ft.Container(
        content=ft.Column([
            ft.Text("Organizar archivos por tipo", color=ft.Colors.BLUE_200, size=24),
            ft.Row([
                ft.ElevatedButton(
                    "Seleccionar carpeta",
                    icon=ft.Icons.FOLDER_OPEN,
                    on_click=lambda _: organize_picker.get_directory_path(),
                ),
                organize_selected_text,
                ft.ElevatedButton(
                    "Organizar",
                    icon=ft.Icons.CLEANING_SERVICES,
                    bgcolor=ft.Colors.BLUE_800,
                    color=ft.Colors.WHITE,
                    on_click=run_organize,
                ),
            ], spacing=10),
            ft.Divider(),
            organize_result_text,
            ft.Text("Moverá imágenes, videos, documentos, etc. a subcarpetas.", color=ft.Colors.BLUE_200, size=12),
        ], expand=True),
        expand=True,
        bgcolor=ft.Colors.with_opacity(0.25, ft.Colors.BLACK),
        padding=20,
        border_radius=8
    )

    # Vistas Placeholder
    resize_files_view = ft.Container(content=ft.Text("Vista: Redimensionar", color=ft.Colors.BLUE_200), padding=20)
    convert_images_view = ft.Container(content=ft.Text("Vista: Convertir", color=ft.Colors.BLUE_200), padding=20)
    extract_audio_view = ft.Container(content=ft.Text("Vista: Extraer Audio", color=ft.Colors.BLUE_200), padding=20)
    merge_pdfs_view = ft.Container(content=ft.Text("Vista: Fusionar PDFs", color=ft.Colors.BLUE_200), padding=20)
    rename_files_view = ft.Container(content=ft.Text("Vista: Renombrar", color=ft.Colors.BLUE_200), padding=20)

    # Contenedor Principal
    content_area = ft.Container(content=duplicate_files_view, expand=True, padding=10)

    # 7. Configuración de Navegación
    def change_view(e):
        idx = e.control.selected_index
        if idx == 0: content_area.content = duplicate_files_view
        elif idx == 1: content_area.content = organize_files_view
        elif idx == 2: content_area.content = resize_files_view
        elif idx == 3: content_area.content = convert_images_view
        elif idx == 4: content_area.content = extract_audio_view
        elif idx == 5: content_area.content = merge_pdfs_view
        elif idx == 6: content_area.content = rename_files_view
        content_area.update()

    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=200,
        destinations=[
            ft.NavigationRailDestination(icon=ft.Icons.DELETE_FOREVER, label="Duplicados"),
            ft.NavigationRailDestination(icon=ft.Icons.FOLDER_COPY, label="Organizar"),
            ft.NavigationRailDestination(icon=ft.Icons.PHOTO_SIZE_SELECT_LARGE, label="Redimensionar"),
            ft.NavigationRailDestination(icon=ft.Icons.TRANSFORM, label="Convertir"),
            ft.NavigationRailDestination(icon=ft.Icons.AUDIOTRACK, label="Extraer Audio"),
            ft.NavigationRailDestination(icon=ft.Icons.MERGE_TYPE, label="Fusionar PDFs"),
            ft.NavigationRailDestination(icon=ft.Icons.EDIT, label="Renombrar"),
        ],
        on_change=change_view,
        bgcolor=ft.Colors.with_opacity(0.45, ft.Colors.GREY_900),
    )

    # 8. Layout Final
    background_image = ft.Image(
        src="fondo.png", 
        fit="cover",
        opacity=1.0,
        gapless_playback=True,
        expand=True,
    )

    layout = ft.Row([rail, ft.VerticalDivider(width=1, color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE)), content_area], expand=True)

    page.add(
        ft.Stack(
            controls=[
                background_image,
                layout,
                # Controles invisibles al final para asegurar que estén en el árbol
                folder_picker,
                organize_picker
            ],
            expand=True
        )
    )

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")