import tkinter as tk
from tkinter import ttk  # <--- C'est CETTE ligne qu'il te manque !
import sqlite3
import os
import subprocess
from gindex_test import setup_database, index_files, get_folders_to_scan
from tkinter import filedialog, messagebox

def run_indexing():
    """Lance l'indexation pour tous les dossiers listés dans config.txt"""
    btn_index.config(state="disabled")
    folders = get_folders_to_scan() # Récupère la liste
    
    conn = setup_database()
    
    for folder in folders:
        status_var.set(f"🔍 Scan en cours : {folder}...")
        root.update()
        if os.path.exists(folder):
            index_files(conn, folder) # Utilise ta logique de scan PDF/TXT
        else:
            print(f"⚠️ Dossier introuvable : {folder}")
            
    conn.close()
    
    status_var.set(f"✅ Terminé ! {len(folders)} source(s) synchronisée(s).")
    btn_index.config(state="normal")

def search():
    query = entry.get()
    for row in tree.get_children():
        tree.delete(row)
    
    conn = sqlite3.connect("gindex.db")
    cursor = conn.cursor()
    # Recherche avec extraits de texte
    cursor.execute("SELECT path, filename, snippet(files_index, 2, '<b>', '</b>', '...', 10) FROM files_index WHERE content MATCH ?", (query,))
    
    for row in cursor.fetchall():
        tree.insert("", "end", values=row)
    conn.close()

def open_file(event):
    item = tree.selection()[0]
    file_path = tree.item(item, "values")[0]
    if os.path.exists(file_path):
        subprocess.run(["xdg-open", file_path]) # Ouvre le fichier sous Linux

def add_source():
    # Ouvre l'explorateur pour choisir un dossier
    folder_selected = filedialog.askdirectory()
    
    if folder_selected:
        # On vérifie si le dossier n'est pas déjà dans le config.txt
        current_folders = get_folders_to_scan()
        if folder_selected not in current_folders:
            # Sécurité : Lire pour vérifier si on a besoin d'un saut de ligne
            try:
                with open("config.txt", "r") as f:
                    content = f.read()
            except FileNotFoundError:
                content = ""

            with open("config.txt", "a") as f:
                # Si le fichier n'est pas vide et ne finit pas par \n, on l'ajoute
                if content and not content.endswith("\n"):
                    f.write("\n")
                f.write(folder_selected)
                
            messagebox.showinfo("GinDex", f"Source ajoutée : {folder_selected}")
            status_var.set(f"✅ Source ajoutée : {folder_selected}")
        else:
            messagebox.showwarning("GinDex", "Ce dossier est déjà une source d'indexation.")

# --- Création de la Fenêtre ---
root = tk.Tk()
root.title("GinDex - Moteur de Recherche Local")
root.geometry("800x500")

# Barre de recherche
frame_top = tk.Frame(root)
frame_top.pack(pady=10, fill="x", padx=10)

entry = tk.Entry(frame_top, font=("Arial", 14))
entry.pack(side="left", fill="x", expand=True, padx=5)
# Permet de lancer la recherche avec la touche Entrée
# La solution la plus élégante : simuler un clic sur le bouton existant
entry.bind('<Return>', lambda event: btn_search.invoke())

# Met le curseur dans la barre de recherche automatiquement au démarrage
entry.focus_set()

btn_search = tk.Button(frame_top, text="Trouver", command=search)
btn_search.pack(side="left", padx=5)

btn_index = tk.Button(frame_top, text="Mettre à jour l'index", command=run_indexing, fg="blue")
btn_index.pack(side="right", padx=5)

btn_add = tk.Button(frame_top, text="📂 + Source", command=add_source)
btn_add.pack(side="right", padx=5)

# Tableau des résultats
columns = ("Chemin", "Nom", "Extrait")
tree = tk.ttk.Treeview(root, columns=columns, show="headings")
tree.heading("Chemin", text="Chemin")
tree.heading("Nom", text="Nom du fichier")
tree.heading("Extrait", text="Aperçu du contenu")
tree.pack(fill="both", expand=True, padx=10, pady=5)
tree.bind("<Double-1>", open_file)

# --- Barre de statut ---
status_var = tk.StringVar(value="Prêt")
status_bar = tk.Label(root, textvariable=status_var, bd=1, relief="sunken", anchor="w")
status_bar.pack(side="bottom", fill="x")

root.mainloop() # Garde la fenêtre ouverte
