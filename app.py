# app.py  ────────────────────────────────────────────────────────
import json, asyncio, streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from tools import run_minimal_mvp_scan


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

with tab_chat:
    st.info("Ask anything about the EU AI Act.")

    if "history" not in st.session_state:
        st.session_state.history = []
    if prompt := st.chat_input("Type your question"):
        st.chat_message("user").markdown(prompt)
        # 1)  Grab 4 most relevant Act chunks for this question
        hits = store.similarity_search(prompt, k=4)
        context = "\n\n".join(h.page_content for h in hits)

        # 2)  Build the prompt: guard-rail + retrieved context
        system_msg = (
                "You are an expert on the EU AI Act. Use the **context** below to help answer the user's question. "
                "If the question is clearly unrelated to the EU AI Act, respond with: \"I'm sorry, I'm not"
                "qualified to answer that.\"If the context doesn't directly answer the question, rely on your own"
                "knowledge of the EU AI Act. \n\n ### Context ###\n" + context
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


# ──────────── 4. Repo scanner  ────────────
with tab_scan:
    st.markdown("### 1-click AI-Act assessment for your repo")
    repo_url = st.text_input("Public GitHub repository URL")

    if "audit_chat_history" not in st.session_state:
        st.session_state.audit_chat_history = []

    if st.button("Run assessment", disabled=not repo_url):
        with st.spinner("Analysing…"):
            # Vector search
            report = run_minimal_mvp_scan(repo_url, llm, store)
            st.session_state.audit_report = report.model_dump(mode="json") # Save it for follow-up chat
            st.success("Done!")
            st.json(st.session_state.audit_report)

    # Interactive chat after report is generated
    if "audit_report" in st.session_state:
        st.markdown("### Audit Report")
        st.json(st.session_state.audit_report)
        st.divider()
        st.markdown("### What would you like to know about the repo audit or the EU AI Act?")

        for msg in st.session_state.audit_chat_history:
            st.chat_message(msg["role"]).markdown(msg["content"])

        if user_q := st.chat_input("Ask a question"):
            st.chat_message("user").markdown(user_q)
            # Build context from EU AI Act chunks
            relevant_chunks = store.similarity_search(user_q, k=4)
            context = "\n\n".join([f"[Context chunk]\n{c.page_content}" for c in relevant_chunks])

            # System prompt includes audit report and guardrails
            sys_prompt = f"""You are an expert EU AI Act compliance expert.
            You have just produced the following audit report for a GitHub repo:
            {json.dumps(st.session_state.audit_report, indent=2)}
            It includes a risk tier,actionable items, and a model card. You may answer follow-up questions that:
            - Clarify the meaning or reasoning behind the audit
            - Explore next steps to implement the recommendations
            - Ask for help planning or executing remediations
            - Refer to specific content from the EU AI Act or the JSON audit
        
            If the user asks something *unrelated to the audit* or *not relevant to AI compliance*,
            politely explain that you're focused only on EU AI Act matters.
        
            Relevant context:
            {context}
            """
            messages = [{"role": "system", "content": sys_prompt}] + \
                       st.session_state.audit_chat_history + \
                       [{"role": "user", "content": user_q}]

            # Stream reply
            stream_area = st.chat_message("assistant").empty()
            response = ""
            for chunk in llm.stream(messages):
                response += chunk.content or ""
                stream_area.markdown(response + "▌")
            stream_area.markdown(response)

            # Update chat history
            st.session_state.audit_chat_history.extend([
                {"role": "user", "content": user_q},
                {"role": "assistant", "content": response},
            ])
