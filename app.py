import streamlit as st
import openai

# CONFIG - Use your API key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

st.set_page_config(page_title="Jeugdzorg AI Prioritizer", layout="centered")
st.title("🔍 Jeugdzorg AI - Intake Prioritizer (Demo)")
st.markdown("Demo that classifies fictional youth care cases into urgency levels using AI.")

# --- FORM INPUTS ---
with st.form("intake_form"):
    st.subheader("1. Case Information")

    st.markdown("💡 Choose a fictional case to autofill:")
    example = st.selectbox("Fictional Case", ["—", "Abuse case (Emma, 7)", "School dropout (Mike, 15)"])

    if example == "Abuse case (Emma, 7)":
        age = 7
        issue = "Abuse"
        family_support = "Low"
        risk_level = "High"
        extra_notes = "Child shows signs of trauma, referred by teacher."
    elif example == "School dropout (Mike, 15)":
        age = 15
        issue = "Truancy"
        family_support = "Medium"
        risk_level = "Medium"
        extra_notes = "Several missed school weeks, parents unresponsive."
    else:
        age = st.number_input("Age of the child", min_value=0, max_value=18, value=10)
        issue = st.selectbox("Primary issue", [
            "Neglect", "Abuse", "Violence in home", "Parental mental health", 
            "Truancy", "Drug use", "Runaway", "Undocumented", "Other"
        ])
        family_support = st.radio("Family support", ["High", "Medium", "Low"])
        risk_level = st.selectbox("Risk indicator", ["Low", "Moderate", "High"])
        extra_notes = st.text_area("Additional notes (optional)", "")

    submitted = st.form_submit_button("Classify Urgency")

# --- CLASSIFY VIA GPT ---
if submitted:
    case_description = f"""
    Age: {age}
    Issue: {issue}
    Family support: {family_support}
    Risk level: {risk_level}
    Notes: {extra_notes}
    """

    prompt = f"""
    You are a Jeugdzorg AI assistant. Based on the case below, return:

    - Urgency: High / Medium / Low  
    - Reason: 1-2 sentences why  
    - Recommended Action: Next step for care worker

    Case:
    {case_description}
    """

    with st.spinner("Classifying via AI..."):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You classify youth care intake cases by urgency."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200
            )
            output = response["choices"][0]["message"]["content"].strip()
            st.success("✅ Case classified:")
            st.text(output)

            st.download_button(
                label="📄 Download Result",
                data=output,
                file_name="urgency_classification.txt",
                mime="text/plain"
            )

        except Exception as e:
            st.error(f"Something went wrong: {e}")

# --- TRANSPARENCY SECTION ---
with st.expander("ℹ️ Classification Criteria (AI uses these hints)"):
    st.markdown("""
    - **Age < 12** = generally higher urgency  
    - **Issues like Abuse, Violence, Neglect** = high risk  
    - **Low family support** increases urgency  
    - **High risk level** = likely high urgency  
    - GPT combines these with case notes to reason output  
    """)

# --- FOOTER ---
st.markdown("---")
st.caption("🚨 This app is a prototype using fictional data and GPT-4. No real cases or sensitive information are processed.")
