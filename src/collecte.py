"""
=============================================================================
Module : collecte.py
Projet : SAE 2.03 – Logiciel de supervision réseau
Auteurs : Groupe 2
Version : 2.0  (ajout check_url + check_url_detaillee)
=============================================================================

Rôle de ce module :
    Ce module est responsable de la COLLECTE des données réseau.
    Il fournit deux familles de fonctions :

    1. ICMP (ping)
       - ping(ip, timeout)            → bool
       - ping_detaille(ip, timeout)   → dict

    2. HTTP (check_url)
       - check_url(url, timeout)             → bool
       - check_url_detaillee(url, timeout)   → dict

Dépendances :
    Natives Python (aucune installation) :
        - subprocess  : exécution commande ping système
        - platform    : détection OS (Windows / Linux / macOS)
        - socket      : résolution DNS
        - datetime    : horodatage des résultats

    Externe (à installer) :
        - requests    : requêtes HTTP  →  pip install requests

=============================================================================
"""

import subprocess
import platform
import socket
from datetime import datetime

import requests                     # pip install requests
from requests.exceptions import (
    ConnectionError   as ReqConnectionError,
    Timeout           as ReqTimeout,
    TooManyRedirects  as ReqTooManyRedirects,
    SSLError          as ReqSSLError,
    InvalidURL        as ReqInvalidURL,
    RequestException  as ReqRequestException,
)


# =============================================================================
# CONSTANTES COMMUNES
# =============================================================================

STATUT_OK       = "OK"
STATUT_ANOMALIE = "ANOMALIE"


# =============================================================================
# ─────────────────────────────────────────────────────────────────────────────
#  FAMILLE 1 — ICMP (ping)
# ─────────────────────────────────────────────────────────────────────────────
# =============================================================================

def _construire_commande_ping(ip: str, timeout: int) -> list:
    """
    Construit la commande ping adaptée au système d'exploitation.

    Différences entre OS :
        Windows : -n (nb paquets)  -w (timeout en millisecondes)
        Unix    : -c (nb paquets)  -W (timeout en secondes)

    Args:
        ip      (str) : Adresse IP ou nom d'hôte cible.
        timeout (int) : Délai maximum en secondes.

    Returns:
        list : Commande ping prête pour subprocess.run().
    """
    systeme = platform.system().lower()

    if systeme == "windows":
        return ["ping", "-n", "1", "-w", str(timeout * 1000), ip]
    else:
        return ["ping", "-c", "1", "-W", str(timeout), ip]


def _resoudre_hote(ip: str) -> bool:
    """
    Vérifie si un nom d'hôte est résolvable via DNS.

    Permet de distinguer une machine injoignable (ping échoue)
    d'un nom d'hôte complètement invalide (DNS échoue).

    Args:
        ip (str) : Adresse IP ou nom d'hôte à résoudre.

    Returns:
        bool : True si résolution DNS réussie, False sinon.
    """
    try:
        socket.gethostbyname(ip)
        return True
    except socket.gaierror:
        return False


def ping(ip: str, timeout: int = 2) -> bool:
    """
    Vérifie si une machine répond au ping ICMP.

    Utilise la commande ping du système d'exploitation via subprocess.
    Aucune dépendance externe requise. Compatible Windows, Linux, macOS.

    Fonctionnement interne :
        1. Résolution DNS préalable (évite un ping inutile)
        2. Construction de la commande ping adaptée à l'OS
        3. Exécution silencieuse (stdout/stderr supprimés)
        4. Analyse du code de retour (0 = succès)

    Args:
        ip      (str) : Adresse IP (ex: "192.168.1.1") ou nom d'hôte
                        (ex: "google.com") à tester.
        timeout (int) : Délai maximum en secondes. Défaut : 2.

    Returns:
        bool :
            True  → machine joignable (ping réussi)
            False → machine injoignable (timeout, erreur réseau,
                    DNS invalide, hôte inconnu)

    Exemples :
        >>> ping("8.8.8.8")
        True
        >>> ping("192.168.99.99")
        False
        >>> ping("google.com")
        True
        >>> ping("site-qui-n-existe-pas.com")
        False
    """
    # Étape 1 — Vérification DNS (rapide, avant d'envoyer un paquet)
    if not _resoudre_hote(ip):
        return False

    # Étape 2 — Construction de la commande ping (dépend de l'OS)
    commande = _construire_commande_ping(ip, timeout)

    # Étape 3 — Exécution et analyse du résultat
    try:
        resultat = subprocess.run(
            commande,
            stdout=subprocess.DEVNULL,  # Supprime la sortie standard
            stderr=subprocess.DEVNULL,  # Supprime les messages d'erreur
            timeout=timeout + 1         # Garde-fou global légèrement supérieur
        )
        # Code 0 = ping réussi / Code 1 ou 2 = échec
        return resultat.returncode == 0

    except subprocess.TimeoutExpired:
        return False
    except subprocess.SubprocessError:
        return False
    except Exception:
        return False


def ping_detaille(ip: str, timeout: int = 2) -> dict:
    """
    Version enrichie de ping() retournant un dictionnaire complet.

    Le dictionnaire retourné est directement compatible avec le format
    attendu par stockage.py pour l'écriture dans historique.json.

    Args:
        ip      (str) : Adresse IP ou nom d'hôte cible.
        timeout (int) : Délai maximum en secondes. Défaut : 2.

    Returns:
        dict : {
            "ip"        : adresse ou hôte testé,
            "statut"    : "OK" ou "ANOMALIE",
            "joignable" : True ou False,
            "timestamp" : horodatage ISO (ex: "2026-04-09T10:32:15"),
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
# ─────────────────────────────────────────────────────────────────────────────
#  FAMILLE 2 — HTTP (check_url)
# ─────────────────────────────────────────────────────────────────────────────
# =============================================================================

# En-tête User-Agent envoyé avec chaque requête HTTP.
# Certains serveurs bloquent les requêtes sans User-Agent reconnu.
_USER_AGENT = "Mozilla/5.0 (compatible; SuperviseurReseau/2.0; SAE2.03)"

# Codes HTTP considérés comme un succès (machine accessible)
# On inclut les redirections 301/302 car elles indiquent un serveur actif
_CODES_SUCCES = {200, 201, 202, 204, 301, 302, 304}


def check_url(url: str, timeout: int = 5) -> bool:
    """
    Vérifie si une URL est accessible via une requête HTTP/HTTPS.

    Utilise la bibliothèque `requests` pour envoyer une requête GET.
    Gère tous les cas d'erreur réseau courants.

    Cas d'erreur gérés :
        - Timeout          : serveur trop lent ou injoignable
        - ConnectionError  : DNS invalide, serveur éteint, port fermé
        - SSLError         : certificat SSL invalide ou auto-signé
                             (retente automatiquement sans vérification SSL
                             pour les équipements internes)
        - TooManyRedirects : boucle de redirections infinie
        - InvalidURL       : URL malformée
        - RequestException : toute autre erreur requests
        - Exception        : filet de sécurité final

    Stratégie :
        Considère l'URL accessible si le code HTTP reçu fait partie
        de _CODES_SUCCES : {200, 201, 202, 204, 301, 302, 304}.
        Un code 404, 500, 503, etc. retourne False.

    Args:
        url     (str) : URL complète à tester avec schéma.
                        (ex: "https://google.com", "http://192.168.1.1:8080")
                        Le schéma https:// est ajouté automatiquement si absent.
        timeout (int) : Délai maximum en secondes. Défaut : 5.

    Returns:
        bool :
            True  → URL accessible (code HTTP dans _CODES_SUCCES)
            False → URL inaccessible (timeout, DNS, SSL, code d'erreur,
                    connexion refusée, URL invalide)

    Exemples :
        >>> check_url("https://google.com")
        True
        >>> check_url("https://site-qui-n-existe-pas.com")
        False
        >>> check_url("https://httpbin.org/status/404")
        False
        >>> check_url("https://httpbin.org/delay/10", timeout=3)
        False
    """
    # --- Validation et normalisation de l'URL ---
    if not url or not isinstance(url, str):
        return False

    # Ajout automatique du schéma HTTPS si absent
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        reponse = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": _USER_AGENT},
            allow_redirects=True,   # Suivre les redirections 301/302
            verify=True             # Vérifier les certificats SSL
        )
        return reponse.status_code in _CODES_SUCCES

    except ReqSSLError:
        # Tentative sans vérification SSL pour équipements internes
        # (routeurs, switchs, caméras avec certificats auto-signés)
        try:
            reponse = requests.get(
                url,
                timeout=timeout,
                headers={"User-Agent": _USER_AGENT},
                allow_redirects=True,
                verify=False
            )
            return reponse.status_code in _CODES_SUCCES
        except Exception:
            return False

    except ReqTimeout:
        # Serveur n'a pas répondu dans le délai imparti
        return False

    except ReqConnectionError:
        # Échec connexion : DNS invalide, serveur éteint, port fermé
        return False

    except ReqTooManyRedirects:
        # Boucle de redirections infinie
        return False

    except ReqInvalidURL:
        # URL malformée (schéma manquant, caractères invalides…)
        return False

    except ReqRequestException:
        # Toutes les autres exceptions liées à requests
        return False

    except Exception:
        # Filet de sécurité final
        return False


def check_url_detaillee(url: str, timeout: int = 5) -> dict:
    """
    Version enrichie de check_url() retournant un dictionnaire complet.

    Collecte les métadonnées utiles pour l'affichage dans l'interface
    et le stockage dans historique.json. Mesure également le temps
    de réponse en millisecondes.

    Informations supplémentaires par rapport à check_url() :
        - code_http        : code HTTP reçu (200, 404, 500…) ou None
        - temps_reponse_ms : temps de réponse mesuré en ms ou None
        - erreur           : description textuelle de l'erreur ou None

    Args:
        url     (str) : URL complète à tester.
        timeout (int) : Délai maximum en secondes. Défaut : 5.

    Returns:
        dict : {
            "url"              : URL testée,
            "statut"           : "OK" ou "ANOMALIE",
            "joignable"        : True ou False,
            "code_http"        : int ou None,
            "temps_reponse_ms" : int ou None,
            "erreur"           : str ou None,
            "timestamp"        : horodatage ISO,
            "type"             : "HTTP"
        }

    Exemple succès :
        {
            "url"              : "https://google.com",
            "statut"           : "OK",
            "joignable"        : True,
            "code_http"        : 200,
            "temps_reponse_ms" : 143,
            "erreur"           : None,
            "timestamp"        : "2026-04-09T10:32:15",
            "type"             : "HTTP"
        }

    Exemple échec :
        {
            "url"              : "https://site-inexistant.com",
            "statut"           : "ANOMALIE",
            "joignable"        : False,
            "code_http"        : None,
            "temps_reponse_ms" : None,
            "erreur"           : "Erreur de connexion (DNS ou réseau)",
            "timestamp"        : "2026-04-09T10:32:16",
            "type"             : "HTTP"
        }
    """
    # Valeurs par défaut — modifiées selon le résultat de la requête
    code_http        = None
    temps_reponse_ms = None
    erreur           = None
    joignable        = False

    # Normalisation de l'URL
    if not url or not isinstance(url, str):
        erreur = "URL invalide ou vide"
    else:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            debut   = datetime.now()
            reponse = requests.get(
                url,
                timeout=timeout,
                headers={"User-Agent": _USER_AGENT},
                allow_redirects=True,
                verify=False        # Tolérant aux certificats auto-signés
            )
            fin = datetime.now()

            code_http        = reponse.status_code
            temps_reponse_ms = int((fin - debut).total_seconds() * 1000)
            joignable        = code_http in _CODES_SUCCES

            if not joignable:
                erreur = f"Code HTTP {code_http} — non considéré comme succès"

        except ReqTimeout:
            erreur = f"Timeout dépassé ({timeout}s)"
        except ReqConnectionError:
            erreur = "Erreur de connexion (DNS ou réseau)"
        except ReqSSLError:
            erreur = "Certificat SSL invalide"
        except ReqTooManyRedirects:
            erreur = "Trop de redirections"
        except ReqInvalidURL:
            erreur = "URL malformée"
        except ReqRequestException as e:
            erreur = f"Erreur requests : {type(e).__name__}"
        except Exception as e:
            erreur = f"Erreur inattendue : {type(e).__name__}"

    return {
        "url"              : url,
        "statut"           : STATUT_OK if joignable else STATUT_ANOMALIE,
        "joignable"        : joignable,
        "code_http"        : code_http,
        "temps_reponse_ms" : temps_reponse_ms,
        "erreur"           : erreur,
        "timestamp"        : datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "type"             : "HTTP"
    }


# =============================================================================
# TESTS RAPIDES (exécution directe uniquement : python collecte.py)
# =============================================================================

if __name__ == "__main__":

    SEP = "=" * 60

    # ─── Tests ICMP ──────────────────────────────────────────────
    print(SEP)
    print("   TESTS ICMP — fonction ping()")
    print(SEP)

    cas_ping = [
        ("8.8.8.8",                   True,  "DNS Google — doit répondre"),
        ("192.168.99.99",             False, "IP inexistante"),
        ("google.com",                True,  "Hôte valide — doit répondre"),
        ("site-qui-n-existe-pas.com", False, "Hôte invalide"),
    ]

    tous_ok_icmp = True
    for ip, attendu, description in cas_ping:
        resultat = ping(ip)
        succes   = resultat == attendu
        statut   = "PASS" if succes else "FAIL"
        if not succes:
            tous_ok_icmp = False
        print(f"  [{statut}] ping('{ip}')")
        print(f"         Attendu={attendu} | Obtenu={resultat} | {description}")

    print(f"\n  Résultat ICMP : {'OK' if tous_ok_icmp else 'ECHEC'}\n")

    # ─── Tests HTTP ──────────────────────────────────────────────
    print(SEP)
    print("   TESTS HTTP — fonction check_url()")
    print(SEP)

    cas_http = [
        ("https://google.com",                True,  "Google — doit répondre",     5),
        ("https://site-qui-n-existe-pas.com", False, "Domaine inexistant",          5),
        ("https://httpbin.org/status/404",    False, "Code 404 — doit échouer",    5),
        ("https://httpbin.org/delay/10",      False, "Timeout 3s — doit échouer",  3),
    ]

    tous_ok_http = True
    for url, attendu, description, t in cas_http:
        resultat = check_url(url, timeout=t)
        succes   = resultat == attendu
        statut   = "PASS" if succes else "FAIL"
        if not succes:
            tous_ok_http = False
        print(f"  [{statut}] check_url('{url}', timeout={t})")
        print(f"         Attendu={attendu} | Obtenu={resultat} | {description}")

    print(f"\n  Résultat HTTP : {'OK' if tous_ok_http else 'ECHEC'}\n")

    # ─── Test version détaillée ───────────────────────────────────
    print(SEP)
    print("   TEST check_url_detaillee('https://google.com')")
    print(SEP)
    details = check_url_detaillee("https://google.com")
    for cle, valeur in details.items():
        print(f"    {cle:<22} : {valeur}")

    print()
    print(SEP)
    global_ok = tous_ok_icmp and tous_ok_http
    print(f"  BILAN : {'TOUS LES TESTS PASSES' if global_ok else 'CERTAINS TESTS ONT ECHOUE'}")
    print(SEP)
