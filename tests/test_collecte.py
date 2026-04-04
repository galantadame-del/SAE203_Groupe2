"""
Tests unitaires pour le module de collecte
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.collecte import ping, check_url

def test_ping_ip_valide():
    assert ping("8.8.8.8") == True

def test_ping_ip_invalide():
    assert ping("192.168.99.99") == False

def test_check_url_valide():
    assert check_url("https://google.com") == True

def test_check_url_invalide():
    assert check_url("https://site-qui-n-existe-pas.com") == False
