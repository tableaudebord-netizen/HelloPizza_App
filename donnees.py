# =====================================================================
#  HELLO PIZZA - LECTURE DES DONNÉES
#  Source principale : Google Sheets (rempli chaque mois par n8n).
#  Secours : les fichiers CSV du dossier « donnees_secours » (si pas d'Internet).
# =====================================================================
import os

import pandas as pd

import config

DOSSIER = os.path.dirname(os.path.abspath(__file__))
SECOURS = os.path.join(DOSSIER, "donnees_secours")

COLONNES_NUM = ["nb_commandes", "ca", "ticket_moyen", "ecart_caisse", "temps_moyen_prep", "taux_retard",
                "taux_dispo_mp", "taux_rupture_nc", "taux_rupture_c", "taux_stock_min",
                "nb_retours", "taux_reclamation", "indice_experience"]


def _nombre(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(" ", "").replace(" ", "").replace("%", "").replace(",", ".")
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def trouver_cle():
    """Cherche la clé Google dans le dossier (même si Windows a ajouté « .json » deux fois)."""
    candidats = [config.CLE_GOOGLE, config.CLE_GOOGLE + ".json"]
    candidats += sorted(f for f in os.listdir(DOSSIER) if f.lower().startswith(("crucial-gasket", "cle_google"))
                        and f.lower().endswith(".json"))
    for nom in candidats:
        chemin = os.path.join(DOSSIER, nom)
        if os.path.exists(chemin):
            return chemin
    raise FileNotFoundError("fichier de la clé Google introuvable dans le dossier de l'application")


def _ouvrir(url):
    import gspread
    client = gspread.service_account(filename=trouver_cle())
    return client.open_by_url(url)


def _lire(feuille, brut=True):
    """Lit un onglet en liste de dictionnaires (sans planter sur les colonnes vides)."""
    try:
        valeurs = feuille.get_all_values(value_render_option="UNFORMATTED_VALUE") if brut else feuille.get_all_values()
    except TypeError:
        valeurs = feuille.get_all_values()
    if not valeurs:
        return []
    entetes = [str(h).strip() for h in valeurs[0]]
    garder = [i for i, h in enumerate(entetes) if h]
    return [{entetes[i]: (ligne[i] if i < len(ligne) else "") for i in garder} for ligne in valeurs[1:]]


def _vers_table(lignes):
    """Liste de dictionnaires (lignes du Sheet) -> DataFrame indexé par mois 'AAAA-MM'."""
    df = pd.DataFrame(lignes)
    if df.empty or "mois" not in df.columns:
        return pd.DataFrame(columns=COLONNES_NUM)
    df["mois"] = df["mois"].astype(str).str.strip().str[:7]
    df = df[df["mois"].str.match(r"^\d{4}-\d{2}$")]
    for c in COLONNES_NUM:
        df[c] = df[c].map(_nombre) if c in df.columns else None
    df = df.drop_duplicates("mois", keep="last").set_index("mois").sort_index()
    return df


def charger_tout():
    """Renvoie (indicateurs, veille, tourisme, avis, source, erreur)."""
    erreur = None
    try:
        if "COLLE_ICI" in config.URL_SHEET_INDICATEURS:
            raise RuntimeError("le lien du Google Sheet n'est pas encore collé dans config.py")
        sh = _ouvrir(config.URL_SHEET_INDICATEURS)
        indicateurs = _vers_table(_lire(sh.worksheet("indicateurs")))
        try:
            veille = pd.DataFrame(_lire(sh.worksheet("veille")))
        except Exception:
            veille = pd.DataFrame()
        try:
            tourisme = pd.DataFrame(_lire(sh.worksheet("tourisme")))
        except Exception:
            tourisme = pd.DataFrame()
        try:
            if "COLLE_ICI" in config.URL_SHEET_AVIS:
                raise RuntimeError
            avis = pd.DataFrame(_lire(_ouvrir(config.URL_SHEET_AVIS).worksheet(config.ONGLET_AVIS), brut=False))
        except Exception:
            avis = _csv("avis.csv")
        source = "Google Sheets (mis à jour par n8n)"
    except Exception as e:  # pas d'Internet, clé absente, lien non collé...
        erreur = str(e) or e.__class__.__name__
        indicateurs = _vers_table(_csv("indicateurs.csv").to_dict("records"))
        veille = _csv("veille.csv")
        tourisme = _csv("tourisme.csv")
        avis = _csv("avis.csv")
        source = "fichiers de secours (hors connexion)"
    return indicateurs, _nettoyer_veille(veille), _nettoyer_tourisme(tourisme), _nettoyer_avis(avis), source, erreur


def _csv(nom):
    chemin = os.path.join(SECOURS, nom)
    if not os.path.exists(chemin):
        return pd.DataFrame()
    return pd.read_csv(chemin, dtype=str, keep_default_na=False)


def _nettoyer_veille(v):
    if v is None or v.empty:
        return pd.DataFrame(columns=["lien", "date_publication", "theme", "processus", "titre", "source"])
    v = v.copy()
    for c in ["lien", "date_collecte", "date_publication", "theme", "processus", "titre", "source", "statut"]:
        if c not in v.columns:
            v[c] = ""
        v[c] = v[c].astype(str).str.strip()
    v = v[v["titre"] != ""]
    return v.sort_values("date_publication", ascending=False)


def _nettoyer_tourisme(t):
    if t is None or t.empty:
        return pd.DataFrame(columns=["periode", "libelle", "nuitees_cumul", "variation_n1_pct", "lien", "media"])
    t = t.copy()
    t["periode"] = t["periode"].astype(str).str.strip().str[:7]
    for c in ["nuitees_cumul", "nuitees_cumul_n1", "variation_n1_pct"]:
        t[c] = t[c].map(_nombre) if c in t.columns else None
    for c in ["libelle", "lien", "media", "titre"]:
        if c not in t.columns:
            t[c] = ""
    t = t[t["periode"].str.match(r"^\d{4}-\d{2}$")]
    return t.drop_duplicates("periode", keep="last").sort_values("periode")


def _nettoyer_avis(a):
    """Avis du Google Forms -> colonnes : mois, reclamation (bool), types (texte)."""
    if a is None or a.empty:
        return pd.DataFrame(columns=["mois", "reclamation", "types"])
    cols = list(a.columns)
    col_date = cols[0]
    col_recl = next((c for c in cols if str(c).strip().lower().startswith("avez-vous rencontr")), None)
    if col_recl is None:
        return pd.DataFrame(columns=["mois", "reclamation", "types"])
    i = cols.index(col_recl)
    col_type = cols[i + 1] if i + 1 < len(cols) else None
    dates = pd.to_datetime(a[col_date].astype(str).str.strip(), errors="coerce", dayfirst=False, format="mixed")
    out = pd.DataFrame({
        "mois": dates.dt.strftime("%Y-%m"),
        "reclamation": a[col_recl].astype(str).str.strip().str.lower().eq("oui"),
        "types": a[col_type].astype(str).str.strip() if col_type else "",
    })
    return out.dropna(subset=["mois"])


def reclamations_par_type(avis, mois_liste):
    """Compte les types de problèmes signalés sur une liste de mois."""
    if avis is None or avis.empty:
        return pd.Series(dtype=int)
    sel = avis[avis["mois"].isin(mois_liste) & avis["reclamation"]]
    compte = {}
    for t in sel["types"]:
        for morceau in str(t).split(","):
            m = morceau.strip()
            if m and m.lower() not in ("nan", "none"):
                compte[m] = compte.get(m, 0) + 1
    return pd.Series(compte, dtype=int).sort_values(ascending=False)
