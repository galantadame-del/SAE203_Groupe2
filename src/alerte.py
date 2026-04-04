"""
Module d'alerte - SAE 2.03
Gère les notifications en cas d'anomalie
"""

import datetime
import os

# Couleurs pour la console
ROUGE = '\033[91m'
RESET = '\033[0m'

def alerte_console(message):
    """Affiche une alerte dans la console en rouge"""
    print(f"{ROUGE}!!! ALERTE : {message}{RESET}")

def alerte_journal(message, log_file="logs/alertes.log"):
    """Écrit l'alerte dans un fichier journal"""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, "a") as f:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] ALERTE : {message}\n")
