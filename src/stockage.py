"""
Module de stockage - SAE 2.03
Gère la sauvegarde des résultats au format JSON
"""

import json
import os
import datetime

def sauvegarder_resultat(cible, type_test, statut, message, data_file="data/historique.json"):
    """Sauvegarde un résultat dans le fichier JSON"""
    os.makedirs(os.path.dirname(data_file), exist_ok=True)
    
    # Charger l'historique existant
    historique = []
    if os.path.exists(data_file):
        with open(data_file, "r") as f:
            historique = json.load(f)
    
    # Ajouter la nouvelle entrée
    entree = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cible": cible,
        "type": type_test,
        "statut": statut,
        "message": message
    }
    historique.append(entree)
    
    # Sauvegarder
    with open(data_file, "w") as f:
        json.dump(historique, f, indent=4)

def lire_historique(nb_max=10, data_file="data/historique.json"):
    """Lit les derniers résultats"""
    if not os.path.exists(data_file):
        return []
    
    with open(data_file, "r") as f:
        historique = json.load(f)
    
    return historique[-nb_max:]
