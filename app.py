from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from src.ocr_engines import create_default_ocr_engine
from src.pipeline import run_pipeline
from src.rivalsmeta_browser import BrowserRivalsMetaClient


st.set_page_config(page_title="Marvel Rivals Ban Helper", layout="centered")

st.title("Marvel Rivals Ban Helper")
st.caption("Local personal MVP: upload one enemy-team screenshot and get two ban ideas.")

uploaded_file = st.file_uploader("Upload enemy-team screenshot", type=["jpg", "jpeg", "png", "webp"])

if uploaded_file is not None:
    st.image(uploaded_file, caption="Uploaded screenshot", use_container_width=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        image_path = Path(tmp.name)

    if st.button("Recommend bans", type="primary"):
        with st.spinner("Reading names and checking RivalsMeta..."):
            try:
                with BrowserRivalsMetaClient() as rivalsmeta_client:
                    result = run_pipeline(
                        image_path,
                        ocr_engine=create_default_ocr_engine(),
                        rivalsmeta_client=rivalsmeta_client,
                    )
            except RuntimeError as exc:
                st.error(str(exc))
                st.info(
                    "The app shell is ready, but the OCR adapter still needs to be configured. "
                    "The backend pipeline is covered by tests using mocked OCR."
                )
            else:
                st.subheader("Recommended bans")
                if result.recommendations:
                    for index, recommendation in enumerate(result.recommendations, start=1):
                        st.metric(
                            f"{index}. {recommendation.hero_name}",
                            f"{recommendation.total_games} ranked games",
                        )
                else:
                    st.warning("No confident ban recommendations could be made.")

                st.subheader("Run summary")
                st.write(f"Extracted names: {', '.join(result.extracted_names) or 'none'}")
                st.write(f"Matched players: {len(result.matched_profiles)}")
                st.write(f"Skipped names: {len(result.skipped_names)}")
