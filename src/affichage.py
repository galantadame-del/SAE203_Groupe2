"""
=============================================================================
Module : affichage.py
Projet : SAE 2.03 – Logiciel de supervision réseau
Auteurs : Groupe 2
Version : 2.0

Tâches couvertes :
    - P2-6 : Lier la collecte au tableau (afficher_tableau)
    - P2-8 : Zone d'alerte basique (enregistrer_alerte, _afficher_zone_alerte)
    - P3-3 : Amélioration de l'interface
        * En-tête avec date et heure
        * Résumé OK / DÉGRADÉ / ANOMALIE
        * Tableau des cibles trié (anomalies en premier)
        * Barre de progression pour le temps restant
        * Heure de la prochaine vérification
    - P3-4 : Paramétrage indirect (affichage de l'intervalle configurable)

Rôle :
    Affiche un tableau de bord professionnel dans le terminal :
        - En-tête avec nom du logiciel et date du jour
        - Résumé OK / DÉGRADÉ / ANOMALIE
        - Tableau des cibles trié (anomalies en premier)
        - Barre de progression pour le temps restant
        - Heure de la prochaine vérification
        - Zone d'alerte avec dernière anomalie

Dépendances :
    - os (natif) : effacement du terminal (cls/clear)
    - time (natif) : gestion des temporisations (indirect)
    - datetime (natif) : horodatage des alertes et calculs d'heure

Aucune dépendance externe requise.
=============================================================================
"""

import os
import time
from datetime import datetime, timedelta


# =============================================================================
# COULEURS TERMINAL (ANSI)
# =============================================================================
# Palette étendue pour P3-3 : ajout de CYAN, MAGENTA, BLANC, DIM
# Permet un affichage plus professionnel et lisible.

VERT    = "\033[92m"   # Succès / équipement OK
ROUGE   = "\033[91m"   # Erreur / anomalie critique
JAUNE   = "\033[93m"   # Attention / état dégradé
BLEU    = "\033[94m"   # Informations générales
CYAN    = "\033[96m"   # Temps de réponse, barre de progression
MAGENTA = "\033[95m"   # Éléments distinctifs (non utilisé ici)
GRIS    = "\033[90m"   # Informations secondaires (séparateurs, heures)
BLANC   = "\033[97m"   # En-tête principal
RESET   = "\033[0m"    # Réinitialisation
BOLD    = "\033[1m"    # Gras
DIM     = "\033[2m"    # Atténué (pour les séparateurs)


# =============================================================================
# DIMENSIONS DU TABLEAU (P3-3)
# =============================================================================
# Ajustées pour un affichage équilibré sur terminal standard.
# LARGEUR_TOTALE = 72 (compatible avec la plupart des terminaux)

LARGEUR_TOTALE  = 72       # Largeur totale de l'affichage
LARGEUR_NOM     = 28       # Col. équipement
LARGEUR_STATUT  = 12       # Col. statut (OK/DEGRADE/ANOMALIE)
LARGEUR_TEMPS   = 14       # Col. temps de réponse
LARGEUR_MESSAGE = 30       # Col. message


# =============================================================================
# VARIABLE GLOBALE — dernière alerte mémorisée (P2-8)
# =============================================================================
# Stocke la dernière anomalie détectée pour l'afficher dans la zone d'alerte.
# Persiste entre les cycles de supervision.
# Structure : {"cible": str, "message": str, "heure": str}

_derniere_alerte = None


# =============================================================================
# FONCTIONS UTILITAIRES INTERNES (préfixe _)
# =============================================================================

def _effacer_terminal():
    """
    Efface le terminal pour simuler un rafraîchissement.
    Compatible Windows (cls) et Unix/Linux/Mac (clear).
    Appelée avant chaque affichage (P2-7, P3-3).
    """
    os.system("cls" if os.name == "nt" else "clear")


def _ligne(car="─", largeur=LARGEUR_TOTALE):
    """
    Retourne une ligne de séparation de la largeur spécifiée.

    Args:
        car (str): Caractère utilisé pour la ligne (défaut: "─")
        largeur (int): Longueur de la ligne

    Returns:
        str: Ligne de caractères répétés
    """
    return car * largeur


def _centrer(texte, largeur=LARGEUR_TOTALE):
    """
    Centre un texte sur la largeur donnée en ignorant les codes de couleur ANSI.

    Args:
        texte (str): Texte contenant éventuellement des codes ANSI
        largeur (int): Largeur totale disponible

    Returns:
        str: Texte centré avec espaces (codes ANSI préservés)
    """
    texte_pur = texte
    # Supprime tous les codes ANSI pour calculer la longueur réelle
    for code in [VERT, ROUGE, JAUNE, BLEU, CYAN, MAGENTA, GRIS, BLANC,
                 RESET, BOLD, DIM, "\033[91m", "\033[92m", "\033[93m",
                 "\033[94m", "\033[95m", "\033[96m", "\033[97m", "\033[90m"]:
        texte_pur = texte_pur.replace(code, "")
    padding = max(0, (largeur - len(texte_pur)) // 2)
    return " " * padding + texte


def _formater_statut(statut):
    """
    Retourne le statut coloré avec icône (P3-3).

    Args:
        statut (str): "OK", "DÉGRADÉ" ou "ANOMALIE"

    Returns:
        str: Statut coloré avec padding de 12 caractères
    """
    if statut == "OK":
        return f"{VERT}{BOLD}✅ UP      {RESET}"      # 12 caractères
    elif statut == "DÉGRADÉ":
        return f"{JAUNE}{BOLD}⚠️  DÉGRADÉ {RESET}"    # 12 caractères
    else:
        return f"{ROUGE}{BOLD}❌ DOWN    {RESET}"      # 12 caractères


def _formater_temps(message):
    """
    Extrait et formate le temps de réponse depuis le message (P3-3).

    Args:
        message (str): Ex. "Réponse en 143ms"

    Returns:
        str: Temps formaté avec couleur, ou "—" en gris
    """
    if "ms" in message:
        try:
            for partie in message.split():
                if "ms" in partie:
                    temps = partie.replace("ms", "")
                    return f"{CYAN}{temps + ' ms':<14}{RESET}"
        except (ValueError, IndexError):
            pass
    return f"{GRIS}{'—':<14}{RESET}"


def _trier_resultats(resultats):
    """
    Trie les résultats : ANOMALIE en premier, puis DÉGRADÉ, puis OK (P3-3).

    Args:
        resultats (list): Liste de dicts avec clé "statut"

    Returns:
        list: Liste triée par ordre de criticité
    """
    ordre = {"ANOMALIE": 0, "DÉGRADÉ": 1, "OK": 2}
    return sorted(resultats, key=lambda r: ordre.get(r.get("statut", "OK"), 2))


# =============================================================================
# BLOCS D'AFFICHAGE (P3-3)
# =============================================================================

def _afficher_entete():
    """
    Affiche l'en-tête du tableau de bord (P3-3) :
    - Nom du logiciel
    - Date et heure du jour
    """
    now = datetime.now()
    date_str = now.strftime("%A %d %B %Y").capitalize()
    heure_str = now.strftime("%H:%M:%S")

    print()
    print(f"  {BOLD}{CYAN}{_ligne('═')}{RESET}")
    print(_centrer(f"{BOLD}{BLANC}  🖥️  SUPERVISION RÉSEAU — SAE 2.03  {RESET}"))
    print(_centrer(f"{GRIS}{date_str}  •  {heure_str}{RESET}"))
    print(f"  {BOLD}{CYAN}{_ligne('═')}{RESET}")


def _afficher_resume(resultats):
    """
    Affiche le résumé en haut du tableau de bord (P3-3) :
    nombre de cibles OK / DÉGRADÉ / ANOMALIE.

    Args:
        resultats (list): Liste des résultats du cycle courant
    """
    nb_ok       = sum(1 for r in resultats if r.get("statut") == "OK")
    nb_degrade  = sum(1 for r in resultats if r.get("statut") == "DÉGRADÉ")
    nb_anomalie = sum(1 for r in resultats if r.get("statut") == "ANOMALIE")

    print()
    print(f"  {BOLD}{_ligne('─')}{RESET}")
    print(_centrer(f"{BOLD}DASHBOARD SUPERVISION{RESET}"))
    print(f"  {BOLD}{_ligne('─')}{RESET}")
    print(
        _centrer(
            f"{VERT}{BOLD}✅ OK : {nb_ok}{RESET}"
            f"  {DIM}|{RESET}  "
            f"{JAUNE}{BOLD}⚠️  DÉGRADÉ : {nb_degrade}{RESET}"
            f"  {DIM}|{RESET}  "
            f"{ROUGE}{BOLD}❌ ANOMALIE : {nb_anomalie}{RESET}"
        )
    )
    print(f"  {BOLD}{_ligne('─')}{RESET}")
    print()


def _afficher_tableau(resultats):
    """
    Affiche le tableau des cibles, trié par priorité d'alerte (P3-3).
    Les anomalies apparaissent en premier, puis les dégradés, puis les OK.

    Args:
        resultats (list): Liste des résultats du cycle courant
    """
    # En-têtes colonnes
    print(
        f"  {BOLD}{BLANC}"
        f"{'ÉQUIPEMENT':<{LARGEUR_NOM}}"
        f"{'STATUT':<{LARGEUR_STATUT}}"
        f"{'TEMPS':<{LARGEUR_TEMPS}}"
        f"{'MESSAGE':<{LARGEUR_MESSAGE}}"
        f"{RESET}"
    )
    print(f"  {_ligne('─')}")

    if not resultats:
        print(f"  {GRIS}Aucun résultat disponible.{RESET}")
        return

    # Tri : anomalies en premier
    resultats_tries = _trier_resultats(resultats)

    precedent_statut = None
    for r in resultats_tries:
        statut  = r.get("statut", "ANOMALIE")
        cible   = str(r.get("cible",   "—"))[:LARGEUR_NOM]
        message = str(r.get("message", "—"))[:LARGEUR_MESSAGE]

        # Ligne de séparation légère entre les groupes de statuts
        if precedent_statut is not None and statut != precedent_statut:
            print(f"  {GRIS}{_ligne('·')}{RESET}")

        print(
            f"  {cible:<{LARGEUR_NOM}}"
            f"{_formater_statut(statut)}"
            f"{_formater_temps(message)}"
            f"{message:<{LARGEUR_MESSAGE}}"
        )
        precedent_statut = statut

    print(f"  {_ligne('─')}")


def _afficher_barre_progression(intervalle, temps_ecoule):
    """
    Affiche une barre de progression pour le temps restant (P3-3, P3-4).

    Args:
        intervalle   (int): Durée totale du cycle en secondes
        temps_ecoule (float): Secondes déjà écoulées dans le cycle
    """
    temps_restant = max(0, intervalle - temps_ecoule)
    pourcentage   = min(1.0, temps_ecoule / intervalle) if intervalle > 0 else 1.0

    largeur_barre = 40
    nb_rempli     = int(pourcentage * largeur_barre)
    nb_vide       = largeur_barre - nb_rempli

    barre = f"{VERT}{'█' * nb_rempli}{GRIS}{'░' * nb_vide}{RESET}"

    prochaine = (datetime.now() + timedelta(seconds=temps_restant)).strftime("%H:%M:%S")

    print()
    print(f"  {GRIS}Prochain cycle  {RESET}[{barre}{RESET}]  "
          f"{CYAN}{int(temps_restant)}s{RESET}  "
          f"{GRIS}(à {prochaine}){RESET}")


def _afficher_zone_alerte():
    """
    Affiche la zone d'alerte avec la dernière anomalie mémorisée (P2-8).
    Affiche un message rassurant si aucune anomalie n'a été détectée.
    """
    print()
    print(f"  {BOLD}{_ligne('─')}{RESET}")
    print(f"  {BOLD}🔔  DERNIÈRE ALERTE{RESET}")
    print(f"  {_ligne('─')}")

    if _derniere_alerte is None:
        print(f"  {VERT}✔  Aucune anomalie détectée depuis le démarrage.{RESET}")
    else:
        print(f"  {ROUGE}{BOLD}⚠  {_derniere_alerte['cible']}{RESET}")
        print(f"  {JAUNE}   Problème : {_derniere_alerte['message']}{RESET}")
        print(f"  {GRIS}   Détectée : {_derniere_alerte['heure']}{RESET}")

    print(f"  {_ligne('─')}")
    print(f"  {GRIS}Ctrl+C pour arrêter la supervision.{RESET}")
    print()


# =============================================================================
# FONCTIONS PUBLIQUES — appelées depuis main.py
# =============================================================================

def afficher_tableau(resultats, timestamp, intervalle):
    """
    POINT D'ENTRÉE PRINCIPAL DE L'AFFICHAGE (P2-6, P3-3).
    Appelée à chaque fin de cycle dans main.py.

    Déroulement :
        1. Efface le terminal
        2. Affiche l'en-tête (nom logiciel + date)
        3. Affiche le résumé OK / DÉGRADÉ / ANOMALIE
        4. Affiche le tableau des cibles (trié par criticité)
        5. Affiche la barre de progression (P3-3, P3-4)
        6. Affiche la zone d'alerte (P2-8)

    Args:
        resultats  (list) : Liste de dicts {"cible", "statut", "message"}
        timestamp  (str)  : Horodatage du cycle (actuellement non utilisé)
        intervalle (int)  : Secondes entre chaque cycle (P3-4)
    """
    _effacer_terminal()
    _afficher_entete()
    _afficher_resume(resultats)
    _afficher_tableau(resultats)
    _afficher_barre_progression(intervalle, temps_ecoule=0)  # P3-3, P3-4
    _afficher_zone_alerte()  # P2-8


def enregistrer_alerte(cible, message):
    """
    Mémorise la dernière anomalie pour l'afficher dans la zone d'alerte (P2-8).
    À appeler depuis main.py dès qu'une anomalie est détectée.

    Args:
        cible   (str): Nom de l'équipement en anomalie
        message (str): Description du problème
    """
    global _derniere_alerte
    _derniere_alerte = {
        "cible":   cible,
        "message": message,
        "heure":   datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }


# =============================================================================
# NOTE : La fonction reinitialiser_alerte() pourrait être ajoutée ici
# pour permettre d'effacer l'alerte quand tout redevient OK (bonus).
# =============================================================================
