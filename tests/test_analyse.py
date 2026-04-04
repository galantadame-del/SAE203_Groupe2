"""
Tests unitaires pour le module d'analyse
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.analyse import analyser

def test_analyse_ok():
    assert analyser(0.020) == "OK"

def test_analyse_degrade():
    assert analyser(0.120) == "DEGRADE"

def test_analyse_anomalie():
    assert analyser(0.250) == "ANOMALIE"

def test_analyse_timeout():
    assert analyser(None) == "ANOMALIE"
