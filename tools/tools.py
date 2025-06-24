import tempfile, git, os
from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate
from tools.schemas import AuditResult
from typing import Dict, Union
import asyncio


# ──────────── 3. Define repo scanning logic ────────────
def collect_code_snippets(repo_url: str, max_files: int = 500, max_lines: int = 300) -> str:
    tmp_dir = tempfile.mkdtemp()
    git.Repo.clone_from(repo_url, tmp_dir, depth=1)

    snippets = []
    count = 0
    for root, _, files in os.walk(tmp_dir):
        for f in files:
            if f.endswith((".py", ".js", ".ts", ".ipynb")) and count < max_files:
                try:
                    with open(os.path.join(root, f), "r", errors="ignore") as file:
                        code = "".join(file.readlines()[:max_lines])
                        snippets.append(f"# File: {f}\n{code}")
                        count += 1
                except Exception:
                    continue
    return "\n\n".join(snippets)


def build_augmented_prompt(vector_store, code_snapshot: str, llm_question: str, parser) -> ChatPromptTemplate:
    act_chunks = vector_store.similarity_search(llm_question, k=4)
    act_context = "\n\n".join([f"[Source chunk]\n{chunk.page_content}" for chunk in act_chunks])
    format_instructions = parser.get_format_instructions()

    return ChatPromptTemplate.from_messages([
        SystemMessage(content="You are an expert EU AI Act compliance auditor. Analyze the following code."),
        HumanMessage(content=(
            f"Context from EU AI Act:\n{act_context}\n\n"
            f"{format_instructions}\n\n"
            f"Analyze the following repo snapshot and return JSON:"
            f"\nCODE_START\n{code_snapshot}\nCODE_END"
        ))
    ])


def run_minimal_mvp_scan(repo_url: str, llm: ChatOpenAI, vector_store) -> Union[AuditResult, Dict]:
    code = collect_code_snippets(repo_url)
    question = "What are the compliance obligations of this codebase under the EU AI Act?"
    parser = PydanticOutputParser(pydantic_object=AuditResult)
    prompt = build_augmented_prompt(vector_store, code, question, parser)
    try:
        chain = prompt | llm | parser
        result = asyncio.run(chain.ainvoke({}))
        return result
    except Exception as e:
        return {"error": f"Exception: {str(e)}"}
