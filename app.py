import streamlit as st
import openai
import json
from datetime import date
from PyPDF2 import PdfReader
import io

st.set_page_config(page_title="Jeugdzorg AI Screening Tool", layout="centered")

# CONFIG
openai.api_key = st.secrets.get("OPENAI_API_KEY", "")
if not openai.api_key:
    st.warning("⚠️ OPENAI_API_KEY ontbreekt. Voeg deze toe via Streamlit Cloud → Secrets.")

st.title("📋 Jeugdzorg AI - Intake en Risicoscreening (Demo)")
st.markdown("Simulatie van een AI-ondersteund intakeproces in de jeugdzorg.")

# --- PDF Upload ---
with st.expander("📄 Upload aanvullende documentatie (optioneel)"):
    uploaded_pdf = st.file_uploader(
        "Upload een PDF-document met aanvullende informatie (zoals eerdere diagnoses, max. 10MB)", 
        type="pdf"
    )
    pdf_text = ""
    if uploaded_pdf is not None:
        if uploaded_pdf.size > 10 * 1024 * 1024:
            st.error("Bestand is te groot. Upload een PDF van maximaal 10MB.")
        else:
            reader = PdfReader(uploaded_pdf)
            for page in reader.pages:
                pdf_text += page.extract_text() or ""
            st.success("Document succesvol toegevoegd en gelezen.")
            
# --- INTAKEFORMULIER ---
with st.form(key="intake_form"):
    # 1. Kerngegevens kind en context
    st.subheader("1. Kerngegevens kind en context")
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Leeftijd kind (0-18)", min_value=0, max_value=18, format="%d")
        gender = st.selectbox("Geslacht", ["", "M", "V", "X"])
    with col2:
        region = st.selectbox(
            "Regio",
            ["", "Noord-Holland", "Zuid-Holland", "Utrecht", "Gelderland", "Friesland", "Drenthe", "Overijssel", "Flevoland", "Limburg", "Zeeland", "Noord-Brabant", "Amsterdam"]
        )
        languages = st.multiselect("Gesproken talen thuis", [
            "Nederlands", "Arabisch", "Pools", "Engels", "Turks", "Tigrinya", "Spaans", "Frans",
            "Koerdisch", "Amazigh", "Farsi", "Dari", "Pashto", "Somalisch", "Tamazight", "Armeens", "Anders"])
        other_language = ""
        if "Anders" in languages:
            other_language = st.text_input("Geef anders opgegeven taal/talen aan")
        interpreter_needed = st.radio("Is een tolk nodig?", ["Ja", "Nee"])
        submission_date = st.date_input("Datum van aanmelding", value=date.today(), format="DD/MM/YYYY")

    # 2. Aanmelding en hoofdproblematiek
    st.subheader("2. Aanmelding en hoofdproblematiek")
    col3, col4 = st.columns(2)
    with col3:
        referral_type = st.selectbox(
            "Wie verwijst?",
            ["", "Huisarts", "Wijkteam", "Onderwijs", "Ziekenhuis", "Politie", "Zelfmelding", "Anders"]
        )
        referral_clarity = st.radio("Is de hulpvraag duidelijk?", ["Ja", "Nee"])
    with col4:
        main_issue = st.selectbox(
            "Hoofdhulpvraag",
            ["", "Verwaarlozing", "Mishandeling", "Huiselijk geweld", "Psychische problemen ouder", "Schooluitval", "Verslavingsproblematiek", "Weggelopen kind", "Onbekend verblijf", "Anders"]
        )
        other_issue = st.text_input(
            "Indien anders, beschrijf de hulpvraag", disabled=(main_issue != "Anders")
        )
    goal_of_intervention = st.text_area("Wat is het doel van deze aanmelding?", height=80)
    immediate_risks = st.text_area("Directe zorgen of crisissituaties?", height=80)

    # 3. Gezondheid en ontwikkeling
    st.subheader("3. Gezondheid en ontwikkeling")
    dev_summary = st.text_area("Ontwikkeling (motorisch, sociaal, emotioneel, taal)", height=80)
    physical_health = st.text_area("Lichamelijke gezondheid / medicatie", height=68)
    mental_health = st.text_area("Psychische voorgeschiedenis (diagnoses/behandeling)", height=68)

    # 4. Ouders en opvoedomgeving
    st.subheader("4. Ouders en opvoedomgeving")
    parenting_skills = st.text_area("Opvoedvaardigheden (structuur, beschikbaarheid, voorbeeldgedrag)", height=80)
    parental_awareness = st.radio("Inzicht van ouders in eigen invloed op het kind?", ["Ja", "Nee", "Beperkt"])
    support_network = st.text_area("Netwerk en betrokken hulpverlening", height=68)

    # 5. Gedrag en functioneren kind
    st.subheader("5. Gedrag en functioneren kind")
    school_performance = st.text_area("Schoolprestaties en gedrag op school", height=68)
    behavioral_concerns = st.multiselect(
        "Gedragsproblemen waargenomen bij kind", 
        ["Agressie", "Terugtrekking", "Hyperactiviteit", "Emotionele instabiliteit", "Pesten of gepest worden", "Zelfbeschadiging"]
    )
    child_view = st.text_area("Hoe ervaart het kind zelf de situatie?", height=68)

    # 6. Risico- en beschermende factoren
    st.subheader("6. Risico- en beschermende factoren")
    risk_factors = st.multiselect("Aanwezige risicofactoren", ["Verwaarlozing", "Mishandeling", "Geweld in gezin", "Psychische problematiek ouder", "Verslaving ouder", "Crimineel gedrag", "Financiële problemen"])
    protective_factors = st.multiselect("Beschermende factoren", ["Positieve schoolervaring", "Stabiele verzorger", "Steunend netwerk", "Zelfvertrouwen kind", "Open communicatie", "Hulpbereidheid ouders"])
    extra_notes = st.text_area("Overige signalen of opmerkingen", height=68)

    # Submit-knop
    submitted = st.form_submit_button("🔍 Analyseer intake en genereer advies")

# --- AI-ANALYSE & ADVIES ---
if submitted:
    case = {
        "Leeftijd": age,
        "Geslacht": gender,
        "Regio": region,
        "Gesproken talen": languages + ([other_language] if other_language else []),
        "Tolk nodig": interpreter_needed,
        "Datum aanmelding": submission_date.strftime("%d-%m-%Y"),
        "Verwijzer": referral_type,
        "Hulpvraag duidelijk": referral_clarity,
        "Hoofdhulpvraag": other_issue if main_issue == "Anders" else main_issue,
        "Doel aanmelding": goal_of_intervention,
        "Directe zorgen": immediate_risks,
        "Ontwikkeling": dev_summary,
        "Lichamelijke gezondheid": physical_health,
        "Psychische gezondheid": mental_health,
        "Opvoedcapaciteiten": parenting_skills,
        "Inzicht ouders": parental_awareness,
        "Netwerk en betrokkenen": support_network,
        "School en gedrag": school_performance,
        "Gedragsproblemen": behavioral_concerns,
        "Kindvisie": child_view,
        "Risicofactoren": risk_factors,
        "Beschermende factoren": protective_factors,
        "Extra signalen": extra_notes,
        "Ingelezen PDF-context": pdf_text
    }

    prompt = f"""
Je bent een AI-assistent gespecialiseerd in jeugdzorg.
Gebruik de intakegegevens en eventueel meegeleverde PDF-context om een bruikbaar advies te genereren voor een hulpverlener.

Beantwoord in het volgende format:

Urgentie: [Hoog / Gemiddeld / Laag]
Samenvatting: [max. 5 zinnen waarin de context, zorgen en doelen helder zijn]
Rode vlaggen: [specifieke zorgen of signalen die direct aandacht vragen]
Advies:
- Aanbevolen type zorg of begeleiding
- Of er meer informatie nodig is (en van wie)
- Suggestie voor urgentievolgorde of tijdslijn (bv. binnen 48 uur vervolggesprek, doorverwijzing binnen 5 werkdagen)

Casusinformatie:
{json.dumps(case, ensure_ascii=False, indent=2)}
"""

    with st.spinner("AI analyseert intake…"):
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Je bent een AI-assistent die jeugdzorgintakes beoordeelt en adviezen formuleert."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.4
            )
            output = response.choices[0].message.content.strip()
            urgency = output.splitlines()[0].split(":")[1].strip()
            emoji = {"Hoog": "🔴", "Gemiddeld": "🟠", "Laag": "🟢"}.get(urgency, "⚪")
            st.markdown(f"### {emoji} Urgentie: **{urgency}**")
            st.text(output)
            st.download_button("📄 Download advies", output, "ai_intakeadvies.txt", "text/plain")
            st.download_button("🗄️ Download intake (JSON)", json.dumps(case, ensure_ascii=False, indent=2), "intake_case.json", "application/json")
        except Exception as e:
            st.error(f"Er ging iets mis: {e}")

st.caption("🧪 Prototype | Fictieve data | GPT-4o Mini | Alleen geautoriseerde toegang | Geen echte persoonsgegevens verwerkt.")
