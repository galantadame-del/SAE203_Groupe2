"""
=============================================================================
Module : collecte.py
Projet : SAE 2.03 – Logiciel de supervision réseau
Auteurs : Groupe 2
Version : 1.0
=============================================================================

Rôle de ce module :
    Ce module est responsable de la COLLECTE des données réseau.
    Il fournit des fonctions permettant de tester la disponibilité
    des équipements supervisés via le protocole ICMP (ping).

Dépendances :
    - subprocess  : exécution de la commande ping système (natif Python)
    - platform    : détection du système d'exploitation (natif Python)
    - socket      : résolution DNS et vérification de connectivité (natif Python)
    - datetime    : horodatage des résultats (natif Python)

Aucune dépendance externe requise.
=============================================================================
"""

import subprocess
import platform
import socket
from datetime import datetime


# =============================================================================
# CONSTANTES
# =============================================================================

# Statuts possibles retournés par les fonctions de collecte
STATUT_OK      = "OK"
STATUT_ANOMALIE = "ANOMALIE"


# =============================================================================
# FONCTIONS UTILITAIRES INTERNES
# =============================================================================

def _construire_commande_ping(ip: str, timeout: int) -> list:
    """
    Construit la commande ping adaptée au système d'exploitation.

    Le paramètre de timeout et de nombre de paquets diffère entre
    Windows et les systèmes Unix/Linux/macOS :
        - Windows : -n (nombre de paquets), -w (timeout en millisecondes)
        - Unix    : -c (nombre de paquets), -W (timeout en secondes)

    Args:
        ip      (str) : Adresse IP ou nom d'hôte cible.
        timeout (int) : Délai maximum d'attente en secondes.

    Returns:
        list : Commande ping sous forme de liste pour subprocess.
    """
    systeme = platform.system().lower()

    if systeme == "windows":
        # -n 1         : envoyer 1 seul paquet
        # -w <timeout> : timeout en millisecondes
        return ["ping", "-n", "1", "-w", str(timeout * 1000), ip]
    else:
        # Linux / macOS / autres Unix
        # -c 1         : envoyer 1 seul paquet
        # -W <timeout> : timeout en secondes
        return ["ping", "-c", "1", "-W", str(timeout), ip]


def _resoudre_hote(ip: str) -> bool:
    """
    Vérifie si un nom d'hôte peut être résolu en adresse IP (DNS).

    Cette vérification préalable permet de distinguer une machine
    injoignable d'un nom d'hôte invalide/inconnu.

    Args:
        ip (str) : Adresse IP ou nom d'hôte à résoudre.

    Returns:
        bool : True si la résolution DNS réussit, False sinon.
    """
    try:
        socket.gethostbyname(ip)
        return True
    except socket.gaierror:
        # Erreur de résolution DNS : nom d'hôte inconnu
        return False


# =============================================================================
# FONCTION PRINCIPALE : ping()
# =============================================================================

def ping(ip: str, timeout: int = 2) -> bool:
    """
    Vérifie si une machine répond au ping ICMP.

    Cette fonction utilise la commande ping du système d'exploitation
    via subprocess, ce qui ne nécessite aucune dépendance externe.
    Elle est compatible Windows, Linux et macOS.

    Fonctionnement :
        1. Vérifie que le nom d'hôte est résolvable (DNS)
        2. Exécute la commande ping système (1 seul paquet)
        3. Analyse le code de retour (0 = succès, autre = échec)
        4. Gère toutes les exceptions possibles

    Args:
        ip      (str) : Adresse IP (ex: "192.168.1.1") ou nom d'hôte
                        (ex: "google.com") de la machine à tester.
        timeout (int) : Délai maximum en secondes avant de considérer
                        la machine comme injoignable. Défaut : 2 secondes.

    Returns:
        bool :
            - True  → la machine répond au ping (joignable)
            - False → la machine ne répond pas (injoignable, timeout,
                      nom d'hôte invalide, réseau indisponible)

    Exemples:
        >>> ping("8.8.8.8")
        True
        >>> ping("192.168.99.99")
        False
        >>> ping("google.com")
        True
        >>> ping("site-qui-n-existe-pas.com")
        False
        >>> ping("192.168.1.1", timeout=5)
        True
    """

    # --- Étape 1 : Vérification de la résolution DNS ---
    # Inutile d'envoyer un ping si le nom d'hôte est invalide
    if not _resoudre_hote(ip):
        return False

    # --- Étape 2 : Construction de la commande ping ---
    commande = _construire_commande_ping(ip, timeout)

    # --- Étape 3 : Exécution du ping ---
    try:
        resultat = subprocess.run(
            commande,
            stdout=subprocess.DEVNULL,   # On ignore la sortie standard
            stderr=subprocess.DEVNULL,   # On ignore la sortie d'erreur
            timeout=timeout + 1          # Sécurité : timeout global légèrement supérieur
        )

        # Code de retour 0 = ping réussi (machine joignable)
        # Code de retour 1 = ping échoué (machine injoignable)
        # Code de retour 2 = erreur réseau ou commande invalide
        return resultat.returncode == 0

    except subprocess.TimeoutExpired:
        # Le processus ping a dépassé le timeout global
        return False

    except subprocess.SubprocessError:
        # Erreur lors de l'exécution de la commande système
        return False

    except Exception:
        # Sécurité : capture toute autre exception inattendue
        return False


# =============================================================================
# FONCTION ENRICHIE : ping_detaille()
# =============================================================================

def ping_detaille(ip: str, timeout: int = 2) -> dict:
    """
    Version enrichie du ping retournant un dictionnaire complet.

    Contrairement à ping() qui retourne un simple booléen,
    cette fonction retourne toutes les informations utiles pour
    le stockage dans l'historique JSON et l'affichage dans l'interface.

    Args:
        ip      (str) : Adresse IP ou nom d'hôte cible.
        timeout (int) : Délai maximum en secondes. Défaut : 2 secondes.

    Returns:
        dict : Dictionnaire contenant les clés suivantes :
            - "ip"         (str)  : Adresse IP ou hôte testé
            - "statut"     (str)  : "OK" ou "ANOMALIE"
            - "joignable"  (bool) : True si la machine répond
            - "timestamp"  (str)  : Horodatage ISO de la vérification
            - "type"       (str)  : Type de vérification ("ICMP")

    Exemple de retour :
        {
            "ip"        : "8.8.8.8",
            "statut"    : "OK",
            "joignable" : True,
            "timestamp" : "2026-04-09T10:32:15",
            "type"      : "ICMP"
        }
    """
    joignable = ping(ip, timeout)

    return {
        "ip"        : ip,
        "statut"    : STATUT_OK if joignable else STATUT_ANOMALIE,
        "joignable" : joignable,
        "timestamp" : datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "type"      : "ICMP"
    }


# =============================================================================
# TESTS RAPIDES (exécution directe du fichier)
# =============================================================================

if __name__ == "__main__":
    """
    Bloc de test exécuté uniquement si on lance directement ce fichier :
        python collecte.py

    Ce bloc NE s'exécute PAS quand le module est importé depuis main.py.
    """

    print("=" * 55)
    print("   TEST DU MODULE COLLECTE — Fonction ping()")
    print("=" * 55)

    # Liste des cas de test
    cas_tests = [
        ("8.8.8.8",                    True,  "DNS Google — doit répondre"),
        ("192.168.99.99",              False, "IP inexistante — ne doit pas répondre"),
        ("google.com",                 True,  "Nom d'hôte valide — doit répondre"),
        ("site-qui-n-existe-pas.com",  False, "Hôte invalide — ne doit pas répondre"),
    ]

    tous_ok = True

    for ip, attendu, description in cas_tests:
        resultat = ping(ip)
        succes   = resultat == attendu
        statut   = "PASS" if succes else "FAIL"

        if not succes:
            tous_ok = False

        print(f"  [{statut}] ping('{ip}')")
        print(f"         → Attendu : {attendu} | Obtenu : {resultat}")
        print(f"         → {description}")
        print()

    print("-" * 55)

    # Test de la version détaillée
    print("\n  TEST ping_detaille('8.8.8.8') :")
    details = ping_detaille("8.8.8.8")
    for cle, valeur in details.items():
        print(f"    {cle:<12} : {valeur}")

    print("\n" + "=" * 55)
    resultat_global = "TOUS LES TESTS PASSES" if tous_ok else "CERTAINS TESTS ONT ECHOUE"
    print(f"  {resultat_global}")
    print("=" * 55)
