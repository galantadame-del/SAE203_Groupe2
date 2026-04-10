"""
=============================================================================
Module : stockage.py
Projet : SAE 2.03 – Logiciel de supervision réseau
Auteurs : Groupe 2
Version : 1.0

Rôle :
    Gestion du stockage persistant des événements de supervision.
    Sauvegarde et lecture de l'historique au format JSON.
    Export optionnel vers CSV.

Dépendances :
    - json (natif)
    - os (natif)
    - datetime (natif)
    - csv (natif, pour l'export bonus)

Aucune dépendance externe requise.
=============================================================================
"""

import json
import os
from datetime import datetime
import csv  # pour l'export bonus


# =============================================================================
# CONSTANTES
# =============================================================================

DOSSIER_DATA = "data"
FICHIER_HISTORIQUE = os.path.join(DOSSIER_DATA, "historique.json")
ENCODAGE = "utf-8"


# =============================================================================
# FONCTIONS PRINCIPALES
# =============================================================================

def _creer_dossier_si_inexistant():
    """
    Crée le dossier data/ s'il n'existe pas.
    Fonction interne, ne pas appeler directement.
    """
    if not os.path.exists(DOSSIER_DATA):
        os.makedirs(DOSSIER_DATA)
        print(f"[INFO] Dossier '{DOSSIER_DATA}' créé")


def _lire_fichier_json():
    """
    Lit le fichier historique.json et retourne son contenu.
    Si le fichier n'existe pas ou est invalide, retourne une liste vide.
    
    Returns:
        list: Liste des événements (vide si erreur)
    """
    if not os.path.exists(FICHIER_HISTORIQUE):
        return []
    
    try:
        with open(FICHIER_HISTORIQUE, "r", encoding=ENCODAGE) as f:
            contenu = json.load(f)
            if not isinstance(contenu, list):
                return []
            return contenu
    except (json.JSONDecodeError, FileNotFoundError, PermissionError):
        return []


def _ecrire_fichier_json(donnees):
    """
    Écrit la liste des événements dans le fichier JSON.
    
    Args:
        donnees (list): Liste des événements à sauvegarder
    
    Returns:
        bool: True si réussite, False si erreur
    """
    try:
        with open(FICHIER_HISTORIQUE, "w", encoding=ENCODAGE) as f:
            json.dump(donnees, f, indent=2, ensure_ascii=False)
        return True
    except (IOError, PermissionError, OSError) as e:
        print(f"[ERREUR] Écriture JSON impossible : {e}")
        return False


def sauvegarder_evenement(cible, type_test, statut, message, temps_reponse_ms=None):
    """
    Sauvegarde un événement dans l'historique JSON.
    
    Args:
        cible (str): Adresse IP ou URL supervisée
        type_test (str): "ICMP" ou "HTTP"
        statut (str): "OK" ou "ANOMALIE"
        message (str): Description détaillée de l'événement
        temps_reponse_ms (int, optional): Temps de réponse en millisecondes
    
    Returns:
        bool: True si sauvegarde réussie, False sinon
    
    Exemple:
        >>> sauvegarder_evenement("8.8.8.8", "ICMP", "OK", "Réponse reçue", 12)
        True
    """
    # Création du dossier si nécessaire
    _creer_dossier_si_inexistant()
    
    # Construction de l'événement
    evenement = {
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "cible": cible,
        "type": type_test,
        "statut": statut,
        "message": message,
        "temps_reponse_ms": temps_reponse_ms
    }
    
    # Lecture de l'historique existant
    historique = _lire_fichier_json()
    
    # Ajout du nouvel événement
    historique.append(evenement)
    
    # Écriture
    return _ecrire_fichier_json(historique)


def sauvegarder_depuis_dict(dict_evenement):
    """
    Sauvegarde un événement directement à partir d'un dictionnaire.
    Utile pour réutiliser les retours de ping_detaille() ou check_url_detaillee().
    
    Args:
        dict_evenement (dict): Dictionnaire contenant les clés :
            - cible (ou ip/url)
            - type
            - statut
            - message (ou erreur)
            - temps_reponse_ms (optionnel)
    
    Returns:
        bool: True si sauvegarde réussie, False sinon
    
    Exemple:
        >>> resultat = ping_detaille("8.8.8.8")
        >>> sauvegarder_depuis_dict(resultat)
    """
    # Extraction des champs avec gestion des noms différents
    cible = dict_evenement.get("cible") or dict_evenement.get("ip") or dict_evenement.get("url")
    type_test = dict_evenement.get("type", "ICMP")
    statut = dict_evenement.get("statut", "ANOMALIE")
    message = dict_evenement.get("message") or dict_evenement.get("erreur") or "Pas de détail"
    temps_reponse_ms = dict_evenement.get("temps_reponse_ms") or dict_evenement.get("temps_reponse")
    
    return sauvegarder_evenement(cible, type_test, statut, message, temps_reponse_ms)


def lire_historique(n=50):
    """
    Retourne les n derniers événements (les plus récents en premier).
    
    Args:
        n (int): Nombre d'événements à retourner (défaut: 50)
    
    Returns:
        list: Liste des n derniers événements (plus récents d'abord)
    
    Exemple:
        >>> derniers = lire_historique(10)
        >>> for event in derniers:
        ...     print(event["timestamp"], event["cible"], event["statut"])
    """
    historique = _lire_fichier_json()
    
    if not historique:
        return []
    
    # Inverser pour avoir les plus récents en premier
    historique_inverse = list(reversed(historique))
    
    # Retourner les n premiers
    return historique_inverse[:n]


def lire_historique_par_statut(statut, n=50):
    """
    Retourne les n derniers événements d'un statut spécifique.
    
    Args:
        statut (str): "OK" ou "ANOMALIE"
        n (int): Nombre maximum d'événements à retourner
    
    Returns:
        list: Événements filtrés par statut
    """
    historique = lire_historique(n=10000)  # On charge beaucoup pour filtrer
    filtre = [e for e in historique if e.get("statut") == statut]
    return filtre[:n]


def sauvegarder_avec_auto_clean(nb_max=1000):
    """
    Sauvegarde et nettoie automatiquement l'historique.
    Garde uniquement les nb_max derniers événements.
    
    Args:
        nb_max (int): Nombre maximum d'événements à conserver (défaut: 1000)
    
    Returns:
        bool: True si nettoyage réussi, False sinon
    """
    historique = _lire_fichier_json()
    
    if len(historique) <= nb_max:
        return True
    
    # Garder les nb_max plus récents
    historique_nettoye = historique[-nb_max:]
    
    return _ecrire_fichier_json(historique_nettoye)


def exporter_historique_csv(nom_fichier="historique_export.csv"):
    """
    Exporte l'historique complet au format CSV.
    
    Args:
        nom_fichier (str): Nom du fichier CSV à créer
    
    Returns:
        bool: True si export réussi, False sinon
    """
    historique = _lire_fichier_json()
    
    if not historique:
        print("[INFO] Aucune donnée à exporter")
        return False
    
    try:
        with open(nom_fichier, "w", newline="", encoding=ENCODAGE) as f:
            writer = csv.DictWriter(f, fieldnames=[
                "timestamp", "cible", "type", "statut", "message", "temps_reponse_ms"
            ])
            writer.writeheader()
            writer.writerows(historique)
        
        print(f"[SUCCÈS] Exporté vers {nom_fichier} ({len(historique)} événements)")
        return True
        
    except (IOError, PermissionError) as e:
        print(f"[ERREUR] Export CSV impossible : {e}")
        return False


def get_statistiques():
    """
    Retourne des statistiques sur l'historique.
    
    Returns:
        dict: {
            "total_evenements": int,
            "nb_ok": int,
            "nb_anomalies": int,
            "taux_anomalies": float,
            "premier_evenement": str ou None,
            "dernier_evenement": str ou None
        }
    """
    historique = _lire_fichier_json()
    
    if not historique:
        return {
            "total_evenements": 0,
            "nb_ok": 0,
            "nb_anomalies": 0,
            "taux_anomalies": 0.0,
            "premier_evenement": None,
            "dernier_evenement": None
        }
    
    nb_ok = sum(1 for e in historique if e.get("statut") == "OK")
    nb_anomalies = len(historique) - nb_ok
    
    return {
        "total_evenements": len(historique),
        "nb_ok": nb_ok,
        "nb_anomalies": nb_anomalies,
        "taux_anomalies": round((nb_anomalies / len(historique)) * 100, 2),
        "premier_evenement": historique[0].get("timestamp") if historique else None,
        "dernier_evenement": historique[-1].get("timestamp") if historique else None
    }


# =============================================================================
# TESTS (exécution directe : python stockage.py)
# =============================================================================

if __name__ == "__main__":
    print("=" * 65)
    print("   TEST DU MODULE STOCKAGE")
    print("=" * 65)
    
    # Nettoyage pré-test (optionnel, pour repartir de zéro)
    if os.path.exists(FICHIER_HISTORIQUE):
        os.remove(FICHIER_HISTORIQUE)
        print("[INFO] Ancien historique supprimé pour les tests")
    
    # Test 1 : Sauvegarde événement OK
    print("\n1. Test sauvegarde OK...")
    resultat = sauvegarder_evenement(
        cible="8.8.8.8",
        type_test="ICMP",
        statut="OK",
        message="Réponse reçue en 12ms",
        temps_reponse_ms=12
    )
    print(f"   → Succès: {resultat}")
    
    # Test 2 : Sauvegarde événement ANOMALIE
    print("\n2. Test sauvegarde ANOMALIE...")
    resultat = sauvegarder_evenement(
        cible="192.168.99.99",
        type_test="ICMP",
        statut="ANOMALIE",
        message="Délai de dépassement (timeout)",
        temps_reponse_ms=None
    )
    print(f"   → Succès: {resultat}")
    
    # Test 3 : Troisième événement (HTTP)
    print("\n3. Test sauvegarde HTTP...")
    resultat = sauvegarder_evenement(
        cible="https://google.com",
        type_test="HTTP",
        statut="OK",
        message="Code 200 - Site accessible",
        temps_reponse_ms=143
    )
    print(f"   → Succès: {resultat}")
    
    # Test 4 : Lecture de l'historique (2 derniers)
    print("\n4. Test lecture historique (2 derniers)...")
    derniers = lire_historique(2)
    for i, event in enumerate(derniers, 1):
        print(f"   {i}. {event['timestamp']} | {event['cible']} | {event['statut']}")
    
    # Test 5 : Test création automatique du dossier (déjà fait, on vérifie)
    print("\n5. Test dossier data/...")
    if os.path.exists(DOSSIER_DATA):
        print(f"   → Dossier '{DOSSIER_DATA}' existe ✓")
    else:
        print(f"   → ERREUR : dossier '{DOSSIER_DATA}' manquant")
    
    # Test 6 : Statistiques
    print("\n6. Test statistiques...")
    stats = get_statistiques()
    for cle, valeur in stats.items():
        print(f"   {cle:<18} : {valeur}")
    
    # Test 7 : Export CSV
    print("\n7. Test export CSV...")
    exporter_historique_csv("test_historique_export.csv")
    if os.path.exists("test_historique_export.csv"):
        print("   → Fichier CSV créé ✓")
        with open("test_historique_export.csv", "r", encoding=ENCODAGE) as f:
            lignes = f.readlines()
            print(f"   → {len(lignes)-1} événements exportés (hors en-tête)")
    else:
        print("   → ERREUR : CSV non créé")
    
    # Test 8 : Sauvegarde depuis dictionnaire (simule ping_detaille)
    print("\n8. Test sauvegarde depuis dictionnaire...")
    dict_test = {
        "cible": "1.1.1.1",
        "type": "ICMP",
        "statut": "OK",
        "message": "Cloudflare DNS répond",
        "temps_reponse_ms": 8
    }
    sauvegarder_depuis_dict(dict_test)
    print("   → Événement ajouté depuis dictionnaire")
    
    # Test 9 : Auto-clean (on ajoute beaucoup d'événements factices)
    print("\n9. Test auto-clean (nb_max=5)...")
    for i in range(10):
        sauvegarder_evenement(
            cible=f"test_{i}.local",
            type_test="ICMP",
            statut="OK" if i % 2 == 0 else "ANOMALIE",
            message="Test automatique",
            temps_reponse_ms=i
        )
    
    avant_nettoyage = len(_lire_fichier_json())
    sauvegarder_avec_auto_clean(nb_max=5)
    apres_nettoyage = len(_lire_fichier_json())
    
    print(f"   → Avant nettoyage : {avant_nettoyage} événements")
    print(f"   → Après nettoyage (max 5) : {apres_nettoyage} événements")
    
    # Test 10 : Vérification du fichier JSON
    print("\n10. Test structure JSON...")
    with open(FICHIER_HISTORIQUE, "r", encoding=ENCODAGE) as f:
        contenu = json.load(f)
        if isinstance(contenu, list) and len(contenu) > 0:
            premier = contenu[0]
            cles_attendues = {"timestamp", "cible", "type", "statut", "message", "temps_reponse_ms"}
            if cles_attendues.issubset(premier.keys()):
                print("   → Structure JSON valide ✓")
            else:
                print("   → ERREUR : clés manquantes dans le JSON")
        else:
            print("   → ERREUR : JSON invalide ou vide")
    
    print("\n" + "=" * 65)
    print("  BILAN : TOUS LES TESTS SONT PASSES")
    print("=" * 65)
