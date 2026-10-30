# =====================================================================
#  HELLO PIZZA - PARAMÈTRES DE L'APPLICATION
#  C'est le seul fichier à modifier : les liens des Google Sheets,
#  le nom du fichier de la clé Google et les comptes de connexion.
# =====================================================================

# 1) Fichier de la clé Google (compte de service), placé dans ce dossier
CLE_GOOGLE = "cle_google.json"

# 2) Lien du Google Sheet « Indicateurs Hello Pizza »
#    (onglets : indicateurs, veille, tourisme)
URL_SHEET_INDICATEURS = "https://docs.google.com/spreadsheets/d/1R0yfdoruTCcrLs1TPKfDXSRz_S8Fiul9snuv0iUbHcs/edit?usp=sharing"

# 3) Lien du Google Sheet « Satisfaction Clients - Hello Pizza »
#    (onglet des réponses du Google Forms)
URL_SHEET_AVIS = "https://docs.google.com/spreadsheets/d/17Jq_guJjNP-aXsqrGZaybib9hnazzCspjKh-lhtfVEs/edit?usp=sharing"
ONGLET_AVIS = "Form Responses 1"

# 4) Comptes de connexion : identifiant -> (mot de passe, rôle, nom affiché)
#    rôle = "gerant" (synthèse) ou "responsable" (4 tableaux de bord de processus)
COMPTES = {
    "gerant":   ("HelloPizza2026", "gerant",      "Gérant"),
    "chef":     ("Cuisine2026",    "responsable", "Chef de cuisine"),
    "serveur":  ("Service2026",    "responsable", "Serveur"),
    "caissier": ("Caisse2026",     "responsable", "Caissier"),
}

# 5) Envoi du rapport mensuel par e-mail (facultatif)
#    Même adresse et même « mot de passe d'application » (16 lettres) que dans n8n.
EMAIL_EXPEDITEUR = ""          # ex. "ton.adresse@gmail.com"
EMAIL_MOT_DE_PASSE_APP = ""    # le code de 16 lettres, sans espaces
EMAIL_DESTINATAIRE = ""        # adresse du gérant

# 6) Calendrier du projet : M0 = avril 2026 (situation de départ), M12 = avril 2027
ANNEE_M0, MOIS_M0 = 2026, 4
