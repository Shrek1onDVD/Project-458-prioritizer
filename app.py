import streamlit as st
import openai
import json
from datetime import date
from PyPDF2 import PdfReader
import io
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode

# Configure page
st.set_page_config(page_title="Jeugdzorg AI Screening Tool", layout="wide")

# API-key
openai.api_key = st.secrets.get("OPENAI_API_KEY", "")
if not openai.api_key:
    st.warning("⚠️ OPENAI_API_KEY ontbreekt. Voeg deze toe via Streamlit Cloud → Secrets.")

st.title("📋 Jeugdzorg AI - Intake en Risicoscreening (Demo)")
st.markdown("Simulatie van een AI-ondersteund intakeproces in de jeugdzorg.")

# Helper: audio-transcriptie via OpenAI Whisper
@st.cache_data(show_spinner=False)
def transcribe_audio(audio_file):
    try:
        audio_file.seek(0)
        transcript = openai.Audio.transcribe(
            model="whisper-1",
            file=audio_file
        )
        return transcript.text
    except Exception as e:
        return f"Fout bij transcriptie: {e}"

# PDF Upload
with st.expander("📄 Upload aanvullende documentatie (optioneel)"):
    uploaded_pdf = st.file_uploader(
        "Upload een PDF-document met aanvullende informatie (max. 10MB)",
        type="pdf"
    )
    pdf_text = ""
    if uploaded_pdf:
        if uploaded_pdf.size > 10 * 1024 * 1024:
            st.error("Bestand is te groot. Upload een PDF van maximaal 10MB.")
        else:
            reader = PdfReader(uploaded_pdf)
            for page in reader.pages:
                pdf_text += page.extract_text() or ""
            st.success("Document succesvol toegevoegd en gelezen.")

# Tabs: intake form and speech-to-text
tab1, tab2 = st.tabs(["Formulier & Analyse", "Spraak naar tekst"])

# Speech-to-text tab
with tab2:
    st.subheader("🎤 Live microfoonopname (Demo)")
    st.info("Voeg 'streamlit-webrtc' toe aan requirements.txt om live audio te ondersteunen.")

    class Recorder(AudioProcessorBase):
        def __init__(self):
            self.frames = []
        def recv(self, frame):
            self.frames.append(frame.to_ndarray().tobytes())
            return frame

    ctx = webrtc_streamer(
        key="audio-record",
        mode=WebRtcMode.SENDONLY,
        audio_processor_factory=Recorder,
        media_stream_constraints={"audio": True, "video": False},
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
    )

    audio_file = None
    if ctx and ctx.audio_processor and hasattr(ctx.audio_processor, 'frames'):
        recorder = ctx.audio_processor
        if recorder.frames:
            wav_bytes = b"".join(recorder.frames)
            audio_file = io.BytesIO(wav_bytes)
            audio_file.name = "mic_recording.wav"
            st.audio(wav_bytes, format="audio/wav")

    if not audio_file:
        uploaded_audio = st.file_uploader(
            "Of upload WAV/MP3/FLAC voor transcriptie", type=["wav", "mp3", "flac"]
        )
        if uploaded_audio:
            audio_file = uploaded_audio

    if audio_file:
        transcript = transcribe_audio(audio_file)
        session_transcript = st.text_area(
            "Transcript (controleer en corrigeer)", transcript, height=200, key="_stt_review"
        )
        st.session_state["transcript"] = session_transcript
    else:
        st.info("Gebruik de microfoon of upload een audio-bestand om te transcriberen.")

# Intake form & analysis tab
with tab1:
    with st.form(key="intake_form"):
        st.subheader("1. Kerngegevens kind en context")
        col1, col2 = st.columns(2)
        with col1:
            age = st.number_input("Leeftijd kind (0-18)", min_value=0, max_value=18)
            gender = st.selectbox("Geslacht", ["", "M", "V", "X"])
        with col2:
            region = st.selectbox(
                "Regio", ["", "Drenthe", "Flevoland", "Friesland", "Gelderland",
              "Groningen", "Limburg", "Noord-Brabant", "Noord-Holland",
              "Overijssel", "Utrecht", "Zeeland", "Zuid-Holland"]
            )
            languages = st.multiselect(
             "Gesproken talen thuis", [
                "Amazigh", "Arabisch", "Armeens", "Dari", "Engels", "Farsi", "Frans",
                "Koerdisch", "Nederlands", "Pashto", "Pools", "Somalisch",
                "Spaans", "Tamazight", "Tigrinya", "Turks", "Anders"
            ]
            )
            other_language = st.text_input("Anders, namelijk") if "Anders" in languages else ""
            interpreter_needed = st.radio("Is een tolk nodig?", ["Ja", "Nee"])
            submission_date = st.date_input("Datum van aanmelding", value=date.today(), format="DD/MM/YYYY")

        st.subheader("2. Aanmelding en hoofdproblematiek")
        col3, col4 = st.columns(2)
        with col3:
            referral_type = st.selectbox("Wie verwijst?", [
                "", "Huisarts", "Wijkteam", "Onderwijs", "Ziekenhuis", "Politie", "Zelfmelding", "Anders"
            ])
            referral_clarity = st.radio("Is de hulpvraag duidelijk?", ["Ja", "Nee"])
        with col4:
            main_issue = st.selectbox("Hoofdhulpvraag", [
                "", "Verwaarlozing", "Mishandeling", "Huiselijk geweld",
                "Psychische problemen ouder", "Schooluitval", "Verslavingsproblematiek",
                "Weggelopen kind", "Onbekend verblijf", "Anders"
            ])
            other_issue = st.text_input("Indien anders, beschrijf", disabled=(main_issue != "Anders"))

        st.subheader("🔊 Transcript spraakinvoer")
        st.text_area(
            "Transcript uit audio-tab", st.session_state.get("transcript", ""),
            height=120, key="transcript", disabled=True
        )

        # Remaining fields…
        goal_of_intervention = st.text_area("Doel van deze aanmelding?", height=80)
        immediate_risks = st.text_area("Directe zorgen of crisissituaties?", height=80)
        dev_summary = st.text_area("Ontwikkeling (motorisch, sociaal, emotioneel, taal)", height=80)
        physical_health = st.text_area("Lichamelijke gezondheid / medicatie", height=68)
        mental_health = st.text_area("Psychische voorgeschiedenis (diagnoses/behandeling)", height=68)
        parenting_skills = st.text_area("Opvoedvaardigheden (structuur, beschikbaarheid, voorbeeldgedrag)", height=80)
        parental_awareness = st.radio("Inzicht van ouders in eigen invloed?", ["Ja", "Nee", "Beperkt"])
        support_network = st.text_area("Netwerk en betrokken hulpverlening", height=68)
        school_performance = st.text_area("Schoolprestaties en gedrag op school", height=68)
        behavioral_concerns = st.multiselect("Gedragsproblemen opgemerkt bij kind", [
            "Agressie", "Terugtrekking", "Hyperactiviteit", "Emotionele instabiliteit",
            "Pesten of gepest worden", "Zelfbeschadiging"
        ])
        child_view = st.text_area("Hoe ervaart het kind zelf de situatie?", height=68)
        risk_factors = st.multiselect("Aanwezige risicofactoren", [
            "Verwaarlozing", "Mishandeling", "Geweld in gezin",
            "Psychische problematiek ouder", "Verslaving ouder", "Crimineel gedrag", "Financiële problemen"
        ])
        protective_factors = st.multiselect("Beschermende factoren", [
            "Positieve schoolervaring", "Stabiele verzorger", "Steunend netwerk",
            "Zelfvertrouwen kind", "Open communicatie", "Hulpbereidheid ouders"
        ])
        extra_notes = st.text_area("Overige signalen of opmerkingen", height=68)
        user_informed = st.checkbox("Gebruiker geïnformeerd over AI?", value=False)
        deviation_reason = st.text_area("Toelichting bij afwijking AI-advies", height=68)

        submitted = st.form_submit_button("🔍 Analyseer intake en genereer advies")

# AI-Analyse (ongewijzigd)
if submitted:
    case = {
        "Leeftijd": age, "Geslacht": gender, "Regio": region,
        "Gesproken talen": languages + ([other_language] if other_language else []),
        "Tolk nodig": interpreter_needed,
        "Datum aanmelding": submission_date.strftime("%d-%m-%Y"),
        "Verwijzer": referral_type,
        "Hulpvraag duidelijk": referral_clarity,
        "Hoofdhulpvraag": other_issue if main_issue == "Anders" else main_issue,
        "Transcript": st.session_state.get("transcript", ""),
        "Doel aanmelding": goal_of_intervention,
        "Directe zorgen": immediate_risks,
        "Ontwikkeling": dev_summary,
        "Lichamelijke gezondheid": physical_health,
        "Psychische gezondheid": mental_health,
        "Opvoedvaardigheden": parenting_skills,
        "Inzicht ouders": parental_awareness,
        "Netwerk": support_network,
        "School en gedrag": school_performance,
        "Gedragsproblemen": behavioral_concerns,
        "Kindvisie": child_view,
        "Risicofactoren": risk_factors,
        "Beschermende factoren": protective_factors,
        "Extra signalen": extra_notes,
        "PDF-context": pdf_text,
        "Gebruiker geïnformeerd over AI": user_informed,
        "Toelichting afwijking": deviation_reason
    }

    prompt = f"""
Je bent een AI-assistent gespecialiseerd in jeugdzorg. Je dient uitsluitend als ondersteuning, niet als beslisser. Je advies moet begrijpelijk, uitlegbaar en voorzichtig geformuleerd zijn.

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
            st.warning("⚠️ Dit advies is gegenereerd door AI en bedoeld als ondersteuning. Je blijft zelf verantwoordelijk.")
            st.markdown(f"### {emoji} Urgentie: **{urgency}**")
            st.text(output)
            st.download_button("📄 Download advies", output, "ai_intakeadvies.txt", "text/plain")
            st.download_button("🗄️ Download intake (JSON)", json.dumps(case, ensure_ascii=False, indent=2), "intake_case.json", "application/json")
        except Exception as e:
            st.error(f"Er ging iets mis: {e}")

st.caption("🧪 Prototype | Fictieve data | GPT-4o Mini | Geen echte persoonsgegevens verwerkt.")
