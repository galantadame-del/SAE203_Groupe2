"""
Module d'analyse - SAE 2.03
Analyse les résultats et retourne un état
"""

# Seuils en secondes
SEUIL_OK = 0.050      # 50ms
SEUIL_DEGRADE = 0.200 # 200ms

def analyser(temps, seuil_ok=SEUIL_OK, seuil_degrade=SEUIL_DEGRADE):
    """
    Analyse un temps de réponse et retourne l'état
    - OK : temps < seuil_ok
    - DEGRADE : seuil_ok <= temps < seuil_degrade
    - ANOMALIE : temps >= seuil_degrade ou temps est None
    """
    if temps is None:
        return "ANOMALIE"
    
    if temps < seuil_ok:
        return "OK"
    elif temps < seuil_degrade:
        return "DEGRADE"
    else:
        return "ANOMALIE"
