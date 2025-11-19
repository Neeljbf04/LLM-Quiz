
# 📘 **LLM Quiz Solver**

This project implements a fully automated quiz-solving agent for the **IITM LLM Analysis Quiz**.
It loads quiz tasks from the official quiz server, extracts questions, uses an LLM to solve them, and submits answers back to the quiz API.

The project includes:

* A FastAPI backend
* Browser automation using Playwright
* A lightweight LLM Orchestrator
* Optional Groq API integration (via `GROQ_API_KEY`)

This repository is submitted as part of the **TDS LLM Analysis Project**.

---

## 🚀 Features

* Fetches quiz pages dynamically using **Playwright**
* Extracts questions automatically
* Handles multi-step quizzes with redirects
* Uses **Groq LLM** (or deterministic fallback) to generate answers
* Submits answers to the official quiz API
* Retries and continues until quiz ends
* Supports deployment (Render recommended)

---

## 🏗 Project Structure

```
LLM_Quiz/
├── server.py
├── orchestrator.py
├── modules/
│   ├── llm_engine.py
│   ├── data_fetch.py
│   ├── data_clean.py
│   ├── visualize.py
│   ├── utils.py
│   └── schemas.py
├── requirements.txt
├── LICENSE
├── README.md
└── .env   (not committed)
```

---

## 🔧 Installation

### 1. Clone the repo

```bash
git clone https://github.com/<your-username>/LLM_Quiz.git
cd LLM_Quiz
```

### 2. Create a virtual environment

```bash
python -m venv llm
source llm/bin/activate      # Linux/macOS
llm\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Playwright browser

```bash
playwright install
```

---

## 🔐 Environment Variables

Create a file named `.env`:

```
SECRET_STRING=panda
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.1-8b-instant
```

**SECRET_STRING must match what you submit in the Google Form.**

---

## ▶️ Running the Server

```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

Open the API docs:

```
http://localhost:8000/docs
```

---

## 🧪 API Endpoints

### **POST /solve**

Submit and solve a quiz task:

```json
{
  "email": "your@email",
  "secret": "panda",
  "url": "https://tds-llm-analysis.s-anand.net/demo"
}
```

Example:

```bash
curl -X POST "http://localhost:8000/solve" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email",
    "secret": "panda",
    "url": "https://tds-llm-analysis.s-anand.net/demo"
  }'
```

---

## 🌐 Deployment (Render)

Deploy on Render with:

* Runtime: **Python 3.10+**
* Start command:

  ```
  uvicorn server:app --host 0.0.0.0 --port $PORT
  ```
* Add environment variables in Render dashboard:

  * `SECRET_STRING`
  * `GROQ_API_KEY`
  * `GROQ_MODEL`

After deploying, your live endpoint will be:

```
https://your-app-name.onrender.com/solve
```

This is the URL you submit in the IITM form.

---

## 📜 License

This project is released under the **MIT License**.
See `LICENSE` file for details.

---

## 👨‍🎓 Author

**Neel Patel**
IIT Madras BS in Data Science & Applications

---

## ✔️ Notes for Evaluators

* This backend fully supports multi-step quiz workflows.
* A safe deterministic fallback is available when no LLM key is configured.
* The system is secure against prompt injection attempts defined in guidelines.
