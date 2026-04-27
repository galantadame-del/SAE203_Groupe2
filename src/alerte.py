"""
=============================================================================
Module : alerte.py
Projet : SAE 2.03 – Logiciel de supervision réseau
Auteurs : Groupe 2
Version : 1.0

Rôle :
    Module de notification d'anomalies. Permet d'émettre des alertes
    via différents canaux : console (couleurs ANSI), journal fichier,
    interface Tkinter (couleurs), et email (bonus).

Tâches couvertes :
    - P3-1 : Codage du module d'alerte
        * alerte_console()  – affichage console
        * alerte_journal()  – écriture dans logs/alertes.log
        * alerte_interface() – affichage Tkinter
        * alerte_email()    – envoi SMTP (bonus)
        * declencher_alertes() – déclenchement multi-canaux

Dépendances :
    - os, logging, smtplib, datetime, email (natif)
    - tkinter (natif – pour alerte_interface uniquement)

Aucune bibliothèque externe requise.
=============================================================================
"""

import os
import logging
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ─────────────────────────────────────────────
# Constantes
# ─────────────────────────────────────────────

LOG_DIR  = "logs"
LOG_FILE = os.path.join(LOG_DIR, "alertes.log")

# Codes couleurs ANSI
ANSI = {
    "error":   "\033[91m",   # rouge
    "warning": "\033[93m",   # jaune
    "info":    "\033[92m",   # vert
    "reset":   "\033[0m",
}

# Couleurs Tkinter selon niveau
TK_COLORS = {
    "error":   "#f38ba8",   # rouge
    "warning": "#fab387",   # orange
    "info":    "#a6e3a1",   # vert
}


# ─────────────────────────────────────────────
# Utilitaire interne
# ─────────────────────────────────────────────

def _formater_message(message: str, niveau: str) -> str:
    """
    Retourne le message formaté sans couleur (console/journal).

    Format : [ALERTE] [NIVEAU] YYYY-MM-DD HH:MM:SS - message
    """
    horodatage = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"[ALERTE] [{niveau.upper()}] {horodatage} - {message}"


def _formater_message_ui(message: str, niveau: str) -> str:
    """
    Retourne le message formaté pour l'interface Tkinter.

    Format : ⚠️ [NIVEAU] YYYY-MM-DD HH:MM:SS - message
    """
    horodatage = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"⚠️ [{niveau.upper()}] {horodatage} - {message}"


# ─────────────────────────────────────────────
# 1. Alerte console
# ─────────────────────────────────────────────

def alerte_console(message: str, niveau: str = "error") -> bool:
    """
    Affiche une alerte colorée dans la console.

    Args:
        message (str) : Texte de l'alerte.
        niveau  (str) : 'error', 'warning' ou 'info'. Défaut : 'error'.

    Returns:
        bool : True si succès, False sinon.
    """
    try:
        couleur = ANSI.get(niveau.lower(), ANSI["error"])
        reset   = ANSI["reset"]
        ligne   = _formater_message(message, niveau)
        print(f"{couleur}{ligne}{reset}")
        return True
    except Exception as e:
        print(f"[alerte_console] Erreur inattendue : {e}")
        return False


# ─────────────────────────────────────────────
# 2. Alerte journal (fichier log)
# ─────────────────────────────────────────────

def _init_logger() -> logging.Logger:
    """
    Initialise et retourne le logger fichier.
    Crée le dossier logs/ si nécessaire.
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger("supervision.alertes")

    # Évite d'ajouter plusieurs handlers si appelé plusieurs fois
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)

    return logger


def alerte_journal(message: str, niveau: str = "error") -> bool:
    """
    Écrit une alerte dans logs/alertes.log.

    Args:
        message (str) : Texte de l'alerte.
        niveau  (str) : 'error', 'warning' ou 'info'. Défaut : 'error'.

    Returns:
        bool : True si succès, False si échec d'écriture.
    """
    try:
        logger = _init_logger()
        ligne  = _formater_message(message, niveau)

        niveau_lower = niveau.lower()
        if niveau_lower == "error":
            logger.error(ligne)
        elif niveau_lower == "warning":
            logger.warning(ligne)
        else:
            logger.info(ligne)

        return True

    except OSError as e:
        print(f"[alerte_journal] Échec d'écriture dans {LOG_FILE} : {e}")
        return False
    except Exception as e:
        print(f"[alerte_journal] Erreur inattendue : {e}")
        return False


# ─────────────────────────────────────────────
# 3. Alerte interface Tkinter
# ─────────────────────────────────────────────

def alerte_interface(message: str, niveau: str = "error",
                     zone_alerte=None) -> bool | str:
    """
    Affiche une alerte dans une zone Tkinter, ou retourne le texte formaté.

    Args:
        message     (str)            : Texte de l'alerte.
        niveau      (str)            : 'error', 'warning' ou 'info'.
        zone_alerte (widget ou None) : Widget Text ou Label Tkinter.
                                       Si None, retourne la chaîne formatée.

    Returns:
        bool  : True si affichage dans le widget réussi, False si erreur.
        str   : Texte formaté si zone_alerte est None (mode test).
    """
    ligne   = _formater_message_ui(message, niveau)
    couleur = TK_COLORS.get(niveau.lower(), TK_COLORS["error"])

    # Aucun widget fourni → mode test, on retourne le texte
    if zone_alerte is None:
        return ligne

    try:
        import tkinter as tk

        # ── Widget Text ──────────────────────────────
        if isinstance(zone_alerte, tk.Text):
            zone_alerte.config(state="normal")
            tag = f"niveau_{niveau.lower()}"
            zone_alerte.tag_configure(tag, foreground=couleur)
            zone_alerte.insert("end", ligne + "\n", tag)
            zone_alerte.see("end")          # défile vers le bas
            zone_alerte.config(state="disabled")

        # ── Widget Label ─────────────────────────────
        elif isinstance(zone_alerte, tk.Label):
            zone_alerte.config(text=ligne, fg=couleur)

        else:
            print(f"[alerte_interface] Type de widget non supporté : "
                  f"{type(zone_alerte)}")
            return False

        return True

    except Exception as e:
        print(f"[alerte_interface] Erreur lors de l'affichage : {e}")
        return False


# ─────────────────────────────────────────────
# 4. Alerte email (bonus)
# ─────────────────────────────────────────────

def alerte_email(destinataire: str, sujet: str, message: str,
                 smtp_config: dict = None) -> bool:
    """
    Envoie une alerte par email via SMTP.
    Ne bloque pas l'application si la config est absente ou incorrecte.

    Args:
        destinataire (str)  : Adresse email du destinataire.
        sujet        (str)  : Sujet du mail.
        message      (str)  : Corps du message.
        smtp_config  (dict) : {
                                  'host'     : str,
                                  'port'     : int,
                                  'user'     : str,
                                  'password' : str,
                                  'use_tls'  : bool  (défaut True)
                              }

    Returns:
        bool : True si envoi réussi, False sinon.
    """
    if smtp_config is None:
        print("[alerte_email] Configuration SMTP absente – email non envoyé.")
        return False

    # Champs obligatoires
    champs = ("host", "port", "user", "password")
    for champ in champs:
        if champ not in smtp_config:
            print(f"[alerte_email] Champ manquant dans smtp_config : '{champ}'")
            return False

    try:
        # Construction du message MIME
        mail = MIMEMultipart()
        mail["From"]    = smtp_config["user"]
        mail["To"]      = destinataire
        mail["Subject"] = sujet
        mail.attach(MIMEText(message, "plain", "utf-8"))

        # Connexion SMTP
        use_tls = smtp_config.get("use_tls", True)
        with smtplib.SMTP(smtp_config["host"], smtp_config["port"],
                          timeout=10) as serveur:
            serveur.ehlo()
            if use_tls:
                serveur.starttls()
                serveur.ehlo()
            serveur.login(smtp_config["user"], smtp_config["password"])
            serveur.sendmail(smtp_config["user"], destinataire,
                             mail.as_string())

        print(f"[alerte_email] Email envoyé à {destinataire}.")
        return True

    except smtplib.SMTPAuthenticationError:
        print("[alerte_email] Échec d'authentification SMTP.")
    except smtplib.SMTPConnectError:
        print(f"[alerte_email] Impossible de contacter "
              f"{smtp_config['host']}:{smtp_config['port']}.")
    except TimeoutError:
        print("[alerte_email] Délai dépassé lors de la connexion SMTP.")
    except Exception as e:
        print(f"[alerte_email] Erreur inattendue : {e}")

    return False


# ─────────────────────────────────────────────
# 5. Fonction unificatrice
# ─────────────────────────────────────────────

def declencher_alertes(cible: str, statut: str, message: str,
                       niveaux: list = None,
                       zone_alerte=None,
                       smtp_config: dict = None,
                       destinataire_email: str = "") -> dict:
    """
    Déclenche plusieurs types d'alertes en un seul appel.

    Args:
        cible             (str)  : Nom de l'équipement concerné.
        statut            (str)  : Statut détecté (ex : 'HORS LIGNE').
        message           (str)  : Message complémentaire.
        niveaux           (list) : Sous-ensemble de
                                   ['console', 'journal', 'interface', 'email'].
                                   Défaut : ['console', 'journal'].
        zone_alerte       (widget) : Widget Tkinter pour le niveau 'interface'.
        smtp_config       (dict)   : Config SMTP pour le niveau 'email'.
        destinataire_email (str)   : Adresse email pour le niveau 'email'.

    Returns:
        dict : {canal: bool} — résultat de chaque canal déclenché.
    """
    if niveaux is None:
        niveaux = ["console", "journal"]

    # Déduire le niveau de sévérité depuis le statut
    statut_upper = statut.upper()
    if "HORS" in statut_upper or "ERROR" in statut_upper:
        niveau = "error"
    elif "ANOMALIE" in statut_upper or "WARNING" in statut_upper:
        niveau = "warning"
    else:
        niveau = "info"

    texte_complet = f"{cible} - {statut} - {message}"
    resultats = {}

    for canal in niveaux:
        canal = canal.lower()

        if canal == "console":
            resultats["console"] = alerte_console(texte_complet, niveau)

        elif canal == "journal":
            resultats["journal"] = alerte_journal(texte_complet, niveau)

        elif canal == "interface":
            res = alerte_interface(texte_complet, niveau, zone_alerte)
            # alerte_interface retourne str en mode test → considéré comme succès
            resultats["interface"] = bool(res)

        elif canal == "email":
            if destinataire_email:
                sujet = f"[Supervision] {statut} – {cible}"
                resultats["email"] = alerte_email(
                    destinataire_email, sujet,
                    texte_complet, smtp_config
                )
            else:
                print("[declencher_alertes] Niveau 'email' demandé "
                      "mais aucun destinataire fourni.")
                resultats["email"] = False

        else:
            print(f"[declencher_alertes] Canal inconnu : '{canal}'")
            resultats[canal] = False

    return resultats


# ─────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import tkinter as tk

    print("=" * 60)
    print("  TESTS DU MODULE alerte.py")
    print("=" * 60)

    # ── Test 1 : alerte_console ──────────────────
    print("\n[TEST 1] alerte_console")
    alerte_console("Serveur principal - HORS LIGNE", "error")
    alerte_console("Imprimante RDC - temps de réponse élevé", "warning")
    alerte_console("Google DNS - connexion rétablie", "info")

    # ── Test 2 : alerte_journal ──────────────────
    print("\n[TEST 2] alerte_journal")
    ok = alerte_journal("Serveur principal - HORS LIGNE", "error")
    print(f"  → Écriture log : {'OK' if ok else 'ÉCHEC'}")
    ok = alerte_journal("Cloudflare DNS - latence anormale", "warning")
    print(f"  → Écriture log : {'OK' if ok else 'ÉCHEC'}")

    # Vérification de la création du fichier
    if os.path.exists(LOG_FILE):
        print(f"  → Fichier créé : {os.path.abspath(LOG_FILE)}")
    else:
        print(f"  → ERREUR : {LOG_FILE} introuvable !")

    # ── Test 3 : alerte_interface (simulée) ──────
    print("\n[TEST 3] alerte_interface (mode test – sans widget)")
    texte = alerte_interface("Machine fantôme - ANOMALIE", "error")
    print(f"  → Résultat : {texte}")

    # ── Test 4 : alerte_interface avec widget Text ─
    print("\n[TEST 4] alerte_interface avec widget Tkinter (Text)")
    root = tk.Tk()
    root.title("Test alerte_interface")
    root.geometry("700x200")
    root.configure(bg="#1e1e2e")

    zone = tk.Text(root, bg="#2a2a3e", fg="#cdd6f4",
                   font=("Segoe UI", 10), state="disabled")
    zone.pack(fill="both", expand=True, padx=10, pady=10)

    alerte_interface("Serveur principal - HORS LIGNE",    "error",   zone)
    alerte_interface("Imprimante RDC - latence élevée",   "warning", zone)
    alerte_interface("Google DNS - connexion rétablie",   "info",    zone)

    root.after(3000, root.destroy)   # ferme après 3 s
    root.mainloop()

    # ── Test 5 : alerte_email (sans config → échec attendu) ─
    print("\n[TEST 5] alerte_email (sans config SMTP)")
    ok = alerte_email("admin@example.com", "Test", "Ceci est un test")
    print(f"  → Résultat attendu False : {ok}")

    # ── Test 6 : declencher_alertes ─────────────
    print("\n[TEST 6] declencher_alertes")
    resultats = declencher_alertes(
        cible="Switch principal",
        statut="HORS LIGNE",
        message="Aucune réponse au ping depuis 60 s",
        niveaux=["console", "journal"],
    )
    print(f"  → Résultats : {resultats}")

    print("\n" + "=" * 60)
    print("  TESTS TERMINÉS")
    print("=" * 60)
