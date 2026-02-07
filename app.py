import flet as ft
from borrar_duplicados import find_duplicates, delete_file
import os
import shutil

# --- Funciones Importadas/Definidas ---
def organize_folder(root_folder):
    if not os.path.isdir(root_folder):
        raise ValueError("Carpeta inválida")

    categories = {
        "Imagenes": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"},
        "Videos": {".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm"},
        "Documentos": {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".md"},
        "Datasets": {".csv", ".tsv", ".json", ".xml", ".parquet"},
        "Comprimidos": {".zip", ".rar", ".7z", ".tar", ".gz"},
    }
    target_dirs = set(categories.keys()) | {"Otros"}
    for d in target_dirs:
        os.makedirs(os.path.join(root_folder, d), exist_ok=True)
    for name in os.listdir(root_folder):
        src_path = os.path.join(root_folder, name)
        if not os.path.isfile(src_path): continue
        ext = os.path.splitext(name)[1].lower()
        dest_dir = "Otros"
        for cat, exts in categories.items():
            if ext in exts:
                dest_dir = cat
                break
        try:
            shutil.move(src_path, os.path.join(root_folder, dest_dir, name))
        except shutil.Error:
            base, ext2 = os.path.splitext(name)
            k = 1
            while True:
                cand = f"{base} ({k}){ext2}"
                cand_path = os.path.join(root_folder, dest_dir, cand)
                if not os.path.exists(cand_path):
                    shutil.move(src_path, cand_path)
                    break
                k += 1

def main(page: ft.Page):
    # 1. Configuración de página
    page.title = "Automatización de Tareas"
    page.window.width = 1000
    page.window.height = 700
    page.padding = 0
    page.bgcolor = ft.Colors.BLACK
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.BLUE, visual_density=ft.VisualDensity.COMFORTABLE)

    # 2. Estado
    state = {
        "current_duplicates": [],
        "current_view": "duplicates",
        "selected_folder": "",
        "organize_input_folder": "",
    }

    # 3. Componentes UI (Declaración Inicial)
    selected_dir_text = ft.Text("No se ha seleccionado ninguna carpeta", size=14, color=ft.Colors.BLUE_200)
    organize_selected_text = ft.Text("No se ha seleccionado ninguna carpeta", color=ft.Colors.BLUE_200)
    result_text = ft.Text("", color=ft.Colors.BLUE_200)
    organize_result_text = ft.Text("", color=ft.Colors.BLUE_200)
    
    duplicates_list = ft.ListView(expand=True, spacing=8, padding=0, auto_scroll=False)

    delete_all_btn = ft.ElevatedButton(
        "Eliminar todos",
        icon=ft.Icons.DELETE_SWEEP,
        bgcolor=ft.Colors.RED_900,
        color=ft.Colors.WHITE,
        visible=False, # Ocultar inicialmente si no hay duplicados
        disabled=True,
    )

    # 4. Lógica y Manejadores
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
                duplicates_list.controls.append(
                    ft.Row([
                        ft.Text(f"Duplicado: {dup}\nOriginal: {orig}", color=ft.Colors.BLUE_200, expand=True),
                        ft.ElevatedButton("Eliminar", icon=ft.Icons.DELETE, color=ft.Colors.WHITE, bgcolor=ft.Colors.RED_900, on_click=make_delete_fn(dup))
                    ])
                )
        duplicates_list.update()
        result_text.update()
        delete_all_btn.update() # Asegurar actualización

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
        delete_all_btn.update()
        
        to_delete = [dup for dup, _ in state["current_duplicates"]]
        ok, fail = 0, 0
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
        result_text.update()
        
        # page.snack_bar es mejor configurarlo al inicio o aquí
        page.snack_bar = ft.SnackBar(ft.Text(result_text.value), open=True)
        page.update()

    delete_all_btn.on_click = perform_delete_all # Asignación directa

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

    # Manejadores de Pickers
    def handle_folder_picker(e: ft.FilePickerResultEvent):
        if e.path:
            state["selected_folder"] = e.path
            selected_dir_text.value = f"Carpeta seleccionada: {e.path}"
            selected_dir_text.update()
            scan_and_show_duplicates()

    def handle_organize_picker(e: ft.FilePickerResultEvent):
        if e.path:
            state["organize_input_folder"] = e.path
            organize_selected_text.value = f"Carpeta a organizar: {e.path}"
            organize_selected_text.update()

    # 5. Inicialización de FilePickers (ORDEN CRÍTICO)
    folder_picker = ft.FilePicker()
    folder_picker.on_result = handle_folder_picker
    
    organize_picker = ft.FilePicker()
    organize_picker.on_result = handle_organize_picker
    # Añadir al inicio del árbol de controles (aunque son invisibles)
    # page.overlay.extend([folder_picker, organize_picker]) <- Eliminado
    # Se añadirán al final junto con el layout principal

    # 6. Construcción de Vistas
    duplicate_files_view = ft.Container(
        content=ft.Column([
            ft.Text("Eliminar Archivos Duplicados", color=ft.Colors.BLUE_200, size=24),
            ft.Row([
                ft.ElevatedButton("Seleccionar carpeta", icon=ft.Icons.FOLDER_OPEN, on_click=lambda _: folder_picker.get_directory_path()),
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

    organize_files_view = ft.Container(
        content=ft.Column([
            ft.Text("Organizar archivos por tipo", color=ft.Colors.BLUE_200, size=24),
            ft.Row([
                ft.ElevatedButton("Seleccionar carpeta", icon=ft.Icons.FOLDER_OPEN, on_click=lambda _: organize_picker.get_directory_path()),
                organize_selected_text,
                ft.ElevatedButton("Organizar", icon=ft.Icons.CLEANING_SERVICES, bgcolor=ft.Colors.BLUE_800, color=ft.Colors.WHITE, on_click=run_organize),
            ], spacing=10),
            ft.Divider(),
            organize_result_text,
            ft.Text("Moverá imágenes, videos, etc. a subcarpetas.", color=ft.Colors.BLUE_200, size=12),
        ], expand=True),
        expand=True,
        bgcolor=ft.Colors.with_opacity(0.25, ft.Colors.BLACK),
        padding=20,
        border_radius=8
    )

    content_area = ft.Container(content=duplicate_files_view, expand=True, padding=10)

    # 7. Navegación
    def change_view(e):
        idx = e.control.selected_index
        if idx == 0: content_area.content = duplicate_files_view
        elif idx == 1: content_area.content = organize_files_view
        content_area.update()

    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=200,
        destinations=[
            ft.NavigationRailDestination(icon=ft.Icons.DELETE_FOREVER, label="Duplicados"),
            ft.NavigationRailDestination(icon=ft.Icons.FOLDER_COPY, label="Organizar"),
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

    page.add(
        ft.Stack(
            controls=[
                background_image,
                ft.Row([rail, ft.VerticalDivider(1, color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE)), content_area], expand=True),
                # Controles invisibles al final
                folder_picker,
                organize_picker
            ],
            expand=True
        )
    )

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
