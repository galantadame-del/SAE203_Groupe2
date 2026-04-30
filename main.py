"""
=============================================================================
Module : main.py
Projet : SAE 2.03 – Logiciel de supervision réseau
Auteurs : Groupe 2
Version : 1.0

Rôle :
    Point d'entrée principal du logiciel de supervision.
    Orchestre la collecte, l'analyse, les alertes, le stockage et l'affichage.

Tâches couvertes :
    - P2-5 : Création de la boucle de supervision
    - P2-6 : Lien entre la collecte et l'affichage
    - P3-4 : Intégration de la configuration (intervalle paramétrable)

Dépendances :
    - src.collecte   : ping(), check_url()
    - src.analyse    : analyser()
    - src.alerte     : alerte_console(), alerte_journal()
    - src.stockage   : sauvegarder_resultat()
    - src.affichage  : afficher_tableau()

Aucune dépendance externe requise (hors modules internes).
=============================================================================
"""

# -----------------------------------------------------------------------------
# IMPORTS
# -----------------------------------------------------------------------------
import json          # Chargement du fichier cibles.json
import time          # Mesure des temps, pauses entre cycles
import signal        # Gestion de l'arrêt propre (Ctrl+C)
import sys           # Sortie du programme en cas d'erreur fatale

# Imports des modules internes du projet
from src.collecte import ping, check_url
from src.analyse import analyser
from src.alerte import alerte_console, alerte_journal
from src.stockage import sauvegarder_resultat
from src.affichage import afficher_tableau


# -----------------------------------------------------------------------------
# CONSTANTES
# -----------------------------------------------------------------------------

CONFIG_FILE = "data/cibles.json"
"""
Chemin vers le fichier de configuration des cibles.
Format attendu : JSON avec une clé "cibles" (liste) et optionnellement "intervalle".
"""


# -----------------------------------------------------------------------------
# GESTION DE L'ARRÊT PROPRE (Ctrl+C)
# -----------------------------------------------------------------------------

arret_demande = False
"""
Variable globale booléenne.
Devient True lorsque l'utilisateur appuie sur Ctrl+C.
Permet une sortie propre de la boucle de supervision.
"""

def arreter(signum, frame):
    """
    Handler pour le signal SIGINT (Ctrl+C).
    
    Args:
        signum : Numéro du signal reçu (non utilisé)
        frame  : Contexte d'exécution (non utilisé)
    
    Modifie la variable globale arret_demande pour stopper la boucle.
    """
    global arret_demande
    arret_demande = True
    print("\nArrêt de la supervision...")

# Enregistrement du handler pour le signal d'interruption clavier
signal.signal(signal.SIGINT, arreter)


# -----------------------------------------------------------------------------
# CHARGEMENT DE LA CONFIGURATION
# -----------------------------------------------------------------------------

def charger_config():
    """
    Charge le fichier de configuration JSON.

    Returns:
        dict: Configuration contenant au minimum une clé "cibles".
              Peut aussi contenir "intervalle".

    Gère les erreurs :
        - Fichier introuvable → affiche erreur et quitte (sys.exit)
        - JSON invalide      → affiche erreur et quitte
    
    Exemple de fichier valide :
        {
            "cibles": [
                {"nom": "Google DNS", "type": "ping", "adresse": "8.8.8.8"}
            ],
            "intervalle": 30
        }
    """
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[ERREUR] Fichier de configuration introuvable : {CONFIG_FILE}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"[ERREUR] Fichier de configuration invalide : {e}")
        sys.exit(1)


# -----------------------------------------------------------------------------
# BOUCLE PRINCIPALE
# -----------------------------------------------------------------------------

def main():
    """
    Point d'entrée principal.
    
    Déroulement :
        1. Charger la configuration (cibles + intervalle)
        2. Entrer dans une boucle infinie (jusqu'à Ctrl+C)
        3. Pour chaque cible :
           a. Effectuer la collecte (ping ou HTTP)
           b. Analyser le résultat (OK / ANOMALIE)
           c. Stocker le résultat
           d. Déclencher des alertes si anomalie
           e. Ajouter le résultat à la liste du cycle
        4. Afficher le tableau de bord (P2-6)
        5. Attendre le temps restant avant le prochain cycle
        6. Recommencer
    """
    # 1. Chargement de la configuration
    config    = charger_config()
    cibles    = config["cibles"]
    intervalle = config.get("intervalle", 30)  # 30 secondes par défaut

    print("Démarrage de la supervision...")

    # 2. Boucle principale (s'arrête sur Ctrl+C)
    while not arret_demande:
        resultats_cycle = []    # Liste pour stocker les résultats du cycle (P2-6)
        debut_cycle = time.time()  # Début du cycle (pour calculer l'attente)

        # 3. Parcours de toutes les cibles
        for cible in cibles:

            # ── 3a. Collecte selon le type ──────────────────────────────────
            if cible["type"] == "ping":
                debut = time.time()
                ok = ping(cible["adresse"])
                temps = time.time() - debut if ok else None
                # Analyse avec conversion secondes → millisecondes
                statut = analyser(temps * 1000 if temps else None)
                message = f"Réponse en {temps * 1000:.0f}ms" if ok else "Timeout"

            elif cible["type"] == "http":
                debut = time.time()
                ok = check_url(cible["adresse"])
                temps = time.time() - debut if ok else None
                # Analyse avec conversion secondes → millisecondes
                statut = analyser(temps * 1000 if temps else None)
                message = f"Réponse en {temps * 1000:.0f}ms" if ok else "Site inaccessible"

            else:
                # Type inconnu : on ignore silencieusement cette cible
                continue

            # ── 3b. Stockage ────────────────────────────────────────────────
            sauvegarder_resultat(cible["nom"], cible["type"], statut, message)

            # ── 3c. Alertes si anomalie ─────────────────────────────────────
            if statut == "ANOMALIE":
                alerte_console(f"{cible['nom']} : {message}")
                alerte_journal(f"{cible['nom']} : {message}")

            # ── 3d. Ajout au cycle courant (pour l'affichage) ───────────────
            resultats_cycle.append({
                "cible": cible["nom"],
                "statut": statut,
                "message": message
            })

        # ── 4. Affichage du tableau de bord (P2-6) ──────────────────────────
        timestamp = time.strftime("%d/%m/%Y %H:%M:%S")
        afficher_tableau(resultats_cycle, timestamp, intervalle)

        # ── 5. Attente avant le prochain cycle ──────────────────────────────
        temps_ecoule = time.time() - debut_cycle
        temps_attente = max(0, intervalle - temps_ecoule)  # Pas de valeur négative
        time.sleep(temps_attente)

    # Sortie de la boucle (après Ctrl+C)
    print("Supervision arrêtée.")


# -----------------------------------------------------------------------------
# POINT D'ENTRÉE
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    """
    Exécution uniquement si le fichier est lancé directement.
    Évite l'exécution automatique lors d'un import.
    """
    main()
