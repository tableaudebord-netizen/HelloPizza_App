# =====================================================================
#  HELLO PIZZA - GRAPHIQUES (Plotly)
#  3 éléments sur chaque graphique : la cible du mois, le réalisé, le cumul.
#  Avril 2026 (M0) = situation de départ ; après le mois choisi :
#  seulement la cible déjà fixée (aucune prévision).
# =====================================================================
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from indicateurs import COULEURS_FEU, cle_du_numero, libelle_mois, nombre

GRIS_CIBLE = "#d6d3d1"
GRIS_FUTUR = "#efebe7"
BLEU_DEPART = "#64748b"
ENCRE = "#1e293b"
POLICE = "Segoe UI, Inter, Arial, sans-serif"

TITRES_AXES = {
    "%": ("Taux du mois (%)", "Cumul (%)"),
    "min": ("Temps du mois (min)", "Cumul (min)"),
    "points": ("Indice du mois (points)", "Cumul (points)"),
    "DH": ("Montant du mois (DH)", "Cumul (DH)"),
    "commandes": ("Commandes du mois", "Cumul (commandes)"),
    "avis": ("Avis du mois", "Cumul (avis)"),
}


def _etiquette(v, unite):
    if v is None:
        return ""
    if unite == "DH" and abs(v) >= 1000:
        return nombre(v / 1000, 1) + " k"
    if unite in ("commandes", "avis"):
        return nombre(v, 0)
    if unite == "DH":
        return nombre(v, 1)
    return nombre(v, 2 if unite == "%" else 1)


def graphique_indicateur(r, hauteur=380):
    """Barres « cible du mois » + barres « réalisé » colorées par le feu + courbe du cumul."""
    u = r["unite"]
    n = r["n"]
    x_mois = list(range(0, 13))
    etiquettes_x = [f"{libelle_mois(cle_du_numero(k), court=True)}<br>M{k}" for k in x_mois]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Situation de départ (avril 2026)
    depart = r["initiale"]   # situation de départ officielle (avril 2026)
    fig.add_trace(go.Bar(x=[0], y=[depart], width=0.55, marker_color=BLEU_DEPART, name="Départ (avril 2026)",
                         text=[_etiquette(depart, u)], textposition="outside",
                         textfont=dict(color=BLEU_DEPART, size=11),
                         hovertemplate=f"Situation de départ : %{{y}} {u}<extra></extra>"), secondary_y=False)

    # Cibles des mois passés (jusqu'au mois choisi)
    xs = list(range(1, n + 1))
    fig.add_trace(go.Bar(x=xs, y=r["cibles"], width=0.38, offset=-0.39, marker_color=GRIS_CIBLE, name="Cible du mois",
                         text=[_etiquette(v, u) for v in r["cibles"]], textposition="outside",
                         textfont=dict(color="#78716c", size=9),
                         hovertemplate=f"Cible du mois : %{{y:.2f}} {u}<extra></extra>"), secondary_y=False)

    # Réalisé, coloré selon le feu
    ys = [v if v is not None else 0 for v in r["realises"]]
    couleurs = [COULEURS_FEU[f] for f in r["feux"]]
    fig.add_trace(go.Bar(x=xs, y=ys, width=0.38, offset=0.01, marker_color=couleurs, name="Réalisé",
                         text=[_etiquette(v, u) for v in r["realises"]], textposition="outside",
                         textfont=dict(color=couleurs, size=10),
                         hovertemplate=f"Réalisé : %{{y:.2f}} {u}<extra></extra>", showlegend=False), secondary_y=False)
    # éléments de légende pour les 3 couleurs
    for f, lib in [("vert", "Réalisé · cible atteinte"), ("orange", "Réalisé · à surveiller"), ("rouge", "Réalisé · en retard")]:
        fig.add_trace(go.Bar(x=[None], y=[None], marker_color=COULEURS_FEU[f], name=lib), secondary_y=False)

    # Mois à venir : seulement la cible déjà fixée (hachurée)
    futurs = list(range(n + 1, 13))
    if futurs:
        vf = [r["toutes_cibles"][k - 1] for k in futurs]
        fig.add_trace(go.Bar(x=futurs, y=vf, width=0.55, name="Cible des mois à venir",
                             marker=dict(color=GRIS_FUTUR, line=dict(color=GRIS_CIBLE, width=1),
                                         pattern=dict(shape="/", fgcolor=GRIS_CIBLE, size=6)),
                             text=[_etiquette(v, u) for v in vf], textposition="outside",
                             textfont=dict(color="#78716c", size=9),
                             hovertemplate=f"Cible fixée : %{{y:.2f}} {u}<extra></extra>"), secondary_y=False)
        fig.add_vline(x=n + 0.5, line_dash="dot", line_color="#a8a29e", line_width=1)
        fig.add_annotation(x=n + 0.6, xanchor="left", y=0.02, yref="paper", showarrow=False, align="left",
                           text="Mois à venir :<br>cible déjà fixée,<br>aucune prévision",
                           font=dict(size=10, color="#78716c"), bgcolor="white", bordercolor="#e7e5e4", borderwidth=1)

    # Cumul (axe de droite)
    cum = r["cumuls"]
    fig.add_trace(go.Scatter(x=xs, y=cum, mode="lines+markers+text", name="Cumul",
                             line=dict(color=ENCRE, width=2.5),
                             marker=dict(size=8, color="white", line=dict(color=ENCRE, width=2)),
                             text=[_etiquette(v, u) for v in cum], textposition="bottom center",
                             textfont=dict(color=ENCRE, size=10),
                             hovertemplate=f"Cumul : %{{y:.2f}} {u}<extra></extra>"), secondary_y=True)

    # Échelles : on « zoome » sur la zone utile pour bien voir les écarts
    toutes = [v for v in r["realises"] + r["toutes_cibles"] + [depart] if v is not None]
    bas, haut = min(toutes), max(toutes)
    marge = (haut - bas) * 0.35 or abs(haut) * 0.1 or 1
    y0 = bas - marge if bas - marge > 0 or bas < 0 else 0
    if r["sens"] == "zero":
        y0 = min(toutes) * 1.25
        haut = max(0, haut)
    fig.update_yaxes(range=[y0, haut + marge * 0.9], secondary_y=False)
    vals_cum = [v for v in cum if v is not None]
    if vals_cum:
        cb, ch = min(vals_cum), max(vals_cum)
        if r["type_cumul"] == "somme":
            if ch >= 0:
                fig.update_yaxes(range=[min(0, cb) - abs(ch) * 0.1, ch * 2.0 if ch > 0 else 1], secondary_y=True)
            else:
                fig.update_yaxes(range=[cb * 2.0, abs(cb) * 0.3], secondary_y=True)
        else:
            sp = max(ch - cb, abs(ch) * 0.02, 0.5)
            fig.update_yaxes(range=[cb - sp * 0.8, ch + sp * 2.8], secondary_y=True)

    t_gauche, t_droite = TITRES_AXES.get(u, (f"Valeur du mois ({u})", f"Cumul ({u})"))
    fig.update_yaxes(title_text=t_gauche, secondary_y=False, gridcolor="#f1efed", zeroline=False,
                     tickfont=dict(size=10, color="#78716c"), title_font=dict(size=11))
    fig.update_yaxes(title_text=t_droite, secondary_y=True, showgrid=False, zeroline=False,
                     tickfont=dict(size=10, color="#475569"), title_font=dict(size=11, color=ENCRE))
    fig.update_xaxes(tickmode="array", tickvals=x_mois, ticktext=etiquettes_x, range=[-0.6, 12.6],
                     tickfont=dict(size=10, color="#292524"))
    fig.update_layout(barmode="overlay", height=hauteur, margin=dict(l=10, r=10, t=40, b=10),
                      paper_bgcolor="white", plot_bgcolor="white", font=dict(family=POLICE),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.5, xanchor="center",
                                  font=dict(size=10)), hovermode="x unified")
    if u == "DH":
        fig.update_yaxes(tickformat=",.0f", secondary_y=False)
        fig.update_yaxes(tickformat=",.0f", secondary_y=True)
    fig.update_layout(separators=", ")
    return fig


def graphique_n1(table, code, unite, cle_choisie):
    """Comparaison des 12 mois : année du projet (mai 2026 → avril 2027) vs les mêmes mois un an avant."""
    xs, actuel, avant = [], [], []
    for k in range(1, 13):
        cle = cle_du_numero(k)
        if cle > cle_choisie:
            break
        cle_av = f"{int(cle[:4]) - 1}-{cle[5:]}"
        xs.append(libelle_mois(cle, court=True))
        actuel.append(_val(table, cle, code))
        avant.append(_val(table, cle_av, code))
    fig = go.Figure()
    fig.add_trace(go.Bar(x=xs, y=avant, name="Même mois, année précédente", marker_color="#cbd5e1",
                         text=[_etiquette(v, unite) for v in avant], textposition="outside"))
    fig.add_trace(go.Bar(x=xs, y=actuel, name="Année du projet", marker_color="#ea580c",
                         text=[_etiquette(v, unite) for v in actuel], textposition="outside"))
    t, _ = TITRES_AXES.get(unite, (f"Valeur ({unite})", ""))
    fig.update_layout(barmode="group", height=340, margin=dict(l=10, r=10, t=40, b=10), paper_bgcolor="white",
                      plot_bgcolor="white", font=dict(family=POLICE), separators=", ",
                      legend=dict(orientation="h", y=1.08, x=0.5, xanchor="center"))
    fig.update_yaxes(title_text=t, gridcolor="#f1efed")
    return fig


def graphique_tourisme(tourisme, table):
    """Croisement : CA cumulé depuis janvier (DH) cette année et l'an dernier + variation officielle des nuitées."""
    t = tourisme.dropna(subset=["nuitees_cumul"])
    xs, ca_n, ca_n1, var = [], [], [], []
    for _, ligne in t.iterrows():
        p = ligne["periode"]
        a, m = int(p[:4]), int(p[5:7])
        cum = sum(_val(table, f"{a}-{k:02d}", "ca") or 0 for k in range(1, m + 1))
        cum1 = sum(_val(table, f"{a - 1}-{k:02d}", "ca") or 0 for k in range(1, m + 1))
        if cum == 0:
            continue
        xs.append(libelle_mois(p, court=True))
        ca_n.append(cum)
        ca_n1.append(cum1 or None)
        v = ligne.get("variation_n1_pct")
        var.append(None if v is None or v != v else v)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=xs, y=ca_n1, name="CA cumulé depuis janvier · année précédente (DH)", marker_color="#cbd5e1"),
                  secondary_y=False)
    fig.add_trace(go.Bar(x=xs, y=ca_n, name="CA cumulé depuis janvier · Hello Pizza (DH)", marker_color="#db2777"),
                  secondary_y=False)
    fig.add_trace(go.Scatter(x=xs, y=var, name="Nuitées à Marrakech · variation officielle vs année précédente (%)",
                             mode="lines+markers+text", text=[("" if v is None else f"{v:+.0f} %") for v in var],
                             textposition="top center", line=dict(color="#0ea5e9", width=3),
                             marker=dict(size=9)), secondary_y=True)
    fig.update_layout(barmode="group", height=420, margin=dict(l=10, r=10, t=60, b=10), paper_bgcolor="white",
                      plot_bgcolor="white", font=dict(family=POLICE), separators=", ",
                      legend=dict(orientation="h", y=1.12, x=0.5, xanchor="center", font=dict(size=10)))
    fig.update_yaxes(title_text="CA cumulé depuis janvier (DH)", tickformat=",.0f", gridcolor="#f1efed", secondary_y=False)
    fig.update_yaxes(title_text="Variation des nuitées (%)", showgrid=False, secondary_y=True)
    return fig


def graphique_nuitees(tourisme):
    t = tourisme.dropna(subset=["nuitees_cumul"])
    fig = go.Figure(go.Bar(x=[libelle_mois(p, court=True) for p in t["periode"]], y=t["nuitees_cumul"] / 1e6,
                           marker_color="#0ea5e9", text=[nombre(v / 1e6, 2) + " M" for v in t["nuitees_cumul"]],
                           textposition="outside",
                           hovertemplate="%{y:.2f} millions de nuitées (cumul depuis janvier)<extra></extra>"))
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=20, b=10), paper_bgcolor="white", plot_bgcolor="white",
                      font=dict(family=POLICE), separators=", ")
    fig.update_yaxes(title_text="Nuitées cumulées depuis janvier (millions)", gridcolor="#f1efed")
    return fig


def graphique_reclamations(serie):
    fig = go.Figure(go.Bar(x=serie.values, y=serie.index, orientation="h", marker_color="#0d9488",
                           text=serie.values, textposition="outside"))
    fig.update_layout(height=max(220, 50 * len(serie) + 60), margin=dict(l=10, r=30, t=10, b=10),
                      paper_bgcolor="white", plot_bgcolor="white", font=dict(family=POLICE))
    fig.update_xaxes(title_text="Nombre de réclamations", gridcolor="#f1efed")
    fig.update_yaxes(autorange="reversed")
    return fig


def _val(table, cle, col):
    try:
        v = float(table.at[cle, col])
        return None if v != v else v
    except (KeyError, TypeError, ValueError):
        return None
