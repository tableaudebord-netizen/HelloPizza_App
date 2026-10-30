# =====================================================================
#  HELLO PIZZA - LES PAGES DE L'APPLICATION
#  Gérant : synthèse et pilotage.  Responsables : 4 tableaux de bord de processus.
# =====================================================================
import pandas as pd
import streamlit as st

import diagnostic as dg
import graphiques as gr
import interface as ui
from donnees import reclamations_par_type
from indicateurs import (COULEURS_FEU, INDICATEURS, LIBELLES_FEU, MAJEURS, OBJECTIF_GLOBAL, PROCESSUS,
                         charger_cibles_modifiees, cible_du_mois, cle_du_numero, enregistrer_cibles, feu, fmt,
                         fmt_ecart, libelle_mois, nombre, score_global, score_processus)


def _compteurs(res, codes):
    feux = [res[c]["feu"] for c in codes]
    return feux.count("vert"), feux.count("orange"), feux.count("rouge")


def carte_complete(ctx, code):
    """Une carte indicateur : infos à gauche, graphique (cible / réalisé / cumul) à droite."""
    r = ctx["res"][code]
    with st.container(border=True):
        ui.entete_carte(r)
        gauche, droite = st.columns([1, 1.9], gap="large")
        with gauche:
            ui.infos_carte(r, dg.sous_titre(r, ctx["table"]), ctx["partiel"])
        with droite:
            ui.afficher_graphique(gr.graphique_indicateur(r))


# ---------------------------------------------------------------------
#  GÉRANT
# ---------------------------------------------------------------------
def synthese(ctx):
    res, n = ctx["res"], ctx["n"]
    v, o, rg = _compteurs(res, MAJEURS)
    tour = dg.derniere_variation_tourisme(ctx["tourisme"], ctx["cle"])
    compteurs = [(v, "cibles du mois atteintes"), (o, "à surveiller"), (rg, "en retard")]
    if tour is not None and tour.get("variation_n1_pct") == tour.get("variation_n1_pct"):
        compteurs.append((f"{tour['variation_n1_pct']:+.0f} %".replace(".", ","), "nuitées Marrakech"))
    etat = " (mois en cours · données partielles)" if ctx["partiel"] else ""
    ui.bandeau(f"Bonjour 👋 voici le mois de {libelle_mois(ctx['cle'])}",
               f"Mois M{n} du projet{etat} · 4 objectifs majeurs · données {ctx['source']}",
               compteurs, score_global(res), round(n / 12 * 100))
    for code in MAJEURS:
        carte_complete(ctx, code)


def carte_objectifs(ctx):
    res = ctx["res"]
    st.subheader("🌳 Carte des objectifs")
    st.caption("De l'objectif global aux objectifs des processus et à leurs indicateurs. "
               "La couleur indique le feu du mois choisi ; le chiffre est le score (mois réussis ÷ 12 × 100).")
    sg = score_global(res)
    html = (f'<div class="hp-tree"><div class="hp-node" style="border-color:#ea580c;background:#fff4ec;max-width:760px">'
            f'<div style="font-size:12px;color:#c2410c;font-weight:800">OBJECTIF OPÉRATIONNEL</div>'
            f'<div style="font-size:16px;font-weight:800">{OBJECTIF_GLOBAL}</div>'
            f'<div style="font-size:13px;margin-top:4px">Score global : <b>{sg} / 100</b></div></div>'
            f'<div style="font-size:26px;color:#a8a29e">↓</div>')
    for proc, p in PROCESSUS.items():
        codes = [c for c, d in INDICATEURS.items() if d["processus"] == proc]
        maj = next(c for c in codes if INDICATEURS[c]["majeur"])
        coul = COULEURS_FEU[res[maj]["feu"]]
        subs = ""
        for c in codes:
            r = res[c]
            fc = COULEURS_FEU[r["feu"]]
            subs += (f'<span class="hp-sub" style="background:{fc}18;border-left:4px solid {fc}">'
                     f'{"⭐ " if r["majeur"] else ""}{r["nom"]} : <b>{fmt(r["realise"], r["unite"])}</b> '
                     f'· score {r["score"]}</span>')
        html += (f'<div class="hp-node" style="border-color:{coul};width:23%;min-width:250px">'
                 f'<div style="color:{p["couleur"]};font-weight:800">{p["icone"]} {proc}</div>'
                 f'<div style="font-size:12px;color:#57534e;margin:4px 0">{p["objectif"]}</div>'
                 f'<div style="font-size:13px">Score du processus : <b>{score_processus(res, proc)} / 100</b></div>{subs}</div>')
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)
    st.caption("⭐ = indicateur de l'objectif majeur du processus.")


def page_diagnostic(ctx):
    st.subheader("💡 Diagnostic automatique du mois")
    st.caption("Des règles de comparaison (réalisé / cible / mois précédents / veille externe) écrivent ces phrases. "
               "Aucune prédiction.")
    ui.encadre("Les 4 objectifs majeurs",
               "".join(f"<p>{p}</p>" for p in dg.phrases(ctx["res"], ctx["table"], ctx["tourisme"], ctx["partiel"])))
    for proc in PROCESSUS:
        codes = [c for c, d in INDICATEURS.items() if d["processus"] == proc and not d["majeur"]]
        ui.encadre(f"{PROCESSUS[proc]['icone']} {proc} · indicateurs détaillés",
                   "".join(f"<p>{p}</p>" for p in dg.phrases(ctx["res"], ctx["table"], ctx["tourisme"], False, codes)),
                   icone="")


def page_reste_a_faire(ctx, codes=None):
    codes = codes or list(INDICATEURS)
    st.subheader("🎯 Ce qu'il reste à faire")
    st.caption("Pour chaque indicateur : l'effort à fournir chaque mois pour atteindre la cible finale d'avril 2027, "
               "comparé au rythme moyen depuis avril 2026.")
    lignes = []
    for code in codes:
        r = ctx["res"][code]
        a = dg.reste_a_faire(r)
        if a is None:
            continue
        u = r["unite"]
        if a["deja"]:
            msg = "✅ Cible finale déjà atteinte : il faut maintenir ce niveau."
        elif a["restants"] <= 0:
            msg = "⏱️ Échéance atteinte."
        else:
            fois = (a["besoin"] / a["rythme"]) if a["rythme"] and (a["besoin"] * a["rythme"] > 0) else None
            msg = (f"Effort nécessaire : <b>{fmt(a['besoin'], u, signe=True)} par mois</b> pendant les "
                   f"{a['restants']} mois restants. Évolution moyenne depuis avril 2026 : {fmt(a['rythme'], u, signe=True)} par mois")
            msg += (f" → effort à multiplier par <b>{nombre(fois, 1)}</b>." if fois and fois > 1.05
                    else " → le rythme actuel suffit." if fois else " → la tendance actuelle va dans le mauvais sens.")
        lignes.append((r, msg))
    for proc in PROCESSUS:
        bloc = [(r, m) for r, m in lignes if r["processus"] == proc]
        if not bloc:
            continue
        html = "".join(f"<p><b>{r['nom']}</b> · aujourd'hui {fmt(r['realise'], r['unite'])} · cible finale "
                       f"{fmt(r['cible_finale'], r['unite'])}<br>{m}</p>" for r, m in bloc)
        ui.encadre(proc, html, icone=PROCESSUS[proc]["icone"])


PHRASE_FEU = {"vert": "atteint la cible du mois", "orange": "est un peu en dessous de la cible du mois (à surveiller)",
              "rouge": "est en dessous de la cible du mois (en retard)", "gris": "n'est pas calculable"}


def page_simulateur(ctx):
    res = ctx["res"]
    n = ctx["n"]
    st.subheader("🎚️ Simulateur « Et si… ? »")
    st.caption("Le gérant fixe un nombre de commandes et un ticket moyen : l'application calcule le chiffre "
               "d'affaires obtenu et le compare à la cible du mois. Rien n'est enregistré.")
    cmd0 = res["nb_commandes"]["realise"] or 540
    tick0 = res["ticket_moyen"]["realise"] or 61
    c1, c2 = st.columns(2)
    cmd = c1.number_input("Nombre de commandes du mois", min_value=0, max_value=5000, value=int(round(cmd0)), step=10)
    tick = c2.number_input("Ticket moyen (DH)", min_value=0.0, max_value=500.0, value=float(round(tick0, 1)), step=0.5)
    ca = cmd * tick
    cible = cible_du_mois("ca", n)
    aug = ca - INDICATEURS["ca"]["initiale"]
    objectif = INDICATEURS["ca"]["finale"] - INDICATEURS["ca"]["initiale"]
    f = feu("ca", ca, cible)
    st.write("")
    ui.tuiles([("Chiffre d'affaires obtenu", fmt(ca, "DH"), "#db2777"),
               (f"Cible du mois ({libelle_mois(ctx['cle'])})", fmt(cible, "DH"), "#57534e"),
               ("Écart avec la cible du mois", fmt_ecart(ca - cible, "DH"), COULEURS_FEU[f]),
               ("Augmentation depuis avril 2026", f"{fmt(aug, 'DH', signe=True)}", "#ea580c")])
    st.write("")
    ui.encadre("Résultat",
               f"<p><b>CA = nombre de commandes × ticket moyen = {nombre(cmd, 0)} × {nombre(tick, 2)} DH = "
               f"{fmt(ca, 'DH')}</b></p>"
               f"<p>Ce chiffre d'affaires <b style='color:{COULEURS_FEU[f]}'>{PHRASE_FEU[f]}</b> "
               f"({fmt(cible, 'DH')}). Par rapport à avril 2026, l'augmentation serait de "
               f"<b>{fmt(aug, 'DH', signe=True)}</b>, pour un objectif de <b>{fmt(objectif, 'DH', signe=True)}</b> "
               f"en avril 2027.</p>"
               f"<p>Pour atteindre la cible du mois avec {nombre(cmd, 0)} commandes, il faudrait un ticket moyen de "
               f"<b>{fmt(cible / cmd if cmd else None, 'DH')}</b> ; avec un ticket de {nombre(tick, 2)} DH, il faudrait "
               f"<b>{nombre(cible / tick if tick else None, 0)} commandes</b>.</p>", icone="🧮")


def page_n1(ctx, codes=None):
    codes = codes or MAJEURS
    st.subheader("📅 Comparaison avec l'année précédente (N-1)")
    st.caption(f"Le mois choisi ({libelle_mois(ctx['cle'])}) comparé au même mois de l'année précédente.")
    lignes = []
    for code in INDICATEURS:
        r = ctx["res"][code]
        lignes.append({"Processus": r["processus"], "Indicateur": r["nom"],
                       libelle_mois(ctx["cle"]): fmt(r["realise"], r["unite"]),
                       libelle_mois(r["cle_n1"]): fmt(r["n1"], r["unite"]),
                       "Différence": fmt_ecart(r["diff_n1"], r["unite"])})
    st.dataframe(pd.DataFrame(lignes), hide_index=True)
    choix = st.selectbox("Indicateur à comparer mois par mois", codes + [c for c in INDICATEURS if c not in codes],
                         format_func=lambda c: INDICATEURS[c]["nom"])
    ui.afficher_graphique(gr.graphique_n1(ctx["table"], choix, INDICATEURS[choix]["unite"], ctx["cle"]))


def page_veille(ctx, processus=None):
    titre = "📰 Veille externe" + (f" · {processus}" if processus else "")
    st.subheader(titre)
    st.caption("Articles collectés et filtrés automatiquement chaque lundi par n8n (Google Actualités). "
               "Aucune saisie ni validation manuelle.")
    v = ctx["veille"]
    if processus == "Préparation":
        st.info("Aucun thème de veille n'est rattaché au processus Préparation "
                "(thèmes suivis : prix des matières premières, attentes des clients, tourisme).")
        return
    if processus:
        v = v[v["processus"] == processus]
    else:
        themes = sorted(t for t in v["theme"].unique() if t)
        choix = st.multiselect("Thèmes", themes, default=themes)
        v = v[v["theme"].isin(choix)]
    if v.empty:
        st.info("Aucun article pour le moment : la collecte n8n a lieu chaque lundi à 7 h.")
    else:
        st.caption(f"{len(v)} article(s)")
        for _, ligne in v.head(30).iterrows():
            ui.article(ligne)
    if processus in (None, "Gestion des ventes"):
        page_tourisme(ctx, court=True)


def page_tourisme(ctx, court=False):
    t = ctx["tourisme"]
    st.subheader("✈️ Tourisme à Marrakech · chiffres officiels")
    if t.empty:
        st.info("Pas encore de chiffre officiel dans l'onglet « tourisme ».")
        return
    dernier = t.dropna(subset=["nuitees_cumul"]).iloc[-1]
    var = dernier.get("variation_n1_pct")
    ui.tuiles([("Dernier chiffre officiel", f"{nombre(dernier['nuitees_cumul'] / 1e6, 2)} M nuitées", "#0ea5e9"),
               ("Période", str(dernier.get("libelle", "")).replace("Cumul ", ""), "#0369a1"),
               ("Variation vs année précédente", "—" if var is None or var != var else f"{var:+.0f} %".replace(".", ","),
                "#16a34a" if (var or 0) >= 0 else "#dc2626")])
    st.caption(f"Source : Observatoire du Tourisme (nuitées dans les hébergements classés de Marrakech), "
               f"relayé par {dernier.get('media', '')} — [lire l'article]({dernier.get('lien', '')})")
    if court:
        ui.afficher_graphique(gr.graphique_nuitees(t))
        return
    st.markdown("#### Croisement : chiffre d'affaires de Hello Pizza et tourisme")
    st.caption("Barres : CA cumulé depuis janvier (DH), cette année et l'année précédente. "
               "Courbe : variation officielle des nuitées à Marrakech par rapport à l'année précédente.")
    ui.afficher_graphique(gr.graphique_tourisme(t, ctx["table"]))
    ui.encadre("Lecture", "".join(f"<p>{p}</p>" for p in dg.phrases(ctx["res"], ctx["table"], t, False, ["ca"])))
    tab = t[["libelle", "nuitees_cumul", "variation_n1_pct", "media", "lien"]].rename(columns={
        "libelle": "Période", "nuitees_cumul": "Nuitées (cumul)", "variation_n1_pct": "Variation N-1 (%)",
        "media": "Média", "lien": "Lien"})
    st.dataframe(tab, hide_index=True)


def page_cibles(ctx):
    st.subheader("⚙️ Fixer et modifier les cibles")
    st.caption("Le gérant peut modifier la cible finale (avril 2027) d'un indicateur. "
               "Les cibles des mois sont recalculées automatiquement. Les modifications sont enregistrées dans cibles.json.")
    modif = charger_cibles_modifiees()
    nouvelles = {}
    for proc in PROCESSUS:
        st.markdown(f"**{PROCESSUS[proc]['icone']} {proc}**")
        codes = [c for c, d in INDICATEURS.items() if d["processus"] == proc]
        cols = st.columns(len(codes))
        for col, code in zip(cols, codes):
            d = INDICATEURS[code]
            nouvelles[code] = col.number_input(f"{d['nom']} ({d['unite']})",
                                               value=float(modif.get(code, d["finale"])), key=f"cible_{code}",
                                               help=f"Départ (avril 2026) : {fmt(d['initiale'], d['unite'])}")
    c1, c2 = st.columns(2)
    if c1.button("💾 Enregistrer les cibles", type="primary"):
        enregistrer_cibles({c: v for c, v in nouvelles.items() if abs(v - INDICATEURS[c]["finale"]) > 1e-9})
        st.success("Cibles enregistrées.")
        st.rerun()
    if c2.button("↩️ Revenir aux cibles de la présentation"):
        enregistrer_cibles({})
        for code in INDICATEURS:
            st.session_state.pop(f"cible_{code}", None)
        st.rerun()


def page_rapport(ctx, processus=None):
    from rapport import creer_pdf, envoyer_email
    codes = MAJEURS if processus is None else [c for c, d in INDICATEURS.items() if d["processus"] == processus]
    titre = "Rapport mensuel de synthèse" if processus is None else f"Tableau de bord {processus}"
    st.subheader("📄 " + titre)
    phrases = dg.phrases(ctx["res"], ctx["table"], ctx["tourisme"], ctx["partiel"], codes)
    score = score_global(ctx["res"]) if processus is None else score_processus(ctx["res"], processus)
    try:
        pdf = creer_pdf(titre, ctx["res"], codes, phrases, score, ctx["source"])
    except Exception as e:
        st.error(f"Impossible de créer le PDF : {e}")
        return
    nom = f"HelloPizza_{(processus or 'synthese').replace(' ', '_')}_{ctx['cle']}.pdf"
    st.download_button("⬇️ Télécharger le PDF", pdf, file_name=nom, mime="application/pdf", type="primary")
    if processus is None:
        if st.button("✉️ Envoyer le rapport mensuel maintenant"):
            try:
                envoyer_email(f"Hello Pizza – rapport de {libelle_mois(ctx['cle'])}",
                              "Bonjour,\n\nVoici le rapport mensuel du tableau de bord Hello Pizza.\n", pdf, nom)
                st.success("Rapport envoyé par e-mail.")
            except Exception as e:
                st.warning(f"Envoi impossible : {e}")
        st.caption("Le rapport est aussi envoyé automatiquement chaque mois par n8n (alertes Gmail).")


# ---------------------------------------------------------------------
#  RESPONSABLES : un tableau de bord par processus
# ---------------------------------------------------------------------
def tableau_processus(ctx, processus):
    res, n = ctx["res"], ctx["n"]
    p = PROCESSUS[processus]
    codes = [c for c, d in INDICATEURS.items() if d["processus"] == processus]
    v, o, rg = _compteurs(res, codes)
    etat = " (mois en cours · données partielles)" if ctx["partiel"] else ""
    ui.bandeau(f"{p['icone']} Tableau de bord · {processus}",
               f"{p['objectif']}<br>{libelle_mois(ctx['cle'])} · mois M{n}{etat}",
               [(v, "cibles du mois atteintes"), (o, "à surveiller"), (rg, "en retard"), (len(codes), "indicateurs")],
               score_processus(res, processus), round(n / 12 * 100), titre_score="score processus")
    onglets = st.tabs(["📊 Indicateurs", "🎯 Ce qu'il reste à faire", "📅 Comparaison N-1",
                       "🙋 Réclamations" if processus == "Service clients" else "💡 Diagnostic",
                       "📰 Veille externe", "📄 Export PDF"])
    with onglets[0]:
        for code in codes:
            carte_complete(ctx, code)
    with onglets[1]:
        page_reste_a_faire(ctx, codes)
    with onglets[2]:
        page_n1(ctx, codes)
    with onglets[3]:
        if processus == "Service clients":
            page_reclamations(ctx)
        else:
            ui.encadre("Diagnostic automatique",
                       "".join(f"<p>{x}</p>" for x in dg.phrases(res, ctx["table"], ctx["tourisme"], ctx["partiel"], codes)))
    with onglets[4]:
        page_veille(ctx, processus)
    with onglets[5]:
        page_rapport(ctx, processus)


def page_reclamations(ctx):
    st.subheader("🙋 Analyse des réclamations par type")
    periode = st.radio("Période", ["Mois choisi", "Depuis le début du projet (M1)"], horizontal=True)
    if periode == "Mois choisi":
        mois = [ctx["cle"]]
    else:
        mois = [cle_du_numero(k) for k in range(1, ctx["n"] + 1)]
    serie = reclamations_par_type(ctx["avis"], mois)
    if serie.empty:
        st.success("Aucune réclamation sur la période 👍")
        return
    c1, c2 = st.columns([1.4, 1])
    with c1:
        ui.afficher_graphique(gr.graphique_reclamations(serie))
    with c2:
        total = int(serie.sum())
        principal = serie.index[0]
        ui.encadre("Lecture",
                   f"<p><b>{total}</b> problème(s) signalé(s) dans les avis Google Forms.</p>"
                   f"<p>Le type le plus fréquent est <b>« {principal} »</b> ({int(serie.iloc[0])} fois) : "
                   f"c'est la priorité à traiter avec la cuisine.</p>", icone="🔎")
