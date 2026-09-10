from __future__ import annotations

import html
import os
from typing import Any

import httpx
import plotly.graph_objects as graph_objects
import streamlit as st

from app.config import PROJECT_ROOT
from app.services.languages import get_language, language_catalog
from app.ui.styles import APP_CSS
from app.ui.three_d import render_word_world


del PROJECT_ROOT  # Importing configuration loads values from the project .env file.
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
VOICE_OPTIONS = {
    "Default voice": "us",
    "English (US)": "us",
    "English (UK)": "uk",
    "English (Australia)": "australia",
}
LANGUAGE_PROFILES = language_catalog()
LANGUAGE_LABELS = [f"{profile.name} · {profile.native_name}" for profile in LANGUAGE_PROFILES]
LEARNER_AVATAR = ":material/person:"
COACH_AVATAR = ":material/record_voice_over:"


st.set_page_config(
    page_title="Lingo Play | English for little learners",
    page_icon="🌈",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(f"<style>{APP_CSS}</style>", unsafe_allow_html=True)


def api_request(method: str, path: str, **kwargs: Any) -> httpx.Response:
    try:
        response = httpx.request(method, f"{API_BASE_URL}{path}", timeout=30, **kwargs)
        response.raise_for_status()
        return response
    except httpx.HTTPStatusError as error:
        try:
            detail = error.response.json().get("detail", "The service could not complete that request.")
        except ValueError:
            detail = "The service could not complete that request."
        raise RuntimeError(detail) from error
    except httpx.HTTPError as error:
        raise RuntimeError("The learning service is unavailable. Start the FastAPI backend and try again.") from error


def get_json(path: str) -> Any:
    return api_request("GET", path).json()


def initialize_session() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hi, friend! Let’s play. Can you say hello and wave?",
                "vocabulary": [],
            }
        ]
    st.session_state.setdefault("audio_by_message", {})
    st.session_state.setdefault("voice_ready", False)
    st.session_state.setdefault("language", "en")


def correction_markup(correction: dict[str, str]) -> str:
    return (
        '<div class="correction-note" role="note">'
        '<div class="correction-title">Try it this way</div>'
        f'<p><span class="correction-before">{html.escape(correction["original"])}</span>'
        f'<span class="correction-arrow">→</span><strong>{html.escape(correction["corrected"])}</strong></p>'
        f'<p>{html.escape(correction["reason"])}</p></div>'
    )


def request_audio(text: str) -> bytes | None:
    try:
        response = api_request(
            "POST",
            "/api/speech/synthesize",
            params={
                "text": text,
                "language": st.session_state.language,
                "voice": VOICE_OPTIONS[st.session_state.voice],
                "speed": st.session_state.speed,
            },
        )
        return response.content
    except RuntimeError as error:
        st.info(f"I can still talk with you, but my voice is taking a rest: {error}")
        return None


def render_assistant_message(message: dict[str, Any], index: int) -> None:
    st.markdown(message["content"])
    correction = message.get("correction")
    if correction:
        st.markdown(correction_markup(correction), unsafe_allow_html=True)
    elif message.get("correction_text"):
        st.markdown(
            f'<div class="correction-note"><div class="correction-title">Try it this way</div>'
            f'<p>{html.escape(message["correction_text"])}</p></div>',
            unsafe_allow_html=True,
        )
    vocabulary = message.get("vocabulary", [])
    if vocabulary:
        chips = "".join(
            f'<span class="vocab-chip">{html.escape(word["word"])}</span>' for word in vocabulary
        )
        st.markdown(chips, unsafe_allow_html=True)
    if st.button("🔊 Hear it", key=f"listen-{index}", use_container_width=False):
        with st.spinner("Preparing audio..."):
            if audio_content := request_audio(message["content"]):
                st.session_state.audio_by_message[index] = audio_content
    if audio_content := st.session_state.audio_by_message.get(index):
        st.audio(audio_content, format="audio/mpeg")


def process_message(user_message: str) -> None:
    st.session_state.messages.append({"role": "user", "content": user_message})
    with st.chat_message("user", avatar=LEARNER_AVATAR):
        st.markdown(user_message)
    with st.chat_message("assistant", avatar=COACH_AVATAR):
        with st.spinner("Thinking..."):
            try:
                response = api_request(
                    "POST",
                    "/api/chat",
                    json={"message": user_message, "language": st.session_state.language},
                ).json()
            except RuntimeError as error:
                st.error(str(error))
                return
        st.markdown(response["reply"])
        if correction := response.get("correction"):
            st.markdown(correction_markup(correction), unsafe_allow_html=True)
        if vocabulary := response.get("vocabulary", []):
            chips = "".join(f'<span class="vocab-chip">{html.escape(word["word"])}</span>' for word in vocabulary)
            st.markdown(chips, unsafe_allow_html=True)
        assistant_index = len(st.session_state.messages)
        audio_content = request_audio(response["reply"])
        if audio_content:
            st.session_state.audio_by_message[assistant_index] = audio_content
            st.audio(audio_content, format="audio/mpeg", autoplay=True)
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": response["reply"],
                "correction": response.get("correction"),
                "vocabulary": response.get("vocabulary", []),
            }
        )


def render_voice_input() -> None:
    if not hasattr(st, "audio_input"):
        return
    st.markdown(
        '<div class="voice-stage"><div class="voice-icon">🎙</div>'
        '<div><h2>Talk to Lingo</h2><p>Tap the microphone, say a few words, then press send.</p></div></div>',
        unsafe_allow_html=True,
    )
    recording = st.audio_input("Tap to record", key="speech-recording")
    if recording:
        st.audio(recording, format="audio/wav")
        st.session_state.voice_ready = True
        if st.button("✨ Send my voice", key="transcribe-recording", type="primary", use_container_width=True):
            with st.spinner("Listening..."):
                try:
                    response = api_request(
                        "POST",
                        "/api/speech/transcribe",
                        params={"language": st.session_state.language},
                        files={"audio": ("response.wav", recording.getvalue(), "audio/wav")},
                    )
                    st.session_state.queued_message = response.json()["transcript"]
                    st.rerun()
                except RuntimeError as error:
                    st.warning(str(error))
    else:
        st.caption("No microphone? A grown-up can use the typing helper below.")


def render_practice() -> None:
    language = get_language(st.session_state.language)
    st.markdown(
        f'<p class="page-kicker">{html.escape(language.native_name)} playtime · ages 2-5</p>',
        unsafe_allow_html=True,
    )
    st.markdown('<h1 class="page-heading">Talk & Play</h1>', unsafe_allow_html=True)
    st.markdown('<p class="page-subheading">Little words. Big smiles. Let’s talk, listen, and play.</p>', unsafe_allow_html=True)
    st.markdown(
        '<div class="mode-strip"><span class="mode-dot"></span><strong>Little Learners mode</strong>'
        '<span class="mode-count">one tiny tip at a time</span></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="play-prompt-label">Pick a game</div>', unsafe_allow_html=True)
    prompt_columns = st.columns(3)
    quick_prompts = [("🎨 Colors", "Tell me about a color."), ("🐶 Animals", "Tell me about an animal."), ("⚽ Play", "Tell me about your toy.")]
    for column, (label, prompt) in zip(prompt_columns, quick_prompts):
        if column.button(label, key=f"quick-{label}", use_container_width=True):
            process_message(prompt)

    with st.expander("🌟 Explore the 3D word world", expanded=False):
        st.caption("Drag the little world. Tap a shape to hear a word.")
        render_word_world()

    render_voice_input()
    for index, message in enumerate(st.session_state.messages):
        with st.chat_message(
            "user" if message["role"] == "user" else "assistant",
            avatar=LEARNER_AVATAR if message["role"] == "user" else COACH_AVATAR,
        ):
            if message["role"] == "user":
                st.markdown(message["content"])
            else:
                render_assistant_message(message, index)

    if queued_message := st.session_state.pop("queued_message", None):
        process_message(queued_message)
    with st.expander("🧑‍🧑‍🧒 Grown-up typing helper", expanded=False):
        typed_message = st.text_input("Type a message for your child", placeholder="Try: I see a red ball.", key="typed-message")
        if st.button("Send typed message", key="send-typed-message") and typed_message.strip():
            process_message(typed_message.strip())


def activity_chart(points: list[dict[str, Any]], title: str, color: str) -> None:
    if not points:
        st.caption("No activity yet.")
        return
    figure = graph_objects.Figure(
        graph_objects.Scatter(
            x=[point["date"] for point in points],
            y=[point["count"] for point in points],
            mode="lines+markers",
            line={"color": color, "width": 3},
            marker={"size": 8, "color": color},
        )
    )
    figure.update_layout(
        title={"text": title, "font": {"family": "DM Sans", "size": 14, "color": "#182c25"}},
        height=260,
        margin={"l": 6, "r": 8, "t": 40, "b": 6},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.64)",
        xaxis={"showgrid": False, "zeroline": False},
        yaxis={"showgrid": True, "gridcolor": "#e4ece5", "zeroline": False, "rangemode": "tozero"},
        showlegend=False,
    )
    st.plotly_chart(figure, use_container_width=True, config={"displayModeBar": False})


def render_progress() -> None:
    st.markdown('<p class="page-kicker">Your learning</p>', unsafe_allow_html=True)
    st.markdown('<h1 class="page-heading">Progress with a pulse</h1>', unsafe_allow_html=True)
    try:
        dashboard = get_json("/api/dashboard")
    except RuntimeError as error:
        st.error(str(error))
        return
    progress = dashboard["progress"]
    metrics = st.columns(3)
    metrics[0].metric("Conversations", progress["total_messages"])
    metrics[1].metric("Words collected", progress["vocabulary_count"])
    metrics[2].metric("Gentle corrections", progress["corrections_given"])
    st.markdown('<div class="metric-band"></div>', unsafe_allow_html=True)
    left, right = st.columns(2)
    with left:
        activity_chart(dashboard["daily_activity"], "Daily learning activity", "#1d694d")
        activity_chart(dashboard["corrections_by_date"], "Corrections by date", "#e87963")
    with right:
        activity_chart(dashboard["new_words_per_week"], "New words per week", "#789d2f")
        st.markdown("#### Most used words")
        for word in dashboard["most_used_words"]:
            st.markdown(
                f'<div class="suggestion"><strong>{html.escape(word["word"])}</strong>'
                f'<p>{html.escape(word["meaning"])} · used {word["frequency"]} times</p></div>',
                unsafe_allow_html=True,
            )
    st.markdown("#### Next practice")
    try:
        suggestions = get_json("/api/practice-suggestions")
        for suggestion in suggestions:
            st.markdown(
                f'<div class="suggestion"><strong>{html.escape(suggestion["word"])}</strong>'
                f'<p>{html.escape(suggestion["prompt"])}</p></div>',
                unsafe_allow_html=True,
            )
    except RuntimeError as error:
        st.warning(str(error))


def render_vocabulary() -> None:
    st.markdown('<p class="page-kicker">Personal collection</p>', unsafe_allow_html=True)
    st.markdown('<h1 class="page-heading">Words worth keeping</h1>', unsafe_allow_html=True)
    try:
        words = get_json("/api/vocabulary")
    except RuntimeError as error:
        st.error(str(error))
        return
    st.metric("Vocabulary collected", len(words))
    with st.expander("Add a word", expanded=False):
        with st.form("add-vocabulary"):
            word = st.text_input("Word")
            meaning = st.text_input("Meaning")
            example_sentence = st.text_input("Example sentence")
            submitted = st.form_submit_button("Add word", type="primary")
        if submitted:
            try:
                api_request(
                    "POST",
                    "/api/vocabulary",
                    json={"word": word, "meaning": meaning, "example_sentence": example_sentence},
                )
                st.rerun()
            except RuntimeError as error:
                st.warning(str(error))
    filter_text = st.text_input("Find a word", placeholder="Search your collection").lower().strip()
    filtered_words = [word for word in words if filter_text in word["word"].lower()]
    if not filtered_words:
        st.caption("No matching vocabulary yet.")
    for word in filtered_words:
        action, content = st.columns([1, 7])
        with content:
            st.markdown(
                f'<div class="word-row"><strong>{html.escape(word["word"])}</strong>'
                f'<span>{html.escape(word["meaning"])}</span>'
                f'<em>{html.escape(word["example_sentence"])}</em>'
                f'<span class="word-frequency">{word["frequency"]} uses</span></div>',
                unsafe_allow_html=True,
            )
        with action:
            if st.button("+1", key=f"frequency-{word['id']}"):
                try:
                    api_request("PATCH", f"/api/vocabulary/{word['word']}/frequency", json={"increment": 1})
                    st.rerun()
                except RuntimeError as error:
                    st.warning(str(error))


def render_sidebar() -> str:
    with st.sidebar:
        st.markdown(
            '<div class="brand-lockup"><span class="brand-mark">L</span><span class="brand-name">Lingo</span></div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="profile-panel"><strong>Amit</strong>Little learner · ages 2-5</div>', unsafe_allow_html=True)
        page = st.radio("Navigation", ["Talk & Play", "Grown-up progress", "Word basket"], label_visibility="collapsed")
        st.markdown('<div class="streak"><span class="streak-dot"></span>Ready for play</div>', unsafe_allow_html=True)
        if st.button("↻ New play", key="new-play", use_container_width=True):
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": "Hi, friend! Let’s play. Can you say hello and wave?",
                    "vocabulary": [],
                }
            ]
            st.session_state.audio_by_message = {}
            st.rerun()
        st.divider()
        selected_language = st.selectbox("Practice language", LANGUAGE_LABELS, index=0)
        st.session_state.language = LANGUAGE_PROFILES[LANGUAGE_LABELS.index(selected_language)].code
        st.caption(f"{len(LANGUAGE_PROFILES)} speech languages available")
        st.caption("Grown-up voice settings")
        st.session_state.voice = st.selectbox("Voice", list(VOICE_OPTIONS), index=0)
        st.session_state.speed = st.slider("Playback speed", 0.5, 1.5, 1.0, 0.1)
        return page


initialize_session()
selected_page = render_sidebar()
if selected_page == "Talk & Play":
    render_practice()
elif selected_page == "Grown-up progress":
    render_progress()
else:
    render_vocabulary()