"""
=============================================================================
Module  : analyse.py
Projet  : SAE 2.03 – Logiciel de supervision réseau
Auteurs : Groupe 2
Version : 1.0

Tâche   : P2-4 – Détection d'état OK / ANOMALIE

Rôle :
    Analyse le résultat brut d'une collecte réseau (ping ou HTTP)
    et retourne un statut normalisé.

    Statuts possibles : "OK" ou "ANOMALIE" uniquement.
    Aucun autre statut n'est autorisé dans ce projet.

Flux de données :
    collecte.py → analyse.py → alerte.py / stockage.py / affichage.py

Dépendances : aucune (module 100% natif Python)
=============================================================================
"""


# =============================================================================
# CONSTANTES — statuts normalisés
# =============================================================================

STATUT_OK       = "OK"        # Équipement joignable et dans les seuils
STATUT_DEGRADE  = "DEGRADE"   # Équipement joignable mais temps de réponse élevé
STATUT_ANOMALIE = "ANOMALIE"  # Équipement injoignable ou hors seuils

# Seuils de temps de réponse (en secondes)
SEUIL_OK       = 0.050   # En dessous : statut OK
SEUIL_DEGRADE  = 0.200   # En dessous : statut DÉGRADÉ, au-dessus : ANOMALIE


# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

def analyser(joignable):
    """
    Analyse le résultat d'une vérification réseau et retourne un statut.

    Règle de décision :
        - joignable est None           → statut "ANOMALIE"
        - joignable est False          → statut "ANOMALIE"
        - joignable est True (bool)    → statut "OK"
        - joignable < 0.050 (float)    → statut "OK"
        - 0.050 <= joignable < 0.200   → statut "DEGRADE"
        - joignable >= 0.200 (float)   → statut "ANOMALIE"

    Args:
        joignable (bool, float ou None) :
            Résultat brut retourné par collecte.py.
            - True  : ping() a réussi (sans mesure de temps)
            - False : ping() a échoué
            - float : temps de réponse en secondes
            - None  : échec sans résultat

    Returns:
        str : "OK", "DEGRADE" ou "ANOMALIE" selon les seuils.

    Exemples :
        >>> analyser(True)
        'OK'
        >>> analyser(False)
        'ANOMALIE'
        >>> analyser(None)
        'ANOMALIE'
        >>> analyser(0.045)
        'OK'
        >>> analyser(0.120)
        'DEGRADE'
        >>> analyser(0.250)
        'ANOMALIE'
    """
    # Cas sans résultat ou échec explicite
    if joignable is None or joignable is False:
        return STATUT_ANOMALIE

    # Cas booléen True (ping réussi sans mesure de temps)
    if joignable is True:
        return STATUT_OK

    # Cas float : analyse par seuils de temps de réponse
    if joignable < SEUIL_OK:
        return STATUT_OK
    if joignable < SEUIL_DEGRADE:
        return STATUT_DEGRADE
    return STATUT_ANOMALIE


# =============================================================================
# TESTS RAPIDES (python3 src/analyse.py)
# =============================================================================

if __name__ == "__main__":

    SEP = "=" * 45
    print(SEP)
    print("  TEST MODULE analyse.py — SAE 2.03")
    print(SEP)

    cas_tests = [
        (True,   STATUT_OK,       "ping réussi (bool)"),
        (False,  STATUT_ANOMALIE, "ping échoué (bool)"),
        (None,   STATUT_ANOMALIE, "pas de réponse"),
        (0.045,  STATUT_OK,       "temps OK     (< 0.050s)"),
        (0.120,  STATUT_DEGRADE,  "temps DÉGRADÉ (0.050–0.200s)"),
        (0.250,  STATUT_ANOMALIE, "temps ANOMALIE (>= 0.200s)"),
        (0,      STATUT_ANOMALIE, "valeur zéro"),
    ]

    tous_ok = True
    for entree, attendu, description in cas_tests:
        resultat = analyser(entree)
        succes   = resultat == attendu
        statut   = "PASS" if succes else "FAIL"
        if not succes:
            tous_ok = False
        print(f"  [{statut}] analyser({entree!r:<8}) → {resultat:<10} | {description}")

    print(SEP)
    print(f"  {'TOUS LES TESTS PASSÉS' if tous_ok else 'CERTAINS TESTS ONT ÉCHOUÉ'}")
    print(SEP)
