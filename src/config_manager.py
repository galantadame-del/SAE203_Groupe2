"""
=============================================================================
Module  : config_manager.py
Projet  : SAE 2.03 – Logiciel de supervision réseau
Tâche   : P3-4 – Ajout de fonctionnalités bonus (paramétrage, fréquence)

Rôle :
    Gère le chargement et l'accès à la configuration globale du logiciel.
    Permet de modifier l'intervalle de supervision sans toucher au code.
    Supporte le mode "une seule fois" pour le débogage.

Fonctionnalités P3-4 couvertes :
    ✅ Fichier config.json lu au démarrage
    ✅ Intervalle modifiable sans recompiler
    ✅ Mode debug (logs supplémentaires)
    ✅ Mode "une seule fois" (1 cycle puis arrêt)
    ✅ Configuration des seuils OK / ANOMALIE
    ✅ Configuration des canaux d'alerte

Dépendances : json, os (natifs Python)
=============================================================================
"""

import json
import os


# =============================================================================
# CHEMIN DU FICHIER DE CONFIGURATION
# =============================================================================

CONFIG_PATH = "config.json"


# =============================================================================
# CONFIGURATION PAR DÉFAUT
# Utilisée si config.json est absent, incomplet ou invalide.
# Statuts : OK / ANOMALIE uniquement — pas de DÉGRADÉ.
# =============================================================================

CONFIG_DEFAUT = {
    "intervalle_global"    : 30,       # secondes entre chaque cycle
    "unite_temps"          : "secondes",
    "mode_debug"           : False,    # affiche les logs détaillés
    "mode_une_seule_fois"  : False,    # exécute 1 cycle puis s'arrête (bonus debug)
    "analyse": {
        "icmp": {
            "seuil_ok_ms"  : 500       # > seuil → ANOMALIE, <= seuil → OK
        },
        "http": {
            "seuil_ok_ms"  : 3000      # > seuil → ANOMALIE, <= seuil → OK
        }
    },
    "alertes": {
        "canaux_actifs": ["console", "journal"],
        "email": {
            "actif"       : False,
            "destinataire": "admin@exemple.com",
            "smtp_host"   : "smtp.gmail.com",
            "smtp_port"   : 587,
            "user"        : "",
            "password"    : ""
        }
    }
}

# Variable interne — chargée une seule fois au démarrage
_configuration = None


# =============================================================================
# CHARGEMENT ET FUSION
# =============================================================================

def charger_configuration(fichier_config=None):
    """
    Charge la configuration depuis config.json au démarrage (P3-4).

    Si le fichier est absent ou invalide, la configuration par défaut
    est utilisée pour que le logiciel démarre quand même.

    La fusion récursive garantit que toute clé absente dans config.json
    est complétée automatiquement par la valeur par défaut.

    Args:
        fichier_config (str, optionnel) : Chemin alternatif vers un fichier JSON.
                                          Par défaut : "config.json"

    Returns:
        dict : Configuration complète et valide
    """
    global _configuration
    chemin = fichier_config or CONFIG_PATH

    # ── Fichier introuvable ───────────────────────────────────────────────────
    if not os.path.exists(chemin):
        print(f"[CONFIG] '{chemin}' introuvable → configuration par défaut utilisée.")
        _configuration = _copie_profonde(CONFIG_DEFAUT)
        return _configuration

    # ── Lecture et fusion ─────────────────────────────────────────────────────
    try:
        with open(chemin, "r", encoding="utf-8") as f:
            config_fichier = json.load(f)

        _configuration = _fusion_config(CONFIG_DEFAUT, config_fichier)
        print(f"[CONFIG] Configuration chargée depuis '{chemin}'")
        print(f"[CONFIG] Intervalle : {_configuration['intervalle_global']}s  |  "
              f"Mode debug : {_configuration['mode_debug']}  |  "
              f"Mode une seule fois : {_configuration['mode_une_seule_fois']}")
        return _configuration

    except json.JSONDecodeError as e:
        print(f"[CONFIG] Erreur JSON dans '{chemin}' : {e}")
        print(f"[CONFIG] Configuration par défaut utilisée.")
        _configuration = _copie_profonde(CONFIG_DEFAUT)
        return _configuration


def _fusion_config(defaut, utilisateur):
    """
    Fusionne récursivement la config utilisateur avec la config par défaut.
    Les clés absentes chez l'utilisateur sont héritées du défaut.

    Args:
        defaut      (dict) : Configuration par défaut
        utilisateur (dict) : Configuration utilisateur (peut être partielle)

    Returns:
        dict : Configuration fusionnée complète
    """
    resultat = defaut.copy()
    for cle, valeur in utilisateur.items():
        if cle in resultat and isinstance(resultat[cle], dict) and isinstance(valeur, dict):
            # Fusion récursive pour les sous-dictionnaires
            resultat[cle] = _fusion_config(resultat[cle], valeur)
        else:
            resultat[cle] = valeur
    return resultat


def _copie_profonde(d):
    """Retourne une copie profonde d'un dictionnaire (sans dépendance externe)."""
    return json.loads(json.dumps(d))


# =============================================================================
# GETTERS — ACCÈS À LA CONFIGURATION
# =============================================================================

def get_config():
    """
    Retourne la configuration complète.
    Charge automatiquement depuis config.json si pas encore fait.

    Returns:
        dict : Configuration complète
    """
    global _configuration
    if _configuration is None:
        charger_configuration()
    return _configuration


def recharger_configuration():
    """
    Recharge la configuration depuis le fichier (utile si modifié à chaud).

    Returns:
        dict : Nouvelle configuration chargée
    """
    global _configuration
    _configuration = None
    return charger_configuration()


def get_intervalle():
    """
    Retourne l'intervalle de supervision en secondes (P3-4).
    Modifiable dans config.json sans toucher au code.

    Returns:
        int : Intervalle en secondes (défaut : 30)
    """
    return int(get_config().get("intervalle_global", 30))


def est_mode_debug():
    """
    Retourne True si le mode debug est activé dans config.json.
    Affiche des logs supplémentaires à chaque cycle.

    Returns:
        bool : True si mode debug actif
    """
    return bool(get_config().get("mode_debug", False))


def est_mode_une_seule_fois():
    """
    Retourne True si le mode "une seule fois" est activé (P3-4 bonus).
    Dans ce mode, la supervision s'exécute 1 cycle puis s'arrête.
    Utile pour tester sans laisser tourner la boucle.

    Returns:
        bool : True si mode une seule fois actif
    """
    return bool(get_config().get("mode_une_seule_fois", False))


def get_seuil_ok_icmp():
    """
    Retourne le seuil de latence ICMP en dessous duquel le statut est OK.
    Au-dessus de ce seuil → ANOMALIE.

    Returns:
        int : Seuil en millisecondes (défaut : 500)
    """
    return int(get_config()["analyse"]["icmp"]["seuil_ok_ms"])


def get_seuil_ok_http():
    """
    Retourne le seuil de latence HTTP en dessous duquel le statut est OK.
    Au-dessus de ce seuil → ANOMALIE.

    Returns:
        int : Seuil en millisecondes (défaut : 3000)
    """
    return int(get_config()["analyse"]["http"]["seuil_ok_ms"])


def get_canaux_alertes():
    """
    Retourne la liste des canaux d'alerte actifs définis dans config.json.

    Returns:
        list : Liste des canaux (ex : ["console", "journal"])
    """
    return get_config().get("alertes", {}).get("canaux_actifs", ["console", "journal"])


def get_config_email():
    """
    Retourne la configuration SMTP si les alertes email sont activées.

    Returns:
        dict  : Configuration email si actif
        None  : Si email désactivé dans config.json
    """
    config_email = get_config().get("alertes", {}).get("email", {})
    if config_email.get("actif", False):
        return config_email
    return None


# =============================================================================
# SETTER — MODIFICATION À CHAUD (BONUS P3-4)
# =============================================================================

def mettre_a_jour_intervalle(nouvel_intervalle):
    """
    Met à jour l'intervalle de supervision en mémoire sans redémarrer (P3-4 bonus).
    La modification est active dès le prochain cycle de supervision.

    Args:
        nouvel_intervalle (int) : Nouvel intervalle en secondes (minimum : 5)
    """
    global _configuration
    if _configuration is None:
        charger_configuration()

    # Validation minimale
    if not isinstance(nouvel_intervalle, int) or nouvel_intervalle < 5:
        print(f"[CONFIG] Intervalle invalide ({nouvel_intervalle}). Minimum : 5 secondes.")
        return

    _configuration["intervalle_global"] = nouvel_intervalle
    print(f"[CONFIG] Intervalle mis à jour → {nouvel_intervalle} secondes")


# =============================================================================
# TESTS (exécution directe : python config_manager.py)
# =============================================================================

if __name__ == "__main__":

    SEP = "=" * 55
    print(SEP)
    print("  TEST DU MODULE config_manager.py — P3-4")
    print(SEP)

    # Test 1 : Chargement
    print("\n[TEST 1] Chargement de config.json")
    config = charger_configuration()
    print(f"  Intervalle         : {get_intervalle()} secondes")
    print(f"  Mode debug         : {est_mode_debug()}")
    print(f"  Mode une seule fois: {est_mode_une_seule_fois()}")
    print(f"  Seuil OK ICMP      : {get_seuil_ok_icmp()} ms")
    print(f"  Seuil OK HTTP      : {get_seuil_ok_http()} ms")
    print(f"  Canaux alertes     : {get_canaux_alertes()}")

    # Test 2 : Modification à chaud
    print("\n[TEST 2] Modification de l'intervalle à chaud")
    print(f"  Avant : {get_intervalle()}s")
    mettre_a_jour_intervalle(15)
    print(f"  Après : {get_intervalle()}s")

    # Test 3 : Validation — valeur invalide
    print("\n[TEST 3] Valeur invalide (doit être rejetée)")
    mettre_a_jour_intervalle(2)  # < 5 → rejeté

    # Test 4 : Rechargement depuis fichier
    print("\n[TEST 4] Rechargement depuis le fichier")
    recharger_configuration()
    print(f"  Intervalle après rechargement : {get_intervalle()}s")

    print(f"\n{SEP}")
    print("  TOUS LES TESTS TERMINÉS")
    print(SEP)
