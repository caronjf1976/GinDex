import os
import sqlite3
import fitz  # Bibliothèque PyMuPDF pour lire les PDF

# Configuration
DB_NAME = "gindex.db"

def get_folders_to_scan(): # <-- Vérifie bien le "s" à folders
    try:
        with open("config.txt", "r") as f:
            # On récupère chaque ligne qui n'est pas vide
            return [line.strip() for line in f.readlines() if line.strip()]
    except:
        return ["./mon_dossier_test"]

# On crée la liste globale pour les tests rapides
FOLDERS_TO_SCAN = get_folders_to_scan()

def setup_database():
    """Crée ou réinitialise la base de données FTS5"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS files_index')
    cursor.execute('''
        CREATE VIRTUAL TABLE files_index USING fts5(
            path, 
            filename, 
            content
        )
    ''')
    conn.commit()
    return conn

def index_files(conn, folder):
    """Parcourt le dossier et indexe TOUS les noms, extrait le texte si possible"""
    cursor = conn.cursor()
    for root, dirs, files in os.walk(folder):
        for file in files:
            path = os.path.join(root, file)
            content = ""
            filename_lower = file.lower()

            # Extraction du texte SEULEMENT pour les fichiers compatibles
            if filename_lower.endswith(".txt"):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except Exception as e:
                    print(f"❌ Erreur lecture TXT {file}: {e}")

            elif filename_lower.endswith(".pdf"):
                try:
                    import fitz  # PyMuPDF
                    doc = fitz.open(path)
                    for page in doc:
                        content += page.get_text()
                    doc.close()
                except Exception as e:
                    print(f"❌ Erreur lecture PDF {file}: {e}")

            # HARMONISATION : On insère TOUJOURS dans la base (v1.2)
            # Même si content est vide, le fichier sera trouvable par son nom !
            cursor.execute(
                "INSERT INTO files_index (path, filename, content) VALUES (?, ?, ?)",
                (path, file, content)
            )
            print(f"✅ Indexé : {file}")
            
    conn.commit()

# Cette fonction n'est plus obligatoire pour le GUI, mais tu peux la garder à la fin
def run_all_indexing(conn, folders_list):
    for folder in folders_list:
        print(f"📂 Passage au dossier : {folder}")
        index_files(conn, folder)

# --- Lancement du programme ---
if __name__ == "__main__":
    if not os.path.exists(FOLDER_TO_SCAN):
        os.makedirs(FOLDER_TO_SCAN)
        print(f"Dossier '{FOLDER_TO_SCAN}' créé. Ajoute des PDF ou TXT dedans.")
    
    db_conn = setup_database()
    index_files(db_conn, FOLDER_TO_SCAN)
    db_conn.close()
    print("\nL'indexation de G-Index est terminée.")
