# =====================================================================
#  HELLO PIZZA - DÉFINITION ET CALCUL DES INDICATEURS
#  Cibles mensuelles, feux (vert / orange / rouge), cumuls et scores.
# =====================================================================
import json
import os

from config import ANNEE_M0, MOIS_M0

DOSSIER = os.path.dirname(os.path.abspath(__file__))
FICHIER_CIBLES = os.path.join(DOSSIER, "cibles.json")

NOMS_MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
             "août", "septembre", "octobre", "novembre", "décembre"]
MOIS_COURTS = ["Janv.", "Févr.", "Mars", "Avr.", "Mai", "Juin", "Juil.",
               "Août", "Sept.", "Oct.", "Nov.", "Déc."]

PROCESSUS = {
    "Achat": {"icone": "🛒", "couleur": "#7c3aed",
              "objectif": "Atteindre un taux de disponibilité des matières premières d'au moins 96 % d'ici avril 2027"},
    "Préparation": {"icone": "🔥", "couleur": "#2563eb",
                    "objectif": "Réduire le temps moyen de préparation des commandes à 15 minutes maximum d'ici avril 2027"},
    "Service clients": {"icone": "⭐", "couleur": "#0d9488",
                        "objectif": "Porter l'indice global d'expérience client de 72,5 à au moins 98,5 points d'ici avril 2027"},
    "Gestion des ventes": {"icone": "💰", "couleur": "#db2777",
                           "objectif": "Augmenter le chiffre d'affaires mensuel de 11 526 DH (de 32 940 à 44 466 DH) d'ici avril 2027"},
}

OBJECTIF_GLOBAL = ("Atteindre un indice global d'expérience client d'au moins 98,5 points tout en assurant "
                   "une augmentation du chiffre d'affaires mensuel de 11 526 DH d'ici 12 mois")

# Chaque indicateur :
#   col        = colonne de l'onglet « indicateurs » du Google Sheet
#   sens       = "haut" (plus c'est haut, mieux c'est) / "bas" / "zero" (le plus proche de 0)
#   trajet     = "lineaire" (progression régulière) / "compose" (+x % par mois) / "constant"
#   cumul      = "somme" / "moyenne" / "ratio_ca" (CA cumulé ÷ commandes cumulées)
#                / "pondere_cmd" (pondéré par les commandes) / "pondere_avis" (pondéré par les avis)
INDICATEURS = {
    # ---------------- ACHAT ----------------
    "taux_dispo_mp": dict(nom="Taux de disponibilité des matières premières", processus="Achat", majeur=True,
                          unite="%", sens="haut", trajet="lineaire", initiale=89.71, finale=96.0, cumul="moyenne",
                          formule="(Matières premières disponibles ÷ nombre total de matières premières) × 100",
                          formule_cumul="moyenne des taux mensuels de M1 au mois choisi"),
    "taux_rupture_nc": dict(nom="Taux de rupture des matières non critiques", processus="Achat", majeur=False,
                            unite="%", sens="bas", trajet="lineaire", initiale=8.93, finale=3.57, cumul="moyenne",
                            formule="(Matières non critiques en rupture ÷ total des matières non critiques) × 100",
                            formule_cumul="moyenne des taux mensuels de M1 au mois choisi"),
    "taux_rupture_c": dict(nom="Taux de rupture des matières critiques", processus="Achat", majeur=False,
                           unite="%", sens="bas", trajet="lineaire", initiale=16.67, finale=0.0, cumul="moyenne",
                           formule="(Matières critiques en rupture ÷ total des matières critiques) × 100",
                           formule_cumul="moyenne des taux mensuels de M1 au mois choisi"),
    "taux_stock_min": dict(nom="Taux de matières respectant le stock minimum", processus="Achat", majeur=False,
                           unite="%", sens="haut", trajet="lineaire", initiale=89.71, finale=95.0, cumul="moyenne",
                           formule="(Matières respectant le stock minimum ÷ nombre total de matières) × 100",
                           formule_cumul="moyenne des taux mensuels de M1 au mois choisi"),
    # ---------------- PRÉPARATION ----------------
    "temps_moyen_prep": dict(nom="Temps moyen de préparation", processus="Préparation", majeur=True,
                             unite="min", sens="bas", trajet="lineaire", initiale=20.0, finale=15.0, cumul="pondere_cmd",
                             formule="Somme des temps de préparation (envoi en cuisine → prêt) ÷ nombre de commandes préparées",
                             formule_cumul="total des temps de M1 au mois choisi ÷ total des commandes préparées"),
    "taux_retard": dict(nom="Taux de commandes en retard", processus="Préparation", majeur=False,
                        unite="%", sens="bas", trajet="lineaire", initiale=10.0, finale=5.0, cumul="pondere_cmd",
                        formule="(Commandes dépassant le délai prévu de 25 min ÷ commandes préparées) × 100",
                        formule_cumul="total des commandes en retard de M1 au mois choisi ÷ total des commandes préparées × 100"),
    # ---------------- SERVICE CLIENTS ----------------
    "indice_experience": dict(nom="Indice global d'expérience client", processus="Service clients", majeur=True,
                              unite="points", sens="haut", trajet="lineaire", initiale=72.5, finale=98.5, cumul="moyenne",
                              formule="(Score des retours + score des réclamations) ÷ 2",
                              formule_cumul="moyenne des indices mensuels de M1 au mois choisi"),
    "nb_retours": dict(nom="Nombre de retours clients", processus="Service clients", majeur=False,
                       unite="avis", sens="haut", trajet="constant", initiale=15, finale=30, cumul="somme",
                       formule="Nombre de réponses enregistrées dans le Google Forms sur le mois",
                       formule_cumul="somme des retours de M1 au mois choisi"),
    "taux_reclamation": dict(nom="Taux de réclamation sur les plats", processus="Service clients", majeur=False,
                             unite="%", sens="bas", trajet="lineaire", initiale=5.0, finale=3.0, cumul="pondere_avis",
                             formule="(Réclamations clients concernant les plats ÷ nombre d'avis du Google Sheet) × 100",
                             formule_cumul="total des réclamations de M1 au mois choisi ÷ total des avis × 100"),
    # ---------------- GESTION DES VENTES ----------------
    "ca": dict(nom="Chiffre d'affaires mensuel", processus="Gestion des ventes", majeur=True,
               unite="DH", sens="haut", trajet="compose", initiale=32940, finale=44466, cumul="somme",
               formule="Somme des ventes TTC du mois (nombre de commandes × ticket moyen), Odoo · caisse",
               formule_cumul="somme des chiffres d'affaires de M1 au mois choisi"),
    "nb_commandes": dict(nom="Nombre de commandes", processus="Gestion des ventes", majeur=False,
                         unite="commandes", sens="haut", trajet="compose", initiale=540, finale=648, cumul="somme",
                         formule="Nombre de commandes payées dans le mois (Odoo · point de vente)",
                         formule_cumul="somme des commandes de M1 au mois choisi"),
    "ticket_moyen": dict(nom="Ticket moyen", processus="Gestion des ventes", majeur=False,
                         unite="DH", sens="haut", trajet="compose", initiale=61, finale=68.62, cumul="ratio_ca",
                         formule="Chiffre d'affaires du mois ÷ nombre de commandes du mois",
                         formule_cumul="CA cumulé de M1 au mois choisi ÷ commandes cumulées"),
    "ecart_caisse": dict(nom="Écart de caisse", processus="Gestion des ventes", majeur=False,
                         unite="DH", sens="zero", trajet="lineaire", initiale=-150, finale=0, cumul="somme",
                         formule="Ventes réelles − ventes encaissées (clôture de caisse Odoo)",
                         formule_cumul="somme des écarts de M1 au mois choisi"),
}

MAJEURS = [k for k, d in INDICATEURS.items() if d["majeur"]]


# ---------------------------------------------------------------------
#  Calendrier du projet
# ---------------------------------------------------------------------
def numero_mois(cle):
    """'2026-10' -> 6 (M6)."""
    a, m = int(cle[:4]), int(cle[5:7])
    return (a - ANNEE_M0) * 12 + (m - MOIS_M0)


def cle_du_numero(n):
    """6 -> '2026-10'."""
    total = ANNEE_M0 * 12 + (MOIS_M0 - 1) + n
    return f"{total // 12}-{total % 12 + 1:02d}"


def cle_annee_precedente(cle):
    return f"{int(cle[:4]) - 1}-{cle[5:7]}"


def libelle_mois(cle, court=False):
    a, m = int(cle[:4]), int(cle[5:7])
    if court:
        return f"{MOIS_COURTS[m - 1]} {str(a)[2:]}"
    return f"{NOMS_MOIS[m - 1]} {a}"


# ---------------------------------------------------------------------
#  Cibles (les cibles finales peuvent être modifiées par le gérant)
# ---------------------------------------------------------------------
def charger_cibles_modifiees():
    try:
        with open(FICHIER_CIBLES, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def enregistrer_cibles(cibles):
    with open(FICHIER_CIBLES, "w", encoding="utf-8") as f:
        json.dump(cibles, f, ensure_ascii=False, indent=2)


def cible_finale(code):
    modif = charger_cibles_modifiees()
    return float(modif.get(code, INDICATEURS[code]["finale"]))


def cible_du_mois(code, n):
    """Cible fixée pour le mois Mn (n de 1 à 12)."""
    d = INDICATEURS[code]
    i, f = float(d["initiale"]), cible_finale(code)
    n = max(0, min(n, 12))
    if d["trajet"] == "constant":
        return f
    if d["trajet"] == "compose":
        return i * (f / i) ** (n / 12)
    return i + (f - i) * n / 12


def cibles_12_mois(code):
    return [cible_du_mois(code, n) for n in range(1, 13)]


# ---------------------------------------------------------------------
#  Feux
# ---------------------------------------------------------------------
TOLERANCE = 0.05   # orange = moins de 5 % d'écart avec la cible du mois


def feu(code, realise, cible):
    """'vert' (cible atteinte), 'orange' (à surveiller), 'rouge' (en retard)."""
    if realise is None:
        return "gris"
    sens = INDICATEURS[code]["sens"]
    if sens == "zero":
        realise, cible, sens = abs(realise), abs(cible), "bas"
    tol = abs(cible) * TOLERANCE
    if sens == "haut":
        if realise >= cible - 1e-9:
            return "vert"
        return "orange" if realise >= cible - tol else "rouge"
    if realise <= cible + 1e-9:
        return "vert"
    return "orange" if realise <= cible + tol else "rouge"


COULEURS_FEU = {"vert": "#16a34a", "orange": "#f59e0b", "rouge": "#dc2626", "gris": "#94a3b8"}
LIBELLES_FEU = {"vert": "Cible atteinte", "orange": "À surveiller", "rouge": "En retard", "gris": "Pas de donnée"}
TEINTES_FEU = {"vert": "rgba(22,163,74,.09)", "orange": "rgba(245,158,11,.13)",
               "rouge": "rgba(220,38,38,.09)", "gris": "rgba(148,163,184,.10)"}


# ---------------------------------------------------------------------
#  Calcul complet d'un indicateur jusqu'au mois choisi
# ---------------------------------------------------------------------
def valeur(table, cle, col):
    """Valeur d'une colonne pour un mois ('2026-10'), ou None."""
    if table is None or cle not in table.index or col not in table.columns:
        return None
    v = table.at[cle, col]
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return None if v != v else v   # NaN -> None


def calculer(code, table, n_choisi):
    """Toutes les informations d'un indicateur pour le mois Mn choisi."""
    d = INDICATEURS[code]
    col = code
    realises, cibles, feux, cles = [], [], [], []
    for n in range(1, n_choisi + 1):
        cle = cle_du_numero(n)
        r = valeur(table, cle, col)
        c = cible_du_mois(code, n)
        realises.append(r)
        cibles.append(c)
        feux.append(feu(code, r, c))
        cles.append(cle)

    # --- cumuls (réalisé et cible) de M1 au mois choisi ---
    cumuls_r, cumuls_c = [], []
    for k in range(len(realises)):
        cumuls_r.append(_cumul(d["cumul"], table, cles[:k + 1], col, realises[:k + 1]))
        cumuls_c.append(_cumul_cible(code, d["cumul"], k + 1))

    cle = cle_du_numero(n_choisi)
    r, c = realises[-1], cibles[-1]
    cle_n1 = cle_annee_precedente(cle)
    n1 = valeur(table, cle_n1, col)
    reussis = feux.count("vert")
    infos = {k: v for k, v in d.items() if k != "cumul"}
    return dict(
        code=code, **infos, type_cumul=d["cumul"], n=n_choisi, cle=cle, realise=r, cible=c,
        ecart=None if r is None else r - c,
        feu=feux[-1], realises=realises, cibles=cibles, feux=feux,
        cumuls=cumuls_r, cumuls_cibles=cumuls_c,
        cumul=cumuls_r[-1], cumul_cible=cumuls_c[-1],
        cible_finale=cible_finale(code), toutes_cibles=cibles_12_mois(code),
        n1=n1, cle_n1=cle_n1, diff_n1=None if (r is None or n1 is None) else r - n1,
        reussis=reussis, score=round(reussis / 12 * 100),
        depart=valeur(table, cle_du_numero(0), col),
    )


def _cumul(type_cumul, table, cles, col, realises):
    vals = [v for v in realises if v is not None]
    if not vals:
        return None
    if type_cumul == "somme":
        return sum(vals)
    if type_cumul == "ratio_ca":
        ca = sum(valeur(table, k, "ca") or 0 for k in cles)
        cmd = sum(valeur(table, k, "nb_commandes") or 0 for k in cles)
        return ca / cmd if cmd else None
    if type_cumul in ("pondere_cmd", "pondere_avis"):
        poids_col = "nb_commandes" if type_cumul == "pondere_cmd" else "nb_retours"
        num = den = 0.0
        for k, v in zip(cles, realises):
            if v is None:
                continue
            p = valeur(table, k, poids_col) or 0
            num += v * p
            den += p
        return num / den if den else sum(vals) / len(vals)
    return sum(vals) / len(vals)


def _cumul_cible(code, type_cumul, n):
    cs = [cible_du_mois(code, k) for k in range(1, n + 1)]
    if type_cumul == "somme":
        return sum(cs)
    if type_cumul == "ratio_ca":
        ca = sum(cible_du_mois("ca", k) for k in range(1, n + 1))
        cmd = sum(cible_du_mois("nb_commandes", k) for k in range(1, n + 1))
        return ca / cmd
    return sum(cs) / len(cs)


def calculer_tout(table, n_choisi):
    return {code: calculer(code, table, n_choisi) for code in INDICATEURS}


def score_global(resultats):
    """Moyenne des scores des 4 indicateurs majeurs."""
    return round(sum(resultats[c]["score"] for c in MAJEURS) / len(MAJEURS))


def score_processus(resultats, processus):
    s = [r["score"] for r in resultats.values() if r["processus"] == processus]
    return round(sum(s) / len(s)) if s else 0


# ---------------------------------------------------------------------
#  Mise en forme des nombres (à la française)
# ---------------------------------------------------------------------
def nombre(v, decimales=2):
    if v is None:
        return "—"
    s = f"{v:,.{decimales}f}".replace(",", " ").replace(".", ",")
    if decimales and "," in s:
        s = s.rstrip("0").rstrip(",")
    return s.replace("-", "−")


def fmt(v, unite, signe=False):
    """Valeur avec son unité, ex. 31 907 DH ; 17,2 min ; 95,59 %."""
    if v is None:
        return "—"
    dec = 0 if unite in ("DH", "commandes", "avis") and abs(v) >= 100 else (0 if unite in ("commandes", "avis") else (1 if unite in ("min", "points") else 2))
    if unite == "DH" and abs(v) < 100:
        dec = 2
    s = nombre(v, dec)
    if signe and v > 0:
        s = "+" + s
    return f"{s} {unite}"


def fmt_ecart(v, unite):
    if v is None:
        return "—"
    u = "pts" if unite == "%" else unite
    return fmt(v, u, signe=True)
