"""
=============================================================================
Module : affichage.py
Projet : SAE 2.03 – Logiciel de supervision réseau
Auteurs : Groupe 2
Version : 1.0

Tâches couvertes :
    - P2-6 : Lier la collecte au tableau (afficher_tableau)
    - P2-7 : Rafraîchissement automatique de l'affichage (_effacer_terminal)
    - P2-8 : Zone d'alerte (enregistrer_alerte, _afficher_zone_alerte)

Rôle :
    Affiche dans le terminal un tableau de supervision mis à jour
    en temps réel, avec une zone d'alerte affichant la dernière anomalie.

Dépendances :
    - os (natif) : effacement du terminal (cls/clear)
    - datetime (natif) : horodatage des alertes

Aucune dépendance externe requise.
=============================================================================
"""

import os
from datetime import datetime


# =============================================================================
# CONSTANTES — couleurs terminal (ANSI)
# =============================================================================
# Compatibles avec la majorité des terminaux modernes (Linux, Mac, Windows depuis
# Windows 10). VERT et ROUGE pour les statuts, JAUNE pour les alertes,
# BLEU pour l'en-tête, GRIS pour les informations secondaires.

VERT   = "\033[92m"   # Succès / équipement OK
ROUGE  = "\033[91m"   # Erreur / anomalie
JAUNE  = "\033[93m"   # Attention / zone d'alerte
BLEU   = "\033[94m"   # En-tête, informations générales
GRIS   = "\033[90m"   # Informations secondaires (horodatage, temps restant)
RESET  = "\033[0m"    # Réinitialisation des couleurs
BOLD   = "\033[1m"    # Gras (mise en évidence)

# Largeurs des colonnes pour l'affichage tabulaire (P2-6)
# Ajustées pour un affichage lisible sur terminal standard (80-120 colonnes)
LARGEUR_NOM     = 30   # Nom de l'équipement
LARGEUR_STATUT  = 10   # Statut (UP / DOWN)
LARGEUR_TEMPS   = 18   # Temps de réponse en ms
LARGEUR_MESSAGE = 35   # Message détaillé


# =============================================================================
# VARIABLE GLOBALE — dernière alerte mémorisée (P2-8)
# =============================================================================
# Stocke la dernière anomalie détectée pour l'afficher dans la zone d'alerte.
# Persiste entre les cycles de supervision.
# Structure : {"cible": str, "message": str, "heure": str}
# Peut être réinitialisée avec reinitialiser_alerte() (bonus).

_derniere_alerte = None


# =============================================================================
# FONCTIONS INTERNES (préfixe _) — usage interne uniquement
# =============================================================================

def _effacer_terminal():
    """
    Efface le terminal pour simuler un rafraîchissement (P2-7).
    Compatible Windows (cls) et Unix/Linux/Mac (clear).
    Appelée avant chaque affichage pour éviter l'accumulation.
    """
    os.system("cls" if os.name == "nt" else "clear")


def _formater_statut(statut):
    """
    Retourne le statut coloré pour l'affichage.
    - OK → "UP" en vert gras
    - Autre → "DOWN" en rouge gras

    Args:
        statut (str): "OK" ou autre (ANOMALIE, DEGRADE, etc.)

    Returns:
        str: Texte formaté avec codes ANSI
    """
    if statut == "OK":
        return f"{VERT}{BOLD}{'UP':<10}{RESET}"
    else:
        return f"{ROUGE}{BOLD}{'DOWN':<10}{RESET}"


def _formater_temps(message):
    """
    Extrait et formate le temps de réponse depuis le message de collecte.
    Recherche un motif "Xms" et l'isole.

    Args:
        message (str): Message de la collecte (ex: "Réponse en 45ms")

    Returns:
        str: Temps formaté avec couleur, ou "—" en gris si non trouvé
    """
    if "ms" in message:
        try:
            for partie in message.split():
                if "ms" in partie:
                    temps = partie.replace("ms", "")
                    return f"{BLEU}{temps + ' ms':<18}{RESET}"
        except (ValueError, IndexError):
            pass
    return f"{GRIS}{'—':<18}{RESET}"


def _ligne_separateur(car="-"):
    """
    Génère une ligne séparatrice de la largeur totale du tableau.
    Utilisée pour délimiter les sections (en-tête, données, pied).

    Args:
        car (str): Caractère utilisé pour la ligne (défaut: "-")

    Returns:
        str: Ligne de caractères répétés
    """
    total = LARGEUR_NOM + LARGEUR_STATUT + LARGEUR_TEMPS + LARGEUR_MESSAGE + 13
    return car * total


# =============================================================================
# ZONE D'ALERTE — P2-8
# =============================================================================

def enregistrer_alerte(cible, message):
    """
    Mémorise la dernière anomalie détectée pour l'afficher dans la zone d'alerte.
    À appeler depuis main.py dès qu'une anomalie est détectée.

    Args:
        cible   (str): Nom de l'équipement en anomalie
        message (str): Description du problème

    Cette fonction est le point d'entrée principal pour la P2-8.
    L'alerte reste affichée jusqu'à la prochaine anomalie (ou réinitialisation).
    """
    global _derniere_alerte
    _derniere_alerte = {
        "cible":   cible,
        "message": message,
        "heure":   datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }


def reinitialiser_alerte():
    """
    Réinitialise la zone d'alerte (bonus - P2-8 étendu).
    À appeler lorsqu'aucune anomalie n'est détectée sur l'ensemble des cibles.
    Permet d'effacer l'affichage de la dernière anomalie quand tout est revenu à OK.
    """
    global _derniere_alerte
    _derniere_alerte = None


def _afficher_zone_alerte():
    """
    Affiche la zone d'alerte dans le terminal (appelée par afficher_tableau).
    Montre la dernière anomalie mémorisée, ou un message OK si aucune alerte.
    """
    print()
    print(f"{BOLD}  ── ZONE D'ALERTE ─────────────────────────────────────{RESET}")

    if _derniere_alerte is None:
        print(f"  {VERT}✔  Aucune anomalie détectée.{RESET}")
    else:
        print(f"  {ROUGE}{BOLD}⚠  DERNIÈRE ANOMALIE DÉTECTÉE{RESET}")
        print(f"  {JAUNE}Équipement : {_derniere_alerte['cible']}{RESET}")
        print(f"  {JAUNE}Problème   : {_derniere_alerte['message']}{RESET}")
        print(f"  {GRIS}Heure      : {_derniere_alerte['heure']}{RESET}")

    print(f"{BOLD}  ────────────────────────────────────────────────────────{RESET}")


# =============================================================================
# FONCTION PRINCIPALE — appelée depuis main.py (P2-6, P2-7, P2-8)
# =============================================================================

def afficher_tableau(resultats, timestamp, intervalle):
    """
    Point d'entrée principal pour l'affichage.
    Appelée à chaque fin de cycle dans main.py.

    Déroulement :
        1. Efface le terminal (P2-7)
        2. Affiche l'en-tête avec timestamp et temps restant (P2-7)
        3. Affiche les en-têtes de colonnes
        4. Affiche chaque ligne de résultat (P2-6)
        5. Affiche les statistiques (UP / DOWN / Total)
        6. Affiche la zone d'alerte (P2-8)

    Args:
        resultats  (list): Liste de dicts avec clés "cible", "statut", "message"
        timestamp  (str) : Horodatage du cycle (format DD/MM/YYYY HH:MM:SS)
        intervalle (int) : Secondes avant le prochain cycle (affiché dans l'en-tête)
    """
    _effacer_terminal()   # P2-7 : rafraîchissement automatique

    # ── En-tête (P2-7 : affichage du temps restant) ────────────────────────
    print(f"\n{BOLD}{BLEU}  SUPERVISION RÉSEAU — SAE 2.03{RESET}")
    print(f"  {GRIS}Dernière mise à jour : {timestamp}   "
          f"Prochain cycle dans : {intervalle}s{RESET}")
    print()

    # ── En-têtes colonnes ────────────────────────────────────────────────────
    print(_ligne_separateur("="))
    print(
        f"  {BOLD}{'ÉQUIPEMENT':<{LARGEUR_NOM}}"
        f"{'STATUT':<{LARGEUR_STATUT}}"
        f"{'TEMPS RÉPONSE':<{LARGEUR_TEMPS}}"
        f"{'MESSAGE':<{LARGEUR_MESSAGE}}{RESET}"
    )
    print(_ligne_separateur("="))

    # ── Lignes de données (P2-6) ────────────────────────────────────────────
    if not resultats:
        print(f"  {GRIS}Aucun résultat disponible.{RESET}")
    else:
        for r in resultats:
            cible   = str(r.get("cible",   "—"))[:LARGEUR_NOM]
            statut  = r.get("statut",  "ANOMALIE")
            message = str(r.get("message", "—"))[:LARGEUR_MESSAGE]

            print(
                f"  {cible:<{LARGEUR_NOM}}"
                f"{_formater_statut(statut)}"
                f"{_formater_temps(message)}"
                f"{message:<{LARGEUR_MESSAGE}}"
            )

    # ── Statistiques ─────────────────────────────────────────────────────────
    print(_ligne_separateur("-"))
    nb_ok       = sum(1 for r in resultats if r.get("statut") == "OK")
    nb_anomalie = len(resultats) - nb_ok
    print(
        f"\n  {VERT}✔ UP : {nb_ok}{RESET}   "
        f"{ROUGE}✘ DOWN : {nb_anomalie}{RESET}   "
        f"{GRIS}Total : {len(resultats)}{RESET}"
    )

    # ── Zone d'alerte (P2-8) ─────────────────────────────────────────────────
    _afficher_zone_alerte()

    print(f"  {GRIS}Appuyez sur Ctrl+C pour arrêter.{RESET}\n")
