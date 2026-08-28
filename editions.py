import gzip
import json

def explorar_dump(ruta_archivo, limite=3):
    print(f"Abriendo el archivo: {ruta_archivo}")
    print(f"Extrayendo los primeros {limite} registros válidos...\n")
    print("="*60)
    
    try:
        # 'rt' significa Read Text. Gzip descomprime la línea al vuelo.
        with gzip.open(ruta_archivo, 'rt', encoding='utf-8') as archivo:
            contador = 0
            
            for linea in archivo:
                # Los dumps de Open Library separan sus 5 columnas con tabulaciones
                columnas = linea.strip().split('\t')
                
                # Verificamos que sea una línea válida de Open Library
                if len(columnas) >= 5:
                    tipo_registro = columnas[0]
                    json_str = columnas[4]
                    
                    try:
                        # Convertimos el texto de la 5ta columna en un diccionario de Python
                        datos = json.loads(json_str)
                        
                        contador += 1
                        print(f"--- REGISTRO {contador} | Tipo: {tipo_registro} ---")
                        # Imprimimos el JSON formateado para que sea fácil de leer por un humano
                        print(json.dumps(datos, indent=2, ensure_ascii=False))
                        print("-" * 60 + "\n")
                        
                        # Detenemos la lectura una vez alcancemos el límite
                        if contador >= limite:
                            break
                            
                    except json.JSONDecodeError:
                        # Si hay un error de formato en esa línea, la saltamos
                        continue
                        
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo '{ruta_archivo}'.")
        print("Asegúrate de que el nombre coincida exactamente y esté en la misma carpeta.")

# ==========================================
# Ejecución del script
# ==========================================
# Cambia este nombre por el nombre exacto de tu archivo descargado
NOMBRE_DEL_ARCHIVO = "ol_dump_editions_latest.txt.gz" 

explorar_dump(NOMBRE_DEL_ARCHIVO, limite=3)