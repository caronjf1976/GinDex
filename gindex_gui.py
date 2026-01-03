import os, sys, io, sqlite3, subprocess, json
import tkinter as tk
from tkinter import ttk, filedialog
from preview_generator.manager import PreviewManager
from PIL import Image, ImageDraw, ImageOps, ImageTk

# --- 🔊 MOTEUR AUDIO (GinBox) ---
try:
    import pygame
    pygame.mixer.init()
    JUKEBOX_OK = True
except Exception:
    JUKEBOX_OK = False

# --- 🏷️ EXTRACTION METADONNÉES ---
try:
    from mutagen import File
    from mutagen.id3 import ID3, APIC
    MUTAGEN_OK = True
except Exception:
    MUTAGEN_OK = False

class GinDexGUI:
    def __init__(self, root):
        # 1. Gestion de la configuration (Mémoire)
        self.config_file = "gindex_config.json"
        self.charger_config()

        # 2. Philosophie Visuelle J-F
        self.c_fond = "#0D2B2D"      # Lagon profond
        self.c_liste = "#1A3A3D"     # Sarcelle
        self.c_texte = "#BDC3C7"     # Gris perle
        self.c_corail = "#CD5C5C"    # Corail Brique
        self.c_contour = "#0D2B2D"   # Bordure Perfect Fit
        self.epaisseur = 4
        self.arrondi = 13

        self.root = root
        self.root.title("GinDex v3.3.5 - Mémoire Active")
        self.root.configure(bg=self.c_fond)
        self.root.geometry("1200x850")

        # Sauvegarde auto à la fermeture
        self.root.protocol("WM_DELETE_WINDOW", self.quitter_proprement)

        self.cache_path = "/tmp/gindex_preview_cache"
        self.preview_manager = PreviewManager(self.cache_path, create_folder=True)
        self.img_references = {}

        # --- 🧰 BARRE D'OUTILS ---
        self.toolbar = tk.Frame(self.root, bg=self.c_fond)
        self.toolbar.pack(fill=tk.X, padx=20, pady=10)
        
        btn_style = {"bg": self.c_liste, "fg": self.c_texte, "relief": "flat", 
                     "highlightbackground": self.c_contour, "highlightthickness": 2, "padx": 15}
        
        tk.Button(self.toolbar, text="📁 Dossier", command=self.ajouter_dossier, **btn_style).pack(side=tk.LEFT, padx=5)
        tk.Button(self.toolbar, text="🔄 Indexer", command=self.indexer, **btn_style).pack(side=tk.LEFT, padx=5)
        
        self.btn_stop = tk.Button(self.toolbar, text="🛑 STOP", command=self.stop_musique, 
                                  bg=self.c_corail, fg="white", relief="flat",
                                  highlightbackground=self.c_contour, highlightthickness=2, padx=15)
        self.btn_stop.pack(side=tk.LEFT, padx=20)

        # --- 📐 LAYOUT DEUX COLONNES ---
        self.main_container = tk.Frame(self.root, bg=self.c_fond)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # GAUCHE (Recherche + Liste)
        self.left_frame = tk.Frame(self.main_container, bg=self.c_fond)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.search_entry = tk.Entry(self.left_frame, font=('Arial', 12), 
                                     bg=self.c_liste, fg="white", 
                                     highlightbackground=self.c_contour, highlightthickness=2,
                                     insertbackground="white", relief="flat")
        self.search_entry.pack(fill=tk.X, pady=(0, 10))
        # On remet la dernière recherche au démarrage
        self.search_entry.insert(0, self.config.get("derniere_recherche", ""))
        self.search_entry.bind('<Return>', lambda e: self.rechercher())

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=self.c_liste, foreground=self.c_texte, 
                        fieldbackground=self.c_liste, rowheight=65, borderwidth=0)
        style.map("Treeview", background=[('selected', self.c_corail)])

        self.tree = ttk.Treeview(self.left_frame, columns=("path"), show="tree")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select_item)
        self.tree.bind("<Double-1>", self.lire_media)

        # DROITE (Zone de Visualisation)
        self.preview_frame = tk.Frame(self.main_container, width=500, bg=self.c_liste,
                                      highlightbackground=self.c_contour, highlightthickness=4)
        self.preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(20, 0))
        self.preview_frame.pack_propagate(False)

        self.preview_label = tk.Label(self.preview_frame, bg=self.c_liste, text="SÉLECTIONNEZ UN FICHIER", 
                                      fg=self.c_texte, font=("Arial", 12, "bold"))
        self.preview_label.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        self.info_label = tk.Label(self.preview_frame, bg=self.c_liste, fg=self.c_texte, 
                                   font=("Arial", 10, "italic"), wraplength=450)
        self.info_label.pack(pady=20)

    # --- MÉTHODES DE CONFIGURATION ---
    def charger_config(self):
        base_config = {"dossiers": [], "derniere_recherche": "", 
                       "export_pref": {"qualite": 95, "vitesse": "medium"}}
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                self.config = json.load(f)
        else:
            self.config = base_config

    def sauver_config(self):
        self.config["derniere_recherche"] = self.search_entry.get()
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=4)

    def quitter_proprement(self):
        self.sauver_config()
        self.root.destroy()

    # --- MÉTHODES MÉDIA ET UI ---
    def stop_musique(self):
        if JUKEBOX_OK: pygame.mixer.music.stop()

    def on_select_item(self, event):
        selected = self.tree.selection()
        if not selected: return
        path = self.tree.item(selected[0], "values")[0]
        self.info_label.config(text=os.path.basename(path))
        img = None
        if path.lower().endswith(('.mp3', '.m4a', '.flac')) and MUTAGEN_OK:
            try:
                audio = File(path)
                if path.lower().endswith('.mp3'):
                    tags = ID3(path)
                    for tag in tags.values():
                        if isinstance(tag, APIC):
                            img = Image.open(io.BytesIO(tag.data))
                            break
                elif hasattr(audio, 'pictures') and audio.pictures:
                    img = Image.open(io.BytesIO(audio.pictures[0].data))
            except: pass
        if img is None:
            try:
                p_path = self.preview_manager.get_jpeg_preview(path, width=450)
                img = Image.open(p_path)
            except: pass
        if img:
            img.thumbnail((450, 450), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.preview_label.config(image=photo, text="")
            self.preview_label.image = photo
        else:
            self.preview_label.config(image='', text="Aperçu non disponible")

    def preparer_miniature(self, path, style_forme="carre"):
        taille = (48, 48)
        img = None
        if MUTAGEN_OK and path.lower().endswith(('.mp3', '.m4a')):
            try:
                if path.lower().endswith('.mp3'):
                    tags = ID3(path)
                    for tag in tags.values():
                        if isinstance(tag, APIC):
                            img = Image.open(io.BytesIO(tag.data))
                            break
            except: pass
        if img is None:
            try:
                p_path = self.preview_manager.get_jpeg_preview(path, width=100)
                img = Image.open(p_path)
            except: pass
        final = Image.new('RGBA', taille, (0,0,0,0))
        if img:
            img = ImageOps.fit(img, taille, Image.LANCZOS)
        else:
            img = Image.new('RGBA', taille, self.c_liste)
            draw_ph = ImageDraw.Draw(img)
            draw_ph.ellipse((22, 22, 26, 26), fill=self.c_texte)
        masque = Image.new('L', taille, 0)
        draw_m = ImageDraw.Draw(masque)
        if style_forme == "cercle":
            draw_m.ellipse((1, 1, 46, 46), fill=255)
        else:
            draw_m.rounded_rectangle((1, 1, 46, 46), radius=self.arrondi, fill=255)
        img.putalpha(masque)
        final.paste(img, (0,0))
        draw_b = ImageDraw.Draw(final)
        if style_forme == "cercle":
            draw_b.ellipse((1, 1, 46, 46), outline=self.c_contour, width=self.epaisseur)
        else:
            draw_b.rounded_rectangle((1, 1, 46, 46), radius=self.arrondi, outline=self.c_contour, width=self.epaisseur)
        return ImageTk.PhotoImage(final)

    def rechercher(self):
        query = self.search_entry.get()
        for item in self.tree.get_children(): self.tree.delete(item)
        conn = sqlite3.connect("gindex.db")
        cursor = conn.cursor()
        cursor.execute("SELECT filename, path FROM files_index WHERE filename LIKE ?", (f"%{query}%",))
        results = cursor.fetchall()
        for row in results:
            filename, path = row[0], row[1]
            style = "cercle" if path.lower().endswith(('.mp3', '.wav', '.flac')) else "carre"
            icon = self.preparer_miniature(path, style)
            self.img_references[path] = icon
            self.tree.insert("", "end", text=f"  {filename}", image=icon, values=(path,))
        conn.close()

    def ajouter_dossier(self):
        dossier = filedialog.askdirectory()
        if dossier and dossier not in self.config["dossiers"]:
            self.config["dossiers"].append(dossier)
            self.sauver_config()

    def indexer(self): print("Indexation en attente d'automatisation...")

    def lire_media(self, event):
        item = self.tree.selection()[0]
        chemin = self.tree.item(item, "values")[0]
        if chemin.lower().endswith(('.mp3', '.wav', '.flac')) and JUKEBOX_OK:
            pygame.mixer.music.load(chemin)
            pygame.mixer.music.play()
        else:
            subprocess.Popen(['xdg-open', chemin])

if __name__ == "__main__":
    root = tk.Tk()
    app = GinDexGUI(root)
    root.mainloop()
