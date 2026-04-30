"""
=============================================================================
Module : main.py
Projet : SAE 2.03 – Logiciel de supervision réseau
Auteurs : Groupe 2
Version : 1.0

Tâches couvertes :
    - P2-6 : Lier la collecte au tableau (afficher_tableau)
    - P2-7 : Boucle de supervision avec rafraîchissement (while + sleep interruptible)
    - P2-8 : Zone d'alerte (enregistrer_alerte)

Rôle :
    Point d'entrée principal.
    Boucle périodique qui orchestre la collecte, l'analyse, le stockage,
    les alertes et l'affichage.

Dépendances :
    - src.collecte   : ping(), check_url()
    - src.analyse    : analyser()
    - src.alerte     : alerte_console(), alerte_journal()
    - src.stockage   : sauvegarder_resultat()
    - src.affichage  : afficher_tableau(), enregistrer_alerte()

Aucune dépendance externe requise (hors modules internes).
=============================================================================
"""

import json
import time
import signal
import sys
from src.collecte import ping, check_url
from src.analyse import analyser
from src.alerte import alerte_console, alerte_journal
from src.stockage import sauvegarder_resultat
from src.affichage import afficher_tableau, enregistrer_alerte


# =============================================================================
# CONSTANTES
# =============================================================================

CONFIG_FILE = "data/cibles.json"
"""
Chemin vers le fichier de configuration des cibles.
Format attendu : JSON avec clé "cibles" (liste) et optionnellement "intervalle".
"""


# =============================================================================
# GESTION DE L'ARRÊT PROPRE (Ctrl+C) - P2-7
# =============================================================================
# Sans cette gestion, Ctrl+C provoquerait une stacktrace et un arrêt brutal.
# Le signal.SIGINT est intercepté pour permettre une sortie propre.

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
    print("\n[INFO] Signal reçu. Arrêt propre en cours...")

# Enregistrement du handler pour le signal d'interruption clavier
signal.signal(signal.SIGINT, arreter)


# =============================================================================
# CHARGEMENT DE LA CONFIGURATION
# =============================================================================

def charger_config():
    """
    Charge le fichier de configuration JSON (data/cibles.json).

    Structure attendue :
    {
        "intervalle": 30,
        "cibles": [
            {"nom": "Google DNS", "adresse": "8.8.8.8",           "type": "ping"},
            {"nom": "Google",     "adresse": "https://google.com", "type": "http"}
        ]
    }

    Gère les erreurs :
        - Fichier introuvable → affiche erreur et quitte (sys.exit)
        - JSON invalide      → affiche erreur et quitte

    Returns:
        dict: Configuration complète
    """
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[ERREUR] Fichier de configuration introuvable : {CONFIG_FILE}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"[ERREUR] Fichier JSON invalide : {e}")
        sys.exit(1)


# =============================================================================
# COLLECTE D'UNE CIBLE
# =============================================================================

def collecter_cible(cible):
    """
    Effectue la vérification d'une cible (ping ou HTTP).
    Calcule le temps de réponse et retourne un résultat structuré.

    Args:
        cible (dict): {"nom": str, "adresse": str, "type": "ping"|"http"}

    Returns:
        dict: {"cible": str, "statut": str, "message": str}
              ou None si le type est inconnu
    """
    nom     = cible["nom"]
    adresse = cible["adresse"]
    type_   = cible["type"]

    if type_ == "ping":
        debut   = time.time()
        ok      = ping(adresse)
        temps   = time.time() - debut if ok else None
        statut  = analyser(temps)
        message = f"Réponse en {temps * 1000:.0f}ms" if ok else "Timeout"

    elif type_ == "http":
        debut   = time.time()
        ok      = check_url(adresse)
        temps   = time.time() - debut if ok else None
        statut  = analyser(temps)
        message = f"Réponse en {temps * 1000:.0f}ms" if ok else "Site inaccessible"

    else:
        print(f"[AVERTISSEMENT] Type inconnu ignoré : '{type_}' pour {nom}")
        return None

    return {
        "cible":   nom,
        "statut":  statut,
        "message": message
    }


# =============================================================================
# BOUCLE PRINCIPALE DE SUPERVISION — P2-7
# =============================================================================

def boucle_supervision(cibles, intervalle):
    """
    Boucle périodique de supervision.
    Tourne indéfiniment jusqu'à Ctrl+C.

    À chaque cycle :
        1. Collecte tous les équipements
        2. Stocke chaque résultat en JSON
        3. Alerte si anomalie + mémorise pour zone d'alerte (P2-8)
        4. Rafraîchit le tableau (P2-6, P2-7)
        5. Attend l'intervalle configuré (attente interruptible)

    Args:
        cibles     (list): Liste des cibles depuis la config
        intervalle (int) : Secondes entre chaque cycle
    """
    global arret_demande
    numero_cycle = 0

    while not arret_demande:
        numero_cycle += 1
        resultats_cycle = []
        debut_cycle     = time.time()

        print(f"[INFO] Cycle #{numero_cycle} en cours...")  # Debug

        # ── 1. Collecte de toutes les cibles ─────────────────────────────
        for cible in cibles:
            resultat = collecter_cible(cible)

            if resultat is None:
                continue  # type inconnu, on passe

            # ── 2. Stockage JSON ──────────────────────────────────────────
            sauvegarder_resultat(
                resultat["cible"],
                cible["type"],
                resultat["statut"],
                resultat["message"]
            )

            # ── 3. Alertes si anomalie + mémorisation P2-8 ────────────────
            if resultat["statut"] == "ANOMALIE":
                alerte_console(f"{resultat['cible']} : {resultat['message']}")
                alerte_journal(f"{resultat['cible']} : {resultat['message']}")
                enregistrer_alerte(resultat["cible"], resultat["message"])

            resultats_cycle.append(resultat)

        # ── 4. Rafraîchissement du tableau (P2-6, P2-7) + zone alerte (P2-8) ──
        timestamp = time.strftime("%d/%m/%Y %H:%M:%S")
        afficher_tableau(resultats_cycle, timestamp, intervalle)

        # ── 5. Attente interruptible avant prochain cycle (P2-7) ─────────────
        temps_ecoule  = time.time() - debut_cycle
        temps_attente = max(0, intervalle - temps_ecoule)

        # Boucle d'attente par secondes permettant de vérifier arret_demande
        # Plus réactive qu'un simple time.sleep(intervalle)
        for _ in range(int(temps_attente)):
            if arret_demande:
                break
            time.sleep(1)


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

def main():
    """
    Point d'entrée principal.
    Charge la configuration, affiche les infos de démarrage,
    et lance la boucle de supervision.
    """
    print("=" * 55)
    print("   SUPERVISION RÉSEAU — SAE 2.03   Groupe 2")
    print("=" * 55)

    config     = charger_config()
    cibles     = config["cibles"]
    intervalle = config.get("intervalle", 30)

    print(f"[INFO] {len(cibles)} cibles chargées — intervalle : {intervalle}s")
    print("[INFO] Démarrage de la supervision... (Ctrl+C pour arrêter)\n")

    boucle_supervision(cibles, intervalle)

    print("\n[INFO] Supervision arrêtée proprement.")
    print("=" * 55)


if __name__ == "__main__":
    """
    Exécution uniquement si le fichier est lancé directement.
    Évite l'exécution automatique lors d'un import.
    """
    main()
