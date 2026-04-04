"""
Logiciel de supervision - SAE 2.03
Point d'entrée principal
"""

import json
import time
import signal
import sys

from src.collecte import ping, check_url
from src.analyse import analyser
from src.alerte import alerte_console, alerte_journal
from src.stockage import sauvegarder_resultat
from src.affichage import afficher_tableau

CONFIG_FILE = "data/cibles.json"
arret_demande = False

def arreter(signum, frame):
    global arret_demande
    arret_demande = True
    print("\nArrêt de la supervision...")

signal.signal(signal.SIGINT, arreter)

def charger_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def main():
    config = charger_config()
    cibles = config["cibles"]
    intervalle = config.get("intervalle", 30)
    
    print("Démarrage de la supervision...")
    
    while not arret_demande:
        resultats_cycle = []
        debut_cycle = time.time()
        
        for cible in cibles:
            if cible["type"] == "ping":
                debut = time.time()
                ok = ping(cible["adresse"])
                temps = time.time() - debut if ok else None
                statut = analyser(temps)
                message = f"Réponse en {temps*1000:.0f}ms" if ok else "Timeout"
            elif cible["type"] == "http":
                debut = time.time()
                ok = check_url(cible["adresse"])
                temps = time.time() - debut if ok else None
                statut = analyser(temps)
                message = f"Réponse en {temps*1000:.0f}ms" if ok else "Site inaccessible"
            else:
                continue
            
            sauvegarder_resultat(cible["nom"], cible["type"], statut, message)
            
            if statut == "ANOMALIE":
                alerte_console(f"{cible['nom']} : {message}")
                alerte_journal(f"{cible['nom']} : {message}")
            
            resultats_cycle.append({
                "cible": cible["nom"],
                "statut": statut,
                "message": message
            })
        
        timestamp = time.strftime("%d/%m/%Y %H:%M:%S")
        afficher_tableau(resultats_cycle, timestamp, intervalle)
        
        temps_ecoule = time.time() - debut_cycle
        temps_attente = max(0, intervalle - temps_ecoule)
        time.sleep(temps_attente)
    
    print("Supervision arrêtée.")

if __name__ == "__main__":
    main()
