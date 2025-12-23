import sqlite3

DB_NAME = "gindex.db"

def search_in_index(keyword):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # La magie du FTS5 : on utilise MATCH pour une recherche ultra-rapide
    query = "SELECT filename, path, snippet(files_index, 2, '[[', ']]', '...', 10) FROM files_index WHERE content MATCH ?"
    
    try:
        cursor.execute(query, (keyword,))
        results = cursor.fetchall()
        
        if not results:
            print(f"🔎 Aucun résultat pour : '{keyword}'")
        else:
            print(f"🚀 {len(results)} résultat(s) trouvé(s) :\n")
            for filename, path, snippet in results:
                print(f"📄 Fichier : {filename}")
                print(f"📍 Chemin  : {path}")
                print(f"💡 Extrait : {snippet}")
                print("-" * 30)
    except Exception as e:
        print(f"❌ Erreur lors de la recherche : {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    mot = input("Entrez un mot à chercher dans vos fichiers : ")
    search_in_index(mot)
