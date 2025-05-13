import streamlit as st
import openai

# CONFIG - Use your API key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

st.set_page_config(page_title="Jeugdzorg AI Prioritizer", layout="centered")
st.title("🔍 Jeugdzorg AI - Intake Prioritizer (Demo)")
st.markdown("Dit prototype simuleert een AI-ondersteund intakeproces in de jeugdzorg.")

# --- FORM INPUTS ---
with st.form("intake_form"):
    st.subheader("📋 Intakeformulier")

    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Leeftijd van het kind", min_value=0, max_value=18, value=10)
    with col2:
        main_issue = st.selectbox("Hoofdhulpvraag", [
            "Verwaarlozing", "Mishandeling", "Huiselijk geweld", "Psychische problemen ouder",
            "Schooluitval", "Verslavingsproblematiek", "Weggelopen kind", "Onbekend verblijf", "Anders"
        ])

    col3, col4 = st.columns(2)
    with col3:
        family_support = st.radio("Mate van steun vanuit gezin", ["Hoog", "Gemiddeld", "Laag"])
    with col4:
        risk_level = st.selectbox("Risico-inschatting", ["Laag", "Matig", "Hoog"])

    col5, col6 = st.columns(2)
    with col5:
        referral_type = st.selectbox("Verwijzer", [
            "Huisarts", "Wijkteam", "Onderwijs", "Ziekenhuis", "Politie", "Zelfmelding", "Anders"
        ])
    with col6:
        referral_clarity = st.radio("Is de hulpvraag duidelijk?", ["Ja", "Nee"])

    family_complexity = st.selectbox("Complexiteit gezinssituatie", ["Laag", "Gemiddeld", "Hoog"])
    prior_interventions = st.radio("Eerdere hulpverlening gehad?", ["Ja", "Nee"])
    explanatory_analysis = st.text_area("Verklarende analyse vanuit verwijzer (optioneel)")
    extra_notes = st.text_area("Overige opmerkingen of signalen")

    submitted = st.form_submit_button("🔍 Classificeer urgentie")

# --- GPT-3.5 CLASSIFICATION ---
if submitted:
    case_description = f"""
Jeugdzorg intake:
Leeftijd: {age}
Hoofdhulpvraag: {main_issue}
Steun vanuit gezin: {family_support}
Risico-inschatting: {risk_level}
Verwijzer: {referral_type}
Hulpvraag duidelijk?: {referral_clarity}
Complexiteit gezin: {family_complexity}
Eerdere hulpverlening: {prior_interventions}
Verklarende analyse: {explanatory_analysis}
Extra notities: {extra_notes}
"""

    prompt = f"""
Je bent een AI-assistent in de jeugdzorg. Geef een inschatting van urgentie op basis van onderstaande intakegegevens.

Gebruik deze regels:
- Leeftijd < 12 = verhoogt urgentie
- Hoofdhulpvraag = 'Mishandeling', 'Verwaarlozing', 'Huiselijk geweld' = verhoogt urgentie
- Lage steun vanuit gezin = verhoogt urgentie
- Risico = Hoog = verhoogt urgentie sterk
- Meerdere van bovenstaande factoren = Hoge urgentie
- Eén = Gemiddelde urgentie
- Geen = Lage urgentie

Beantwoord in dit vaste format:

Urgentie: [Hoog / Gemiddeld / Laag]  
Reden: [1-2 zinnen met uitleg o.b.v. intakefactoren]  
Aanbevolen Actie: [Korte suggestie voor vervolg door hulpverlener]

Input:
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

            # Extract urgency line
            urgency_line = output.split("\n")[0]
            urgency = urgency_line.split(":")[1].strip()

            # Visual urgency indicator
            urgency_color = {"Hoog": "🔴", "Gemiddeld": "🟠", "Laag": "🟢"}
            emoji = urgency_color.get(urgency, "⚪")
            st.markdown(f"### {emoji} Urgentie: **{urgency}**")

            st.success("✅ AI-classificatie afgerond:")
            st.text(output)

            st.download_button(
                label="📄 Download resultaat",
                data=output,
                file_name="ai_urgentieadvies.txt",
                mime="text/plain"
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
