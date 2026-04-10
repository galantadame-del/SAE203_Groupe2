"""
=============================================================================
Module : affichage.py
Projet : SAE 2.03 – Logiciel de supervision réseau
Auteurs : Groupe 2
Version : 2.0

Rôle :
    Interface graphique de l'application de supervision.
    Permet la gestion (CRUD) des équipements supervisés avec affichage
    codé selon leur statut (NORMAL / ANOMALIE / HORS LIGNE).

Tâches couvertes :
    - P2-1 : Fenêtre principale Tkinter
    - P2-2 : Tableau des équipements (Treeview)
    - P3-2 : Filtres (implémentés via barre de recherche)
    - P3-3 : Barre de recherche (filtrage dynamique)
    - P3-4 : Bouton "Ajouter équipement" (fenêtre modale)

Dépendances :
    - tkinter (natif)
    - ttk   (natif)

Aucune dépendance externe requise (CustomTkinter non utilisé ici).
=============================================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox


# =============================================================================
# CLASSE PRINCIPALE – Application Tkinter
# =============================================================================

class MainApp(tk.Tk):
    """
    Application principale de gestion des équipements réseau.
    Hérite de tk.Tk (fenêtre racine).
    """

    # -------------------------------------------------------------------------
    # P2-1 – Initialisation et configuration de la fenêtre principale
    # -------------------------------------------------------------------------
    def __init__(self):
        """Constructeur : initialise la fenêtre, les styles et les composants."""
        super().__init__()

        # Configuration de la fenêtre (P2-1)
        self.title("Gestion des Équipements")
        self.geometry("950x580")
        self.minsize(700, 450)
        self.configure(bg="#1e1e2e")  # Thème sombre (Catppuccin)

        # Style des composants ttk
        self.style = ttk.Style(self)
        self._configure_styles()

        # Construction des éléments d'interface
        self._build_header()          # En-tête avec titre
        self._build_toolbar()         # Barre d'outils (boutons + recherche)
        self._build_treeview()        # P2-2 : Tableau des équipements
        self._build_statusbar()       # Barre de statut en bas

    # -------------------------------------------------------------------------
    # Configuration des styles visuels
    # -------------------------------------------------------------------------
    def _configure_styles(self):
        """
        Configure les styles des composants ttk (Treeview, boutons, etc.)
        Thème "Catppuccin Mocha" : couleurs sombres pour un look moderne.
        """
        self.style.theme_use("clam")

        # Style du tableau (Treeview)
        self.style.configure(
            "Equipements.Treeview",
            background="#2a2a3e",
            foreground="#cdd6f4",
            fieldbackground="#2a2a3e",
            rowheight=30,
            font=("Segoe UI", 10),
            borderwidth=0,
        )
        # Style des en-têtes du tableau
        self.style.configure(
            "Equipements.Treeview.Heading",
            background="#313244",
            foreground="#89b4fa",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
        )
        # Style au survol/sélection
        self.style.map(
            "Equipements.Treeview",
            background=[("selected", "#45475a")],
            foreground=[("selected", "#cdd6f4")],
        )

        # Style du bouton "Action" (Ajouter / Modifier)
        self.style.configure(
            "Action.TButton",
            background="#89b4fa",
            foreground="#1e1e2e",
            font=("Segoe UI", 9, "bold"),
            padding=(10, 5),
            relief="flat",
            borderwidth=0,
        )
        self.style.map("Action.TButton", background=[("active", "#74c7ec")])

        # Style du bouton "Danger" (Supprimer)
        self.style.configure(
            "Danger.TButton",
            background="#f38ba8",
            foreground="#1e1e2e",
            font=("Segoe UI", 9, "bold"),
            padding=(10, 5),
            relief="flat",
            borderwidth=0,
        )
        self.style.map("Danger.TButton", background=[("active", "#eba0ac")])

    # -------------------------------------------------------------------------
    # En-tête de l'application
    # -------------------------------------------------------------------------
    def _build_header(self):
        """
        Construit l'en-tête de la fenêtre avec le titre et la version.
        """
        header = tk.Frame(self, bg="#181825", pady=12)
        header.pack(fill="x")

        tk.Label(
            header,
            text="⚙  Liste des Équipements Réseau",
            bg="#181825", fg="#cdd6f4",
            font=("Segoe UI", 16, "bold"),
        ).pack(side="left", padx=20)

        tk.Label(
            header, text="v1.0",
            bg="#181825", fg="#6c7086",
            font=("Segoe UI", 9),
        ).pack(side="right", padx=20, anchor="s")

    # -------------------------------------------------------------------------
    # Barre d'outils (boutons + barre de recherche)
    # P3-2 : Filtres (via recherche)
    # P3-3 : Barre de recherche
    # P3-4 : Bouton "Ajouter équipement"
    # -------------------------------------------------------------------------
    def _build_toolbar(self):
        """
        Construit la barre d'outils contenant :
        - Bouton Ajouter (P3-4)
        - Bouton Modifier
        - Bouton Supprimer
        - Champ de recherche (P3-3)
        """
        bar = tk.Frame(self, bg="#1e1e2e", pady=8, padx=16)
        bar.pack(fill="x")

        # Bouton Ajouter (P3-4)
        ttk.Button(bar, text="  Ajouter", style="Action.TButton",
                   command=self._ajouter).pack(side="left", padx=(0, 6))

        # Bouton Modifier
        ttk.Button(bar, text="  Modifier", style="Action.TButton",
                   command=self._modifier).pack(side="left", padx=(0, 6))

        # Bouton Supprimer
        ttk.Button(bar, text="  Supprimer", style="Danger.TButton",
                   command=self._supprimer).pack(side="left", padx=(0, 6))

        # Espaceur
        tk.Label(bar, text="", bg="#1e1e2e", fg="#89b4fa",
                 font=("Segoe UI", 11)).pack(side="right", padx=(0, 4))

        # Barre de recherche (P3-3)
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._on_search)  # Recherche en temps réel
        tk.Entry(
            bar, textvariable=self._search_var,
            bg="#313244", fg="#cdd6f4",
            insertbackground="#cdd6f4",
            relief="flat", font=("Segoe UI", 10), width=24,
        ).pack(side="right", ipady=5, padx=(0, 8))

    # -------------------------------------------------------------------------
    # P2-2 – Tableau des équipements (Treeview)
    # -------------------------------------------------------------------------
    def _build_treeview(self):
        """
        Construit le tableau (Treeview) affichant la liste des équipements.
        Colonnes : ID, Nom, Adresse, Type, Statut.
        Gère le scroll, le tri, le double-clic et les couleurs par statut.
        """
        frame = tk.Frame(self, bg="#1e1e2e", padx=16, pady=4)
        frame.pack(fill="both", expand=True)

        # Définition des colonnes
        columns = ("id", "nom", "adresse", "type", "statut")
        self.tree = ttk.Treeview(
            frame, columns=columns,
            show="headings",
            style="Equipements.Treeview",
            selectmode="browse",
        )

        # Configuration des en-têtes et largeurs
        headers = {
            "id":      ("ID",                  50,  "center"),
            "nom":     ("Nom de l'équipement", 220, "w"),
            "adresse": ("Adresse IP / URL",    230, "w"),
            "type":    ("Type",                 90, "center"),
            "statut":  ("Statut attendu",      150, "center"),
        }
        for col, (label, width, anchor) in headers.items():
            self.tree.heading(col, text=label,
                              command=lambda c=col: self._sort_column(c))
            self.tree.column(col, width=width, anchor=anchor, minwidth=40)

        # Barres de défilement
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Placement
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        # Tags de couleur pour les lignes (zèbre + statut)
        self.tree.tag_configure("odd",        background="#25253a")
        self.tree.tag_configure("even",       background="#2a2a3e")
        self.tree.tag_configure("normal",     foreground="#a6e3a1")   # Vert
        self.tree.tag_configure("anomalie",   foreground="#f38ba8")   # Rouge
        self.tree.tag_configure("hors_ligne", foreground="#fab387")   # Orange

        # Données initiales (exemples conformes au tableau fourni)
        self._all_data = [
            ("1",  "Serveur principal",        "192.168.1.10",                   "Ping", "NORMAL"),
            ("2",  "Passerelle (routeur)",      "192.168.1.1",                    "Ping", "NORMAL"),
            ("3",  "Google DNS",               "8.8.8.8",                        "Ping", "NORMAL"),
            ("4",  "Cloudflare DNS",           "1.1.1.1",                        "Ping", "NORMAL"),
            ("5",  "Site web Google",          "https://google.com",             "HTTP", "NORMAL"),
            ("6",  "Site web interne",         "https://intranet.entreprise.com","HTTP", "ANOMALIE (test)"),
            ("7",  "Imprimante RDC",           "192.168.1.50",                   "Ping", "HORS LIGNE (test)"),
            ("8",  "Machine fantôme (test)",   "192.168.99.99",                  "Ping", "ANOMALIE"),
            ("9",  "Serveur fichier",          "192.168.1.20",                   "Ping", "NORMAL"),
            ("10", "Site web inexistant",      "https://site-qui-n-existe-pas.com","HTTP","ANOMALIE"),
            ("11", "Switch principal",         "192.168.1.2",                    "Ping", "NORMAL"),
            ("12", "Caméra IP entrée",         "192.168.1.100",                  "Ping", "NORMAL"),
        ]

        self._populate(self._all_data)

        # Double-clic pour voir les détails
        self.tree.bind("<Double-1>", self._on_double_click)

    # -------------------------------------------------------------------------
    # Méthodes utilitaires du tableau
    # -------------------------------------------------------------------------
    def _statut_tag(self, statut):
        """
        Retourne le nom du tag de couleur associé à un statut.
        "NORMAL" → "normal" (vert)
        "ANOMALIE" → "anomalie" (rouge)
        "HORS LIGNE" → "hors_ligne" (orange)
        """
        s = statut.upper()
        if "HORS" in s:
            return "hors_ligne"
        if "ANOMALIE" in s:
            return "anomalie"
        return "normal"

    def _populate(self, data):
        """
        Remplit (ou rafraîchit) le tableau avec les données fournies.
        Applique les tags de couleur (zèbre + statut).
        """
        for row in self.tree.get_children():
            self.tree.delete(row)
        for i, row in enumerate(data):
            tag_zebra = "odd" if i % 2 else "even"
            tag_statut = self._statut_tag(row[4])
            self.tree.insert("", "end", values=row,
                             tags=(tag_zebra, tag_statut))

    def _build_statusbar(self):
        """
        Construit la barre de statut en bas de la fenêtre.
        Affiche le nombre d'équipements chargés.
        """
        self._status_var = tk.StringVar(
            value=f"{len(self._all_data)} équipements chargés")
        tk.Label(
            self, textvariable=self._status_var,
            bg="#181825", fg="#6c7086",
            font=("Segoe UI", 9),
            anchor="w", padx=16, pady=4,
        ).pack(fill="x", side="bottom")

    # -------------------------------------------------------------------------
    # Actions CRUD (Ajouter, Modifier, Supprimer)
    # -------------------------------------------------------------------------
    def _ajouter(self):
        """Ouvre le formulaire d'ajout d'un nouvel équipement (P3-4)."""
        self._open_form()

    def _modifier(self):
        """Ouvre le formulaire de modification de l'équipement sélectionné."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sélection requise",
                                   "Veuillez sélectionner un équipement.")
            return
        self._open_form(self.tree.item(sel[0], "values"))

    def _supprimer(self):
        """Supprime l'équipement sélectionné après confirmation."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sélection requise",
                                   "Veuillez sélectionner un équipement.")
            return
        nom = self.tree.item(sel[0], "values")[1]
        if messagebox.askyesno("Confirmer", f"Supprimer « {nom} » ?"):
            item_id = self.tree.item(sel[0], "values")[0]
            self._all_data = [r for r in self._all_data if r[0] != item_id]
            self._populate(self._all_data)
            self._status_var.set(f"{len(self._all_data)} équipements")

    # -------------------------------------------------------------------------
    # P3-3 – Barre de recherche (filtrage dynamique)
    # -------------------------------------------------------------------------
    def _on_search(self, *_):
        """
        Filtre le tableau en fonction du texte saisi dans la barre de recherche.
        Recherche dans toutes les colonnes (insensible à la casse).
        """
        q = self._search_var.get().lower()
        if not q:
            self._populate(self._all_data)
            self._status_var.set(f"{len(self._all_data)} équipements")
            return

        filtered = [r for r in self._all_data
                    if any(q in str(v).lower() for v in r)]
        self._populate(filtered)
        self._status_var.set(f"{len(filtered)} résultat(s) pour « {q} »")

    # -------------------------------------------------------------------------
    # Tri du tableau par colonne
    # -------------------------------------------------------------------------
    def _sort_column(self, col):
        """
        Trie les données selon la colonne sélectionnée.
        """
        cols = ("id", "nom", "adresse", "type", "statut")
        idx = cols.index(col)
        self._all_data.sort(key=lambda r: str(r[idx]).lower())
        self._populate(self._all_data)

    # -------------------------------------------------------------------------
    # Double-clic : affichage des détails
    # -------------------------------------------------------------------------
    def _on_double_click(self, _event):
        """
        Affiche une fenêtre popup avec les détails de l'équipement sélectionné.
        """
        sel = self.tree.selection()
        if not sel:
            return
        v = self.tree.item(sel[0], "values")
        messagebox.showinfo(
            f"Détails – {v[1]}",
            f"ID       : {v[0]}\n"
            f"Nom      : {v[1]}\n"
            f"Adresse  : {v[2]}\n"
            f"Type     : {v[3]}\n"
            f"Statut   : {v[4]}",
        )

    # -------------------------------------------------------------------------
    # P3-4 – Formulaire d'ajout / modification (fenêtre modale)
    # -------------------------------------------------------------------------
    def _open_form(self, values=None):
        """
        Ouvre une fenêtre modale pour ajouter ou modifier un équipement.

        Args:
            values (tuple, optionnel): Si fourni, pré-remplit le formulaire
                                       pour la modification.
        """
        win = tk.Toplevel(self)
        win.title("Ajouter" if not values else "Modifier")
        win.geometry("420x300")
        win.configure(bg="#1e1e2e")
        win.grab_set()  # Fenêtre modale

        labels = ["ID", "Nom de l'équipement", "Adresse IP / URL", "Type", "Statut attendu"]
        entries = []

        for i, lbl in enumerate(labels):
            tk.Label(win, text=lbl, bg="#1e1e2e", fg="#89b4fa",
                     font=("Segoe UI", 10)).grid(row=i, column=0,
                                                  sticky="w", padx=20, pady=6)
            var = tk.StringVar(value=(values[i] if values else ""))
            e = tk.Entry(win, textvariable=var, bg="#313244", fg="#cdd6f4",
                         insertbackground="#cdd6f4", relief="flat",
                         font=("Segoe UI", 10), width=30)
            e.grid(row=i, column=1, padx=10, pady=6, ipady=4)
            entries.append(var)

        def _save():
            """Sauvegarde les données du formulaire et met à jour le tableau."""
            row = tuple(v.get().strip() for v in entries)
            if not row[0] or not row[1]:
                messagebox.showwarning("Champs requis", "ID et Nom obligatoires.")
                return

            if values:
                # Modification : remplacer l'ancienne entrée
                self._all_data = [row if r[0] == values[0] else r
                                  for r in self._all_data]
            else:
                # Ajout
                self._all_data.append(row)

            self._populate(self._all_data)
            self._status_var.set(f"{len(self._all_data)} équipements")
            win.destroy()

        ttk.Button(win, text="  Enregistrer", style="Action.TButton",
                   command=_save).grid(row=len(labels), column=0,
                                       columnspan=2, pady=14)


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

if __name__ == "__main__":
    """
    Lancement direct de l'application pour les tests.
    Commande : python affichage.py
    """
    app = MainApp()
    app.mainloop()
