import json
import os
import sys

# Limit PyTorch memory usage and threads to fit in Render's 512MB limit
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

from contextlib import asynccontextmanager
from typing import List, Optional

# Ensure Backend directory is in Python path for local package imports
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

import models
import schemas
import auth
from database import engine, get_db, SessionLocal
from ai_service import AIService

# Initialize AI Service
ai_service = AIService()

def init_tags(db: Session):
    """Pre-populate system tags and generate their embeddings on startup."""
    default_tags = {
        "Mathematics": "Study of numbers, formulas, structures, shapes, and spaces.",
        "Physics": "Study of matter, energy, motion, force, and physical laws.",
        "Chemistry": "Study of elements, compounds, chemical reactions, and properties.",
        "Biology": "Study of living organisms, cells, evolution, and ecosystems.",
        "Computer Science": "Study of algorithms, coding, software, databases, and AI.",
        "History": "Study of past events, civilizations, societies, and historical figures.",
        "Literature": "Study of written works, prose, poetry, analysis, and language arts."
    }
    
    for tag_name, tag_desc in default_tags.items():
        # Check if tag already exists
        existing_tag = db.query(models.Tag).filter(models.Tag.name == tag_name).first()
        if not existing_tag:
            print(f"Initializing default tag: {tag_name}")
            # Create tag
            new_tag = models.Tag(name=tag_name, description=tag_desc, is_system=True)
            db.add(new_tag)
            db.commit()
            db.refresh(new_tag)
            
            # Generate and save embedding
            # Embedding is based on the tag name and description combined for rich semantics
            combined_text = f"{tag_name}: {tag_desc}"
            emb_vector = ai_service.get_embedding(combined_text)
            
            tag_emb = models.TagEmbedding(
                tag_id=new_tag.id,
                embedding=json.dumps(emb_vector)
            )
            db.add(tag_emb)
            db.commit()

def calculate_keyword_boost(text: str, tag_name: str, tag_desc: str) -> float:
    """Calculate keyword boost for tag recommendations to combine keyword precision with semantic embeddings."""
    text_lower = text.lower()
    tag_name_lower = tag_name.lower()
    
    # Specific keywords related to each subject tag
    tag_stems = {
        "mathematics": ["math", "calculus", "algebra", "derivative", "equation", "formula", "arithmetic", "geometry", "integral", "limit", "numbers", "fraction", "matrix"],
        "physics": ["physics", "gravity", "energy", "motion", "force", "speed", "velocity", "mechanics", "thermodynamics", "quantum", "relativity", "light"],
        "chemistry": ["chemistry", "chemical", "molecule", "atom", "reaction", "periodic table", "elements", "compound", "bond", "acid", "base"],
        "biology": ["biology", "photosynthesis", "organism", "cell", "evolution", "ecosystem", "dna", "gene", "plant", "animal", "specie", "bacteria"],
        "computer science": ["computer", "code", "coding", "programming", "software", "algorithm", "database", "python", "javascript", "react", "html", "css", "java", "c++", "query", "frontend", "backend"],
        "history": ["history", "civilization", "historical", "ancient", "war", "century", "empire", "revolution", "president", "reign", "archaeology"],
        "literature": ["literature", "poetry", "prose", "novel", "author", "write", "book", "playwright", "shakespeare", "poem", "essay", "literary"]
    }
    
    boost = 0.0
    
    # Direct tag name check
    if tag_name_lower in text_lower:
        boost += 0.25
        
    # Check manual stems
    stems = tag_stems.get(tag_name_lower, [])
    for stem in stems:
        if stem in text_lower:
            boost += 0.22
            break  # add boost once
            
    # For custom user tags, check if the tag name words appear in the question
    if not stems: # custom tag
        words = [w.strip() for w in tag_name_lower.split() if len(w.strip()) >= 3]
        for w in words:
            if w in text_lower:
                boost += 0.20
                break
                
        # Also check description words for custom tag
        if tag_desc:
            desc_lower = tag_desc.lower()
            desc_words = [w.strip(".,;:()\"'") for w in desc_lower.split()]
            desc_words = [w for w in desc_words if len(w) >= 5 and w not in ["about", "their", "study", "other", "using", "which", "would", "these", "those"]]
            for dw in desc_words:
                if dw in text_lower:
                    boost += 0.15
                    break
                
    return boost

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("Starting up: Initializing database and pre-populating tags...")
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        init_tags(db)
    except Exception as e:
        print(f"Error initializing database tags: {e}")
    finally:
        db.close()
    yield
    # Shutdown logic
    print("Shutting down...")

app = FastAPI(
    title="Similar Question Finder API",
    description="Local AI-powered question similarity and auto-tagging system.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# AUTH ENDPOINTS
# ==========================================

@app.post("/api/auth/signup", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(models.User).filter(models.User.username == user_in.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Hash password and create user
    hashed_pw = auth.get_password_hash(user_in.password)
    db_user = models.User(username=user_in.username, hashed_password=hashed_pw)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/api/auth/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Find user
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create JWT token
    access_token = auth.create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me", response_model=schemas.UserResponse)
def get_current_user_profile(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

# ==========================================
# TAG ENDPOINTS
# ==========================================

@app.get("/api/tags", response_model=List[schemas.TagResponse])
def list_tags(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return db.query(models.Tag).all()

@app.post("/api/tags", response_model=schemas.TagResponse, status_code=status.HTTP_201_CREATED)
def create_tag(tag_in: schemas.TagCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    # Clean tag name
    cleaned_name = tag_in.name.strip()
    
    # Check if duplicate name
    existing_tag = db.query(models.Tag).filter(models.Tag.name.ilike(cleaned_name)).first()
    if existing_tag:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tag '{cleaned_name}' already exists"
        )
    
    # Create tag
    new_tag = models.Tag(
        name=cleaned_name, 
        description=tag_in.description, 
        is_system=False
    )
    db.add(new_tag)
    db.commit()
    db.refresh(new_tag)
    
    # Compute tag embedding
    combined_text = f"{new_tag.name}: {new_tag.description or ''}"
    emb_vector = ai_service.get_embedding(combined_text)
    
    tag_emb = models.TagEmbedding(
        tag_id=new_tag.id,
        embedding=json.dumps(emb_vector)
    )
    db.add(tag_emb)
    db.commit()
    
    return new_tag

# ==========================================
# QUESTION ANALYSES AND OPERATIONS
# ==========================================

@app.post("/api/questions/analyze", response_model=schemas.QuestionAnalyzeResponse)
def analyze_question(
    payload: schemas.QuestionCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    question_text = payload.text.strip()
    if not question_text:
        raise HTTPException(status_code=400, detail="Question text cannot be empty")
        
    # 1. Compute Question Embedding
    q_emb = ai_service.get_embedding(question_text)
    
    # 2. Compute similarities against all tags
    suggested_tags = []
    tags = db.query(models.Tag).all()
    
    for tag in tags:
        if tag.embedding:
            tag_vector = json.loads(tag.embedding.embedding)
            sim = ai_service.calculate_cosine_similarity(q_emb, tag_vector)
            boost = calculate_keyword_boost(question_text, tag.name, tag.description or "")
            final_score = min(0.99, sim + boost)
            
            # Soft threshold: we will return all tags with their scores, 
            # but let the frontend handle showing high-match scores.
            suggested_tags.append(
                schemas.TagAnalysisItem(
                    tag_id=tag.id,
                    name=tag.name,
                    similarity_score=final_score
                )
            )
    
    # Sort tags by similarity score descending
    suggested_tags.sort(key=lambda x: x.similarity_score, reverse=True)
    
    # 3. Compute similarities against all existing questions (Semantic Search)
    similar_questions = []
    questions = db.query(models.Question).all()
    
    for q in questions:
        if q.embedding:
            q_vector = json.loads(q.embedding.embedding)
            sim = ai_service.calculate_cosine_similarity(q_emb, q_vector)
            
            # map relationships
            tag_schemas = [
                schemas.TagResponse(
                    id=t.id, 
                    name=t.name, 
                    description=t.description, 
                    is_system=t.is_system
                ) for t in q.tags
            ]
            
            similar_questions.append(
                schemas.SimilarityResult(
                    id=q.id,
                    text=q.text,
                    similarity_score=sim,
                    user_id=q.user_id,
                    username=q.user.username,
                    created_at=q.created_at,
                    tags=tag_schemas
                )
            )
            
    # Sort similar questions by similarity score descending
    similar_questions.sort(key=lambda x: x.similarity_score, reverse=True)
    
    # Limit to top 5 similar questions for the preview panel
    top_similar = similar_questions[:5]
    
    return schemas.QuestionAnalyzeResponse(
        text=question_text,
        suggested_tags=suggested_tags,
        similar_questions=top_similar
    )

@app.post("/api/questions", response_model=schemas.QuestionResponse, status_code=status.HTTP_201_CREATED)
def create_question(
    payload: schemas.QuestionCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    question_text = payload.text.strip()
    if not question_text:
        raise HTTPException(status_code=400, detail="Question text cannot be empty")
        
    # Calculate embedding
    q_emb = ai_service.get_embedding(question_text)
    
    # Find tags
    selected_tags = []
    
    if payload.tags:
        # User explicitly supplied tags
        for t_name in payload.tags:
            tag_obj = db.query(models.Tag).filter(models.Tag.name.ilike(t_name.strip())).first()
            if tag_obj:
                selected_tags.append(tag_obj)
    else:
        # Auto-tagging: Find tags where similarity is above 0.32.
        # If none, we take the single highest-scoring tag if it is above 0.22.
        tags = db.query(models.Tag).all()
        scored_tags = []
        for tag in tags:
            if tag.embedding:
                tag_vector = json.loads(tag.embedding.embedding)
                sim = ai_service.calculate_cosine_similarity(q_emb, tag_vector)
                boost = calculate_keyword_boost(question_text, tag.name, tag.description or "")
                final_score = min(0.99, sim + boost)
                scored_tags.append((tag, final_score))
        
        # Sort by similarity descending
        scored_tags.sort(key=lambda x: x[1], reverse=True)
        
        # Add tags above threshold
        for tag, sim in scored_tags:
            if sim >= 0.32:
                selected_tags.append(tag)
        
        # Fallback: if no tag is above 0.32, add the single best match if it's above 0.22
        if not selected_tags and scored_tags:
            best_tag, best_sim = scored_tags[0]
            if best_sim >= 0.22:
                selected_tags.append(best_tag)
                
    # Create question
    new_question = models.Question(
        text=question_text,
        user_id=current_user.id,
        tags=selected_tags
    )
    db.add(new_question)
    db.commit()
    db.refresh(new_question)
    
    # Save embedding
    q_emb_obj = models.QuestionEmbedding(
        question_id=new_question.id,
        embedding=json.dumps(q_emb)
    )
    db.add(q_emb_obj)
    db.commit()
    
    # Return formatted response
    tag_responses = [
        schemas.TagResponse(
            id=t.id, 
            name=t.name, 
            description=t.description, 
            is_system=t.is_system
        ) for t in new_question.tags
    ]
    
    return schemas.QuestionResponse(
        id=new_question.id,
        text=new_question.text,
        user_id=new_question.user_id,
        username=current_user.username,
        created_at=new_question.created_at,
        tags=tag_responses
    )

@app.get("/api/questions", response_model=List[schemas.QuestionResponse])
def list_questions(
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    questions = db.query(models.Question).order_by(models.Question.created_at.desc()).all()
    
    results = []
    for q in questions:
        tag_responses = [
            schemas.TagResponse(
                id=t.id, 
                name=t.name, 
                description=t.description, 
                is_system=t.is_system
            ) for t in q.tags
        ]
        results.append(
            schemas.QuestionResponse(
                id=q.id,
                text=q.text,
                user_id=q.user_id,
                username=q.user.username,
                created_at=q.created_at,
                tags=tag_responses
            )
        )
    return results

@app.get("/api/questions/search", response_model=List[schemas.SimilarityResult])
def search_similar_questions(
    query: str = Query(..., min_length=2),
    threshold: float = Query(0.35, ge=0.0, le=1.0),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    query_text = query.strip()
    if not query_text:
        raise HTTPException(status_code=400, detail="Search query cannot be empty")
        
    # Generate query embedding
    q_emb = ai_service.get_embedding(query_text)
    
    # Compute similarity against all questions
    results = []
    questions = db.query(models.Question).all()
    
    for q in questions:
        if q.embedding:
            q_vector = json.loads(q.embedding.embedding)
            sim = ai_service.calculate_cosine_similarity(q_emb, q_vector)
            
            if sim >= threshold:
                tag_responses = [
                    schemas.TagResponse(
                        id=t.id, 
                        name=t.name, 
                        description=t.description, 
                        is_system=t.is_system
                    ) for t in q.tags
                ]
                results.append(
                    schemas.SimilarityResult(
                        id=q.id,
                        text=q.text,
                        similarity_score=sim,
                        user_id=q.user_id,
                        username=q.user.username,
                        created_at=q.created_at,
                        tags=tag_responses
                    )
                )
                
    # Sort by similarity score descending
    results.sort(key=lambda x: x.similarity_score, reverse=True)
    
    return results[:limit]

@app.delete("/api/questions/{question_id}", status_code=status.HTTP_200_OK)
def delete_question(
    question_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
        
    # Check ownership
    if question.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to delete this question"
        )
        
    db.delete(question)
    db.commit()
    return {"message": "Question successfully deleted"}

# ==========================================
# STATIC FILES SERVING & SPA FALLBACK
# ==========================================

# Resolve Frontend folder relative to this main.py file location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "Frontend"))

# Mount Frontend static resources
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
def read_root():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/{catchall:path}")
def read_index(catchall: str):
    # If the path exists under /api, return 404, else serve the SPA index file
    if catchall.startswith("api") or catchall.startswith("docs") or catchall.startswith("openapi.json"):
        raise HTTPException(status_code=404, detail="Not Found")
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
