"""
=============================================================================
Module  : main.py
Projet  : SAE 2.03 – Logiciel de supervision réseau
Auteurs : Groupe 2
Version : 1.3 — P3-4 final + scan automatique

Tâches couvertes :
    P2-6 : Lier la collecte au tableau d'affichage
    P2-7 : Boucle de supervision avec rafraîchissement automatique
    P2-8 : Zone d'alerte (mémorisation de la dernière anomalie)
    P3-4 : Paramétrage depuis config.json (intervalle, debug, une seule fois)
    P3-5 : Scan automatique au premier lancement (découverte des équipements)

Fonctionnement :
    1. Si cibles.json est vide ou inexistant → scan automatique du réseau
    2. Charge config.json      → intervalle, mode debug, mode une seule fois
    3. Charge cibles.json      → liste des équipements à superviser
    4. Lance la boucle de supervision dans le thread principal
    5. Chaque cycle : collecte → analyse → stockage → alerte → affichage
    6. Ctrl+C pour arrêt propre
=============================================================================
"""

import json
import time
import signal
import sys
import os

from src.collecte       import ping, check_url
from src.analyse        import analyser
from src.alerte         import alerte_console, alerte_journal
from src.stockage       import sauvegarder_evenement as sauvegarder_resultat
from src.affichage      import afficher_tableau, enregistrer_alerte
from src.config_manager import (
    charger_configuration,
    get_intervalle,
    est_mode_debug,
    est_mode_une_seule_fois,
    get_seuil_ok_icmp,
    get_seuil_ok_http,
)
from src.scanner import scanner_et_mettre_a_jour

# =============================================================================
# CONSTANTES
# =============================================================================

CHEMIN_CIBLES = "data/cibles.json"


# =============================================================================
# SCAN AUTOMATIQUE AU PREMIER LANCEMENT
# =============================================================================

def verifier_et_scanner_si_necessaire():
    """
    Vérifie si cibles.json existe et contient des équipements.
    Si non, lance le scanner automatiquement.
    """
    cibles_path = CHEMIN_CIBLES
    
    # Si le fichier n'existe pas
    if not os.path.exists(cibles_path):
        print("[INFO] Aucune cible configurée. Lancement du scan automatique...")
        from src.scanner import scanner_et_mettre_a_jour
        scanner_et_mettre_a_jour(forcer=True)  # ← aligné avec le from
        return
    
    # Si le fichier existe mais ne contient pas de cibles
    try:
        with open(cibles_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            cibles = data.get("cibles", [])
            if not cibles:
                print("[INFO] Aucune cible dans cibles.json. Lancement du scan automatique...")
                from scanner import scanner_et_mettre_a_jour
                scanner_et_mettre_a_jour(forcer=True)
    except (json.JSONDecodeError, Exception):
        print("[INFO] Fichier cibles.json corrompu. Lancement du scan automatique...")
        from scanner import scanner_et_mettre_a_jour
        scanner_et_mettre_a_jour(forcer=True)


# =============================================================================
# GESTION DE L'ARRÊT PROPRE (Ctrl+C)
# =============================================================================

_arret_demande = False


def _arreter(signum, frame):
    """Intercepte Ctrl+C pour un arrêt propre sans stacktrace."""
    global _arret_demande
    _arret_demande = True
    print("\n[INFO] Arrêt demandé — fin du cycle en cours puis arrêt...")


signal.signal(signal.SIGINT, _arreter)


# =============================================================================
# CHARGEMENT DES CIBLES
# =============================================================================

def charger_cibles():
    """
    Charge la liste des équipements depuis data/cibles.json.

    Structure attendue :
    {
        "cibles": [
            {"nom": "DNS Google",  "adresse": "8.8.8.8",            "type": "ping"},
            {"nom": "Google Web",  "adresse": "https://google.com",  "type": "http"}
        ]
    }

    Returns:
        list : Liste des cibles (dicts)
    """
    try:
        with open(CHEMIN_CIBLES, "r", encoding="utf-8") as f:
            data = json.load(f)
        cibles = data.get("cibles", [])
        if not cibles:
            print(f"[AVERTISSEMENT] Aucune cible dans '{CHEMIN_CIBLES}'.")
        return cibles

    except FileNotFoundError:
        print(f"[ERREUR] Fichier de cibles introuvable : '{CHEMIN_CIBLES}'")
        print(f"[ERREUR] Créez le fichier avec au moins une cible et relancez.")
        sys.exit(1)

    except json.JSONDecodeError as e:
        print(f"[ERREUR] '{CHEMIN_CIBLES}' est mal formé : {e}")
        sys.exit(1)


# =============================================================================
# COLLECTE D'UNE CIBLE
# =============================================================================

def collecter_cible(cible, mode_debug=False):
    """
    Effectue la vérification d'une cible (ping ICMP ou HTTP).
    Mesure le temps de réponse et retourne un résultat normalisé.

    Statuts possibles : "OK" ou "ANOMALIE" uniquement.
    Les seuils de latence sont lus depuis config.json (P3-4).

    Args:
        cible      (dict) : {"nom", "adresse", "type"}
        mode_debug (bool) : Affiche des logs détaillés si True

    Returns:
        dict : {"cible", "statut", "message"} ou None si type inconnu
    """
    nom     = cible.get("nom",     "Inconnu")
    adresse = cible.get("adresse", "")
    type_   = cible.get("type",    "").lower()

    if mode_debug:
        print(f"[DEBUG] Vérification de '{nom}' ({adresse}) via {type_.upper()}")

    # ── Collecte ICMP ─────────────────────────────────────────────────────────
    if type_ == "ping":
        debut     = time.time()
        joignable = ping(adresse)
        temps_ms  = (time.time() - debut) * 1000 if joignable else None

        # Seuil OK lu depuis config.json — au-dessus → ANOMALIE
        seuil = get_seuil_ok_icmp()
        if joignable and temps_ms is not None and temps_ms <= seuil:
            statut  = "OK"
            message = f"Réponse en {temps_ms:.0f}ms"
        elif joignable:
            # Joignable mais trop lent → ANOMALIE
            statut  = "ANOMALIE"
            message = f"Trop lent : {temps_ms:.0f}ms (seuil : {seuil}ms)"
        else:
            statut  = "ANOMALIE"
            message = "Timeout — hôte injoignable"

    # ── Collecte HTTP ─────────────────────────────────────────────────────────
    elif type_ == "http":
        debut     = time.time()
        joignable = check_url(adresse)
        temps_ms  = (time.time() - debut) * 1000 if joignable else None

        seuil = get_seuil_ok_http()
        if joignable and temps_ms is not None and temps_ms <= seuil:
            statut  = "OK"
            message = f"Réponse en {temps_ms:.0f}ms"
        elif joignable:
            statut  = "ANOMALIE"
            message = f"Trop lent : {temps_ms:.0f}ms (seuil : {seuil}ms)"
        else:
            statut  = "ANOMALIE"
            message = "Site inaccessible"

    # ── Type inconnu ──────────────────────────────────────────────────────────
    else:
        print(f"[AVERTISSEMENT] Type '{type_}' inconnu pour '{nom}' — ignoré.")
        return None

    if mode_debug:
        print(f"[DEBUG] '{nom}' → {statut} ({message})")

    return {
        "cible"  : nom,
        "statut" : statut,
        "message": message,
    }


# =============================================================================
# BOUCLE DE SUPERVISION
# =============================================================================

def boucle_supervision(cibles, intervalle, mode_debug=False, une_seule_fois=False):
    """
    Boucle principale de supervision (P2-7 + P3-4).

    Tourne indéfiniment jusqu'à Ctrl+C, sauf si mode "une seule fois"
    est activé dans config.json — dans ce cas, 1 cycle puis arrêt (P3-4 bonus).

    À chaque cycle :
        1. Collecte chaque cible (ICMP ou HTTP)
        2. Sauvegarde le résultat dans historique.json
        3. Déclenche les alertes si ANOMALIE
        4. Mémorise la dernière anomalie (zone d'alerte P2-8)
        5. Rafraîchit l'affichage (P2-6)
        6. Attend l'intervalle configuré avant le prochain cycle

    Args:
        cibles         (list) : Équipements à superviser
        intervalle     (int)  : Secondes entre chaque cycle (P3-4 : depuis config.json)
        mode_debug     (bool) : Logs détaillés si True
        une_seule_fois (bool) : 1 cycle puis arrêt si True (P3-4 bonus)
    """
    global _arret_demande
    numero_cycle = 0

    if une_seule_fois:
        print("[INFO] Mode 'une seule fois' actif — 1 cycle puis arrêt automatique.")

    while not _arret_demande:
        numero_cycle += 1
        resultats_cycle = []
        debut_cycle     = time.time()

        if mode_debug:
            print(f"\n[DEBUG] ── Cycle #{numero_cycle} démarré ──")

        # ── 1. Collecte de toutes les cibles ─────────────────────────────────
        for cible in cibles:
            resultat = collecter_cible(cible, mode_debug)

            if resultat is None:
                continue  # type inconnu → ignoré

            # ── 2. Sauvegarde JSON ────────────────────────────────────────────
            sauvegarder_resultat(
                resultat["cible"],
                cible.get("type", "ping"),
                resultat["statut"],
                resultat["message"],
            )

            # ── 3. Alertes et mémorisation zone d'alerte (P2-8) ──────────────
            if resultat["statut"] == "ANOMALIE":
                msg_alerte = f"{resultat['cible']} : {resultat['message']}"
                alerte_console(msg_alerte)
                alerte_journal(msg_alerte)
                enregistrer_alerte(resultat["cible"], resultat["message"])

            resultats_cycle.append(resultat)

        # ── 4. Rafraîchissement de l'affichage (P2-6 + P3-4) ─────────────────
        timestamp    = time.strftime("%d/%m/%Y %H:%M:%S")
        temps_ecoule = time.time() - debut_cycle
        afficher_tableau(resultats_cycle, timestamp, intervalle)

        if mode_debug:
            print(f"[DEBUG] Cycle #{numero_cycle} terminé en {temps_ecoule:.2f}s")

        # ── 5. Mode "une seule fois" — arrêt après 1 cycle (P3-4 bonus) ──────
        if une_seule_fois:
            print(f"\n[INFO] Mode 'une seule fois' : cycle #{numero_cycle} exécuté. Arrêt.")
            break

        # ── 6. Attente interruptible avant le prochain cycle ──────────────────
        temps_restant = max(0, intervalle - temps_ecoule)
        for _ in range(int(temps_restant)):
            if _arret_demande:
                break
            time.sleep(1)


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

def main():
    """
    Point d'entrée principal.

    Ordre de démarrage (P3-4 + scan automatique) :
        0. Si cibles.json est vide ou inexistant → scan automatique
        1. Charge config.json → paramètres globaux
        2. Charge cibles.json → équipements à superviser
        3. Lance la boucle avec les paramètres configurés
    """
    print("=" * 55)
    print("   SUPERVISION RÉSEAU — SAE 2.03 — Groupe 2")
    print("=" * 55)

    # ── Étape 0 : Scan automatique si nécessaire ─────────────────────────────
    verifier_et_scanner_si_necessaire()

    # ── Étape 1 : Chargement de la configuration (P3-4) ──────────────────────
    charger_configuration()
    intervalle     = get_intervalle()
    mode_debug     = est_mode_debug()
    une_seule_fois = est_mode_une_seule_fois()

    # ── Étape 2 : Chargement des cibles ──────────────────────────────────────
    cibles = charger_cibles()
    print(f"[INFO] {len(cibles)} cible(s) chargée(s) depuis '{CHEMIN_CIBLES}'")
    print(f"[INFO] Intervalle : {intervalle}s  |  "
          f"Debug : {mode_debug}  |  "
          f"Une seule fois : {une_seule_fois}")
    print("[INFO] Démarrage... (Ctrl+C pour arrêter)\n")

    # ── Étape 3 : Lancement de la boucle ─────────────────────────────────────
    boucle_supervision(cibles, intervalle, mode_debug, une_seule_fois)

    print("\n[INFO] Supervision arrêtée proprement.")
    print("=" * 55)


if __name__ == "__main__":
    main()
