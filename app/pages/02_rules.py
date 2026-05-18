# app/pages/02_rules.py
"""
Compliance Rules Editor — configure detection rules via UI.
Changes take effect on the next scan — no restart needed.
"""
import streamlit as st
from config.rules import load_rules, save_rules

st.set_page_config(page_title="Compliance Rules", page_icon="⚙️", layout="wide")

st.title("⚙️ Compliance Rules Configuration")
st.markdown("Customize what the scanner detects. Changes are saved instantly and apply to the next scan.")

rules = load_rules()

with st.form("compliance_rules_form"):
    st.subheader("🔴 PII Detection")
    col1, col2 = st.columns(2)
    with col1:
        pii_enabled = st.toggle("Enable PII Detection", value=rules["pii"]["enabled"])
        detect_email = st.checkbox("📧 Email Addresses", value=rules["pii"].get("detect_email", True))
        detect_phone = st.checkbox("📱 Phone Numbers", value=rules["pii"].get("detect_phone", True))
        detect_ssn = st.checkbox("🪪 SSN / Aadhaar / PAN", value=rules["pii"].get("detect_ssn_aadhaar", True))
    with col2:
        detect_credit_card = st.checkbox("💳 Credit/Debit Cards", value=rules["pii"].get("detect_credit_card", True))
        detect_address = st.checkbox("🏠 Physical Addresses", value=rules["pii"].get("detect_address", True))
        detect_dob = st.checkbox("🎂 Dates of Birth", value=rules["pii"].get("detect_dob", True))
        pii_confidence = st.slider(
            "Minimum PII Confidence Threshold",
            0.5, 1.0,
            value=rules["pii"].get("min_confidence", 0.75),
            step=0.05,
            help="Flags below this confidence level are ignored"
        )

    st.markdown("---")
    st.subheader("🔐 Confidentiality Detection")
    col3, col4 = st.columns(2)
    with col3:
        conf_enabled = st.toggle("Enable Confidentiality Detection", value=rules["confidentiality"]["enabled"])
        detect_api_keys = st.checkbox("🔑 API Keys & Tokens", value=rules["confidentiality"].get("detect_api_keys", True))
        detect_passwords = st.checkbox("🔒 Passwords & Secrets", value=rules["confidentiality"].get("detect_passwords", True))
        detect_trade_secrets = st.checkbox("💼 Trade Secrets", value=rules["confidentiality"].get("detect_trade_secrets", True))
    with col4:
        detect_financial = st.checkbox("💰 Financial Forecasts", value=rules["confidentiality"].get("detect_financial_data", True))
        detect_ma = st.checkbox("🤝 M&A Information", value=rules["confidentiality"].get("detect_merger_acquisition", True))
        conf_confidence = st.slider(
            "Minimum Confidentiality Threshold",
            0.5, 1.0,
            value=rules["confidentiality"].get("min_confidence", 0.70),
            step=0.05
        )

    st.markdown("#### Custom Keywords to Flag")
    current_keywords = "\n".join(rules.get("confidentiality", {}).get("custom_keywords", []))
    custom_keywords_text = st.text_area(
        "One keyword per line (case-insensitive)",
        value=current_keywords,
        height=100,
        help="These words will always be flagged as CUSTOM_KEYWORD in confidentiality checks"
    )

    st.markdown("---")
    st.subheader("🔤 Encoding & Language")
    col5, col6 = st.columns(2)
    with col5:
        enc_enabled = st.toggle("Enable Encoding Check", value=rules["encoding"]["enabled"])
        require_utf8 = st.checkbox("Require UTF-8 Encoding", value=rules["encoding"].get("require_utf8", True))
        flag_non_ascii = st.checkbox("Flag Non-ASCII Characters", value=rules["encoding"].get("flag_non_ascii", True))
    with col6:
        non_ascii_threshold = st.number_input(
            "Non-ASCII character threshold (flag if count exceeds)",
            min_value=1, max_value=100,
            value=rules["encoding"].get("non_ascii_threshold", 5)
        )
        enc_confidence = st.slider(
            "Min Encoding Detection Confidence",
            0.5, 1.0,
            value=rules["encoding"].get("min_encoding_confidence", 0.85),
            step=0.05
        )

    st.markdown("---")
    st.subheader("⚠️ Abuse & Unlawful Content")
    col7, col8 = st.columns(2)
    with col7:
        abuse_enabled = st.toggle("Enable Abuse Detection", value=rules["abuse"]["enabled"])
        detect_hate = st.checkbox("🏴 Hate Speech", value=rules["abuse"].get("detect_hate_speech", True))
        detect_sexual = st.checkbox("🔞 Sexual Content", value=rules["abuse"].get("detect_sexual_content", True))
        detect_violence = st.checkbox("⚡ Violence Incitement", value=rules["abuse"].get("detect_violence_incitement", True))
    with col8:
        detect_illegal = st.checkbox("⚖️ Illegal Content", value=rules["abuse"].get("detect_illegal_content", True))
        detect_harassment = st.checkbox("😡 Harassment", value=rules["abuse"].get("detect_harassment", True))
        sensitivity = st.select_slider(
            "AI Detection Sensitivity",
            options=["low", "medium", "high", "very_high"],
            value=rules.get("sensitivity", "high")
        )

    st.markdown("---")
    submitted = st.form_submit_button("💾 Save Rules", type="primary", use_container_width=True)

if submitted:
    custom_keywords_list = [
        kw.strip() for kw in custom_keywords_text.split("\n")
        if kw.strip()
    ]

    updated_rules = {
        **rules,
        "sensitivity": sensitivity,
        "pii": {
            "enabled": pii_enabled,
            "detect_email": detect_email,
            "detect_phone": detect_phone,
            "detect_ssn_aadhaar": detect_ssn,
            "detect_credit_card": detect_credit_card,
            "detect_address": detect_address,
            "detect_dob": detect_dob,
            "min_confidence": pii_confidence,
            "risk_threshold": "medium",
        },
        "confidentiality": {
            "enabled": conf_enabled,
            "detect_api_keys": detect_api_keys,
            "detect_passwords": detect_passwords,
            "detect_trade_secrets": detect_trade_secrets,
            "detect_financial_data": detect_financial,
            "detect_merger_acquisition": detect_ma,
            "custom_keywords": custom_keywords_list,
            "min_confidence": conf_confidence,
        },
        "encoding": {
            "enabled": enc_enabled,
            "require_utf8": require_utf8,
            "allowed_languages": ["en"],
            "min_encoding_confidence": enc_confidence,
            "flag_non_ascii": flag_non_ascii,
            "non_ascii_threshold": non_ascii_threshold,
        },
        "abuse": {
            "enabled": abuse_enabled,
            "detect_hate_speech": detect_hate,
            "detect_sexual_content": detect_sexual,
            "detect_violence_incitement": detect_violence,
            "detect_illegal_content": detect_illegal,
            "detect_harassment": detect_harassment,
            "sensitivity_level": sensitivity,
            "zero_tolerance_categories": ["child_safety", "terrorism"],
        },
    }

    save_rules(updated_rules)
    st.success("✅ Rules saved successfully! They will apply to the next scan.")
    st.balloons()
