"""
Module de collecte - SAE 2.03
Fonctions pour vérifier l'état des cibles
"""

import subprocess
import requests
import platform

def ping(ip, timeout=2):
    """Vérifie si une machine répond au ping"""
    try:
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        resultat = subprocess.run(
            ['ping', param, '1', ip],
            timeout=timeout,
            capture_output=True
        )
        return resultat.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False

def check_url(url, timeout=5):
    """Vérifie si une URL est accessible (code HTTP 200)"""
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False
