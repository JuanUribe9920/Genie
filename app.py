"""
Genie — Pregúntale a tus apuntes
Groq (Llama 3.3-70b) · LangChain · ChromaDB · Streamlit
"""

from __future__ import annotations

import base64
import os
import tempfile
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from groq import Groq

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Genie",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed",
)

MODEL = "llama-3.3-70b-versatile"

# ─────────────────────────────────────────────────────────────────────────────
# Design tokens
# ─────────────────────────────────────────────────────────────────────────────
GOLD    = "#c9a96e"
GOLD_DIM = "#c9a96e22"
PEARL   = "#e8e8e8"
MUTED   = "#6b6b75"
BG      = "#080808"
CARD    = "#111113"
BORDER  = "#222228"
DANGER  = "#c0392b"

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', system-ui, sans-serif;
    background-color: {BG};
    color: {PEARL};
}}
#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{ padding: 3rem 2rem 5rem; max-width: 780px; margin: 0 auto; }}

/* ── Lamp flame animation ── */
.lamp-flame {{
    animation: flame-float 3s ease-in-out infinite;
    transform-origin: 26px 22px;
    transform-box: fill-box;
}}
@keyframes flame-float {{
    0%   {{ transform: translateY(0)   scale(1);    opacity: 0.75; filter: drop-shadow(0 0 3px {GOLD}); }}
    40%  {{ transform: translateY(-3px) scale(1.25); opacity: 1;    filter: drop-shadow(0 0 7px {GOLD}); }}
    100% {{ transform: translateY(0)   scale(1);    opacity: 0.75; filter: drop-shadow(0 0 3px {GOLD}); }}
}}

/* ── Noise texture overlay ── */
body::after {{
    content: '';
    position: fixed;
    inset: 0;
    background-image: url("data:image/svg+xml,<svg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/><feColorMatrix type='saturate' values='0'/></filter><rect width='100%25' height='100%25' filter='url(%23n)'/></svg>");
    opacity: 0.032;
    pointer-events: none;
    z-index: 9990;
}}

/* ── Header ── */
.genie-header {{
    text-align: center;
    padding: 3rem 0 2.5rem;
    border-bottom: 1px solid {BORDER};
    margin-bottom: 2.5rem;
}}
.genie-lamp {{
    margin: 0 auto 1.5rem;
    display: block;
    filter: drop-shadow(0 0 18px {GOLD}44);
}}
.genie-title {{
    font-size: 2.2rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    color: {PEARL};
    margin: 0 0 0.4rem;
    text-transform: uppercase;
}}
.genie-subtitle {{
    font-size: 0.82rem;
    color: {MUTED};
    letter-spacing: 0.06em;
    margin: 0;
}}

/* ── Welcome tips ── */
.tips-block {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 16px;
    padding: 1.5rem 1.8rem;
    margin-bottom: 1.8rem;
}}
.tips-block .tips-heading {{
    font-size: 0.7rem;
    font-weight: 600;
    color: {GOLD};
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 1.1rem;
}}
.tips-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.7rem 2rem;
}}
.tip-row {{
    display: flex;
    align-items: flex-start;
    gap: 0.55rem;
}}
.tip-row .tip-dot {{
    color: {GOLD};
    font-size: 0.65rem;
    margin-top: 3px;
    flex-shrink: 0;
    opacity: 0.8;
}}
.tip-row .tip-text {{
    font-size: 0.8rem;
    color: {MUTED};
    line-height: 1.45;
}}
.tip-row .tip-text b {{
    color: {PEARL};
    font-weight: 500;
    display: block;
    margin-bottom: 1px;
}}

/* ── Upload zone ── */
[data-testid="stFileUploader"] {{
    background: {CARD};
    border: 1px dashed {BORDER};
    border-radius: 16px;
    padding: 0.5rem 1rem;
    transition: border-color 0.25s;
}}
[data-testid="stFileUploader"]:hover {{ border-color: {GOLD}66; }}
[data-testid="stFileUploaderDropzone"] {{ background: transparent !important; }}

/* ── Status widget ── */
[data-testid="stStatusWidget"] {{
    background: {CARD} !important;
    border: 1px solid {BORDER} !important;
    border-left: 2px solid {GOLD} !important;
    border-radius: 12px !important;
    margin: 0.6rem 0 !important;
    font-size: 0.85rem !important;
}}

/* ── State cards (loading / done / error) ── */
.state-card {{
    display: flex;
    align-items: center;
    gap: 0.9rem;
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 0.9rem 1.2rem;
    margin: 0.5rem 0;
    font-size: 0.85rem;
    color: {MUTED};
}}
.state-card.done  {{ border-left: 2px solid {GOLD}; color: {PEARL}; }}
.state-card.error {{ border-left: 2px solid {DANGER}; }}

/* Spinning ring */
.ring {{
    width: 18px;
    height: 18px;
    border: 2px solid {BORDER};
    border-top-color: {GOLD};
    border-radius: 50%;
    animation: spin 0.75s linear infinite;
    flex-shrink: 0;
}}
@keyframes spin {{ to {{ transform: rotate(360deg); }} }}

/* Done star */
.done-star {{
    color: {GOLD};
    font-size: 1rem;
    flex-shrink: 0;
    animation: pop 0.3s ease-out;
}}
@keyframes pop {{
    0%   {{ transform: scale(0.5); opacity: 0; }}
    70%  {{ transform: scale(1.2); }}
    100% {{ transform: scale(1); opacity: 1; }}
}}

/* ── Chat interface ── */
.chat-wrap {{
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin-top: 1.5rem;
}}

/* User bubble */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {{
    background: {CARD} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 14px 14px 4px 14px !important;
    padding: 0.9rem 1.1rem !important;
    margin-left: 3rem !important;
    box-shadow: 0 2px 12px #00000033 !important;
}}

/* Genie bubble */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {{
    background: #0e0e10 !important;
    border: 1px solid {GOLD}22 !important;
    border-radius: 14px 14px 14px 4px !important;
    padding: 0.9rem 1.1rem !important;
    margin-right: 3rem !important;
    box-shadow: 0 2px 20px {GOLD}0a !important;
}}

/* Chat input */
[data-testid="stChatInput"] {{
    background: {CARD} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 14px !important;
    margin-top: 1rem !important;
}}
[data-testid="stChatInput"]:focus-within {{
    border-color: {GOLD}55 !important;
    box-shadow: 0 0 0 3px {GOLD}0a !important;
}}

/* ── Divider ── */
.genie-divider {{
    border: none;
    border-top: 1px solid {BORDER};
    margin: 1.8rem 0;
}}

/* ── Source pill ── */
.source-pill {{
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: {GOLD}10;
    border: 1px solid {GOLD}30;
    color: {GOLD};
    font-size: 0.7rem;
    font-weight: 500;
    padding: 0.2rem 0.7rem;
    border-radius: 100px;
    margin: 0.4rem 0.3rem 0 0;
    letter-spacing: 0.03em;
}}

/* ── Buttons ── */
.stButton > button {{
    background: transparent !important;
    color: {GOLD} !important;
    border: 1px solid {GOLD}55 !important;
    border-radius: 12px !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    padding: 0.5rem 1.2rem !important;
    transition: all 0.2s !important;
    letter-spacing: 0.02em !important;
}}
.stButton > button:hover {{
    background: {GOLD}10 !important;
    border-color: {GOLD} !important;
}}

/* ── Footer ── */
.genie-footer {{
    text-align: center;
    padding: 2rem 0 0.5rem;
    margin-top: 3rem;
    border-top: 1px solid {BORDER};
}}
.genie-footer span {{
    font-size: 0.68rem;
    color: #333338;
    letter-spacing: 0.05em;
}}
.genie-footer span b {{ color: {MUTED}; font-weight: 500; }}
</style>
"""

# ─────────────────────────────────────────────────────────────────────────────
# SVG — Abstract lamp icon
# ─────────────────────────────────────────────────────────────────────────────
LAMP_SVG = f"""
<svg class="genie-lamp" width="52" height="52" viewBox="0 0 52 52" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <radialGradient id="glow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="{GOLD}" stop-opacity="0.25"/>
      <stop offset="100%" stop-color="{GOLD}" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <!-- Glow halo -->
  <circle cx="26" cy="24" r="22" fill="url(#glow)"/>
  <!-- Lamp body -->
  <path d="M26 6C17 6 12 15 12 22C12 31 19 39 26 43C33 39 40 31 40 22C40 15 35 6 26 6Z"
        stroke="{GOLD}" stroke-width="1.2" fill="none" stroke-linejoin="round"/>
  <!-- Spout -->
  <path d="M36 38L44 44" stroke="{GOLD}" stroke-width="1.2" stroke-linecap="round"/>
  <!-- Handle -->
  <path d="M12 25C7 25 5 29 5 32C5 35 7 38 12 38"
        stroke="{GOLD}" stroke-width="1.2" stroke-linecap="round" fill="none"/>
  <!-- Flame -->
  <circle class="lamp-flame" cx="26" cy="22" r="2.5" fill="{GOLD}" opacity="0.75"/>
  <!-- Flame wisp -->
  <path d="M26 6C25 3 27 1 26 -1" stroke="{GOLD}" stroke-width="0.8"
        stroke-linecap="round" opacity="0.3"/>
</svg>
"""

# ─────────────────────────────────────────────────────────────────────────────
# State card helpers
# ─────────────────────────────────────────────────────────────────────────────
def state_loading(msg: str) -> str:
    return f'<div class="state-card"><div class="ring"></div><span>{msg}</span></div>'

def state_done(msg: str) -> str:
    return f'<div class="state-card done"><span class="done-star">✦</span><span>{msg}</span></div>'

def state_error(msg: str) -> str:
    return f'<div class="state-card error"><span style="color:#c0392b">✕</span><span>{msg}</span></div>'


# ─────────────────────────────────────────────────────────────────────────────
# Welcome tips
# ─────────────────────────────────────────────────────────────────────────────
PDF_TIPS = [
    ("Texto seleccionable", "No PDFs escaneados como imagen — el texto debe ser copiable."),
    ("Sin contraseña", "El archivo debe estar desbloqueado para procesarse."),
    ("Idioma consistente", "Mejor si todo el documento está en un solo idioma."),
    ("Máximo 50 MB", "Por archivo. Puedes subir varios a la vez."),
    ("Sin tablas complejas", "Las tablas simples funcionan. Evita fusiones de celdas."),
    ("Una sola fuente", "Evita PDFs generados desde múltiples formatos distintos."),
]

IMG_TIPS = [
    ("Texto legible", "La letra debe ser clara — manuscrita o impresa, sin desenfoque."),
    ("Buena iluminación", "Sin sombras fuertes ni reflejos sobre el texto."),
    ("Encuadre recto", "La imagen de frente, sin ángulo pronunciado."),
    ("Formatos aceptados", "JPG, PNG y WEBP. Máximo 20 MB por imagen."),
    ("Sin fondo saturado", "Mejor fondo blanco o neutro para mayor precisión."),
    ("Un tema por imagen", "Funciona mejor si cada imagen cubre un solo tema o página."),
]

def render_tips() -> None:
    def make_rows(tips):
        return "".join(
            f'<div class="tip-row"><span class="tip-dot">✦</span>'
            f'<span class="tip-text"><b>{t}</b>{d}</span></div>'
            for t, d in tips
        )

    st.markdown(f"""
    <div class="tips-block">
        <div class="tips-heading">📄 Para PDFs</div>
        <div class="tips-grid">{make_rows(PDF_TIPS)}</div>
        <div class="tips-heading" style="margin-top:1.2rem">🖼️ Para imágenes con texto</div>
        <div class="tips-grid">{make_rows(IMG_TIPS)}</div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# RAG pipeline
# ─────────────────────────────────────────────────────────────────────────────
IMAGE_EXTS = {"jpg", "jpeg", "png", "webp"}


def extract_text_from_image(image_bytes: bytes, filename: str, api_key: str) -> str:
    client = Groq(api_key=api_key)
    ext  = filename.rsplit(".", 1)[-1].lower()
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
    b64  = base64.b64encode(image_bytes).decode("utf-8")
    resp = client.chat.completions.create(
        model="llama-3.2-11b-vision-preview",
        messages=[{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
            {"type": "text", "text": "Extrae todo el texto visible en esta imagen fielmente, sin interpretaciones adicionales."},
        ]}],
        max_tokens=2000,
    )
    return resp.choices[0].message.content


def build_vectorstore(uploaded_files: list, api_key: str = "") -> tuple:
    """Process PDFs and images; return (vectorstore, file_names). Shows loading states."""
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import Chroma
    from langchain.schema import Document

    all_docs   = []
    file_names = []
    state_ph   = st.empty()

    # ── Read files ───────────────────────────────────────────────────────────
    for uf in uploaded_files:
        state_ph.markdown(state_loading(f"Leyendo <b>{uf.name}</b>…"), unsafe_allow_html=True)
        ext = uf.name.rsplit(".", 1)[-1].lower()
        try:
            if ext in IMAGE_EXTS:
                text = extract_text_from_image(uf.getvalue(), uf.name, api_key)
                all_docs.append(Document(page_content=text, metadata={"source": uf.name}))
            else:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uf.getvalue())
                    tmp_path = tmp.name
                loader = PyPDFLoader(tmp_path)
                docs   = loader.load()
                all_docs.extend(docs)
                os.unlink(tmp_path)
            file_names.append(uf.name)
        except Exception as e:
            state_ph.markdown(state_error(f"Error leyendo {uf.name}: {e}"), unsafe_allow_html=True)
            return None, []

    state_ph.markdown(state_done(f"{len(file_names)} archivo(s) leídos correctamente"), unsafe_allow_html=True)

    # ── Split ────────────────────────────────────────────────────────────────
    state_ph2 = st.empty()
    state_ph2.markdown(state_loading("Dividiendo contenido en fragmentos…"), unsafe_allow_html=True)

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks   = splitter.split_documents(all_docs)

    state_ph2.markdown(state_done(f"{len(chunks)} fragmentos creados"), unsafe_allow_html=True)

    # ── Embed ────────────────────────────────────────────────────────────────
    state_ph3 = st.empty()
    state_ph3.markdown(state_loading("Creando base de conocimiento…"), unsafe_allow_html=True)

    embeddings   = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore  = Chroma.from_documents(chunks, embedding=embeddings)

    state_ph3.markdown(state_done("Base de conocimiento lista — Genie está listo"), unsafe_allow_html=True)

    return vectorstore, file_names


def ask_genie(vectorstore, question: str, api_key: str) -> tuple[str, list[str]]:
    """Query the vectorstore and generate answer. Returns (answer, sources)."""
    from langchain_groq import ChatGroq
    from langchain.chains import RetrievalQA
    from langchain.prompts import PromptTemplate

    llm = ChatGroq(api_key=api_key, model_name=MODEL, temperature=0.3)

    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template="""Eres Genie, un asistente experto en analizar documentos. Responde en español de forma clara y precisa basándote ÚNICAMENTE en el contexto proporcionado. Si la respuesta no está en el contexto, dilo claramente.

Contexto:
{context}

Pregunta: {question}

Respuesta:"""
    )

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 4}),
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt},
    )

    result  = chain.invoke({"query": question})
    answer  = result["result"]
    sources = list({doc.metadata.get("source", "").split("/")[-1]
                    for doc in result.get("source_documents", [])
                    if doc.metadata.get("source")})
    return answer, sources


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    st.markdown(CSS, unsafe_allow_html=True)

    # Session state
    for key, default in [("vectorstore", None), ("file_names", []),
                         ("messages", []), ("file_key", None)]:
        if key not in st.session_state:
            st.session_state[key] = default

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("Configura GROQ_API_KEY en tu archivo .env")
        st.stop()

    # ── Header ───────────────────────────────────────────────────────────────
    st.markdown(f'<div class="genie-header">{LAMP_SVG}<div class="genie-title">Genie</div><div class="genie-subtitle">Pregúntale a tus apuntes</div></div>', unsafe_allow_html=True)

    # ── Upload ────────────────────────────────────────────────────────────────
    if not st.session_state.vectorstore:
        render_tips()

    uploaded = st.file_uploader(
        "",
        type=["pdf", "jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    # ── Process new files ────────────────────────────────────────────────────
    if uploaded:
        file_key = "_".join(f"{f.name}{f.size}" for f in uploaded)

        if st.session_state.file_key != file_key:
            st.session_state.messages  = []
            st.session_state.file_key  = file_key
            vectorstore, file_names    = build_vectorstore(uploaded, api_key)
            st.session_state.vectorstore = vectorstore
            st.session_state.file_names  = file_names

    # ── Chat ─────────────────────────────────────────────────────────────────
    if st.session_state.vectorstore:
        # File pills
        if st.session_state.file_names:
            pills = "".join(
                f'<span class="source-pill">✦ {name}</span>'
                for name in st.session_state.file_names
            )
            st.markdown(f'<div style="margin:1rem 0 0.5rem">{pills}</div>', unsafe_allow_html=True)

        st.markdown('<hr class="genie-divider">', unsafe_allow_html=True)

        # History
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("sources"):
                    src_html = "".join(
                        f'<span class="source-pill">✦ {s}</span>'
                        for s in msg["sources"]
                    )
                    st.markdown(src_html, unsafe_allow_html=True)

        # Input
        if question := st.chat_input("Pregúntale a Genie…"):
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)

            with st.chat_message("assistant"):
                ph = st.empty()
                ph.markdown(state_loading("Genie está pensando…"), unsafe_allow_html=True)
                try:
                    answer, sources = ask_genie(st.session_state.vectorstore, question, api_key)
                    ph.empty()
                    st.markdown(answer)
                    if sources:
                        src_html = "".join(
                            f'<span class="source-pill">✦ {s}</span>'
                            for s in sources
                        )
                        st.markdown(src_html, unsafe_allow_html=True)
                    st.session_state.messages.append({
                        "role": "assistant", "content": answer, "sources": sources
                    })
                except Exception as e:
                    ph.markdown(state_error(f"Error: {e}"), unsafe_allow_html=True)

        # Reset
        if st.session_state.messages:
            st.markdown("<div style='margin-top:1rem'>", unsafe_allow_html=True)
            if st.button("Limpiar conversación"):
                st.session_state.messages = []
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # ── Footer ───────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="genie-footer">
        <span>Desarrollado por <b>Juan Uribe</b> · Asistido con IA</span>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
