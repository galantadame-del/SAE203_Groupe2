# Superviseur Réseau Local — Baraka'IT Solution

> **SAE 2.03** — Mettre en place une solution informatique pour l'entreprise  
> IUT de La Réunion — Département Réseaux & Télécommunications — BUT RT 1ère année — 2025-2026

---

## Présentation

**Baraka'IT Solution** propose un logiciel de supervision réseau local développé entièrement en Python.  
Il permet à un administrateur réseau de surveiller en temps réel l'état des équipements de son infrastructure, de détecter les anomalies et de conserver un historique des événements.

### Équipe

| Membre | Rôle |
|---|---|
| GALANT Adame | Chef de projet |
| DILMAHAMOD Rehaan | Développeur Front |
| BOUCHRANI Ambdouroihamane | Développeur Back |
| SAUTRON-CICIA Markus | Testeur / Documentaliste |

---

## Fonctionnalités

- **Surveillance ICMP** — ping via commande système (`subprocess`), compatible Windows / Linux / macOS
- **Surveillance HTTP/HTTPS** — vérification d'accessibilité via `requests`
- **Détection d'état** — statuts `OK` / `ANOMALIE` uniquement
- **Tableau de bord terminal** — affichage coloré, trié par criticité, rafraîchi automatiquement
- **Zone d'alerte** — mémorisation et affichage de la dernière anomalie détectée
- **Journal des événements** — `logs/alertes.log` mis à jour en temps réel
- **Historique JSON** — `data/historique.json` conservé entre les sessions
- **Paramétrage sans recompiler** — intervalle, timeouts et seuils configurables dans `config.json`
- **Mode debug** — logs détaillés activables dans `config.json`
- **Mode "une seule fois"** — exécute 1 cycle puis s'arrête (utile pour les tests)

---

## Architecture

```
superviseur-reseau/
├── main.py                  ← Point d'entrée
├── config.json              ← Paramètres globaux (intervalle, seuils, alertes)
├── requirements.txt         ← Dépendances Python
├── .gitignore
├── README.md
│
├── src/
│   ├── __init__.py
│   ├── collecte.py          ← ping() + check_url() — collecte ICMP et HTTP
│   ├── analyse.py           ← analyser() — détection OK / ANOMALIE
│   ├── alerte.py            ← alerte_console() + alerte_journal()
│   ├── affichage.py         ← afficher_tableau() — tableau de bord terminal
│   ├── stockage.py          ← sauvegarder_resultat() + lecture historique
│   └── config_manager.py   ← Chargement et accès à config.json
│
├── data/
│   ├── cibles.json          ← Équipements à superviser (à configurer)
│   └── historique.json      ← Généré automatiquement (non versionné)
│
├── logs/
│   └── alertes.log          ← Généré automatiquement (non versionné)
│
└── tests/
    ├── __init__.py
    └── test_collecte.py     ← Tests unitaires (unittest)
```

---

## Prérequis

- Python **3.8 ou supérieur**
- Git installé
- Droits **administrateur** (sudo sur Linux/macOS, Administrateur sur Windows) — requis pour envoyer des paquets ICMP
- Accès au réseau local à superviser

Vérifier la version Python :
```bash
python --version
```

---

## Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/votre-equipe/superviseur-reseau.git
cd superviseur-reseau
```

### 2. Créer l'environnement virtuel

```bash
# Création
python -m venv venv

# Activation — Linux / macOS
source venv/bin/activate

# Activation — Windows
venv\Scripts\activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

Dépendances installées :

| Bibliothèque | Version | Usage |
|---|---|---|
| `requests` | 2.31.0 | Vérification HTTP/HTTPS |
| `customtkinter` | 5.2.2 | Interface graphique (optionnelle) |

Les bibliothèques suivantes sont **natives Python** (aucune installation) :
`subprocess`, `platform`, `socket`, `json`, `logging`, `datetime`, `threading`, `signal`

---

## Configuration

### Équipements à superviser — `data/cibles.json`

Modifier ce fichier pour lister les équipements de votre réseau :

```json
{
    "cibles": [
        {
            "nom"    : "DNS Google",
            "adresse": "8.8.8.8",
            "type"   : "ping"
        },
        {
            "nom"    : "Portail intranet",
            "adresse": "https://192.168.1.100",
            "type"   : "http"
        }
    ]
}
```

| Champ | Type | Valeurs acceptées |
|---|---|---|
| `nom` | string | Nom affiché dans le tableau |
| `adresse` | string | Adresse IP ou URL complète |
| `type` | string | `ping` (ICMP) ou `http` (HTTP/HTTPS) |

### Paramètres globaux — `config.json`

```json
{
    "intervalle_global"   : 30,
    "mode_debug"          : false,
    "mode_une_seule_fois" : false,
    "analyse": {
        "icmp": { "seuil_ok_ms": 500  },
        "http": { "seuil_ok_ms": 3000 }
    }
}
```

| Paramètre | Défaut | Description |
|---|---|---|
| `intervalle_global` | `30` | Secondes entre chaque cycle de supervision |
| `mode_debug` | `false` | Affiche les logs détaillés dans le terminal |
| `mode_une_seule_fois` | `false` | Exécute 1 cycle puis s'arrête automatiquement |
| `seuil_ok_ms` (icmp) | `500` | Latence max en ms pour statut OK (ICMP) |
| `seuil_ok_ms` (http) | `3000` | Latence max en ms pour statut OK (HTTP) |

---

## Lancement

```bash
# Linux / macOS (droits ICMP requis)
sudo python main.py

# Windows — lancer le terminal en tant qu'Administrateur
python main.py
```

### Sortie attendue au démarrage

```
=======================================================
   SUPERVISION RÉSEAU — SAE 2.03 — Groupe 2
=======================================================
[CONFIG] Configuration chargée depuis 'config.json'
[CONFIG] Intervalle : 30s  |  Mode debug : False  |  Mode une seule fois : False
[INFO] 4 cible(s) chargée(s) depuis 'data/cibles.json'
[INFO] Démarrage... (Ctrl+C pour arrêter)
```

Appuyer sur **Ctrl+C** pour arrêter proprement la supervision.

---

## Tests

Lancer les tests unitaires :

```bash
python -m unittest discover tests/
```

Tests couverts :

| Fichier | Fonction testée | Cas |
|---|---|---|
| `test_collecte.py` | `ping()` | Loopback (127.0.0.1), IP invalide, hôte valide, hôte inexistant |
| `test_collecte.py` | `check_url()` | URL accessible, code 404, timeout dépassé |

---

## Dépannage

| Erreur | Cause | Solution |
|---|---|---|
| `ModuleNotFoundError: requests` | Dépendance non installée | `pip install requests==2.31.0` |
| `ModuleNotFoundError: customtkinter` | Dépendance non installée | `pip install customtkinter==5.2.2` |
| `Permission denied` (Linux) | Droits ICMP insuffisants | Lancer avec `sudo python main.py` |
| `FileNotFoundError: cibles.json` | Fichier absent | Créer `data/cibles.json` avec au moins une cible |
| `JSONDecodeError` | Fichier JSON mal formé | Valider le JSON sur [jsonlint.com](https://jsonlint.com) |
| Toutes les cibles en ANOMALIE | Pas de réseau disponible | Vérifier la connexion réseau et les droits |

---

## Fichiers générés automatiquement

Ces fichiers sont créés lors de l'exécution et sont exclus du dépôt Git (`.gitignore`) :

| Fichier | Contenu |
|---|---|
| `data/historique.json` | Résultats horodatés de chaque vérification |
| `logs/alertes.log` | Journal des anomalies détectées |

---

## Références

- [Documentation Python officielle](https://docs.python.org)
- [Bibliothèque requests](https://docs.python-requests.org)
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- [unittest — framework de tests Python](https://docs.python.org/3/library/unittest.html)

---

## 📄 Licence

Projet réalisé dans le cadre pédagogique de la SAE 2.03 — IUT de La Réunion.  
Usage académique uniquement.

---

*Baraka'IT Solution — SAE 2.03 — Groupe 2 — IUT de La Réunion — 2025-2026*
