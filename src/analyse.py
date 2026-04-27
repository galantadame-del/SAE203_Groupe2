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

# ---------------------------------------------------------------------------
# SEUILS PAR DÉFAUT (peuvent être surchargés par config.json)
# ---------------------------------------------------------------------------

CONFIG_PAR_DEFAUT = {
    "icmp": {
        "seuil_ok_ms": 50,       # <= 50ms  → OK
        "seuil_degrade_ms": 500  # <= 500ms → dégradé interne, > 500ms → ANOMALIE
    },
    "http": {
        "seuil_ok_ms": 1000,     # <= 1s    → OK
        "seuil_degrade_ms": 2000 # <= 2s    → dégradé interne, > 2s   → ANOMALIE
    }
}

# Configuration active (modifiable via configurer_analyse())
CONFIG = CONFIG_PAR_DEFAUT.copy()


# ---------------------------------------------------------------------------
# FONCTION DE CONFIGURATION
# ---------------------------------------------------------------------------

def configurer_analyse(config_dict):
    """
    Surcharge la configuration depuis config.json.
    À appeler une seule fois au démarrage dans main.py.

    Exemple d'appel :
        configurer_analyse(config["analyse"])
    """
    global CONFIG
    for categorie in ["icmp", "http"]:
        if categorie in config_dict:
            CONFIG[categorie].update(config_dict[categorie])


# ---------------------------------------------------------------------------
# FONCTION INTERNE : _etat_icmp (3 niveaux — usage interne uniquement)
# ---------------------------------------------------------------------------

def _etat_icmp(temps_ms):
    """
    Calcule l'état interne ICMP sur 3 niveaux.
    Ne pas appeler directement depuis les autres modules.

    Retourne : "OK", "_DEGRADE" ou "ANOMALIE"
    """
    if temps_ms is None:
        return "ANOMALIE"

    seuil_ok      = CONFIG["icmp"]["seuil_ok_ms"]
    seuil_degrade = CONFIG["icmp"]["seuil_degrade_ms"]

    if temps_ms <= seuil_ok:
        return "OK"
    elif temps_ms <= seuil_degrade:
        return "_DEGRADE"  # préfixe _ = usage interne uniquement
    else:
        return "ANOMALIE"


# ---------------------------------------------------------------------------
# FONCTION INTERNE : _etat_http (3 niveaux — usage interne uniquement)
# ---------------------------------------------------------------------------

def _etat_http(accessible, temps_ms=None):
    """
    Calcule l'état interne HTTP sur 3 niveaux.
    Ne pas appeler directement depuis les autres modules.

    Retourne : "OK", "_DEGRADE" ou "ANOMALIE"
    """
    if not accessible:
        return "ANOMALIE"

    if temps_ms is None:
        return "OK"

    seuil_ok      = CONFIG["http"]["seuil_ok_ms"]
    seuil_degrade = CONFIG["http"]["seuil_degrade_ms"]

    if temps_ms <= seuil_ok:
        return "OK"
    elif temps_ms <= seuil_degrade:
        return "_DEGRADE"
    else:
        return "ANOMALIE"


# ---------------------------------------------------------------------------
# FONCTION PUBLIQUE : analyser_icmp
# ---------------------------------------------------------------------------

def analyser_icmp(temps_ms):
    """
    Analyse un résultat ICMP et retourne l'état binaire.

    Paramètres :
        temps_ms (float | None) : temps de réponse en ms, ou None si injoignable.

    Retourne :
        str : "OK" ou "ANOMALIE"

    Exemples :
        analyser_icmp(None)   → "ANOMALIE"
        analyser_icmp(12.0)   → "OK"
        analyser_icmp(300.0)  → "ANOMALIE"
        analyser_icmp(600.0)  → "ANOMALIE"
    """
    etat = _etat_icmp(temps_ms)
    return "ANOMALIE" if etat == "_DEGRADE" else etat


# ---------------------------------------------------------------------------
# FONCTION PUBLIQUE : analyser_http
# ---------------------------------------------------------------------------

def analyser_http(accessible, temps_ms=None):
    """
    Analyse un résultat HTTP et retourne l'état binaire.

    Paramètres :
        accessible (bool)        : True si HTTP 200, False sinon.
        temps_ms (float | None)  : temps de réponse en ms (optionnel).

    Retourne :
        str : "OK" ou "ANOMALIE"

    Exemples :
        analyser_http(False)              → "ANOMALIE"
        analyser_http(True, 200.0)        → "OK"
        analyser_http(True, 1500.0)       → "ANOMALIE"
        analyser_http(True, 3500.0)       → "ANOMALIE"
    """
    etat = _etat_http(accessible, temps_ms)
    return "ANOMALIE" if etat == "_DEGRADE" else etat


# ---------------------------------------------------------------------------
# POINT D'ENTRÉE UNIFIÉ : analyser
# ---------------------------------------------------------------------------

def analyser(type_check, **kwargs):
    """
    Point d'entrée unifié pour l'analyse, quel que soit le protocole.
    Toujours en sortie binaire : "OK" ou "ANOMALIE".

    Paramètres :
        type_check (str) : "ICMP" ou "HTTP"
        **kwargs         : temps_ms (float|None), accessible (bool)

    Retourne :
        str : "OK" ou "ANOMALIE"

    Exemples d'appel depuis main.py :
        analyser("ICMP", temps_ms=12.5)
        analyser("ICMP", temps_ms=None)
        analyser("HTTP", accessible=True, temps_ms=350.0)
        analyser("HTTP", accessible=False)
    """
    if type_check == "ICMP":
        return analyser_icmp(kwargs.get("temps_ms"))
    elif type_check == "HTTP":
        return analyser_http(
            kwargs.get("accessible", False),
            kwargs.get("temps_ms")
        )
    else:
        return "ANOMALIE"  # type inconnu → ANOMALIE par sécurité


# ---------------------------------------------------------------------------
# TESTS LOCAUX — python analyse.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print("=== Tests module analyse.py v3.1 ===")
    print("    Sortie toujours binaire : OK / ANOMALIE\n")

    cas_icmp = [
        (None,   "ANOMALIE"),
        (10.0,   "OK"),
        (75.0,   "ANOMALIE"),  # dégradé interne → ANOMALIE en sortie
        (300.0,  "ANOMALIE"),
        (600.0,  "ANOMALIE"),
    ]

    print("-- ICMP --")
    for temps, attendu in cas_icmp:
        resultat = analyser_icmp(temps)
        symbole  = "✅" if resultat == attendu else "❌"
        print(f"  {symbole} analyser_icmp({temps}) → {resultat}  (attendu : {attendu})")

    print()

    cas_http = [
        (False, None,   "ANOMALIE"),
        (True,  200.0,  "OK"),
        (True,  1500.0, "ANOMALIE"),  # dégradé interne → ANOMALIE
        (True,  2500.0, "ANOMALIE"),
        (False, 100.0,  "ANOMALIE"),
    ]

    print("-- HTTP --")
    for accessible, temps, attendu in cas_http:
        resultat = analyser_http(accessible, temps)
        symbole  = "✅" if resultat == attendu else "❌"
        print(f"  {symbole} analyser_http(accessible={accessible}, temps_ms={temps}) → {resultat}  (attendu : {attendu})")

    print()
    print("-- Fonction analyser() unifiée --")
    print(f"  analyser('ICMP', temps_ms=12)     → {analyser('ICMP', temps_ms=12)}")
    print(f"  analyser('ICMP', temps_ms=None)    → {analyser('ICMP', temps_ms=None)}")
    print(f"  analyser('HTTP', accessible=True)  → {analyser('HTTP', accessible=True)}")
    print(f"  analyser('HTTP', accessible=False) → {analyser('HTTP', accessible=False)}")
    print(f"  analyser('INCONNU')                → {analyser('INCONNU')}")
