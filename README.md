# QuestionMind AI - Similar Question Finder & Auto-Tagging

An AI-powered web application that helps students and educators find semantically similar study questions and automatically categorizes them. The system uses a local, open-source machine learning model to perform context-aware matching and zero-shot tag suggestions.

## 📋 Selected Assignment Option
**Option B**: Similar Question Finder with Auto-Tagging

---

## 🛠️ Technology Stack
- **Backend Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python)
- **AI/ML Libraries**:
  - [Scikit-Learn](https://scikit-learn.org/) (for text feature extraction, TF-IDF vectorization, and tokenization)
  - [NumPy](https://numpy.org/) (for vector mathematics & cosine similarity calculations)
  - [SciPy](https://scipy.org/) (for optimized vector arrays)
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

To ensure production stability on constrained memory environments (such as Render's 512MB RAM free tier), we migrated from standard PyTorch models to an optimized **Scikit-Learn TF-IDF vector embedding engine**. This reduced active memory consumption from 600MB+ to **less than 40MB**, with zero cold-start delay.

### 1. Curated Academic Vocabulary Map
The AI service utilizes a rich, custom academic vocabulary of common concepts spanning:
- Mathematics (calculus, derivative, limit, equation, etc.)
- Physics (gravity, force, quantum, speed, light, etc.)
- Chemistry (compound, periodic, atom, reaction, bond, etc.)
- Biology (photosynthesis, cell, mitosis, dna, organism, etc.)
- Computer Science (algorithm, compile, react, coding, class, etc.)
- Literature & History (poetry, novel, empire, revolution, author, etc.)
- Machine Learning (backpropagation, weights, neural, dataset, model, etc.)

This vocabulary acts as a **semantic feature coordinate system** of size 206, mapping every query or tag to a dense multi-dimensional concept vector.

### 2. Auto-Tagging Recommendation System
When a question is entered, the backend computes its TF-IDF vector representation $V_q$. It retrieves the vectors of all registered tags $V_t$ and computes the **cosine similarity** between them:

$$\text{Similarity}(V_q, V_t) = \frac{V_q \cdot V_t}{\|V_q\| \|V_t\|}$$

- **Hybrid Keyword Boosting**: To combine neural vector similarity with exact keyword matching precision, the backend scans questions for relevant stems. If math-related keywords appear in a question, the Mathematics tag score receives an automatic boost.
- Tags above a threshold are assigned. If none exceed the threshold, the single best match is assigned as a fallback.
- User-created custom tags (e.g., "Web Development") are instantly embedded combining their name and description, enabling **zero-shot categorization for new custom subjects on the fly**!

### 3. Semantic Similarity Search & Duplication Finder
The search query is converted into a vector and compared against all stored question vectors in the database. Stored vectors are pre-computed and cached in the database for instant lookup. Results are returned sorted by similarity score descending, matching concepts (e.g., matching "weight updates" in neural networks to "backpropagation").

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
   Install the lightweight packages listed in `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

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
