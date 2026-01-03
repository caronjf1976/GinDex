import os
import sqlite3
import configparser

def update_index():
    # 1. Chargement de la configuration centralisée
    config = configparser.ConfigParser()
    config.read('settings.ini')
    
    # Lecture des dossiers (on sépare les lignes)
    folders_raw = config.get('PATHS', 'folders', fallback='')
    paths = [p.strip() for p in folders_raw.split('\n') if p.strip() and os.path.exists(p.strip())]
    
    # Lecture des extensions et transformation en ensemble (set)
    ext_raw = config.get('FILTERS', 'extensions', fallback='.pdf,.mp3,.jpg')
    ext_list = {e.strip().lower() for e in ext_raw.split(',')}

    # 2. Connexion à la base de données
    conn = sqlite3.connect("gindex.db")
    cursor = conn.cursor()
    cursor.execute("CREATE VIRTUAL TABLE IF NOT EXISTS files_index USING fts5(filename, path)")
    cursor.execute("DELETE FROM files_index")

    print(f"🚀 Indexation de {len(paths)} dossiers ciblés...")
    
    count = 0
    for root_path in paths:
        for root, dirs, files in os.walk(root_path):
            for filename in files:
                ext = os.path.splitext(filename)[1].lower()
                if ext in ext_list:
                    full_path = os.path.join(root, filename)
                    cursor.execute("INSERT INTO files_index (filename, path) VALUES (?, ?)", (filename, full_path))
                    count += 1

    conn.commit()
    conn.close()
    print(f"✅ Terminé ! {count} fichiers utiles indexés.")

if __name__ == "__main__":
    update_index()
