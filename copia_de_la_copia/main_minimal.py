"""
Versión mínima estable de main_minimal.py (archivo raíz), restaurada para asegurar arranque
- UI simple: seleccionar carpeta, buscar duplicados, lista con checkboxes y eliminar seleccionados.
- FilePicker creado de forma compatible (asignando on_result/on_change como atributo).
- Evita llamadas a APIs que dependan de versiones concretas de flet (no usa parametros incompatibles).
"""

import flet as ft
from flet import Colors as colors, Icons as icons
from borrar_duplicados import find_duplicates, delete_file

import os
import threading
from urllib.parse import unquote

APP_TITLE = "Duplicados - Minimal (estable)"
WINDOW_SIZE = (900, 640)


def path_to_file_url(path: str) -> str:
    if not path:
        return ''
    p = os.path.abspath(path)
    if os.name == 'nt':
        p = p.replace('\\', '/')
        return f"file:///{p}"
    return f"file://{p}"


def main(page: ft.Page):
    page.title = APP_TITLE
    page.window.width, page.window.height = WINDOW_SIZE
    page.padding = 12
    page.bgcolor = colors.BLACK
    page.theme_mode = ft.ThemeMode.DARK

    state = {"folder": "", "duplicates": [], "checkboxes": {}}

    # Helper para ejecutar funciones en el hilo principal de la UI
    def run_on_page(fn):
        try:
            caller = getattr(page, 'call_from_thread', None)
            if callable(caller):
                caller(fn)
                return
        except Exception:
            pass
        # Fallback: intentar ejecutar directamente (puede funcionar si la librería lo permite)
        try:
            fn()
        except Exception as e:
            print('run_on_page fallback error:', e)

    selected_dir = ft.Text("No se ha seleccionado ninguna carpeta", color=colors.BLUE_200)
    status_text = ft.Text("", color=colors.GREY_400)
    duplicates_list = ft.ListView(expand=True, spacing=8)

    def select_all(flag: bool):
        for p, cb in state['checkboxes'].items():
            try:
                cb.value = flag
            except Exception:
                pass
        duplicates_list.update()

    # FilePicker compatible
    def sanitize_path(p: str) -> str:
        if not p:
            return p
        # quitar esquema file:// o file:/// si aparece
        if p.startswith('file:///'):
            p = p[8:]
        elif p.startswith('file://'):
            p = p[7:]
        # Unquote URL-encoded paths
        p = unquote(p)
        # Normalize
        p = os.path.abspath(p)
        return p

    def extract_path_from_event(e):
        # soportar varias firmas de FilePickerResultEvent
        for attr in ('path', 'selected_path', 'directory', 'directory_path'):
            p = getattr(e, attr, None)
            if p:
                return sanitize_path(p)
        # algunos retornan listas de archivos
        files = getattr(e, 'files', None) or getattr(e, 'paths', None) or getattr(e, 'selected_files', None)
        if files:
            # files puede ser lista de objetos con .path o lista de strings
            try:
                first = files[0]
                return sanitize_path(getattr(first, 'path', first))
            except Exception:
                return None
        return None

    def on_folder_result(e):
        path = extract_path_from_event(e)
        if path:
            state['folder'] = path
            selected_dir.value = f"Carpeta: {path}"
            selected_dir.update()
            scan()

    # Crear FilePicker sin argumentos y asignar handler por atributo (más compatible)
    folder_picker = ft.FilePicker()
    try:
        folder_picker.on_result = on_folder_result
    except Exception:
        try:
            folder_picker.on_change = on_folder_result
        except Exception:
            pass
    page.overlay.append(folder_picker)

    # Actions
    def scan():
        folder = state.get('folder')
        if not folder or not os.path.isdir(folder):
            status_text.value = 'Selecciona una carpeta válida'
            status_text.update()
            return

        # Diagnóstico: contar archivos y mostrar antes de buscar duplicados
        try:
            total_files = 0
            for _, _, files in os.walk(folder):
                total_files += len(files)
        except Exception:
            total_files = 0

        status_text.value = f'Buscando... (archivos: {total_files})'
        status_text.update()

        # Ejecutar sin threading para asegurar actualización correcta de UI
        try:
            duplicates = find_duplicates(folder) or []
        except Exception as e:
            print(f"Error in find_duplicates: {e}")
            duplicates = []
        state['duplicates'] = duplicates

        # Mostrar resultados en la UI (hilo principal)
        duplicates_list.controls.clear()
        state['checkboxes'].clear()
        for idx, (dup, orig) in enumerate(duplicates, start=1):
            cb = ft.Checkbox(label=f"{os.path.basename(dup)}", value=False)
            state['checkboxes'][dup] = cb
            cb.on_change = lambda e, _p=dup: None  # preview removed
            row = ft.Row([cb, ft.Text(orig, selectable=True), ft.IconButton(icons.DELETE, on_click=lambda e, p=dup: single_delete(p))], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            duplicates_list.controls.append(ft.Container(content=row, padding=6))

        if duplicates:
            status_text.value = f"{len(duplicates)} duplicados encontrados"
        else:
            status_text.value = 'No se encontraron duplicados'
        status_text.update()
        duplicates_list.update()

    def single_delete(path):
        ok = delete_file(path)
        if ok:
            scan()
            page.snack_bar = ft.SnackBar(ft.Text('Archivo eliminado', color=colors.WHITE), bgcolor=colors.GREEN_700)
            page.snack_bar.open = True
            page.update()

    def delete_selected(e=None):
        to_delete = [p for p, cb in state['checkboxes'].items() if getattr(cb, 'value', False)]
        if not to_delete:
            page.snack_bar = ft.SnackBar(ft.Text('No hay archivos seleccionados', color=colors.WHITE), bgcolor=colors.ORANGE_400)
            page.snack_bar.open = True
            page.update()
            return

        def worker():
            ok = fail = 0
            for p in to_delete:
                try:
                    if delete_file(p):
                        ok += 1
                    else:
                        fail += 1
                except Exception:
                    fail += 1

            def finish():
                scan()
                page.snack_bar = ft.SnackBar(ft.Text(f"✓ Eliminados: {ok}. Fallidos: {fail}", color=colors.WHITE), bgcolor=colors.GREEN_700 if fail==0 else colors.ORANGE_400)
                page.snack_bar.open = True
                page.update()

            run_on_page(finish)

        threading.Thread(target=worker, daemon=True).start()

    # Buttons (use ElevatedButton for compatibility con la versión instalada de Flet)
    btn_select_folder = ft.ElevatedButton('📁 Seleccionar carpeta', on_click=lambda e: folder_picker.get_directory_path())
    btn_scan = ft.ElevatedButton('🔍 Buscar duplicados', on_click=lambda e: scan())
    btn_select_all = ft.ElevatedButton('Seleccionar todos', on_click=lambda e: select_all(True))
    btn_deselect_all = ft.ElevatedButton('Deseleccionar', on_click=lambda e: select_all(False))
    btn_delete_selected = ft.ElevatedButton('🗑️ ELIMINAR', on_click=delete_selected, bgcolor=colors.RED_700)

    # Campo para forzar carpeta (diagnóstico): pegar ruta y forzar scan
    folder_input = ft.TextField(label='Pegar ruta de carpeta y presionar Forzar', width=260)
    def force_folder(e):
        v = folder_input.value.strip()
        if not v:
            page.snack_bar = ft.SnackBar(ft.Text('Introduce una ruta válida', color=colors.WHITE), bgcolor=colors.ORANGE_400)
            page.snack_bar.open = True
            page.update()
            return
        path = sanitize_path(v)
        state['folder'] = path
        selected_dir.value = f"Carpeta: {path}"
        selected_dir.update()
        scan()
    btn_force = ft.ElevatedButton('Forzar carpeta y escanear', on_click=force_folder)

    # Agregar botón Diagnosticar para ver conteo/primeros duplicados (diagnóstico rápido)
    def diagnose(e):
        folder = state.get('folder')
        if not folder or not os.path.isdir(folder):
            page.snack_bar = ft.SnackBar(ft.Text('Selecciona una carpeta válida para diagnosticar', color=colors.WHITE), bgcolor=colors.ORANGE_400)
            page.snack_bar.open = True
            page.update()
            return

        # crear diálogo con handler de cierre compatible
        def _close_dlg(e):
            try:
                dlg.open = False
                page.update()
            except Exception:
                pass

        dlg = ft.AlertDialog(title=ft.Text('Diagnóstico'), content=ft.Column([ft.Text('Escaneando...')]), actions=[ft.TextButton('Cerrar', on_click=_close_dlg)])
        page.dialog = dlg
        dlg.open = True
        page.update()

        def worker_diag():
            try:
                dups = find_duplicates(folder)
            except Exception as err:
                dups = None
                msg = f'Error: {err}'
            if dups is None:
                content = [ft.Text('Error al ejecutar diagnóstico')]
            elif not dups:
                content = [ft.Text('No se encontraron duplicados')]
            else:
                content = [ft.Text(f'{len(dups)} duplicados encontrados'), ft.Divider(height=6)]
                for dup, orig in dups[:20]:
                    content.append(ft.Text(f"dup: {os.path.basename(dup)}  -> orig: {os.path.basename(orig)}"))

            def show():
                dlg.content = ft.Column(content)
                dlg.update()
            run_on_page(show)

        threading.Thread(target=worker_diag, daemon=True).start()

    btn_diag = ft.ElevatedButton('Diagnosticar', on_click=diagnose)

    # Construir la columna izquierda con botones, input forzar carpeta y preview
    left = ft.Column([btn_select_folder, btn_scan, btn_select_all, btn_force, btn_diag, folder_input, ft.Container(height=8)], spacing=8, width=300)
    right = ft.Column([btn_deselect_all, btn_delete_selected], spacing=8, width=140)

    # Layout con fondo (imagen en assets)
    content = ft.Row([left, right, ft.VerticalDivider(), ft.Column([selected_dir, ft.Container(height=8), status_text, ft.Container(height=8), duplicates_list], expand=True)], expand=True)
    layout = ft.Stack(controls=[ft.Image(src='fondo.png', opacity=0.25, expand=True), ft.Container(content=content, padding=12)], expand=True)

    page.add(layout)
    page.update()

    # Nota: el comportamiento de "modo diagnóstico" por variable de entorno se removió
    # para mantener este archivo limpio; usa el campo "Pegar ruta..." y "Forzar carpeta"
    # para probar rutas manualmente cuando sea necesario.


if __name__ == '__main__':
    # usar ft.app para compatibilidad con la versión instalada
    ft.app(target=main, assets_dir='assets')
