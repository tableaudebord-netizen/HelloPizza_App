# =====================================================================
#  HELLO PIZZA - APPLICATION « TABLEAU DE BORD »  (Python · Streamlit)
#  Lancement :  python -m streamlit run app.py
# =====================================================================
from datetime import date

import streamlit as st

import config
import interface as ui
import pages
from donnees import charger_tout
from indicateurs import PROCESSUS, calculer_tout, cle_du_numero, libelle_mois, numero_mois

st.set_page_config(page_title="Hello Pizza · Tableau de bord", page_icon="🍕", layout="wide")
ui.appliquer_style()


@st.cache_data(ttl=600, show_spinner="Lecture des données Google Sheets…")
def donnees():
    return charger_tout()


# ---------------------------------------------------------------------
#  1. Connexion
# ---------------------------------------------------------------------
def page_connexion():
    _, milieu, _ = st.columns([1, 1.2, 1])
    with milieu:
        st.markdown('<div style="height:60px"></div>', unsafe_allow_html=True)
        st.markdown('<div class="hp-hero" style="justify-content:center;text-align:center"><div>'
                    '<h1>🍕 Hello Pizza</h1><p>Tableau de bord · système d\'information du restaurant (Marrakech)</p>'
                    '</div></div>', unsafe_allow_html=True)
        with st.form("connexion"):
            st.markdown("#### Se connecter")
            identifiant = st.text_input("Identifiant", placeholder="gerant, chef, serveur ou caissier")
            mot_de_passe = st.text_input("Mot de passe", type="password")
            ok = st.form_submit_button("Se connecter", type="primary")
        if ok:
            compte = config.COMPTES.get(identifiant.strip().lower())
            if compte and compte[0] == mot_de_passe:
                st.session_state["utilisateur"] = {"id": identifiant.strip().lower(), "role": compte[1], "nom": compte[2]}
                st.rerun()
            else:
                st.error("Identifiant ou mot de passe incorrect.")
        st.caption("Le gérant voit la synthèse et les fonctions de pilotage ; les responsables voient les "
                   "4 tableaux de bord de processus.")


if "utilisateur" not in st.session_state:
    page_connexion()
    st.stop()

user = st.session_state["utilisateur"]

# ---------------------------------------------------------------------
#  2. Données et mois choisi
# ---------------------------------------------------------------------
table, veille, tourisme, avis, source, erreur = donnees()

mois_dispo = [m for m in table.index if 1 <= numero_mois(m) <= 12 and table.loc[m].notna().any()]
if not mois_dispo:
    st.error("Aucune donnée trouvée pour les mois M1 (mai 2026) à M12 (avril 2027) dans l'onglet « indicateurs ».")
    st.stop()

# ---------------------------------------------------------------------
#  3. Menu de gauche
# ---------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="hp-logo">Hello <span>Pizza</span> 🍕</div>'
                '<div class="hp-tag">Tableau de bord · Marrakech</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="hp-user"><div class="hp-av">{user["nom"][0]}</div><div><b>{user["nom"]}</b>'
                f'<small>{"Accès synthèse et pilotage" if user["role"] == "gerant" else "Accès aux 4 tableaux de bord"}'
                f'</small></div></div>', unsafe_allow_html=True)

    if user["role"] == "gerant":
        menu = ["📊 Synthèse", "🌳 Carte des objectifs", "💡 Diagnostic du mois", "🎯 Ce qu'il reste à faire",
                "🎚️ Simulateur « Et si… ? »", "📅 Comparaison N-1", "📰 Veille externe", "✈️ Tourisme & ventes",
                "⚙️ Cibles", "📄 Rapport mensuel"]
        choix = st.radio("Pilotage", menu, label_visibility="collapsed")
    else:
        choix = st.radio("Processus", list(PROCESSUS), format_func=lambda p: f"{PROCESSUS[p]['icone']} {p}")

    st.divider()
    cle = st.selectbox("Mois analysé", mois_dispo[::-1],
                       format_func=lambda m: f"{libelle_mois(m)} · M{numero_mois(m)}")
    if st.button("🔄 Actualiser les données"):
        st.cache_data.clear()
        st.rerun()
    if st.button("🚪 Se déconnecter"):
        st.session_state.clear()
        st.rerun()
    st.caption(f"Source : {source}")
    if erreur:
        st.caption(f"⚠️ Google Sheets indisponible ({erreur}) : affichage des données de secours.")

# ---------------------------------------------------------------------
#  4. Calculs et affichage de la page
# ---------------------------------------------------------------------
n = numero_mois(cle)
aujourd_hui = date.today()
ctx = dict(table=table, veille=veille, tourisme=tourisme, avis=avis, source=source, cle=cle, n=n,
           res=calculer_tout(table, n),
           partiel=(cle == f"{aujourd_hui.year}-{aujourd_hui.month:02d}"))

if user["role"] == "gerant":
    if choix.startswith("📊"):
        pages.synthese(ctx)
    elif choix.startswith("🌳"):
        pages.carte_objectifs(ctx)
    elif choix.startswith("💡"):
        pages.page_diagnostic(ctx)
    elif choix.startswith("🎯"):
        pages.page_reste_a_faire(ctx)
    elif choix.startswith("🎚️"):
        pages.page_simulateur(ctx)
    elif choix.startswith("📅"):
        pages.page_n1(ctx)
    elif choix.startswith("📰"):
        pages.page_veille(ctx)
    elif choix.startswith("✈️"):
        pages.page_tourisme(ctx)
    elif choix.startswith("⚙️"):
        pages.page_cibles(ctx)
    else:
        pages.page_rapport(ctx)
else:
    pages.tableau_processus(ctx, choix)
