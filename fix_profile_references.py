import os
from pathlib import Path

# Directorio donde se encuentran los perfiles a corregir
PROFILES_DIR = Path('motores/motor_extraccion/schemas/data/ES/electricity/profiles/')

# Mapeo de los nombres de archivo antiguos a los nuevos
FILENAME_MAPPING = {
    'consumo_energia.json': 'energy_consumption.json',
    'termino_potencia.json': 'power_term.json',
    'resumen_factura.json': 'invoice_summary.json',
    'autoconsumo.json': 'self_consumption.json',
    'energia_reactiva.json': 'reactive_energy.json',
    'excesos_potencia.json': 'power_excess.json'
}

def fix_profile_references():
    """
    Recorre todos los perfiles .yaml y actualiza las referencias a los componentes
    cuyos nombres de archivo han sido cambiados.
    """
    if not PROFILES_DIR.is_dir():
        print(f"Error: El directorio de perfiles no existe: {PROFILES_DIR}")
        return

    print(f"Buscando archivos .yaml en: {PROFILES_DIR}\n")
    
    # Usamos rglob para buscar en todos los subdirectorios (html, pdf, xls)
    profile_files = list(PROFILES_DIR.rglob('*.yaml'))
    
    if not profile_files:
        print("No se encontraron archivos de perfil .yaml para procesar.")
        return

    print(f"Se encontraron {len(profile_files)} perfiles para procesar.")
    files_changed = 0

    for filepath in profile_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content
            
            # Aplicar todos los reemplazos de nombres de archivo
            for old_name, new_name in FILENAME_MAPPING.items():
                content = content.replace(old_name, new_name)
            
            # Si el contenido ha cambiado, guardar el archivo
            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  -> Actualizado: {filepath.relative_to(Path.cwd())}")
                files_changed += 1

        except Exception as e:
            print(f"Error procesando el archivo {filepath}: {e}")

    print(f"\nProceso completado. Se actualizaron {files_changed} de {len(profile_files)} perfiles.")

if __name__ == "__main__":
    fix_profile_references()
