import flet as ft
from borrar_duplicados import find_duplicates, delete_file
import os
import shutil

# --- Constantes Cyberpunk ---
# Paleta de Colores Neón
COLOR_PRIMARY = "#00FFFF"      # Cian Eléctrico
COLOR_SECONDARY = "#FF00FF"    # Magenta Neón
COLOR_BG_DARK = "#120524" # Azul Oscuro Profundo / Negro
COLOR_BG_PANEL = "#95000000"   # Panel mucho más transparente para ver el fondo
COLOR_TEXT = "#E0FFFF"         # Cian pálido casi blanco
COLOR_ERROR = "#FF2A6D"        # Rojo/Rosa Neón Error
COLOR_SUCCESS = "#05ffa1"      # Verde Matrix

# Fuentes
FONT_FAMILY = "Courier New"    # Estilo Terminal / Retro

# --- Funciones Mismas ---
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
    # 1. Configuración de página Cyberpunk
    page.title = "CYBER // TASK_MANAGER_V1.0"
    page.window.width = 1100
    page.window.height = 750
    page.padding = 0
    page.bgcolor = COLOR_BG_DARK
    page.theme_mode = ft.ThemeMode.DARK
    page.fonts = {
        "Cyber": "Courier New",
    }
    page.theme = ft.Theme(
        font_family="Cyber",
        color_scheme=ft.ColorScheme(
            primary=COLOR_PRIMARY,
            secondary=COLOR_SECONDARY,
            background=COLOR_BG_DARK,
            surface=COLOR_BG_PANEL,
            on_primary=COLOR_BG_DARK,
            on_surface=COLOR_TEXT,
        ),
        visual_density=ft.VisualDensity.COMFORTABLE,
    )

    # 2. Estado
    state = {
        "current_duplicates": [],
        "current_view": "duplicates",
        "selected_folder": "",
        "organize_input_folder": "",
        "selected_for_delete": set(), # Nuevo estado para selección múltiple
    }

    # 3. Componentes UI Estilizados
    def create_neon_text(value, color=COLOR_TEXT, size=14, weight=None):
        return ft.Text(value, size=size, color=color, font_family="Cyber", weight=weight)
    
    def create_neon_button(text, icon, on_click, is_primary=True, disabled=False):
        # Estilo Cyber: Botones con bordes afilados y colores neón
        color = COLOR_PRIMARY if is_primary else COLOR_SECONDARY
        return ft.OutlinedButton(
            content=ft.Row([ft.Icon(icon, color=color), ft.Text(text, color=color, font_family="Cyber")], alignment=ft.MainAxisAlignment.CENTER),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=2), # Bordes casi rectos
                side=ft.BorderSide(1, color),
                overlay_color=ft.Colors.with_opacity(0.1, color),
            ),
            on_click=on_click,
            disabled=disabled,
        )

    selected_dir_text = create_neon_text(">> SISTEMA: ESPERANDO SELECCIÓN DE CARPETA...", COLOR_PRIMARY)
    organize_selected_text = create_neon_text(">> SISTEMA: ESPERANDO TARGET...", COLOR_PRIMARY)
    
    result_text = create_neon_text("")
    organize_result_text = create_neon_text("")
    
    duplicates_list = ft.ListView(expand=True, spacing=5, padding=10, auto_scroll=False)

    # Botón Eliminar Seleccionados (NUEVO)
    delete_selected_btn = ft.OutlinedButton(
        content=ft.Row([ft.Icon(ft.Icons.DELETE, color=COLOR_SECONDARY), ft.Text("ELIMINAR SELECCIÓN", color=COLOR_SECONDARY, font_family="Cyber")], alignment=ft.MainAxisAlignment.CENTER),
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=2),
            side=ft.BorderSide(1, COLOR_SECONDARY),
            overlay_color=ft.Colors.with_opacity(0.1, COLOR_SECONDARY),
        ),
        visible=False, 
        disabled=True,
    )

    # Botón Eliminar Todos (Especial: Rojo Peligro)
    delete_all_btn = ft.OutlinedButton(
        content=ft.Row([ft.Icon(ft.Icons.DELETE_SWEEP, color=COLOR_ERROR), ft.Text("ELIMINAR TODO", color=COLOR_ERROR, font_family="Cyber")], alignment=ft.MainAxisAlignment.CENTER),
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=2),
            side=ft.BorderSide(1, COLOR_ERROR),
            overlay_color=ft.Colors.with_opacity(0.2, COLOR_ERROR),
        ),
        visible=False, 
        disabled=True,
    )

    # 4. Lógica y Manejadores
    def scan_and_show_duplicates(e=None):
        folder = state["selected_folder"]
        if not folder or not os.path.isdir(folder):
            result_text.value = ">> ERROR: RUTA INVÁLIDA O INACCESIBLE"
            result_text.color = COLOR_ERROR
            result_text.update()
            delete_all_btn.visible = False
            delete_all_btn.disabled = True
            delete_all_btn.update()
            return
        
        duplicates = find_duplicates(folder)
        state["current_duplicates"] = duplicates
        duplicates_list.controls.clear()

        if not duplicates:
            result_text.value = ">> ESCANEO COMPLETADO: 0 AMENAZAS (DUPLICADOS) DETECTADAS"
            result_text.color = COLOR_SUCCESS
            delete_all_btn.visible = False
            delete_all_btn.disabled = True
            delete_selected_btn.visible = False
            delete_selected_btn.disabled = True
        else:
            result_text.value = f">> ALERTA: {len(duplicates)} ARCHIVOS REDUNDANTES DETECTADOS"
            result_text.color = COLOR_SECONDARY
            delete_all_btn.visible = True
            delete_all_btn.disabled = False
            # El de seleccionados depende de si hay items en el set, al escanear se resetea
            state["selected_for_delete"] = set()
            delete_selected_btn.visible = True
            delete_selected_btn.disabled = True # Empieza deshabilitado
            
            for dup, orig in duplicates:
                def make_delete_fn(dup_file):
                    return lambda _ev: delete_and_refresh(dup_file)
                
                def on_checkbox_change(e, file_path=dup):
                    if e.control.value:
                        state["selected_for_delete"].add(file_path)
                    else:
                        state["selected_for_delete"].discard(file_path)
                    
                    # Actualizar estado botón Eliminar Selección
                    if state["selected_for_delete"]:
                        delete_selected_btn.disabled = False
                        delete_selected_btn.style.side = ft.BorderSide(1, COLOR_SECONDARY) # Activo visualmente
                    else:
                        delete_selected_btn.disabled = True
                        delete_selected_btn.style.side = ft.BorderSide(1, ft.Colors.with_opacity(0.3, COLOR_SECONDARY))
                    delete_selected_btn.update()

                # Item de lista estilo terminal con Checkbox
                item = ft.Container(
                    content=ft.Row([
                        # Checkbox para seleccionar
                        ft.Checkbox(value=False, on_change=on_checkbox_change, fill_color=COLOR_PRIMARY),
                        # Icono de advertencia
                        ft.Icon(ft.Icons.WARNING_AMBER, color=COLOR_SECONDARY, size=24),
                        ft.Column([
                            create_neon_text(f"DUP: {dup}", COLOR_TEXT, size=12),
                            create_neon_text(f"ORI: {orig}", ft.Colors.with_opacity(0.5, COLOR_TEXT), size=10),
                        ], expand=True),
                        # Boton borrar individual se mantiene
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color=COLOR_ERROR,
                            tooltip="ELIMINAR ESTE ELEMENTO",
                            on_click=make_delete_fn(dup),
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=10,
                    border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.2, COLOR_PRIMARY))),
                )
                duplicates_list.controls.append(item)

        duplicates_list.update()
        result_text.update()
        delete_all_btn.update()
        delete_selected_btn.update()

    def delete_and_refresh(dup_file):
        if delete_file(dup_file):
            state["current_duplicates"] = [item for item in state["current_duplicates"] if item[0] != dup_file]
            state["selected_for_delete"].discard(dup_file) # Limpiar del set si existía
            # Aviso de exito individual
            page.snack_bar = ft.SnackBar(ft.Text("ARCHIVO BORRADO CON ÉXITO", font_family="Cyber"), bgcolor=COLOR_SUCCESS, open=True)
            page.update()
            scan_and_show_duplicates()
        else:
            result_text.value = f">> ERROR CRÍTICO AL ELIMINAR: {dup_file}"
            result_text.color = COLOR_ERROR
            result_text.update()

    def perform_delete_selected(e=None):
        to_delete = list(state["selected_for_delete"])
        if not to_delete: return
        
        ok, fail = 0, 0
        for dup in to_delete:
            if delete_file(dup): ok += 1
            else: fail += 1
        
        scan_and_show_duplicates()
        if fail == 0:
            result_text.value = f">> EXITO: SE HAN BORRADO EXITOSAMENTE {ok} ARCHIVOS SELECCIONADOS"
            result_text.color = COLOR_SUCCESS
        else:
            result_text.value = f">> BORRADO PARCIAL: {ok} ÉXITOS // {fail} FALLOS"
            result_text.color = COLOR_SECONDARY
        result_text.update()
        page.snack_bar = ft.SnackBar(ft.Text(result_text.value, font_family="Cyber"), bgcolor=COLOR_BG_PANEL, open=True)
        page.update()

    delete_selected_btn.on_click = perform_delete_selected

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
            result_text.value = f">> EXITO: SE HAN BORRADO EXITOSAMENTE {ok} ARCHIVOS"
            result_text.color = COLOR_SUCCESS
        else:
            result_text.value = f">> BORRADO PARCIAL: {ok} ÉXITOS // {fail} FALLOS"
            result_text.color = COLOR_SECONDARY
        result_text.update()
        
        page.snack_bar = ft.SnackBar(ft.Text(result_text.value, font_family="Cyber"), bgcolor=COLOR_BG_PANEL, open=True)
        page.update()

    delete_all_btn.on_click = perform_delete_all

    def run_organize(_ev=None):
        folder = state.get("organize_input_folder") or ""
        if not folder or not os.path.isdir(folder):
            organize_result_text.value = ">> ERROR: SELECCIONAR CARPETA DE ORIGEN"
            organize_result_text.color = COLOR_ERROR
            organize_result_text.update()
            return
        try:
            organize_folder(folder)
            organize_result_text.value = ">> OPERACIÓN DE ORGANIZACIÓN: EXITOSA"
            organize_result_text.color = COLOR_SUCCESS
        except Exception as ex:
            organize_result_text.value = f">> FALLO EN SISTEMA: {ex}"
            organize_result_text.color = COLOR_ERROR
        organize_result_text.update()
        page.snack_bar = ft.SnackBar(ft.Text(organize_result_text.value, font_family="Cyber"), bgcolor=COLOR_BG_PANEL, open=True)
        page.update()

    # Manejadores de Pickers
    def handle_folder_picker(e: ft.FilePickerResultEvent):
        if e.path:
            state["selected_folder"] = e.path
            selected_dir_text.value = f">> TARGET: {e.path}"
            selected_dir_text.update()
            scan_and_show_duplicates()

    def handle_organize_picker(e: ft.FilePickerResultEvent):
        if e.path:
            state["organize_input_folder"] = e.path
            organize_selected_text.value = f">> TARGET: {e.path}"
            organize_selected_text.update()

    # 5. Inicialización de FilePickers
    folder_picker = ft.FilePicker()
    folder_picker.on_result = handle_folder_picker
    
    organize_picker = ft.FilePicker()
    organize_picker.on_result = handle_organize_picker

    # 6. Construcción de Vistas Cyberpunk
    def create_cyber_panel(title, content_list):
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=create_neon_text(title, COLOR_PRIMARY, 20, "bold"),
                    padding=ft.padding.only(bottom=10),
                    border=ft.border.only(bottom=ft.BorderSide(1, COLOR_PRIMARY))
                ),
                *content_list
            ], expand=True),
            expand=True,
            bgcolor=COLOR_BG_PANEL,
            padding=25,
            border=ft.border.all(1, ft.Colors.with_opacity(0.3, COLOR_PRIMARY)),
            border_radius=0, # Bordes afilados
            # blur eliminado para que no desenfoque el fondo
            margin=10,
        )

    duplicate_files_view = create_cyber_panel(">> MÓDULO: ELIMINAR DUPLICADOS", [
        ft.Container(height=20),
        ft.Row([
            create_neon_button("SELECCIONAR RUTA", ft.Icons.FOLDER_OPEN, lambda _: folder_picker.get_directory_path()),
            ft.VerticalDivider(width=10, thickness=1, color=COLOR_PRIMARY),
            delete_selected_btn, # Boton nuevo
            delete_all_btn,
        ]),
        ft.Container(height=10),
        selected_dir_text,
        ft.Container(height=20),
        result_text,
        ft.Divider(color=ft.Colors.with_opacity(0.2, COLOR_PRIMARY)),
        duplicates_list
    ])

    organize_files_view = create_cyber_panel(">> MÓDULO: ORGANIZAR DIRECTORIO", [
        ft.Container(height=20),
        ft.Row([
            create_neon_button("SELECCIONAR RUTA", ft.Icons.FOLDER_OPEN, lambda _: organize_picker.get_directory_path()),
            organize_selected_text,
        ]),
        ft.Container(height=20),
        create_neon_button("EJECUTAR ORGANIZACIÓN", ft.Icons.CLEANING_SERVICES, run_organize, is_primary=False),
        ft.Container(height=20),
        ft.Divider(color=ft.Colors.with_opacity(0.2, COLOR_PRIMARY)),
        organize_result_text,
        create_neon_text(">> SISTEMA MOVERÁ ARCHIVOS A SUBCARPETAS SEGÚN EXTENSIÓN.", ft.Colors.with_opacity(0.6, COLOR_TEXT), 12),
    ])

    content_area = ft.Container(content=duplicate_files_view, expand=True, padding=20)

    # 7. Navegación Cyberpunk
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
        group_alignment=-0.9,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.DELETE_FOREVER_OUTLINED, 
                selected_icon=ft.Icons.DELETE_FOREVER, 
                label="ELIMINAR"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.FOLDER_COPY_OUTLINED, 
                selected_icon=ft.Icons.FOLDER_COPY, 
                label="ORGANIZAR"
            ),
        ],
        on_change=change_view,
        bgcolor=COLOR_BG_PANEL, # Semitransparente
        indicator_color=ft.Colors.with_opacity(0.2, COLOR_PRIMARY),
    )

    # 8. Layout Final
    background_image = ft.Image(
        src="fondo.png", 
        fit=ft.ImageFit.COVER, 
        # opacity eliminado, por defecto es 1.0
        gapless_playback=True,
        expand=True,
    )

    # (Overlay gradiente eliminado a petición del usuario para ver bien el logo)

    page.add(
        ft.Stack(
            controls=[
                background_image,
                # background_gradient eliminado
                ft.Row([
                    ft.Container(content=rail, border=ft.border.only(right=ft.BorderSide(1, COLOR_PRIMARY))), # Borde neón al menú
                    content_area,
                ], expand=True),
                # Controles invisibles
                folder_picker,
                organize_picker
            ],
            expand=True
        )
    )

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
