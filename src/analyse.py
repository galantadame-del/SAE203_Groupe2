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
STATUT_ANOMALIE = "ANOMALIE"  # Équipement injoignable ou hors seuils


# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

def analyser(joignable):
    """
    Analyse le résultat d'une vérification réseau et retourne un statut.

    Règle de décision :
        - joignable est évalué à True  → statut "OK"
        - joignable est évalué à False → statut "ANOMALIE"
        - joignable est None           → statut "ANOMALIE"

    Args:
        joignable (bool, float ou None) :
            Résultat brut retourné par collecte.py.
            - True  : ping() a réussi
            - False : ping() a échoué
            - float : temps de réponse en secondes (évalué comme True)
            - None  : échec sans résultat (évalué comme False)

    Returns:
        str : "OK" si l'équipement est joignable, "ANOMALIE" sinon.

    Exemples :
        >>> analyser(True)
        'OK'
        >>> analyser(False)
        'ANOMALIE'
        >>> analyser(None)
        'ANOMALIE'
        >>> analyser(0.045)
        'OK'
    """
    if joignable:
        return STATUT_OK
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
        (True,   STATUT_OK,       "ping réussi"),
        (False,  STATUT_ANOMALIE, "ping échoué"),
        (None,   STATUT_ANOMALIE, "pas de réponse"),
        (0.045,  STATUT_OK,       "temps de réponse float"),
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
