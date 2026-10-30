# =====================================================================
#  HELLO PIZZA - ÉLÉMENTS VISUELS (style, cartes, anneaux, bandeau)
# =====================================================================
import math

import streamlit as st

from indicateurs import (COULEURS_FEU, LIBELLES_FEU, PROCESSUS, TEINTES_FEU, fmt, fmt_ecart, libelle_mois)

CSS = """
<style>
html, body, [class*="css"] { font-family: "Segoe UI", Inter, Arial, sans-serif; }
.block-container { padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1500px; }
[data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #efe7df; }
[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 18px !important; background: #ffffff;
    border: 1px solid #efe7df !important; box-shadow: 0 6px 18px rgba(120,80,40,.07); }
.hp-logo { font-size: 24px; font-weight: 900; letter-spacing: -.5px; margin-bottom: 0; }
.hp-logo span { color: #f97316; }
.hp-tag { font-size: 12px; color: #78716c; margin-bottom: 14px; }
.hp-user { display:flex; gap:10px; align-items:center; background:#fff4ec; border-radius:12px; padding:10px; margin-bottom:10px; }
.hp-av { width:36px; height:36px; border-radius:50%; background:linear-gradient(135deg,#ef4444,#f97316);
    display:flex; align-items:center; justify-content:center; color:#fff; font-weight:800; }
.hp-user b { font-size:14px; display:block; } .hp-user small { font-size:11.5px; color:#78716c; }
.hp-hero { display:flex; justify-content:space-between; align-items:center; gap:20px; border-radius:20px; padding:22px 28px;
    color:#fff; margin-bottom:16px; box-shadow:0 10px 30px rgba(234,88,12,.22);
    background: radial-gradient(circle at 85% 20%, rgba(255,255,255,.18), transparent 40%),
                linear-gradient(120deg,#b91c1c,#ea580c 60%,#f59e0b); }
.hp-hero h1 { font-size:27px; font-weight:900; margin:0; color:#fff; padding:0; }
.hp-hero p { font-size:13.5px; opacity:.92; margin:4px 0 0; }
.hp-chips { display:flex; gap:10px; margin-top:14px; flex-wrap:wrap; }
.hp-hc { background:rgba(0,0,0,.22); border-radius:12px; padding:8px 14px; font-size:12px; }
.hp-hc b { font-size:20px; display:block; }
.hp-score { display:flex; align-items:center; gap:16px; background:rgba(0,0,0,.2); border-radius:18px; padding:12px 18px; }
.hp-score .l { font-size:12px; opacity:.95; } .hp-score .l b { font-size:16px; display:block; }
.hp-box { background:#fff; border:1px solid #f1e4d6; border-radius:16px; padding:14px 18px; margin-bottom:16px;
    box-shadow:0 4px 14px rgba(120,80,40,.06); }
.hp-box h4 { margin:0 0 6px; font-size:14px; color:#c2410c; }
.hp-box p, .hp-box li { font-size:13.5px; color:#44403c; line-height:1.55; margin:0 0 4px; }
.hp-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:2px; }
.hp-chip { font-size:12px; font-weight:700; padding:3px 11px; border-radius:20px; border:1px solid; }
.hp-badge { font-size:12px; font-weight:800; padding:4px 12px; border-radius:20px; }
.hp-bar { height:5px; border-radius:4px; margin:-6px -6px 10px; }
.hp-nm { font-size:17px; font-weight:800; margin:8px 0 2px; color:#1c1917; }
.hp-row { display:flex; justify-content:space-between; align-items:center; gap:10px; }
.hp-val { font-size:40px; font-weight:900; letter-spacing:-1px; line-height:1.1; }
.hp-val small { font-size:16px; margin-left:5px; color:#78716c; font-weight:700; letter-spacing:0; }
.hp-sous { font-size:12.5px; color:#78716c; }
.hp-mts { display:grid; grid-template-columns:repeat(2,1fr); gap:8px; margin:12px 0 10px; }
.hp-mt { background:#faf6f1; border-radius:10px; padding:8px 10px; border:1px solid #f0e7dd; }
.hp-mt span { font-size:11px; color:#78716c; display:block; } .hp-mt b { font-size:14.5px; }
.hp-fx { font-size:12px; color:#57534e; display:grid; gap:4px; padding:8px 10px; border-radius:10px;
    border:1px dashed #e7ddd3; background:#fffdfb; }
.hp-fx i { display:inline-block; width:16px; color:#ea580c; font-weight:800; font-style:normal; }
.hp-fx b { color:#1c1917; margin-right:4px; }
.hp-tile { background:#fff; border-radius:14px; padding:12px 16px; border:1px solid #efe7df; border-left:5px solid; }
.hp-tile .l { font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:.4px; }
.hp-tile .v { font-size:24px; font-weight:900; margin-top:2px; }
.hp-art { background:#fff; border:1px solid #efe7df; border-radius:14px; padding:12px 16px; margin-bottom:10px; }
.hp-art a { font-weight:700; color:#1c1917; text-decoration:none; font-size:14.5px; }
.hp-art small { color:#78716c; font-size:12px; }
.hp-tree { text-align:center; }
.hp-node { display:inline-block; border-radius:14px; padding:10px 14px; margin:6px; border:2px solid; background:#fff; vertical-align:top; }
.hp-sub { display:block; font-size:12px; border-radius:10px; padding:5px 8px; margin-top:6px; text-align:left; }
</style>
"""


def appliquer_style():
    st.markdown(CSS, unsafe_allow_html=True)


def anneau(part, couleur, taille=96, epaisseur=9, texte=None, sous_texte="", fond="#ece7e2", couleur_texte="#1c1917",
           couleur_sous="#78716c"):
    r = (taille - epaisseur) / 2
    c = 2 * math.pi * r
    p = max(0.0, min(part, 1.0))
    texte = f"{p * 100:.0f}" if texte is None else texte
    return (f'<svg width="{taille}" height="{taille}" viewBox="0 0 {taille} {taille}">'
            f'<circle cx="{taille / 2}" cy="{taille / 2}" r="{r}" stroke="{fond}" stroke-width="{epaisseur}" fill="none"/>'
            f'<circle cx="{taille / 2}" cy="{taille / 2}" r="{r}" stroke="{couleur}" stroke-width="{epaisseur}" fill="none" '
            f'stroke-linecap="round" stroke-dasharray="{c * p:.1f} {c:.1f}" transform="rotate(-90 {taille / 2} {taille / 2})"/>'
            f'<text x="50%" y="47%" text-anchor="middle" fill="{couleur_texte}" font-size="{taille * 0.25:.0f}" '
            f'font-weight="800" dy=".1em">{texte}</text>'
            f'<text x="50%" y="70%" text-anchor="middle" fill="{couleur_sous}" font-size="{taille * 0.115:.0f}">{sous_texte}</text></svg>')


def bandeau(titre, sous_titre, compteurs, score, score_max, titre_score="score global",
            legende="Part de l'année gagnée<br>(mois où la cible est atteinte)"):
    chips = "".join(f'<div class="hp-hc"><b>{v}</b>{t}</div>' for v, t in compteurs)
    ring = anneau(score / 100, "#ffffff", 112, 11, str(score), titre_score, fond="rgba(255,255,255,.3)",
                  couleur_texte="#ffffff", couleur_sous="#ffe8d6")
    st.markdown(f"""<div class="hp-hero"><div><h1>{titre}</h1><p>{sous_titre}</p><div class="hp-chips">{chips}</div></div>
<div class="hp-score">{ring}<div class="l">{legende}<b>{score} / 100</b>
<span style="font-size:11.5px;opacity:.9">maximum possible à ce mois : {score_max}</span></div></div></div>""",
                unsafe_allow_html=True)


def encadre(titre, contenu_html, icone="💡"):
    st.markdown(f'<div class="hp-box"><h4>{icone} {titre}</h4>{contenu_html}</div>', unsafe_allow_html=True)


def tuiles(liste):
    """liste de (libellé, valeur, couleur)."""
    cols = st.columns(len(liste))
    for col, (lib, val, coul) in zip(cols, liste):
        col.markdown(f'<div class="hp-tile" style="border-left-color:{coul}"><div class="l" style="color:{coul}">{lib}</div>'
                     f'<div class="v" style="color:{coul}">{val}</div></div>', unsafe_allow_html=True)


def entete_carte(r):
    p = PROCESSUS[r["processus"]]
    coul = COULEURS_FEU[r["feu"]]
    st.markdown(f"""<div class="hp-bar" style="background:{coul}"></div>
<div class="hp-head"><span class="hp-chip" style="color:{p['couleur']};border-color:{p['couleur']}55;background:{p['couleur']}14">
{p['icone']} {r['processus']}</span>
<span class="hp-badge" style="color:{coul};background:{TEINTES_FEU[r['feu']]}">● {LIBELLES_FEU[r['feu']]}</span></div>""",
                unsafe_allow_html=True)


def infos_carte(r, sous_titre="", partiel=False):
    """Partie gauche d'une carte : nom, réalisé, anneau, cases, formules."""
    coul = COULEURS_FEU[r["feu"]]
    u = r["unite"]
    val = fmt(r["realise"], u).rsplit(" ", 1)[0] if r["realise"] is not None else "—"
    mois = libelle_mois(r["cle"])
    n1_lib = libelle_mois(r["cle_n1"])
    cases = [
        ("Cible du mois", fmt(r["cible"], u), ""),
        ("Écart avec la cible", fmt_ecart(r["ecart"], u), coul),
        (f"Cumul M1 → M{r['n']}", fmt(r["cumul"], u), ""),
        ("Cumul cible", fmt(r["cumul_cible"], u), ""),
        (f"Même mois N-1 ({n1_lib})", fmt(r["n1"], u), ""),
        ("Différence avec N-1", fmt_ecart(r["diff_n1"], u), ""),
    ]
    html_cases = "".join(f'<div class="hp-mt"><span>{a}</span><b style="color:{c or "#1c1917"}">{b}</b></div>'
                         for a, b, c in cases)
    alerte = ('<div class="hp-sous" style="color:#b45309">⚠️ Mois en cours : données partielles.</div>' if partiel else "")
    ring = anneau(r["reussis"] / 12, coul, 96, 9, str(r["score"]), f"{r['reussis']} / 12 mois")
    st.markdown(f"""<div class="hp-nm">{r['nom']}</div>
<div class="hp-row"><div><div class="hp-sous">Réalisé · {mois}</div>
<div class="hp-val" style="color:{coul}">{val}<small>{u}</small></div><div class="hp-sous">{sous_titre}</div>{alerte}</div>
<div title="Score = mois où la cible est atteinte ÷ 12 × 100">{ring}</div></div>
<div class="hp-mts">{html_cases}</div>
<div class="hp-fx"><div><i>ƒ</i> <b>Formule</b> {r['formule']}</div><div><i>Σ</i> <b>Cumul</b> {r['formule_cumul']}</div></div>""",
                unsafe_allow_html=True)


def afficher_graphique(fig):
    """Compatible avec les anciennes et nouvelles versions de Streamlit."""
    config = {"displaylogo": False, "locale": "fr"}
    try:
        st.plotly_chart(fig, width="stretch", config=config)
    except TypeError:
        st.plotly_chart(fig, use_container_width=True, config=config)


def article(ligne):
    proc = ligne.get("processus", "")
    p = PROCESSUS.get(proc, {"couleur": "#64748b", "icone": "📰"})
    date = str(ligne.get("date_publication", ""))[:10]
    st.markdown(f"""<div class="hp-art"><span class="hp-chip" style="color:{p['couleur']};border-color:{p['couleur']}55;
background:{p['couleur']}14;font-size:11px">{p['icone']} {ligne.get('theme', '')}</span>
<div style="margin-top:6px"><a href="{ligne.get('lien', '#')}" target="_blank">{ligne.get('titre', '')}</a></div>
<small>{ligne.get('source', '')} · publié le {date} · processus : {proc}</small></div>""", unsafe_allow_html=True)
