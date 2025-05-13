import streamlit as st
import openai
import json
from datetime import date

# CONFIG - Use your API key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Complete list of regions (replace with real data when available)
REGIONS = {
    "Noord-Holland": 3,
    "Zuid-Holland": 1,
    "Utrecht": 0,
    "Gelderland": 2,
    "Friesland": 4,
    "Drenthe": 1,
    "Overijssel": 3,
    "Flevoland": 2,
    "Limburg": 3,
    "Zeeland": 1,
    "Noord-Brabant": 2,
    "Amsterdam": 5
}

st.set_page_config(page_title="Jeugdzorg AI Prioritizer", layout="centered")
st.title("🔍 Jeugdzorg AI - Intake Prioritizer (Demo)")
st.markdown("Dit prototype simuleert een AI-ondersteund intakeproces in de jeugdzorg.")

# --- FORM INPUTS ---
with st.form("intake_form"):
    st.subheader("📋 Intakeformulier")

    # Region & Availability (mocked for now)
    region = st.selectbox("Regio", list(REGIONS.keys()), index=-1)  # Start with an empty dropdown
    st.markdown(f"**Beschikbare plekken in {region if region else 'de geselecteerde regio'}**: {REGIONS.get(region, 0)}")

    # Core inputs
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Leeftijd van het kind", 0, 18, 10)
        submission_date = st.date_input("Datum van aanmelding", value=date.today())  # Date format adjustment
    with col2:
        main_issue = st.selectbox("Hoofdhulpvraag", [
            "Verwaarlozing", "Mishandeling", "Huiselijk geweld", "Psychische problemen ouder",
            "Schooluitval", "Verslavingsproblematiek", "Weggelopen kind", "Onbekend verblijf", "Anders"
        ], index=-1)  # Start with an empty dropdown
        
        # Show text box if "Anders" is selected
        if main_issue == "Anders":
            other_issue = st.text_input("Beschrijf de hulpvraag (optioneel)")

    # Family & risk factors
    col3, col4 = st.columns(2)
    with col3:
        family_support = st.radio("Mate van steun vanuit gezin", ["Hoog", "Gemiddeld", "Laag"])
        family_complexity = st.selectbox("Complexiteit gezinssituatie", ["Laag", "Gemiddeld", "Hoog"], index=-1)  # Start with an empty dropdown
    with col4:
        risk_level = st.selectbox("Risico-inschatting", ["Laag", "Matig", "Hoog"], index=-1)  # Start with an empty dropdown
        prior_interventions = st.radio("Eerdere hulpverlening gehad?", ["Ja", "Nee"])

    # Referral details
    col5, col6 = st.columns(2)
    with col5:
        referral_type = st.selectbox("Verwijzer", [
            "Huisarts", "Wijkteam", "Onderwijs", "Ziekenhuis", "Politie", "Zelfmelding", "Anders"
        ], index=-1)  # Start with an empty dropdown
        
        # Show text box if "Anders" is selected
        if referral_type == "Anders":
            other_referral = st.text_input("Beschrijf de verwijzer (optioneel)")
    with col6:
        referral_clarity = st.radio("Is de hulpvraag duidelijk?", ["Ja", "Nee"])

    extra_notes = st.text_area("Overige opmerkingen of signalen (optioneel)")

    # Simple data validation
    if not main_issue or not family_support or not risk_level:
        st.warning("Zorg ervoor dat alle verplichte velden ingevuld zijn.")
    
    submitted = st.form_submit_button("🔍 Classificeer urgentie")

# --- GPT-3.5 CLASSIFICATION ---
if submitted:
    # Build case description
    case = {
        "region": region,
        "age": age,
        "issue": main_issue if main_issue != "Anders" else other_issue,
        "submission_date": str(submission_date),  # Changed field name
        "family_support": family_support,
        "family_complexity": family_complexity,
        "risk_level": risk_level,
        "prior_interventions": prior_interventions,
        "referral_type": referral_type if referral_type != "Anders" else other_referral,
        "referral_clarity": referral_clarity,
        "extra_notes": extra_notes
    }
    case_description = "\n".join(f"{k}: {v}" for k, v in case.items())

    prompt = f"""
Je bent een AI-assistent gespecialiseerd in het beoordelen van urgentie bij intakegevallen binnen de jeugdzorg. Classificeer onderstaande casus nauwkeurig op basis van specifieke criteria:

Gebruik hierbij deze gedetailleerde richtlijnen:

1. Leeftijd:
   - Kind jonger dan 12 jaar verhoogt de urgentie.

2. Type hulpvraag:
   - Mishandeling, Verwaarlozing, Huiselijk geweld verhogen sterk de urgentie.
   - Psychische problemen ouder en Weggelopen kind verhogen de urgentie matig.

3. Mate van steun vanuit gezin:
   - Laag verhoogt sterk de urgentie.
   - Gemiddeld verhoogt matig.

4. Risico-inschatting:
   - Hoog verhoogt sterk de urgentie.
   - Matig verhoogt de urgentie enigszins.

5. Complexiteit gezinssituatie:
   - Hoge complexiteit verhoogt urgentie matig.

6. Historie:
   - Eerdere hulpverlening verhoogt de urgentie licht.

Bepaal vervolgens de totale urgentie:
- 3 of meer sterke factoren = Hoog
- 1-2 sterke factoren of meerdere matige factoren = Gemiddeld
- Geen sterke factoren en maximaal één matige factor = Laag

Antwoord verplicht in dit exacte format:

Urgentie: [Hoog / Gemiddeld / Laag]  
Reden: [Geef in 2-3 duidelijke zinnen uitleg op basis van de aanwezige factoren uit de intakegegevens.]  
Aanbevolen Actie: [Specifieke en korte aanbeveling voor vervolgstappen door hulpverlener, zoals onmiddellijke huisbezoek, spoedinterventie, aanvullende analyse of regulier vervolgtraject.]

Casusinformatie:
{case_description}
"""

    with st.spinner("AI-classificatie wordt uitgevoerd..."):
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Je bent een AI die intakecases in de jeugdzorg classificeert op urgentie."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300
            )
            output = response.choices[0].message.content.strip()
            
            # Confidence Level (optional)
            confidence = response.choices[0].finish_reason
            st.markdown(f"**AI Confidence Level**: {confidence}")

            # Extract urgency line
            urgency_line = output.split("\n")[0]
            urgency = urgency_line.split(":")[1].strip()

            # Visual urgency indicator
            urgency_color = {"Hoog": "🔴", "Gemiddeld": "🟠", "Laag": "🟢"}
            emoji = urgency_color.get(urgency, "⚪")
            st.markdown(f"### {emoji} Urgentie: **{urgency}**")

            st.success("✅ AI-classificatie afgerond:")
            st.text(output)

            # Download result as TXT
            st.download_button(
                label="📄 Download resultaat",
                data=output,
                file_name="ai_urgentieadvies.txt",
                mime="text/plain"
            )

            # Download result as JSON
            st.download_button(
                label="🗄️ Download intake (JSON)",
                data=json.dumps(case, ensure_ascii=False, indent=2),
                file_name="intake_case.json",
                mime="application/json"
            )

        except Exception as e:
            st.error(f"Er is iets misgegaan: {e}")

# --- EXPLANATION SECTION ---
with st.expander("ℹ️ Classificatieregels die de AI volgt"):
    st.markdown("""
- **Leeftijd < 12 jaar** = verhoogde urgentie  
- **Hulpvragen zoals mishandeling of verwaarlozing** = verhoogde urgentie  
- **Lage steun vanuit gezin** = verhoogde urgentie  
- **Risico-inschatting 'Hoog'** = verhoogt urgentie sterk  
- AI combineert deze signalen en onderbouwt de classificatie kort
    """)

# --- FOOTER ---
st.caption("🚨 Dit prototype gebruikt fictieve data en GPT-3.5. Geen echte persoonsgegevens worden verwerkt.")
