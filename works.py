# Exploración del dump de works

import gzip
import json

# Ruta a tu archivo descargado
ruta_dump = "ol_dump_works_2026-07-31.txt.gz"  # Cambia esto por el nombre real de tu archivo

print("Leyendo el dump de Open Library...")

libros_procesados = []
contador = 0

# Usamos gzip.open para leer el archivo comprimido sin descomprimirlo completo en disco
with gzip.open(ruta_dump, "rt", encoding="utf-8") as archivo:
    for linea in archivo:
        # Separar las columnas por tabulación
        columnas = linea.strip().split("\t")
        
        if len(columnas) < 5:
            continue
            
        tipo_registro = columnas[0]
        json_str = columnas[4]
        
        # Nos aseguramos de que sea un registro de tipo 'work'
        if tipo_registro == "/type/work":
            try:
                data = json.loads(json_str)

                # Imprimir todo el JSON para inspección (opcional, comentar en producción)
                # print(json.dumps(data, indent=2, ensure_ascii=False))
                
                # 1. Extraer Título
                titulo = data.get("title")
                if not titulo:
                    continue  # Si no tiene título, no nos sirve
                
                # 2. Extraer Sinopsis (En Open Library puede venir como string o como objeto dict)
                descripcion_raw = data.get("description", "")
                if isinstance(descripcion_raw, dict):
                    sinopsis = descripcion_raw.get("value", "")
                else:
                    sinopsis = descripcion_raw
                
                # Si el libro no tiene sinopsis, quizás quieras saltarlo
                if not sinopsis:
                    continue

                # 3. Extraer Tags (Subjects)
                subjects = data.get("subjects", [])
                # Convertir a minúsculas y limpiar por si hay objetos extraños
                tags = [str(subj).lower() for subj in subjects if isinstance(subj, (str, dict))]
                # Nota: a veces Open Library guarda los subjects como diccionarios, ajusta según veas la estructura
                
                libro_procesado = {
                    "titulo": titulo,
                    "sinopsis": sinopsis,
                    "tags": tags[:15], # Nos quedamos con los primeros 15 tags
                    "open_library_key": data.get("key")
                }
                
                libros_procesados.append(libro_procesado)
                contador += 1
                
                # Ejemplo: Imprimir los primeros 10 para verificar
                if contador <= 10:
                    print(f"\n--- Libro {contador} ---")
                    print(json.dumps(libro_procesado, indent=2, ensure_ascii=False))
                else:
                    break
                    # En producción, aquí harías un INSERT por lotes (Batch Insert) a tu PostgreSQL.
            except json.JSONDecodeError:
                continue

print(f"\nProceso finalizado. Se extrajeron {contador} libros con éxito.")