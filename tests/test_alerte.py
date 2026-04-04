"""
Tests unitaires pour le module d'alerte
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.alerte import alerte_console, alerte_journal

def test_alerte_console():
    try:
        alerte_console("Test d'alerte")
        resultat = True
    except:
        resultat = False
    assert resultat == True

def test_alerte_journal():
    try:
        alerte_journal("Test d'écriture dans le log")
        resultat = True
    except:
        resultat = False
    assert resultat == True
