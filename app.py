# app.py  ────────────────────────────────────────────────────────
import os, tempfile, textwrap, json, git, asyncio, streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from langchain_community.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings

# ──────────── 1. Environment & LLM  ────────────
load_dotenv()
llm = ChatOpenAI(model="gpt-4o", temperature=0.0, streaming=True)

# load the vector store you saved earlier
emb = OpenAIEmbeddings(model="text-embedding-3-small")
store = FAISS.load_local("faiss_index", emb,
                         allow_dangerous_deserialization=True)

st.set_page_config(page_title="EU AI-Act Ready MVP", layout="centered")
st.title("EU AI Act Readiness – MVP")

# ──────────── 2. Tabs layout  ────────────
tab_chat, tab_scan = st.tabs(["Chat assistant", "Repo scan"])

if prompt := st.chat_input("Type your question"):
    # 1)  Grab 4 most relevant Act chunks for this question
    hits = store.similarity_search(prompt, k=4)
    context = "\n\n".join(h.page_content for h in hits)

    # 2)  Build the prompt: guard-rail + retrieved context
    system_msg = (
        "\n\nUse the **context** below to answer. "
        "If the question is unrelated to the EU AI Act, "
        "reply: \"I'm sorry, I'm not qualified to answer that.\"\n\n"
        "### Context ###\n" + context
    )

    messages = [
        {"role": "system", "content": system_msg},
        *st.session_state.history,
        {"role": "user", "content": prompt},
    ]

    # 3)  Stream answer
    stream_area = st.chat_message("assistant").empty()
    response = ""
    for chunk in llm.stream(messages):
        response += chunk.content or ""
        stream_area.markdown(response + "▌")
    stream_area.markdown(response)

    # 4)  Persist turn
    st.session_state.history.extend([
        {"role": "user", "content": prompt},
        {"role": "assistant", "content": response},
    ])


# ──────────── 5. Worker coroutine  ────────────
async def run_scan(repo_url: str, llm: ChatOpenAI) -> dict:
    """Clone repo (shallow), sample up to 500 source files,
       ask GPT-4o to generate risk assessment."""
    tmp = tempfile.mkdtemp()
    git.Repo.clone_from(repo_url, tmp, depth=1)

    # collect snippets (first 300 lines) of .py/.js/.ts/.ipynb
    corpus, count = "", 0
    for root, _, files in os.walk(tmp):
        for f in files:
            if f.endswith((".py", ".js", ".ts", ".ipynb")) and count < 500:
                path = os.path.join(root, f)
                try:
                    with open(path, "r", errors="ignore") as fp:
                        snippet = "".join(fp.readlines()[:300])
                    corpus += f"\n\n# File: {f}\n{snippet}"
                    count += 1
                except Exception:
                    pass

    prompt = textwrap.dedent(f"""
    You are an AI compliance auditor. Analyse the code snapshot below.
    Return valid JSON with keys:
      tier  : one of ["minimal","limited","high","unacceptable"]
      actions : array of <=10 concise mandatory actions
      model_card_md : GitHub-flavored Markdown describing the model
    CODE_START
    {corpus}
    CODE_END
    """)
    raw = (await llm.agenerate([[HumanMessage(content=prompt)]])).generations[0][0].text
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"error": "LLM returned malformed JSON", "raw": raw}

# ──────────── 4. Repo scanner  ────────────
with tab_scan:
    st.markdown("### 1-click AI-Act assessment for your repo")
    repo_url = st.text_input("Public GitHub repository URL")
    if st.button("Run assessment", disabled=not repo_url):
        with st.spinner("Cloning & analysing…"):
            report = asyncio.run(run_scan(repo_url, llm))
            st.success("Done!")
            st.json(report)
            st.download_button("Download JSON",
                               json.dumps(report, indent=2),
                               file_name="ai-act-report.json",
                               mime="application/json")


