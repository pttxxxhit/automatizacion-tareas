BOTONES DE LA APP - explicación

Este archivo resume qué hacen los botones "Forzar carpeta y escanear" y "Diagnosticar" en `main_minimal.py`.

1) Forzar carpeta y escanear
- Acción: toma la ruta pegada en el campo "Pegar ruta de carpeta y presionar Forzar", la sanea (quita "file:///", decodifica URL-encoding y normaliza) y la establece como carpeta activa.
- Flujo: asigna la ruta a `state['folder']`, actualiza la etiqueta de carpeta en la UI y llama a `scan()` para ejecutar `find_duplicates`.
- Resultado en UI: `status_text` muestra "Buscando... (archivos: N)" durante el conteo y luego:
  - si hay duplicados: "X duplicados encontrados" y la lista `duplicates_list` se llena con entradas (checkbox + ruta original);
  - si no hay duplicados: "No se encontraron duplicados".
- Cuándo usar: cuando quieres probar una ruta concreta sin usar el diálogo de selección de carpetas; útil para depuración o para rutas repetidas.

2) Diagnosticar
- Acción: ejecuta `find_duplicates` en la carpeta activa y muestra un diálogo modal con un resumen del resultado.
- Flujo: abre un diálogo que primero muestra "Escaneando...", ejecuta el escaneo en segundo plano y, al terminar, reemplaza el contenido del diálogo con:
  - "No se encontraron duplicados", o
  - "N duplicados encontrados" más una lista resumida (primeras entradas: "dup: X -> orig: Y").
- Resultado en UI: diálogo modal con información resumida; no modifica la lista principal salvo que el usuario lo haga manualmente después.
- Cuándo usar: para comprobar rápidamente si `find_duplicates` detecta duplicados en la carpeta sin poblar o alterar la lista principal; útil para aislar problemas de detección.

Notas técnicas útiles
- `sanitize_path` se encarga de limpiar rutas pegadas desde el Explorador u otras apps (quita `file:///`, decodifica y normaliza), evitando errores por rutas codificadas.
- `status_text` es la guía rápida del progreso y resultados (conteo de archivos y resultado del escaneo).
- Si la app no encuentra duplicados, primero prueba a usar "Forzar carpeta" con la ruta exacta y luego "Diagnosticar" para confirmar.

Cómo subir a GitHub (resumen)
- Ya preparé y commité localmente los cambios en `main_minimal.py` y añadí este `BOTONES.md`.
- Para subir al remoto: añade el remoto y empuja:
  git remote add origin <URL_DEL_REPO>
  git push -u origin main

Si me pasas la URL del repo remoto, puedo añadirla y empujar los commits por ti.
