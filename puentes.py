import gzip
import json
import sqlite3
import logging
import time

# Configuración del Logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def crear_puentes():
    tiempo_total_inicio = time.time()
    logger.info("Iniciando la creación de bases de datos puente SQLite...")
    
    conexion = sqlite3.connect("puente.db")
    cursor = conexion.cursor()
    
    # --- 1. PUENTE DE PÁGINAS ---
    logger.info("=== FASE 1: Procesando Ediciones (Páginas) ===")
    cursor.execute('CREATE TABLE IF NOT EXISTS raw_editions (work_key TEXT, pages INTEGER)')
    lote = []
    lineas_leidas = 0
    ediciones_validas = 0
    
    inicio_fase = time.time()
    try:
        with gzip.open("ol_dump_editions_latest.txt.gz", 'rt', encoding='utf-8') as archivo:
            for linea in archivo:
                lineas_leidas += 1
                if lineas_leidas % 1_000_000 == 0:
                    logger.info(f"[Ediciones] Leídas {lineas_leidas:,} líneas...")
                
                cols = linea.strip().split('\t')
                if len(cols) >= 5 and cols[0] == "/type/edition":
                    try:
                        datos = json.loads(cols[4])
                        paginas = datos.get("number_of_pages")
                        obras = datos.get("works")
                        if paginas and str(paginas).isdigit() and int(paginas) > 0 and obras:
                            work_key = obras[0].get("key")
                            if work_key:
                                lote.append((work_key, int(paginas)))
                                ediciones_validas += 1
                        
                        if len(lote) >= 50000:
                            cursor.executemany('INSERT INTO raw_editions VALUES (?, ?)', lote)
                            lote = []
                    except json.JSONDecodeError:
                        continue
            if lote:
                cursor.executemany('INSERT INTO raw_editions VALUES (?, ?)', lote)
    except FileNotFoundError:
        logger.error("No se encontró el archivo ol_dump_editions.txt.gz")
        return

    logger.info("Consolidando promedio de páginas en SQLite...")
    cursor.execute('CREATE TABLE IF NOT EXISTS works_pages AS SELECT work_key, CAST(ROUND(AVG(pages)) AS INTEGER) as paginas FROM raw_editions GROUP BY work_key')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_work_key_pages ON works_pages(work_key)')
    cursor.execute('DROP TABLE raw_editions')
    logger.info(f"Fase 1 completada en {time.time() - inicio_fase:.2f}s. Ediciones válidas extraídas: {ediciones_validas:,}")

    # --- 2. PUENTE DE POPULARIDAD ---
    logger.info("=== FASE 2: Procesando Ratings (Popularidad) ===")
    cursor.execute('CREATE TABLE IF NOT EXISTS raw_ratings (work_key TEXT)')
    lote = []
    lineas_leidas = 0
    
    inicio_fase = time.time()
    try:
        with gzip.open("ol_dump_ratings_2026-07-31.txt.gz", 'rt', encoding='utf-8') as archivo:
            for linea in archivo:
                lineas_leidas += 1
                if lineas_leidas % 1_000_000 == 0:
                    logger.info(f"[Ratings] Leídas {lineas_leidas:,} líneas...")
                    
                cols = linea.strip('\n').split('\t')
                if len(cols) >= 1:
                    lote.append((cols[0],))
                if len(lote) >= 50000:
                    cursor.executemany('INSERT INTO raw_ratings VALUES (?)', lote)
                    lote = []
            if lote: 
                cursor.executemany('INSERT INTO raw_ratings VALUES (?)', lote)
    except FileNotFoundError:
        logger.error("No se encontró el archivo ol_dump_ratings.txt.gz")
        return
        
    logger.info("Consolidando recuento de popularidad en SQLite...")
    cursor.execute('CREATE TABLE IF NOT EXISTS works_popularidad AS SELECT work_key, COUNT(*) as popularidad FROM raw_ratings GROUP BY work_key')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_work_key_pop ON works_popularidad(work_key)')
    cursor.execute('DROP TABLE raw_ratings')
    logger.info(f"Fase 2 completada en {time.time() - inicio_fase:.2f}s.")
    
    conexion.commit()
    conexion.close()
    logger.info(f"🎉 Bases de datos puente creadas exitosamente. Tiempo total: {(time.time() - tiempo_total_inicio)/60:.2f} minutos.")

def verificar_puentes(ruta_db="puente.db", limite_muestra=5):
    """
    Lee las tablas creadas en SQLite para confirmar que los datos 
    existen, contar los totales y mostrar una muestra de cómo quedaron.
    """
    logger.info("=========================================")
    logger.info(f"🔍 VERIFICANDO LA BASE DE DATOS: {ruta_db}")
    logger.info("=========================================")
    
    try:
        conexion = sqlite3.connect(ruta_db)
        cursor = conexion.cursor()
        
        # --- Verificar Tabla de Páginas ---
        try:
            # Contar total
            cursor.execute("SELECT COUNT(*) FROM works_pages")
            total_paginas = cursor.fetchone()[0]
            logger.info(f"📚 Tabla 'works_pages' creada exitosamente.")
            logger.info(f"   -> Total de obras con páginas: {total_paginas:,}")
            
            # Obtener muestra aleatoria
            cursor.execute("SELECT work_key, paginas FROM works_pages ORDER BY RANDOM() LIMIT ?", (limite_muestra,))
            muestra_pag = cursor.fetchall()
            logger.info(f"   -> Muestra aleatoria de {limite_muestra} registros:")
            for row in muestra_pag:
                logger.info(f"      * Obra: {row[0]} | Promedio Páginas: {row[1]}")
        except sqlite3.OperationalError:
            logger.error("❌ La tabla 'works_pages' no existe. ¿Falló la Fase 1?")

        logger.info("-" * 40)

        # --- Verificar Tabla de Popularidad ---
        try:
            # Contar total
            cursor.execute("SELECT COUNT(*) FROM works_popularidad")
            total_pop = cursor.fetchone()[0]
            logger.info(f"⭐ Tabla 'works_popularidad' creada exitosamente.")
            logger.info(f"   -> Total de obras con reseñas: {total_pop:,}")
            
            # Obtener los libros MÁS populares (ordenados descendentemente)
            cursor.execute("SELECT work_key, popularidad FROM works_popularidad ORDER BY popularidad DESC LIMIT ?", (limite_muestra,))
            muestra_pop = cursor.fetchall()
            logger.info(f"   -> Top {limite_muestra} obras con más reseñas:")
            for row in muestra_pop:
                logger.info(f"      * Obra: {row[0]} | Total Reseñas: {row[1]:,}")
        except sqlite3.OperationalError:
            logger.error("❌ La tabla 'works_popularidad' no existe. ¿Falló la Fase 2?")

        logger.info("=========================================")
            
    except Exception as e:
        logger.error(f"Error crítico al leer SQLite: {e}")
    finally:
        if 'conexion' in locals():
            conexion.close()

if __name__ == "__main__":
    # crear_puentes()
    verificar_puentes()