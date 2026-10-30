# =====================================================================
#  HELLO PIZZA - RAPPORT PDF ET ENVOI PAR E-MAIL
# =====================================================================
import re
import smtplib
from datetime import datetime
from email.message import EmailMessage

from fpdf import FPDF

import config
from indicateurs import LIBELLES_FEU, fmt, fmt_ecart, libelle_mois

COULEURS_RVB = {"vert": (22, 163, 74), "orange": (245, 158, 11), "rouge": (220, 38, 38), "gris": (148, 163, 184)}


def _latin(texte):
    """Les polices de base du PDF n'acceptent que les caractères latins simples."""
    t = re.sub(r"<[^>]+>", "", str(texte))
    for a, b in {"−": "-", "→": "->", "≥": ">=", "≤": "<=", "×": "x", "÷": "/", "’": "'", "…": "...",
                 " ": " ", " ": " ", "Σ": "Somme", "ƒ": "f", "œ": "oe", "Œ": "OE"}.items():
        t = t.replace(a, b)
    return t.encode("latin-1", "ignore").decode("latin-1").strip()


def creer_pdf(titre, res, codes, phrases, score=None, source=""):
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    cle = res[codes[0]]["cle"]

    # Bandeau
    pdf.set_fill_color(234, 88, 12)
    pdf.rect(0, 0, 297, 26, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_xy(10, 6)
    pdf.cell(0, 8, _latin(f"Hello Pizza - {titre}"))
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(10, 15)
    pdf.cell(0, 6, _latin(f"Mois analysé : {libelle_mois(cle)} (M{res[codes[0]]['n']})   ·   "
                          f"édité le {datetime.now():%d/%m/%Y %H:%M}   ·   source : {source}"))
    pdf.set_text_color(28, 25, 23)
    pdf.set_xy(10, 32)
    if score is not None:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 7, _latin(f"Score : {score} / 100  (mois où la cible est atteinte ÷ 12 × 100)"))
        pdf.ln(9)

    # Tableau des indicateurs
    entetes = ["Indicateur", "Réalisé", "Cible du mois", "Écart", "Feu", "Cumul", "Cumul cible", "Mois réussis"]
    largeurs = [78, 28, 30, 30, 26, 32, 32, 21]
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(245, 240, 235)
    for e, w in zip(entetes, largeurs):
        pdf.cell(w, 8, _latin(e), border=1, align="C", fill=True)
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    for code in codes:
        r = res[code]
        u = r["unite"]
        valeurs = [r["nom"], fmt(r["realise"], u), fmt(r["cible"], u), fmt_ecart(r["ecart"], u),
                   LIBELLES_FEU[r["feu"]], fmt(r["cumul"], u), fmt(r["cumul_cible"], u), f"{r['reussis']} / 12"]
        for i, (v, w) in enumerate(zip(valeurs, largeurs)):
            if i == 4:
                pdf.set_text_color(*COULEURS_RVB[r["feu"]])
                pdf.set_font("Helvetica", "B", 9)
            pdf.cell(w, 7, _latin(v), border=1, align="L" if i == 0 else "C")
            pdf.set_text_color(28, 25, 23)
            pdf.set_font("Helvetica", "", 9)
        pdf.ln()

    # Diagnostic
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(194, 65, 12)
    pdf.cell(0, 7, "Diagnostic automatique du mois")
    pdf.ln(8)
    pdf.set_text_color(28, 25, 23)
    pdf.set_font("Helvetica", "", 9.5)
    for p in phrases:
        pdf.multi_cell(0, 5.5, _latin("- " + p), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    # Formules
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Formules de calcul")
    pdf.ln(7)
    pdf.set_font("Helvetica", "", 8.5)
    for code in codes:
        r = res[code]
        pdf.multi_cell(0, 4.6, _latin(f"{r['nom']} : {r['formule']}  |  Cumul : {r['formule_cumul']}"),
                       new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())


def envoyer_email(sujet, texte, pdf_octets, nom_fichier):
    if not (config.EMAIL_EXPEDITEUR and config.EMAIL_MOT_DE_PASSE_APP and config.EMAIL_DESTINATAIRE):
        raise RuntimeError("l'envoi par e-mail n'est pas configuré (voir la partie 5 de config.py)")
    msg = EmailMessage()
    msg["From"] = f"Hello Pizza <{config.EMAIL_EXPEDITEUR}>"
    msg["To"] = config.EMAIL_DESTINATAIRE
    msg["Subject"] = sujet
    msg.set_content(texte)
    msg.add_attachment(pdf_octets, maintype="application", subtype="pdf", filename=nom_fichier)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as s:
        s.login(config.EMAIL_EXPEDITEUR, config.EMAIL_MOT_DE_PASSE_APP)
        s.send_message(msg)
