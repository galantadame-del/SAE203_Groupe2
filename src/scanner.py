"""
=============================================================================
Module  : scanner.py
Projet  : SAE 2.03 – Logiciel de supervision réseau
Auteurs : Groupe 2
Version : 1.0

Rôle :
    Scanne automatiquement le réseau local pour détecter les équipements
    actifs et les ajouter dans data/cibles.json.

    Fonctionnement :
        1. Détecte automatiquement l'adresse IP locale de la machine
        2. Déduit le sous-réseau (ex: 192.168.1.0/24)
        3. Ping chaque IP du sous-réseau en parallèle (threading)
        4. Ajoute les IP qui répondent dans cibles.json

Dépendances : socket, subprocess, platform, threading, json (natifs Python)
=============================================================================
"""

import socket
import subprocess
import platform
import threading
import json
import os
from datetime import datetime


# =============================================================================
# CONSTANTES
# =============================================================================

CHEMIN_CIBLES   = "data/cibles.json"
MAX_THREADS     = 50    # Nombre de threads simultanés pour le scan
TIMEOUT_SCAN    = 1     # Timeout en secondes pour chaque ping du scan


# =============================================================================
# DÉTECTION DU RÉSEAU LOCAL
# =============================================================================

def get_ip_locale():
    """
    Retourne l'adresse IP locale de la machine.

    Returns:
        str : Adresse IP locale (ex: "192.168.1.42")
             ou "127.0.0.1" si non trouvée
    """
    try:
        # Ouvre une connexion UDP fictive pour obtenir l'IP locale
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def get_prefixe_reseau(ip_locale):
    """
    Déduit le préfixe réseau depuis l'IP locale.
    Suppose un masque /24 (255.255.255.0).

    Args:
        ip_locale (str) : IP locale (ex: "192.168.1.42")

    Returns:
        str : Préfixe réseau (ex: "192.168.1")
    """
    parties = ip_locale.split(".")
    return ".".join(parties[:3])


# =============================================================================
# PING RAPIDE POUR LE SCAN
# =============================================================================

def _ping_scan(ip, timeout=TIMEOUT_SCAN):
    """
    Effectue un ping rapide pour le scan réseau.
    Version allégée de collecte.ping() optimisée pour la vitesse.

    Args:
        ip      (str) : Adresse IP à tester
        timeout (int) : Timeout en secondes

    Returns:
        bool : True si l'IP répond, False sinon
    """
    systeme = platform.system().lower()

    if systeme == "windows":
        commande = ["ping", "-n", "1", "-w", str(timeout * 1000), ip]
    else:
        commande = ["ping", "-c", "1", "-W", str(timeout), ip]

    try:
        resultat = subprocess.run(
            commande,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout + 1
        )
        return resultat.returncode == 0
    except Exception:
        return False


def _essayer_nom_hote(ip):
    """
    Tente de résoudre le nom d'hôte depuis l'IP (DNS inversé).

    Args:
        ip (str) : Adresse IP

    Returns:
        str : Nom d'hôte si trouvé, sinon "Équipement-{derniers chiffres IP}"
    """
    try:
        nom = socket.gethostbyaddr(ip)[0]
        # Raccourcir si trop long
        if len(nom) > 25:
            nom = nom[:25]
        return nom
    except Exception:
        # Nom générique basé sur le dernier octet
        dernier_octet = ip.split(".")[-1]
        return f"Équipement-{dernier_octet}"


# =============================================================================
# SCAN DU RÉSEAU
# =============================================================================

def scanner_reseau(prefixe=None, timeout=TIMEOUT_SCAN, callback=None):
    """
    Scanne toutes les IP du sous-réseau /24 en parallèle.

    Args:
        prefixe  (str)      : Préfixe réseau (ex: "192.168.1").
                              Si None, détecté automatiquement.
        timeout  (int)      : Timeout par ping en secondes.
        callback (function) : Fonction appelée à chaque IP découverte
                              (optionnel, pour affichage en temps réel).
                              Signature : callback(ip, nom)

    Returns:
        list : Liste de dicts {"nom", "adresse", "type"} des IP actives
    """
    # Détection automatique du préfixe réseau
    if prefixe is None:
        ip_locale = get_ip_locale()
        prefixe   = get_prefixe_reseau(ip_locale)
        print(f"[SCANNER] IP locale détectée : {ip_locale}")
        print(f"[SCANNER] Scan du réseau     : {prefixe}.0/24")

    equipements_trouves = []
    lock = threading.Lock()
    semaphore = threading.Semaphore(MAX_THREADS)

    def _tester_ip(i):
        ip = f"{prefixe}.{i}"
        with semaphore:
            if _ping_scan(ip, timeout):
                nom = _essayer_nom_hote(ip)
                equipement = {
                    "nom"    : nom,
                    "adresse": ip,
                    "type"   : "ping"
                }
                with lock:
                    equipements_trouves.append(equipement)
                if callback:
                    callback(ip, nom)

    # Lancement des threads pour toutes les IP du /24 (1 à 254)
    threads = []
    print(f"[SCANNER] Scan en cours... (peut prendre 30-60 secondes)")

    for i in range(1, 255):
        t = threading.Thread(target=_tester_ip, args=(i,))
        t.daemon = True
        threads.append(t)
        t.start()

    # Attendre que tous les threads se terminent
    for t in threads:
        t.join(timeout=timeout + 2)

    # Trier par ordre d'IP
    equipements_trouves.sort(
        key=lambda e: int(e["adresse"].split(".")[-1])
    )

    print(f"[SCANNER] {len(equipements_trouves)} équipement(s) détecté(s).")
    return equipements_trouves


# =============================================================================
# MISE À JOUR DE cibles.json
# =============================================================================

def mettre_a_jour_cibles(equipements_nouveaux, fusionner=True):
    """
    Met à jour data/cibles.json avec les équipements découverts.

    Args:
        equipements_nouveaux (list) : Équipements détectés par le scan
        fusionner            (bool) : Si True, conserve les cibles existantes
                                      et ajoute uniquement les nouvelles IP.
                                      Si False, remplace tout le fichier.

    Returns:
        int : Nombre de nouveaux équipements ajoutés
    """
    os.makedirs("data", exist_ok=True)

    # Chargement des cibles existantes
    cibles_existantes = []
    if fusionner and os.path.exists(CHEMIN_CIBLES):
        try:
            with open(CHEMIN_CIBLES, "r", encoding="utf-8") as f:
                data = json.load(f)
                cibles_existantes = data.get("cibles", [])
        except (json.JSONDecodeError, FileNotFoundError):
            cibles_existantes = []

    # IP déjà présentes dans le fichier
    ips_existantes = {c["adresse"] for c in cibles_existantes}

    # Ajout uniquement des nouvelles IP
    nouveaux_ajoutes = []
    for eq in equipements_nouveaux:
        if eq["adresse"] not in ips_existantes:
            nouveaux_ajoutes.append(eq)
            ips_existantes.add(eq["adresse"])

    # Fusion et sauvegarde
    cibles_finales = cibles_existantes + nouveaux_ajoutes

    with open(CHEMIN_CIBLES, "w", encoding="utf-8") as f:
        json.dump({"cibles": cibles_finales}, f, indent=4, ensure_ascii=False)

    print(f"[SCANNER] {len(nouveaux_ajoutes)} nouvelle(s) cible(s) ajoutée(s) dans '{CHEMIN_CIBLES}'")
    print(f"[SCANNER] Total cibles : {len(cibles_finales)}")
    return len(nouveaux_ajoutes)


# =============================================================================
# FONCTION PRINCIPALE — appelée depuis main.py
# =============================================================================

def scanner_et_mettre_a_jour(forcer=False):
    """
    Fonction principale appelée depuis main.py au démarrage.

    Lance un scan du réseau local et met à jour cibles.json.
    Si cibles.json existe déjà et contient des cibles, le scan
    est ignoré sauf si forcer=True.

    Args:
        forcer (bool) : Si True, scanne même si cibles.json existe déjà.

    Returns:
        list : Liste des cibles finales (après fusion)
    """
    # Vérifier si cibles.json existe et contient déjà des cibles
    if not forcer and os.path.exists(CHEMIN_CIBLES):
        try:
            with open(CHEMIN_CIBLES, "r", encoding="utf-8") as f:
                data = json.load(f)
                cibles = data.get("cibles", [])
                if cibles:
                    print(f"[SCANNER] cibles.json existant ({len(cibles)} cibles) — scan ignoré.")
                    print(f"[SCANNER] Utilisez forcer=True ou supprimez cibles.json pour rescanner.")
                    return cibles
        except Exception:
            pass

    # Lancement du scan
    print(f"\n[SCANNER] ── Scan automatique du réseau local ──")
    print(f"[SCANNER] Démarré le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")

    def afficher_decouverte(ip, nom):
        print(f"[SCANNER] ✅ Trouvé : {ip:<18} → {nom}")

    equipements = scanner_reseau(callback=afficher_decouverte)

    if equipements:
        mettre_a_jour_cibles(equipements, fusionner=True)
    else:
        print("[SCANNER] ⚠️  Aucun équipement détecté. Vérifiez votre connexion réseau.")

    # Retourner les cibles finales
    try:
        with open(CHEMIN_CIBLES, "r", encoding="utf-8") as f:
            return json.load(f).get("cibles", [])
    except Exception:
        return []


# =============================================================================
# TEST AUTONOME (python3 src/scanner.py)
# =============================================================================

if __name__ == "__main__":
    print("=" * 50)
    print("  TEST SCANNER — SAE 2.03")
    print("=" * 50)

    ip_locale = get_ip_locale()
    prefixe   = get_prefixe_reseau(ip_locale)
    print(f"\n  IP locale  : {ip_locale}")
    print(f"  Réseau     : {prefixe}.0/24")
    print(f"  Max threads: {MAX_THREADS}")
    print(f"  Timeout    : {TIMEOUT_SCAN}s par IP\n")

    cibles = scanner_et_mettre_a_jour(forcer=True)

    print(f"\n{'='*50}")
    print(f"  RÉSULTAT : {len(cibles)} cible(s) dans cibles.json")
    for c in cibles:
        print(f"    • {c['adresse']:<18} {c['nom']}")
    print("=" * 50)
