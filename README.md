# Seguimiento de Atajados

Aplicación Qt para gestionar y realizar seguimiento de obras de atajados.
La interfaz utiliza el tema oscuro de **QDarkStyle** y muestra un gráfico de
estado en la pestaña de inicio. Ahora se incluye una pestaña de **Resumen** que
muestra el porcentaje de avance por atajado ordenado por fecha de registro.
## Instalación

1. Cree un entorno virtual de Python.
2. Instale las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Ejecute la aplicación:
   ```bash
   python app.py
   ```

## Desarrollo

El proyecto utiliza SQLite para almacenar los datos. El archivo de base de datos
se genera automáticamente en la primera ejecución. Las imágenes y fotografías se
almacenan en las carpetas `images/` y `photos/`, que están excluidas del control
de versiones.

## Pruebas

Para ejecutar las pruebas unitarias:

```bash
python -m unittest discover tests
```