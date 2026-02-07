import flet as ft

def main(page: ft.Page):
    page.add(ft.Text("Prueba de FilePicker"))
    
    # Intento simple: agregar al overlay
    try:
        fp = ft.FilePicker()
        page.overlay.append(fp)
        page.add(ft.ElevatedButton("Abrir Picker", on_click=lambda _: fp.get_directory_path()))
    except Exception as e:
        page.add(ft.Text(f"Error al inicializar Picker: {e}", color="red"))

ft.app(target=main)
