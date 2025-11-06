# 🧠 RMIT Academic Policies Chatbot
**AI-Assisted Supporter Chatbot for New RMIT Students**

This chatbot helps new RMIT students understand **academic policies** such as academic integrity, assessment extensions, appeals, and course progress through natural language queries.  
Instead of reading hundreds of pages of policy documents, it provides **accurate, citation-backed answers** based on official RMIT policies using **Retrieval-Augmented Generation (RAG)** with AWS Bedrock (Claude Sonnet / Haiku).

---

## 🚀 Quick Start

### 1️⃣ Clone the repository
```bash
git clone https://github.com/abedakhanam/chatbot-cld.git
cd DataCommAssm3
```

### 2️⃣ Create and activate a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 3️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Run the chatbot
```bash
streamlit run app.py
```

The app will start on **http://localhost:8501**

---

## 📊 Scraping Policy Data

The chatbot includes a web scraper to automatically download policy documents from RMIT's website.

### Option 1: Use the Scraper Button in the UI
1. Launch the application: `streamlit run app.py`
2. In the sidebar, click **"🔄 Run Scraper"**
3. Wait 5-6 minutes for the scraper to complete
4. The scraper will:
   - Fetch all policy links from https://policies.rmit.edu.au/browse.php
   - Download and parse each policy document
   - Convert to structured JSON format
   - Save to `/data/policies/` directory
5. Click **"🔄 Re-index Policies"** to load the newly scraped policies

### Option 2: Upload JSON Files Directly
1. Place policy JSON files in the `/data/policies/` directory or upload it directly in website
2. Click **"🔄 Re-index Policies"** in the sidebar
3. The system will automatically index all JSON files

**Note:** Initial indexing takes a few seconds as the system creates embeddings for all policy passages.

---

## 📂 Project Structure
```
academic-policies-chatbot/
├── app.py                     # Main Streamlit application
├── rag_policies.py            # RAG system logic
├── scraper.py                 # Web scraping functionality
├── requirements.txt           # Python dependencies
├── .gitignore
├── data/
│   └── policies/              # Policy JSON files (auto-generated)
└── README.md
```

---

## 🧰 Technology Stack

- **Streamlit** — Web UI framework for chat interface
- **AWS Bedrock (Claude 3.5 Sonnet)** — Large language model for generating responses
- **boto3** — AWS SDK for Python to communicate with Bedrock
- **sentence-transformers** — Text embeddings (model: `all-MiniLM-L6-v2`)
- **FAISS** — Fast vector similarity search library
- **BeautifulSoup4** — HTML parsing for web scraping
- **requests** — HTTP requests for scraping

---

## ✨ Features

- 🎨 **Modern UI** - Streamlit-based interface (mobile-friendly)
- ⚙️ **RAG System** - Retrieval-Augmented Generation with FAISS + sentence-transformers
- 🧠 **Context-Aware** - Conversation memory maintains context across queries
- 💬 **Smart Clarification** - Automatically handles vague queries and asks clarifying questions
- 📚 **Auto-Indexing** - Automatically indexes uploaded policy JSON files
- 🕷️ **Web Scraper** - Built-in scraper to download policies from RMIT website
- 🧩 **Responsible AI** - Guardrails ensure answers only use official RMIT policies
- 📖 **Citations** - Clause-level citations for every factual answer

---

## 🔧 How It Works

### System Architecture
```
User Question 
    ↓
[Streamlit UI] - Captures input
    ↓
[FAISS Search] - Finds relevant policy clauses (top 6 results)
    ↓
[Build Prompt] - Combines question + retrieved policies with citations
    ↓
[AWS Bedrock Claude] - Generates answer using context
    ↓
[Display Response] - Shows answer with policy citations
```

### Main Query Processing Pipeline

1. **Validate user input** - Check input is not empty
2. **Search FAISS index** - Find top 6 relevant policy passages
3. **Check similarity threshold** - Ensure results meet minimum similarity (0.35)
4. **Build prompt** - Combine question + retrieved policies with citation format
5. **Send to Claude** - Call AWS Bedrock API with formatted prompt
6. **Parse response** - Extract answer and return to user with citations

### What is FAISS?

**FAISS = Facebook AI Similarity Search**  
Library for fast similarity search in high-dimensional vectors. Used to find policy passages most similar to user query.

#### How FAISS Works

**Step 1: Text to Vector Conversion**
```
Text: "What is plagiarism?" 
    ↓ [SentenceTransformer] 
    ↓
Vector: [0.31, -0.22, 0.91, ..., -0.15] (384 dimensions)
```

**Step 2: Similarity Measurement**
- Uses **cosine similarity** via inner product
- After normalization, inner product = cosine similarity

**Score interpretation:**
- **0.9-1.0:** Very similar (almost identical meaning)
- **0.7-0.9:** Similar (related topic)
- **0.5-0.7:** Somewhat related
- **0.3-0.5:** Weakly related
- **<0.3:** Not related

**FAISS Index Type: IndexFlatIP**
- **Flat:** Brute-force search (checks all vectors), 100% accurate, good for <10,000 passages
- **IP (Inner Product):** Measures dot product between vectors, equivalent to cosine similarity when normalized

---

## ⚡ System Workflow

### Startup Sequence

1. Streamlit initializes
2. Load libraries
3. Initialize AWS Bedrock client
4. Load policy JSONs from `/mnt/project/` or `/data/policies/`
5. Flatten to passages (~500 passages)
6. Load SentenceTransformer model
7. Create embeddings for all passages
8. Build FAISS index
9. Display UI - READY

### Query Processing

1. Capture input from user
2. Add to conversation history
3. Display in chat interface
4. Encode query to vector
5. FAISS search for similar passages
6. Filter by minimum similarity threshold (0.35)
7. Build prompt with top-6 results
8. Call AWS Bedrock API
9. Parse response
10. Display answer with citations
11. Add to conversation history
12. Ready for next question

---

## 📊 Performance Breakdown

| Operation | Time | Percentage |
|-----------|------|------------|
| Encode query | 50ms | 1% |
| FAISS search | 5ms | <1% |
| Build prompt | 10ms | <1% |
| **AWS Bedrock API** | **2-5s** | **98%** |
| Display response | 50ms | 1% |

**Note:** AWS Bedrock API is the slowest component as Claude generates text token-by-token on remote GPUs.

---

## ⚙️ Important Constants

| Parameter | Value | Description |
|-----------|-------|-------------|
| **Embedding dimensions** | 384 | Vector size from SentenceTransformer |
| **Top-k results** | 6 | Number of retrieved policy clauses |
| **Min similarity** | 0.35 | Confidence threshold for relevance |
| **Temperature** | 0.2 | Creativity control (low = consistent) |
| **Top-p** | 0.9 | Response diversity |
| **Max tokens** | 4096 | Maximum response length |
| **Model** | `all-MiniLM-L6-v2` | Embedding model |
| **LLM** | `claude-3-5-sonnet-20241022-v2:0` | AWS Bedrock model |
| **FAISS index** | `IndexFlatIP` | Flat inner product index |

---

## 🔒 Responsible AI Rules

- ✅ Responds **only** using official RMIT policies
- ✅ Adds **citations** to every factual statement
- ✅ Politely **refuses** unrelated or personal queries
- ✅ Displays a clear **disclaimer** for transparency
- ✅ No hallucination - only answers from indexed policies

---

## 🧠 Example Queries

Try asking:
- "What counts as plagiarism?"
- "How do I apply for an assessment extension?"
- "How do I appeal a final course result?"
- "What happens if I fail the same course twice?"
- "What is the academic integrity policy?"
- "Can I defer my exam?"

---

## 🧪 Testing

Once the app is running, go to:
```
http://localhost:8501
```

Test various queries and verify:
- Each response includes relevant policy citations
- Citations format: `[Policy Name, Clause X, Section Y]`
- System refuses to answer questions outside of policy scope

---

## 🌐 Hosted Application

The chatbot is also available online:
```
https://chatbot-claude.streamlit.app/
```
---

## 📚 Additional Resources

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [FAISS Documentation](https://github.com/facebookresearch/faiss)
- [Sentence Transformers](https://www.sbert.net/)
- [Streamlit Documentation](https://docs.streamlit.io/)

---

## 👥 Authors

- **Wong Hon Jun** – s4060180  
- **Abeda Sultana Khanam** – s4187699  
- **Turin Sayed** – s4092247  

---

## 🪪 License

This project is for **educational purposes** under RMIT's Academic Use Policy.  
Do not redistribute or deploy publicly with institutional credentials.

---
