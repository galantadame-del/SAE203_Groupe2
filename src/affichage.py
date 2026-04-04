"""
Module d'affichage - SAE 2.03
Gère l'interface utilisateur en console
"""

import os

# Codes couleurs ANSI
VERT = '\033[92m'
JAUNE = '\033[93m'
ROUGE = '\033[91m'
RESET = '\033[0m'

def nettoyer_console():
    """Nettoie l'affichage de la console"""
    os.system('cls' if os.name == 'nt' else 'clear')

def afficher_tableau(resultats, timestamp, intervalle):
    """Affiche le tableau de bord"""
    nettoyer_console()
    
    # Compteurs
    nb_ok = sum(1 for r in resultats if r.get("statut") == "OK")
    nb_degrade = sum(1 for r in resultats if r.get("statut") == "DEGRADE")
    nb_anomalie = sum(1 for r in resultats if r.get("statut") == "ANOMALIE")
    
    print("=" * 50)
    print("         DASHBOARD SUPERVISION")
    print("=" * 50)
    print(f"✅ OK : {nb_ok}  |  ⚠️ DÉGRADÉ : {nb_degrade}  |  ❌ ANOMALIE : {nb_anomalie}")
    print("=" * 50)
    print(f"Dernière vérification : {timestamp}")
    print("-" * 50)
    
    for r in resultats:
        if r.get("statut") == "OK":
            couleur = VERT
            symbole = "✅"
        elif r.get("statut") == "DEGRADE":
            couleur = JAUNE
            symbole = "⚠️"
        else:
            couleur = ROUGE
            symbole = "❌"
        
        print(f"{symbole} {couleur}[{r.get('statut')}]{RESET} {r.get('cible')}")
    
    print("-" * 50)
    print(f"Prochain cycle dans {intervalle} secondes...")
    print("=" * 50)
    print("Appuyez sur Ctrl+C pour arrêter")
