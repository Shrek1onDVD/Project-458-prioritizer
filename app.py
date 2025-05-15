import streamlit as st
import openai
import json
from datetime import date

# CONFIG
openai.api_key = st.secrets["OPENAI_API_KEY"]

st.set_page_config(page_title="Jeugdzorg AI Screening Tool", layout="centered")
st.title("📋 Jeugdzorg AI - Intake en Risicoscreening (Demo)")
st.markdown("Simulatie van een AI-ondersteund intakeproces in de jeugdzorg.")

# --- FORM ---
with st.form("intake_form"):
    st.subheader("1. Persoons- en contextinformatie")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Naam van het kind")
        age = st.number_input("Leeftijd", min_value=0, max_value=18)
        gender = st.selectbox("Geslacht", ["", "M", "V", "X"])
        birth_date = st.date_input("Geboortedatum", format="DD/MM/YYYY")
    with col2:
        region = st.selectbox("Regio", ["", "Noord-Holland", "Zuid-Holland", "Utrecht", "Gelderland", "Friesland", "Drenthe", "Overijssel", "Flevoland", "Limburg", "Zeeland", "Noord-Brabant", "Amsterdam"])
        languages = st.text_input("Gesproken talen thuis")
        interpreter_needed = st.radio("Tolk nodig?", ["Ja", "Nee"])
        submission_date = st.date_input("Datum van aanmelding", value=date.today(), format="DD/MM/YYYY")

    st.subheader("2. Huidige situatie en verwijzing")
    col3, col4 = st.columns(2)
    with col3:
        referral_type = st.selectbox("Verwijzer", ["", "Huisarts", "Wijkteam", "Onderwijs", "Ziekenhuis", "Politie", "Zelfmelding", "Anders"])
        referral_clarity = st.radio("Is de hulpvraag duidelijk?", ["Ja", "Nee"])
    with col4:
        main_issue = st.selectbox("Hoofdhulpvraag", ["", "Verwaarlozing", "Mishandeling", "Huiselijk geweld", "Psychische problemen ouder", "Schooluitval", "Verslavingsproblematiek", "Weggelopen kind", "Onbekend verblijf", "Anders"])
        other_issue = ""
        if main_issue == "Anders":
            other_issue = st.text_input("Beschrijf de hulpvraag")
    goal_of_intervention = st.text_area("Wat is het doel van de aanmelding volgens verwijzer?", height=50)
    immediate_risks = st.text_area("Directe zorgen of crisissituaties", height=50)

    st.subheader("3. Ontwikkeling en gezondheid")
    dev_summary = st.text_area("Samenvatting van ontwikkeling (motorisch, sociaal, emotioneel, taal)", height=80)
    physical_health = st.text_area("Lichamelijke gezondheid en medicatie", height=50)
    mental_health = st.text_area("Psychische voorgeschiedenis (diagnoses/behandeling)", height=50)

    st.subheader("4. Gezinssituatie en opvoedcapaciteiten")
    parenting_skills = st.text_area("Inschatting opvoedcapaciteiten (structuur, beschikbaarheid, voorbeeldgedrag)", height=80)
    parental_awareness = st.radio("Is er inzicht bij ouders in hun eigen gedrag en impact op kind?", ["Ja", "Nee", "Beperkt"])
    support_network = st.text_input("Beschikbare steun (familie, netwerk, professionals)")

    st.subheader("5. Gedrag, school en functioneren kind")
    school_performance = st.text_area("Schoolprestaties en gedrag op school", height=50)
    behavioral_concerns = st.multiselect("Gedragsproblemen", ["Agressie", "Terugtrekking", "Hyperactiviteit", "Emotionele instabiliteit", "Pesten of gepest worden", "Zelfbeschadiging"])
    child_view = st.text_area("Hoe ervaart het kind zelf de situatie?", height=50)

    st.subheader("6. Risico- en beschermende factoren")
    risk_factors = st.multiselect("Risicofactoren aanwezig", ["Verwaarlozing", "Mishandeling", "Geweld in gezin", "Psychische problematiek ouder", "Verslaving ouder", "Crimineel gedrag", "Financiële problemen"])
    protective_factors = st.multiselect("Beschermende factoren", ["Positieve schoolervaring", "Stabiele verzorger", "Steunend netwerk", "Zelfvertrouwen kind", "Open communicatie", "Hulpbereidheid ouders"])
    extra_notes = st.text_area("Overige opmerkingen of signalen", height=50)

    submitted = st.form_submit_button("🔍 Analyseer intake en genereer advies")

# --- AI PROMPT ---
if submitted:
    case = {
        "Naam": name, "Leeftijd": age, "Geslacht": gender,
        "Regio": region, "Talen": languages, "Tolk": interpreter_needed,
        "Datum aanmelding": submission_date.strftime("%d-%m-%Y"),
        "Verwijzer": referral_type, "Hulpvraag duidelijk": referral_clarity,
        "Hoofdhulpvraag": other_issue if main_issue == "Anders" else main_issue,
        "Doel interventie": goal_of_intervention, "Directe zorgen": immediate_risks,
        "Ontwikkeling": dev_summary, "Lichamelijke gezondheid": physical_health, "Psychische gezondheid": mental_health,
        "Opvoedcapaciteiten": parenting_skills, "Inzicht ouders": parental_awareness, "Steunnetwerk": support_network,
        "School": school_performance, "Gedragsproblemen": behavioral_concerns,
        "Kind visie": child_view, "Risicofactoren": risk_factors,
        "Beschermende factoren": protective_factors, "Overige": extra_notes
    }
    prompt = f"""
Je bent een AI-assistent die een intake in de jeugdzorg analyseert.
Geef een korte samenvatting, markeer rode vlaggen of ontbrekende informatie, en suggereer mogelijke vervolgstappen of verwijzingen.
Gebruik dit format:

Urgentie: [Hoog / Gemiddeld / Laag]
Samenvatting: [max. 5 zinnen]
Rode vlaggen: [kort opsommen van zorgen of hiaten]
Vervolgstappen: [concrete suggesties voor vervolg, hulp of doorverwijzing]

Casusinformatie:
{json.dumps(case, ensure_ascii=False, indent=2)}
"""

    with st.spinner("AI analyseert intake..."):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o Mini",
                messages=[
                    {"role": "system", "content": "Je bent een AI-assistent die jeugdzorgintakes beoordeelt en adviezen formuleert."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=600,
                temperature=0.4
            )
            output = response.choices[0].message.content.strip()
            urgency_line = output.split("\n")[0]
            urgency = urgency_line.split(":")[1].strip()
            emoji = {"Hoog": "🔴", "Gemiddeld": "🟠", "Laag": "🟢"}.get(urgency, "⚪")
            st.markdown(f"### {emoji} Urgentie: **{urgency}**")
            st.text(output)
            st.download_button("📄 Download advies", output, "ai_intakeadvies.txt", "text/plain")
            st.download_button("🗄️ Download intake (JSON)", json.dumps(case, ensure_ascii=False, indent=2), "intake_case.json", "application/json")
        except Exception as e:
            st.error(f"Er ging iets mis: {e}")

st.caption("🧪 Prototype | Fictieve data | GPT-4o Mini | Geen echte persoonsgegevens verwerkt.")
