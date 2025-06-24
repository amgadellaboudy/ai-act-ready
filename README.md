# 🧠 AI-Act-Ready

**A GPT-powered assistant that helps developers and companies understand their responsibilities under the EU AI Act.**

Built with OpenAI + LangChain, this interactive tool allows you to ask questions and get plain-language explanations from actual EU AI Act text and guidance documents.

---

## ✨ What It Does

- 📜 Loads key provisions of the EU AI Act
- 🤖 Uses GPT to answer questions and explain clauses
- 🔍 Retrieves relevant sections using semantic search (RAG)
- 📂 Optionally scan your own repository for an analysis against the EU AI Act

---

## 🔧 Use Cases

- ✅ OSS Maintainers: Check if your AI tool meets transparency obligations
- ✅ Startups: Understand how risk levels apply to your product
- ✅ Legal & Policy Teams: Quickly explore or summarize legal text
- ✅ AI Engineers: Build your own compliance agent using this base

---

## 🚀 Demo (WIP)

![Demo](demo/demo.gif)

> *“What are the obligations for general-purpose AI systems?”*  
→ GPT summarizes Article 52, 53 with references and plain-English breakdown.

---

## 📦 Quickstart

You will need to source an OpenAI Api key to get started, you can source one from https://openai.com/api/
Once you have that key, create a .env file, in the same format as the .env.example file in the repo.
The rest is below:

```bash
# Clone the repo
git clone https://github.com/amgadellaboudy/ai-act-ready.git
cd ai-act-ready

# Set up a virtual environment (optional)
python -m venv venvsource venv/bin/activate

MacOS:
source venv/bin/activate

Windows:
.\venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

