# QuestionMind AI - Similar Question Finder & Auto-Tagging

An AI-powered web application that helps students and educators find semantically similar study questions and automatically categorizes them. The system uses a local, open-source embedding model to perform context-aware matching and zero-shot tag suggestions.

## 📋 Selected Assignment Option
**Option B**: Similar Question Finder with Auto-Tagging

---

## 🛠️ Technology Stack
- **Backend Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python)
- **AI/ML Libraries**:
  - [Sentence-Transformers](https://www.sbert.net/) (for text embeddings)
  - [Hugging Face Transformers](https://huggingface.co/docs/transformers/index) (Local execution)
  - [NumPy](https://numpy.org/) (for vector mathematics & cosine similarity)
  - [PyTorch](https://pytorch.org/) (Model inference backend)
- **Database & ORM**:
  - [SQLAlchemy](https://www.sqlalchemy.org/) (Object Relational Mapper)
  - [SQLite](https://www.sqlite.org/index.html) (Local development) / [PostgreSQL](https://www.postgresql.org/) (Automatic fallback for production)
- **Security**:
  - [PyJWT](https://pyjwt.readthedocs.io/) (JSON Web Tokens)
  - [Bcrypt](https://pypi.org/project/bcrypt/) (Secure password hashing)
- **Frontend SPA**:
  - **Structure**: Semantic HTML5
  - **Styling**: Vanilla CSS3 (Glassmorphism layout, vibrant neon highlights, dark theme)
  - **Logic**: Vanilla JavaScript ES6 (Asynchronous API fetch orchestration, debounced keystroke listeners)

---

## 🤖 AI/ML Implementation Details

The core intelligence of this application runs **100% locally** using open-source packages. No external paid APIs (such as OpenAI, Gemini, or Claude) are used.

### 1. Local Sentence Embedding Model
The application loads the `all-MiniLM-L6-v2` model from `sentence-transformers` on startup. 
- **Model Size**: ~120MB (runs extremely fast on standard CPUs).
- **Output**: Converts any input text (a study question or a tag name/description) into a **384-dimensional floating-point vector** representing its semantic meaning.

### 2. Auto-Tagging Recommendation System
When you enter a question, the backend generates its embedding vector. It then retrieves the embeddings of all registered subject tags (system and custom user-created tags) from the database and calculates the **cosine similarity** between the question vector ($V_q$) and each tag vector ($V_t$):

$$\text{Similarity}(V_q, V_t) = \frac{V_q \cdot V_t}{\|V_q\| \|V_t\|}$$

- Tags with a similarity score above a tuned threshold (default `0.32`) are automatically assigned.
- If no tags meet the threshold, the system defaults to recommending the single highest-matching tag (provided it is above `0.22`).
- The frontend calls this endpoint in real-time as you type, rendering percentage match indicator bars.

### 3. Custom Tag Indexing
When a user adds a new custom tag with a name and description, the backend generates an embedding for that tag combining both the name and description. The vector is saved to the database. New questions are instantly compared against this new vector, enabling **dynamic, immediate AI zero-shot categorization** for new subjects!

### 4. Semantic Similarity Search & Duplication Finder
Instead of basic keyword matches, the system performs a vector search. The search query is embedded and compared against all stored question vectors in the database. Results are sorted by similarity score descending, showing the user matches like "How to sort a list in Python?" when searching for "python sorting array method".

---

## 🚀 Local Setup Instructions

### Prerequisites
- Python 3.10 or higher installed on your system.
- Git (optional, for cloning).

### Steps

1. **Clone or Extract the Repository**
   ```bash
   git clone <repository-link>
   cd SimilarQuestionFinder
   ```

2. **Set up Virtual Environment**
   Create a virtual environment and activate it:
   - **Windows (Command Prompt / PowerShell)**:
     ```powershell
     python -m venv Backend/venv
     .\Backend\venv\Scripts\activate
     ```
   - **macOS / Linux**:
     ```bash
     python3 -m venv Backend/venv
     source Backend/venv/bin/activate
     ```

3. **Install Dependencies**
   Install the required packages listed in `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: On the first run, the backend will automatically download the `all-MiniLM-L6-v2` embedding model (~120MB) from Hugging Face and store it in your local cache.*

4. **Run the Application**
   Navigate to the `Backend` folder and start the FastAPI web server using Uvicorn:
   ```bash
   cd Backend
   python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
   ```

5. **Access the App**
   Open your browser and navigate to:
   - **Web Interface**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
   - **Interactive API Documentation (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
