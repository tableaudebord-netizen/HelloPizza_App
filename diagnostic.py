# =====================================================================
#  HELLO PIZZA - DIAGNOSTIC AUTOMATIQUE ET TEXTES D'EXPLICATION
#  Règles de comparaison écrites en Python (pas de prédiction).
# =====================================================================
from indicateurs import INDICATEURS, MAJEURS, fmt, libelle_mois, nombre, valeur


def sous_titre(r, table):
    """Petite phrase d'explication sous le chiffre réalisé."""
    cle, v = r["cle"], r["realise"]
    if v is None:
        return "Pas encore de donnée pour ce mois."
    code = r["code"]
    nb = valeur(table, cle, "nb_commandes")
    if code == "ca":
        aug = v - r["initiale"]
        obj = r["cible_finale"] - r["initiale"]
        tick = valeur(table, cle, "ticket_moyen")
        debut = f"{nombre(nb, 0)} commandes × {nombre(tick, 1)} DH · " if nb and tick else ""
        return (f"{debut}augmentation depuis avril 2026 : <b>{fmt(aug, 'DH', signe=True)}</b> "
                f"(objectif : {fmt(obj, 'DH', signe=True)})")
    if code == "nb_commandes":
        return (f"augmentation depuis avril 2026 : <b>{fmt(v - r['initiale'], 'commandes', signe=True)}</b> "
                f"(objectif : {fmt(r['cible_finale'] - r['initiale'], 'commandes', signe=True)})")
    if code == "ticket_moyen":
        return (f"augmentation depuis avril 2026 : <b>{fmt(v - r['initiale'], 'DH', signe=True)}</b> "
                f"(objectif : {fmt(r['cible_finale'] - r['initiale'], 'DH', signe=True)})")
    if code == "ecart_caisse":
        return "négatif = argent manquant dans la caisse à la clôture"
    if code == "taux_dispo_mp":
        return f"{round(68 * v / 100)} matières disponibles sur 68"
    if code == "taux_rupture_nc":
        return f"{round(56 * v / 100)} matière(s) non critique(s) en rupture sur 56"
    if code == "taux_rupture_c":
        return f"{round(12 * v / 100)} matière(s) critique(s) en rupture sur 12"
    if code == "taux_stock_min":
        return f"{round(68 * v / 100)} matières au-dessus du stock minimum sur 68"
    if code == "temps_moyen_prep":
        return "mesuré par l'écran cuisine Odoo (envoi en cuisine → prêt)"
    if code == "taux_retard":
        return "retard = préparation de plus de 25 minutes"
    nb_av = valeur(table, cle, "nb_retours")
    tx = valeur(table, cle, "taux_reclamation")
    rec = round((nb_av or 0) * (tx or 0) / 100)
    if code == "indice_experience":
        return f"{nombre(nb_av, 0)} avis Google Forms · {rec} réclamation(s)"
    if code == "nb_retours":
        return "réponses au questionnaire Google Forms"
    if code == "taux_reclamation":
        return f"{rec} réclamation(s) sur {nombre(nb_av, 0)} avis"
    return ""


def derniere_variation_tourisme(tourisme, cle):
    """Dernier chiffre officiel des nuitées publié jusqu'au mois choisi."""
    if tourisme is None or tourisme.empty:
        return None
    t = tourisme[tourisme["periode"] <= cle].dropna(subset=["nuitees_cumul"])
    if t.empty:
        return None
    return t.iloc[-1]


def phrases(res, table, tourisme, partiel=False, codes=None):
    """Liste de phrases (HTML) qui expliquent le mois choisi."""
    codes = codes or MAJEURS
    out = []
    ca = res.get("ca")
    tour = derniere_variation_tourisme(tourisme, res[codes[0]]["cle"])
    mois = libelle_mois(res[codes[0]]["cle"])

    for code in codes:
        r = res[code]
        if r["realise"] is None:
            out.append(f"<b>{r['nom']}</b> : pas encore de donnée pour {mois}.")
            continue
        u = r["unite"]
        ecart = abs(r["ecart"])
        if r["sens"] == "haut":
            sens_txt = "au-dessus" if r["ecart"] >= 0 else "en dessous"
        elif r["sens"] == "bas":
            sens_txt = "en dessous" if r["ecart"] <= 0 else "au-dessus"
        else:
            sens_txt = "plus proche de 0" if abs(r["realise"]) <= abs(r["cible"]) else "plus loin de 0"
        ecart_txt = f"{nombre(ecart, 2)} points" if u == "%" else fmt(ecart, u)
        phrase = (f"<b>{r['nom']}</b> : {fmt(r['realise'], u)}, soit <b>{ecart_txt} {sens_txt}</b> "
                  f"de la cible du mois ({fmt(r['cible'], u)}).")
        if code == "ca":
            aug = r["realise"] - r["initiale"]
            obj = r["cible_finale"] - r["initiale"]
            phrase += (f" Depuis avril 2026, l'augmentation du CA est de <b>{fmt(aug, 'DH', signe=True)}</b>, "
                       f"pour un objectif de <b>{fmt(obj, 'DH', signe=True)}</b> en avril 2027.")
        serie = _serie_reussite(r["feux"])
        if serie >= 3:
            phrase += f" Cible atteinte <b>{serie} mois de suite</b> 👍"
        elif serie <= -2:
            phrase += f" Cible manquée <b>{-serie} mois de suite</b> : action nécessaire."
        out.append(phrase)

    # Croisement avec la veille externe (tourisme)
    if ca is not None and ca["realise"] is not None and tour is not None and "ca" in codes:
        var = tour.get("variation_n1_pct")
        if var is not None and var == var:
            if ca["ecart"] < 0 and var > 0:
                out.append(f"🔎 <b>Croisement avec la veille</b> : les nuitées à Marrakech progressent de "
                           f"<b>{nombre(var, 1)} %</b> ({tour.get('libelle', '')}) alors que le CA est sous sa cible : "
                           f"le recul ne vient pas du tourisme, la cause est plutôt interne "
                           f"(nombre de commandes : {nombre(valeur(table, ca['cle'], 'nb_commandes'), 0)}).")
            elif ca["ecart"] < 0 and var <= 0:
                out.append(f"🔎 <b>Croisement avec la veille</b> : les nuitées à Marrakech reculent "
                           f"({nombre(var, 1)} %) : le contexte touristique explique en partie le CA sous sa cible.")
            else:
                out.append(f"🔎 <b>Croisement avec la veille</b> : nuitées à Marrakech {'+' if var > 0 else ''}"
                           f"{nombre(var, 1)} % ({tour.get('libelle', '')}) ; le CA atteint sa cible du mois.")

    # Points d'attention sur les autres indicateurs
    rc = res.get("taux_rupture_c")
    if rc and rc["realise"] and rc["realise"] > 0 and "taux_rupture_c" not in codes:
        out.append(f"⚠️ {round(12 * rc['realise'] / 100)} matière(s) <b>critique(s)</b> en rupture ce mois-ci.")
    if partiel:
        out.append("⚠️ Le mois choisi n'est pas terminé : ses chiffres sont <b>partiels</b>.")
    return out


def _serie_reussite(feux):
    """+k si les k derniers mois sont verts, −k si les k derniers sont non verts."""
    if not feux:
        return 0
    dernier = feux[-1] == "vert"
    k = 0
    for f in reversed(feux):
        if (f == "vert") == dernier:
            k += 1
        else:
            break
    return k if dernier else -k


def reste_a_faire(r):
    """Effort mensuel nécessaire pour atteindre la cible finale d'avril 2027."""
    if r["realise"] is None:
        return None
    restants = 12 - r["n"]
    reste = r["cible_finale"] - r["realise"]
    if r["sens"] == "zero":
        reste = 0 - r["realise"]
    rythme = (r["realise"] - r["initiale"]) / r["n"] if r["n"] else 0
    besoin = reste / restants if restants > 0 else reste
    if r["sens"] == "haut":
        deja = r["realise"] >= r["cible_finale"]
    elif r["sens"] == "bas":
        deja = r["realise"] <= r["cible_finale"]
    else:
        deja = abs(r["realise"]) <= abs(r["cible_finale"])
    return dict(restants=restants, reste=reste, besoin=besoin, rythme=rythme, deja=deja)
