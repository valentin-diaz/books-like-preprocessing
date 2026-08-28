import gzip

def explorar_ratings(ruta_archivo, limite=5):
    print(f"Abriendo el archivo de ratings: {ruta_archivo}")
    print(f"Extrayendo los primeros {limite} registros...\n")
    print("="*60)
    
    try:
        with gzip.open(ruta_archivo, 'rt', encoding='utf-8') as archivo:
            contador = 0
            
            for linea in archivo:
                # Separamos por tabulación
                columnas = linea.strip('\n').split('\t')
                
                # Para evitar procesar líneas en blanco por error
                if len(columnas) >= 3:
                    contador += 1
                    
                    work_key = columnas[0]
                    edition_key = columnas[1] if len(columnas) > 1 and columnas[1] else "N/A"
                    rating = columnas[2] if len(columnas) > 2 else "N/A"
                    fecha = columnas[3] if len(columnas) > 3 else "N/A"
                    
                    print(f"--- RATING {contador} ---")
                    print(f"Obra:        {work_key}")
                    print(f"Edición:     {edition_key}")
                    print(f"Calificación: {rating} estrellas")
                    print(f"Fecha:       {fecha}")
                    print("-" * 60)
                    
                    if contador >= limite:
                        break
                        
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo '{ruta_archivo}'.")

# ==========================================
# Ejecución del script
# ==========================================
NOMBRE_DEL_ARCHIVO = "ol_dump_ratings_2026-07-31.txt.gz" 
explorar_ratings(NOMBRE_DEL_ARCHIVO, limite=5)