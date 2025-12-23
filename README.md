🍸 GinDex

GinDex est un moteur de recherche local léger et performant qui permet d'indexer le contenu de vos fichiers PDF et TXT à travers plusieurs sources de stockage. Que vos documents soient sur votre disque principal, une partition d'archive ou une clé USB, GinDex les retrouve instantanément.

🚀 Pourquoi GinDex ?
   - Multi-Sources : Indexez plusieurs dossiers simultanément via un fichier de configuration simple.
   - Recherche Intelligente : Grâce à SQLite FTS5, cherchez des mots-clés à l'intérieur même des documents et visualisez un extrait du contenu.
   - Rapidité Linux : Conçu spécifiquement pour l'écosystème Ubuntu/Debian avec intégration de xdg-open pour une ouverture immédiate des fichiers.

🛠️ Installation
   1. Dépendances : Installez la bibliothèque de traitement PDF :
        #Bash
        pip install pymupdf
   2. Configuration : Créez un fichier config.txt dans le dossier du projet et listez vos chemins (un par ligne) :
        #Plaintext
        /home/user/Documents
        /mnt/Archives
        /media/user/MaCleUSB

📖 Mode d'emploi (v1.0)
   1. Lancez l'interface : python3 gindex_gui.py.
   2. Cliquez sur Mettre à jour l'index (assurez-vous que vos disques externes sont branchés !).
   3. Tapez votre recherche et laissez GinDex faire le reste.

🗺️ Roadmap (À venir)
   - v2.0 : Intégration d'un sélecteur de dossiers visuel (filedialog) directement dans l'interface.
   - Support de formats supplémentaires (Word, Markdown, etc.).
   - Option de tri (par date de modification, etc.).
