import streamlit as st


def inject_global_css():
    st.markdown(
        """
        <style>
            .stApp {
                background: #020617;
                color: #e2e8f0;
            }
            .app-hero {
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 60%, #334155 100%);
                border-radius: 18px;
                padding: 20px 24px;
                color: #f8fafc;
                border: 1px solid #334155;
                box-shadow: 0 10px 26px rgba(2, 6, 23, 0.45);
                margin-bottom: 10px;
            }
            .app-hero h1 {
                margin: 0;
                font-size: 30px;
                font-weight: 800;
                letter-spacing: .2px;
            }
            .soft-card {
                border: 1px solid #334155;
                border-radius: 10px;
                padding: 10px 12px;
                background: #111827;
                margin-bottom: 8px;
            }
            .metric-label {
                color: #93c5fd;
                font-size: 13px;
                margin-bottom: 2px;
            }
            .metric-value {
                color: #f8fafc;
                font-size: 22px;
                font-weight: 800;
                line-height: 1.1;
            }
            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, #0b1220 0%, #111827 100%);
                border-right: 1px solid #334155;
            }
            [data-testid="stSidebar"] .block-container {
                padding-top: 1.2rem;
            }
            .side-indicator {
                margin-top: 8px;
                margin-bottom: 12px;
                border: 1px solid #475569;
                background: #1e293b;
                color: #e2e8f0;
                border-radius: 10px;
                padding: 8px 10px;
                font-size: 13px;
            }
            div.stButton > button[kind="primary"] {
                background: #2563eb;
                color: #ffffff;
                border: 1px solid #1d4ed8;
            }
            div.stButton > button[kind="primary"]:hover {
                background: #1d4ed8;
                border-color: #1e40af;
                color: #ffffff;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
