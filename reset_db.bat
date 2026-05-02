@echo off
echo ========================================
echo Reiniciando Base de Datos de FacilAdmin
echo ========================================
echo.

REM Borrar base de datos SQLite
echo [1/5] Borrando base de datos antigua...
if exist db.sqlite3 (
    del /F db.sqlite3
    echo   ✓ Base de datos borrada
) else (
    echo   - No habia base de datos previa
)
echo.

REM Borrar archivos de migracion (excepto __init__.py)
echo [2/5] Limpiando migraciones antiguas...
for /d %%D in (apps\*) do (
    if exist "%%D\migrations" (
        echo   Limpiando %%D\migrations...
        del /F /Q "%%D\migrations\*.py" 2>nul
        rmdir /S /Q "%%D\migrations\__pycache__" 2>nul
        echo # Migrations > "%%D\migrations\__init__.py"
    )
)
echo   ✓ Migraciones limpiadas
echo.

REM Crear nuevas migraciones
echo [3/5] Creando nuevas migraciones...
python manage.py makemigrations
echo.

REM Aplicar migraciones
echo [4/5] Aplicando migraciones a la base de datos...
python manage.py migrate
echo.

REM Crear directorios de media
echo [5/5] Creando directorios necesarios...
if not exist media mkdir media
if not exist staticfiles mkdir staticfiles
echo   ✓ Directorios creados
echo.

echo ========================================
echo ✓ Base de datos reiniciada exitosamente
echo ========================================
echo.
echo Ahora ejecuta:
echo   python manage.py createsuperuser
echo   python manage.py runserver
echo.
pause
