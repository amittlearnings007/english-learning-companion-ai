APP_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600;700&family=Nunito:wght@400;600;700;800&display=swap');

:root {
  --ink: #17324d;
  --forest: #136b5a;
  --mint: #dff8ef;
  --lime: #ffd75a;
  --coral: #ef7d6b;
  --sky: #e0f4ff;
  --paper: #fffaf1;
  --line: #e4e7df;
  --muted: #667785;
}

.stApp {
  background-color: var(--paper);
  background-image: radial-gradient(#f1dfaf 1px, transparent 1px);
  background-size: 22px 22px;
  color: var(--ink);
  font-family: 'Nunito', sans-serif;
}

#MainMenu, footer, header { visibility: hidden; }
.block-container { max-width: 1200px; padding: 2.1rem 3.3rem 3rem; }

[data-testid="stSidebar"] {
  background: #f1f6f1;
  border-right: 1px solid var(--line);
}

[data-testid="stSidebar"] > div:first-child { padding-top: 1.4rem; }
[data-testid="stSidebar"] .stRadio label { color: var(--muted); font-weight: 600; }
[data-testid="stSidebar"] .stRadio label:has(input:checked) { color: var(--forest); }

.brand-lockup { display: flex; align-items: center; gap: 0.7rem; margin: 0.2rem 0 2rem; }
.brand-mark { display: grid; place-items: center; width: 2.2rem; height: 2.2rem; border-radius: 0.75rem; background: var(--forest); color: white; font: 700 1.25rem 'Fredoka', sans-serif; }
.brand-name { font: 600 1.55rem 'Fredoka', sans-serif; color: var(--ink); }
.profile-panel { border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); padding: 1rem 0; margin: 1.4rem 0; color: var(--muted); font-size: 0.83rem; }
.profile-panel strong { display: block; color: var(--ink); font-size: 0.93rem; margin-bottom: 0.2rem; }
.streak { display: flex; align-items: center; gap: 0.55rem; padding: 0.7rem 0; color: var(--forest); font-weight: 700; font-size: 0.84rem; }
.streak-dot { width: 0.72rem; height: 0.72rem; border-radius: 50%; background: var(--lime); box-shadow: 0 0 0 4px #e8f5c8; }

.page-kicker { color: var(--forest); font-size: 0.78rem; font-weight: 800; letter-spacing: 0.1em; text-transform: uppercase; margin: 0 0 0.35rem; }
.page-heading { color: var(--ink); font: 600 clamp(2.35rem, 5vw, 4.1rem) 'Fredoka', sans-serif; letter-spacing: 0; margin: 0; }
.page-subheading { color: var(--muted); margin: 0.55rem 0 1.5rem; font-size: 1.05rem; }
.mode-strip { display: flex; align-items: center; gap: 0.55rem; padding: 0.9rem 1rem; background: var(--mint); border: 1px solid #c7ebdd; border-radius: 0.8rem; color: var(--forest); font-size: 0.9rem; margin-bottom: 1.25rem; }
.mode-dot { width: 0.55rem; height: 0.55rem; border-radius: 50%; background: #5eab70; }
.mode-count { margin-left: auto; padding: 0.25rem 0.55rem; background: white; border: 1px solid #c7ebdd; border-radius: 0.4rem; font-size: 0.75rem; }

.play-prompt-label { color: var(--muted); font-size: 0.8rem; font-weight: 800; margin: 0 0 0.35rem; }
.voice-stage { display: flex; align-items: center; gap: 1rem; padding: 1rem 1.1rem; margin: 1rem 0 0.7rem; background: var(--sky); border: 2px solid #bde5f7; border-radius: 1rem; }
.voice-icon { display: grid; place-items: center; width: 3.1rem; height: 3.1rem; border-radius: 1rem; background: white; font-size: 1.65rem; box-shadow: 0 3px 0 #b7dcec; }
.voice-stage h2 { margin: 0; color: var(--ink); font: 600 1.45rem 'Fredoka', sans-serif; }
.voice-stage p { margin: 0.2rem 0 0; color: var(--muted); font-size: 0.88rem; }

[data-testid="stChatMessage"] { background: transparent; border: 0; padding: 0.75rem 0.2rem; }
[data-testid="stChatMessage"] [data-testid="stChatMessageContent"] { font-size: 1.02rem; line-height: 1.65; }
[data-testid="stChatMessage"] [data-testid="stChatMessageAvatarUser"] { background: var(--coral); }
[data-testid="stChatMessage"] [data-testid="stChatMessageAvatarAssistant"] { background: var(--forest); color: white; }
.correction-note { border-left: 4px solid var(--coral); background: #fff2ed; padding: 0.9rem 1rem; margin: 0.75rem 0 0.15rem; border-radius: 0.2rem 0.8rem 0.8rem 0.2rem; }
.correction-title { color: #a74d3e; font-size: 0.8rem; font-weight: 800; letter-spacing: 0.04em; text-transform: uppercase; margin-bottom: 0.3rem; }
.correction-note p { margin: 0.25rem 0; font-size: 0.95rem; }
.correction-before { color: #a3655b; text-decoration: line-through; }
.correction-arrow { color: var(--coral); padding: 0 0.35rem; }
.vocab-chip { display: inline-block; margin: 0.65rem 0.35rem 0 0; padding: 0.35rem 0.65rem; color: var(--forest); background: var(--mint); border-radius: 0.55rem; font-size: 0.8rem; font-weight: 800; }

.metric-band { border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); margin: 1rem 0 1.8rem; padding: 1.05rem 0; }
[data-testid="stMetric"] { background: transparent; }
[data-testid="stMetricLabel"] { color: var(--muted); font-size: 0.76rem; }
[data-testid="stMetricValue"] { color: var(--ink); font: 600 2rem 'Newsreader', serif; }

.word-row { display: grid; grid-template-columns: minmax(90px, 0.8fr) 1.6fr 1.4fr 90px; align-items: center; column-gap: 1rem; padding: 0.8rem 0; border-bottom: 1px solid var(--line); }
.word-row strong { font: 600 1.05rem 'Newsreader', serif; }
.word-row span, .word-row em { color: var(--muted); font-size: 0.82rem; font-style: normal; }
.word-frequency { color: var(--forest) !important; font-weight: 700; }
.suggestion { border-left: 2px solid var(--lime); padding: 0.65rem 0.85rem; margin: 0.55rem 0; background: rgba(255, 255, 255, 0.58); }
.suggestion strong { color: var(--forest); font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em; }
.suggestion p { margin: 0.25rem 0 0; color: var(--muted); font-size: 0.86rem; }

.stButton > button, .stDownloadButton > button { min-height: 3rem; border-radius: 0.75rem; border: 2px solid #d4e0d8; color: var(--forest); font-weight: 800; background: #ffffff; }
.stButton > button[kind="primary"] { background: var(--forest); color: white; border-color: var(--forest); }
.stTextInput input, .stTextArea textarea, [data-baseweb="select"] > div { border-radius: 0.65rem; border-color: #ccd9cf; background: white; min-height: 3rem; }
[data-testid="stAudioInput"] { background: #ffffff; border: 2px solid #bde5f7; border-radius: 0.8rem; padding: 0.6rem; }
[data-testid="stAudioInput"] button { min-height: 3.4rem; }
[data-testid="stExpander"] { border: 1px solid var(--line); border-radius: 0.8rem; background: rgba(255,255,255,0.7); }

@media (max-width: 760px) {
  .block-container { padding: 1.3rem 1rem 2rem; }
  .page-heading { font-size: 2.7rem; }
  .voice-stage { align-items: flex-start; }
  .word-row { grid-template-columns: 1fr; gap: 0.35rem; }
  [data-testid="stSidebar"] { min-width: 17rem; }
}
"""