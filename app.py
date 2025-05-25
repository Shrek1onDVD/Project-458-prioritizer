import streamlit as st
import openai
import json
from datetime import datetime
from PyPDF2 import PdfReader
from lxml import etree

# === Configuratie ===
st.set_page_config(page_title="Valuation Review Tool", layout="wide")
st.title("🏢 Vastgoedtaxatie Review Tool")

openai.api_key = st.secrets.get("OPENAI_API_KEY", "")
if not openai.api_key:
    st.warning("⚠️ OPENAI_API_KEY ontbreekt. Voeg deze toe via Streamlit Cloud → Secrets.")

# === PDF Upload ===
uploaded_pdf = st.sidebar.file_uploader("Upload taxatierapport (PDF)", type=["pdf"])
pdf_text = ""
if uploaded_pdf:
    reader = PdfReader(uploaded_pdf)
    for page in reader.pages:
        pdf_text += page.extract_text() or ""

# === Extractie via GPT ===
def extract_fields_from_pdf(text):
    prompt = (
        "Je bent een AI die Nederlandse vastgoedtaxatierapporten analyseert.\n"
        "Geef alleen geldige JSON terug, zonder uitleg of opmaak.\n"
        "Velden:\n"
        "- object_type, address, city, country, ownership_type\n"
        "- lettable_floor_area, construction_year, energy_label\n"
        "- appraiser, valuation_approach, valuation_definition, valuation_date\n"
        "- lfa_vvo, bfa_vvo\n"
        "- rental_information: lijst van huurders met\n"
        "  tenant, total_lfa_sqm, kantoor_m2_vvo, opslag_m2_vvo, mezzanine_m2_vvo,\n"
        "  parkeren_stuks, expiration_date, walt, gross_contract_rent, gross_market_rent\n"
        f"PDF tekst:\n{text[:8000]}"
    )

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Je retourneert alleen JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        raw = response.choices[0].message.content
        json_block = re.search(r"\{(?:.|\n)*\}", raw)
        if not json_block:
            return {}
        return json.loads(json_block.group())
    except Exception:
        return {}

# === XBRL Export functie ===
def generate_xbrl(data):
    root = etree.Element("ValuationReport")

    for key, value in data.items():
        if isinstance(value, list) and key == "rental_information":
            section = etree.SubElement(root, key)
            for item in value:
                entry = etree.SubElement(section, "Tenant")
                for subkey, subval in item.items():
                    etree.SubElement(entry, subkey).text = str(subval) if subval else ""
        elif key == "valuation_date" and isinstance(value, str):
            try:
                parsed_date = datetime.strptime(value, "%Y-%m-%d")
                etree.SubElement(root, key).text = parsed_date.strftime("%d-%m-%Y")
            except Exception:
                etree.SubElement(root, key).text = value
        elif key == "appraiser":
            etree.SubElement(root, key).text = value if value else ""
        else:
            etree.SubElement(root, key).text = str(value)

    return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8")

# === Analyse & Resultaat ===
data = extract_fields_from_pdf(pdf_text) if uploaded_pdf else {}

if data:
    st.subheader("📋 Samenvatting Extractie")
    st.json(data)
    st.download_button("📤 Download XBRL", generate_xbrl(data), "valuation.xbrl", "application/xml")
else:
    st.info("Upload een PDF om te starten.")
