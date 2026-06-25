/**
 * QuestionMind AI - Frontend SPA Engine
 */

// API Base URL (empty string because we serve it from the same host in production/local)
const API_BASE = "";

// Global App State
const state = {
    token: localStorage.getItem("token") || null,
    user: null,
    activeSection: "dashboard",
    tags: [],
    questions: [],
    analysisTimeout: null,
    selectedAnalysisTags: new Set()
};

// UI Elements Cache
const el = {
    authView: document.getElementById("auth-view"),
    appView: document.getElementById("app-view"),
    loginForm: document.getElementById("login-form"),
    signupForm: document.getElementById("signup-form"),
    goToSignup: document.getElementById("go-to-signup"),
    goToLogin: document.getElementById("go-to-login"),
    
    // Sidebar & Navigation
    navLinks: document.querySelectorAll(".nav-link"),
    userDisplayName: document.getElementById("user-display-name"),
    logoutBtn: document.getElementById("logout-btn"),
    sectionTitle: document.getElementById("current-section-title"),
    sectionDesc: document.getElementById("current-section-desc"),
    
    // Dashboard Section
    statTotalQuestions: document.getElementById("stat-total-questions"),
    statTotalTags: document.getElementById("stat-total-tags"),
    questionsFeed: document.getElementById("questions-feed"),
    recentQuestionsLoader: document.getElementById("recent-questions-loader"),
    emptyQuestionsMsg: document.getElementById("empty-questions-msg"),
    
    // Add Question Section
    questionTextarea: document.getElementById("question-textarea"),
    analyzeBtn: document.getElementById("analyze-btn"),
    submitQuestionBtn: document.getElementById("submit-question-btn"),
    aiTagsLoader: document.getElementById("ai-tags-loader"),
    aiTagsDefaultMsg: document.getElementById("ai-tags-default-msg"),
    suggestedTagsContainer: document.getElementById("suggested-tags-container"),
    aiSimilarityLoader: document.getElementById("ai-similarity-loader"),
    aiSimilarityDefaultMsg: document.getElementById("ai-similarity-default-msg"),
    similarQuestionsContainer: document.getElementById("similar-questions-container"),
    
    // Search Section
    searchQueryInput: document.getElementById("search-query-input"),
    clearSearchBtn: document.getElementById("clear-search-btn"),
    searchBtn: document.getElementById("search-btn"),
    thresholdSlider: document.getElementById("threshold-slider"),
    thresholdVal: document.getElementById("threshold-val"),
    searchResultsLoader: document.getElementById("search-results-loader"),
    searchEmptyState: document.getElementById("search-empty-state"),
    searchResultsFeed: document.getElementById("search-results-feed"),
    searchResultsCount: document.getElementById("search-results-count"),
    
    // Tags Section
    createTagForm: document.getElementById("create-tag-form"),
    tagNameInput: document.getElementById("tag-name-input"),
    tagDescInput: document.getElementById("tag-desc-input"),
    tagsListLoader: document.getElementById("tags-list-loader"),
    tagsGrid: document.getElementById("tags-grid"),
    
    // Toasts
    toastContainer: document.getElementById("toast-container")
};

/* ==========================================================================
   TOAST NOTIFICATION UTILS
   ========================================================================== */
function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    
    let iconClass = "fa-circle-info";
    if (type === "success") iconClass = "fa-circle-check";
    if (type === "error") iconClass = "fa-circle-exclamation";
    if (type === "warning") iconClass = "fa-triangle-exclamation";
    
    toast.innerHTML = `
        <i class="fa-solid ${iconClass}"></i>
        <div class="toast-content">${message}</div>
        <button class="toast-close"><i class="fa-solid fa-xmark"></i></button>
    `;
    
    el.toastContainer.appendChild(toast);
    
    // Close button event
    toast.querySelector(".toast-close").addEventListener("click", () => {
        removeToast(toast);
    });
    
    // Auto-remove after 4 seconds
    setTimeout(() => {
        removeToast(toast);
    }, 4000);
}

function removeToast(toast) {
    toast.style.animation = "toastSlideOut 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards";
    toast.addEventListener("animationend", () => {
        toast.remove();
    });
}

/* ==========================================================================
   API FETCH WRAPPER
   ========================================================================== */
async function apiFetch(endpoint, options = {}) {
    const headers = {};
    
    // Add content type if sending body and not Form Data
    if (options.body && !(options.body instanceof FormData)) {
        headers["Content-Type"] = "application/json";
    }
    
    // Inject Authorization header if token exists
    if (state.token) {
        headers["Authorization"] = `Bearer ${state.token}`;
    }
    
    const config = {
        ...options,
        headers: {
            ...headers,
            ...options.headers
        }
    };
    
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, config);
        
        // Handle 401 Unauthenticated / Token Expiry
        if (response.status === 401) {
            if (state.token) {
                showToast("Session expired. Please log in again.", "warning");
                logout();
            }
            throw new Error("Unauthorized");
        }
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || "Something went wrong");
        }
        
        return data;
    } catch (error) {
        console.error(`API Error fetching ${endpoint}:`, error);
        throw error;
    }
}

/* ==========================================================================
   AUTHENTICATION LOGIC
   ========================================================================== */
async function login(username, password) {
    try {
        // OAuth2 Password Request Form requires x-www-form-urlencoded
        const formData = new URLSearchParams();
        formData.append("username", username);
        formData.append("password", password);
        
        const result = await apiFetch("/api/auth/login", {
            method: "POST",
            body: formData,
            headers: {
                "Content-Type": "application/x-www-form-urlencoded"
            }
        });
        
        state.token = result.access_token;
        localStorage.setItem("token", result.access_token);
        
        showToast("Log in successful!", "success");
        await checkAuth();
    } catch (error) {
        showToast(error.message, "error");
    }
}

async function signup(username, password) {
    try {
        await apiFetch("/api/auth/signup", {
            method: "POST",
            body: JSON.stringify({ username, password })
        });
        
        showToast("Sign up successful! Logging you in...", "success");
        // Automatically login
        await login(username, password);
    } catch (error) {
        showToast(error.message, "error");
    }
}

function logout() {
    state.token = null;
    state.user = null;
    localStorage.removeItem("token");
    
    el.appView.classList.add("hidden");
    el.authView.classList.remove("hidden");
    el.loginForm.reset();
    el.signupForm.reset();
    showToast("Logged out successfully.", "info");
}

async function checkAuth() {
    if (!state.token) {
        el.authView.classList.remove("hidden");
        el.appView.classList.add("hidden");
        return;
    }
    
    try {
        const user = await apiFetch("/api/auth/me");
        state.user = user;
        el.userDisplayName.textContent = user.username;
        
        el.authView.classList.add("hidden");
        el.appView.classList.remove("hidden");
        
        // Load initial app data
        await loadAppContext();
        switchSection(state.activeSection);
    } catch (error) {
        console.error("Auth check failed:", error);
        logout();
    }
}

/* ==========================================================================
   NAVIGATION & SCREEN ROUTING
   ========================================================================== */
function switchSection(sectionId) {
    state.activeSection = sectionId;
    
    // Toggle active link visual style
    el.navLinks.forEach(link => {
        if (link.dataset.section === sectionId) {
            link.classList.add("active");
        } else {
            link.classList.remove("active");
        }
    });
    
    // Hide all sections
    document.querySelectorAll(".app-section").forEach(sec => {
        sec.classList.add("hidden");
    });
    
    // Show selected section
    const targetSection = document.getElementById(`${sectionId}-section`);
    if (targetSection) {
        targetSection.classList.remove("hidden");
    }
    
    // Update Header titles
    updateHeaderTitles(sectionId);
    
    // Load context data based on section
    if (sectionId === "dashboard") {
        fetchDashboardData();
    } else if (sectionId === "tags") {
        fetchTagsCloud();
    } else if (sectionId === "add-question") {
        resetAddQuestionForm();
    } else if (sectionId === "search") {
        resetSearchForm();
    }
}

function updateHeaderTitles(sectionId) {
    const titles = {
        "dashboard": {
            title: "Dashboard",
            desc: "Quick statistics and recent study question activities."
        },
        "add-question": {
            title: "Ask Study Question",
            desc: "AI-powered auto-categorization and semantic duplicate finding."
        },
        "search": {
            title: "Semantic Similarity Search",
            desc: "Search study questions using natural language embeddings, not just keywords."
        },
        "tags": {
            title: "Categories & Embeddings",
            desc: "Manage default system tags and custom tags with automatic indexing."
        }
    };
    
    if (titles[sectionId]) {
        el.sectionTitle.textContent = titles[sectionId].title;
        el.sectionDesc.textContent = titles[sectionId].desc;
    }
}

/* ==========================================================================
   CORE CONTEXT LOADING
   ========================================================================== */
async function loadAppContext() {
    try {
        // Fetch all tags to keep local state up to date
        state.tags = await apiFetch("/api/tags");
    } catch (e) {
        console.error("Failed to load app context tags:", e);
    }
}

/* ==========================================================================
   DASHBOARD FUNCTIONS
   ========================================================================== */
async function fetchDashboardData() {
    el.recentQuestionsLoader.classList.remove("hidden");
    el.questionsFeed.classList.add("hidden");
    el.emptyQuestionsMsg.classList.add("hidden");
    
    try {
        const questions = await apiFetch("/api/questions");
        state.questions = questions;
        
        // Update stats counter
        el.statTotalQuestions.textContent = questions.length;
        
        // Reload tags count
        state.tags = await apiFetch("/api/tags");
        el.statTotalTags.textContent = state.tags.length;
        
        el.recentQuestionsLoader.classList.add("hidden");
        
        if (questions.length === 0) {
            el.emptyQuestionsMsg.classList.remove("hidden");
            el.questionsFeed.classList.add("hidden");
        } else {
            el.emptyQuestionsMsg.classList.add("hidden");
            el.questionsFeed.classList.remove("hidden");
            renderQuestionsList(questions, el.questionsFeed);
        }
    } catch (error) {
        el.recentQuestionsLoader.classList.add("hidden");
        showToast("Error loading dashboard content.", "error");
    }
}

function renderQuestionsList(questions, targetElement, showSimilarity = false) {
    targetElement.innerHTML = "";
    
    questions.forEach(q => {
        const card = document.createElement("div");
        card.className = "question-card";
        
        // Similarity score display if available
        let similarityBadge = "";
        if (showSimilarity && q.similarity_score !== undefined) {
            const pct = Math.round(q.similarity_score * 100);
            let ratingClass = "sim-badge-low";
            if (pct >= 75) ratingClass = "sim-badge-high";
            else if (pct >= 50) ratingClass = "sim-badge-med";
            
            similarityBadge = `
                <div class="card-similarity-badge ${ratingClass}">
                    <i class="fa-solid fa-chart-simple"></i>
                    <span>${pct}% Match</span>
                </div>
            `;
        }
        
        // Render tags
        const tagsHtml = q.tags.map(t => {
            const classType = t.is_system ? "tag-system" : "tag-custom";
            return `<span class="tag-badge ${classType}" title="${t.description || ''}">${t.name}</span>`;
        }).join("");
        
        // Date formatting
        const qDate = new Date(q.created_at);
        const dateStr = qDate.toLocaleDateString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
        
        // Delete action button if current user is owner
        let deleteBtn = "";
        if (state.user && q.user_id === state.user.id) {
            deleteBtn = `
                <button class="btn btn-sm btn-danger delete-q-btn" data-id="${q.id}" title="Delete Question">
                    <i class="fa-regular fa-trash-can"></i>
                </button>
            `;
        }
        
        card.innerHTML = `
            ${similarityBadge}
            <div class="q-header">
                <div class="q-meta">
                    <span class="q-author"><i class="fa-regular fa-circle-user"></i> ${q.username}</span>
                    <span class="q-date"><i class="fa-regular fa-calendar"></i> ${dateStr}</span>
                </div>
            </div>
            <div class="q-body">${escapeHtml(q.text)}</div>
            <div class="q-footer">
                <div class="q-tags">${tagsHtml || '<span class="text-dark" style="font-size:0.75rem">No tags</span>'}</div>
                <div class="card-actions">
                    <button class="btn btn-sm btn-outline find-similar-btn" data-text="${escapeAttribute(q.text)}" title="Find questions similar to this">
                        <i class="fa-solid fa-wand-magic-sparkles"></i> Compare
                    </button>
                    ${deleteBtn}
                </div>
            </div>
        `;
        
        targetElement.appendChild(card);
    });
    
    // Attach delete handlers
    targetElement.querySelectorAll(".delete-q-btn").forEach(btn => {
        btn.addEventListener("click", async (e) => {
            e.stopPropagation();
            const qId = btn.dataset.id;
            if (confirm("Are you sure you want to delete this question?")) {
                await deleteQuestion(qId);
            }
        });
    });
    
    // Attach compare handlers
    targetElement.querySelectorAll(".find-similar-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            e.stopPropagation();
            const text = btn.dataset.text;
            switchSection("search");
            el.searchQueryInput.value = text;
            triggerSemanticSearch();
        });
    });
}

async function deleteQuestion(id) {
    try {
        await apiFetch(`/api/questions/${id}`, { method: "DELETE" });
        showToast("Question deleted successfully", "success");
        // Reload current view
        if (state.activeSection === "dashboard") {
            await fetchDashboardData();
        } else if (state.activeSection === "search") {
            await triggerSemanticSearch();
        }
    } catch (e) {
        showToast(e.message, "error");
    }
}

/* ==========================================================================
   ADD QUESTION & AI ANALYSIS LOGIC
   ========================================================================== */
function resetAddQuestionForm() {
    el.questionTextarea.value = "";
    el.aiTagsLoader.classList.add("hidden");
    el.aiTagsDefaultMsg.classList.remove("hidden");
    el.suggestedTagsContainer.classList.add("hidden");
    el.suggestedTagsContainer.innerHTML = "";
    
    el.aiSimilarityLoader.classList.add("hidden");
    el.aiSimilarityDefaultMsg.classList.remove("hidden");
    el.similarQuestionsContainer.classList.add("hidden");
    el.similarQuestionsContainer.innerHTML = "";
    
    state.selectedAnalysisTags.clear();
}

async function runRealtimeAnalysis() {
    const text = el.questionTextarea.value.trim();
    if (text.length < 5) {
        // Reset analysis indicators
        el.aiTagsLoader.classList.add("hidden");
        el.aiTagsDefaultMsg.classList.remove("hidden");
        el.suggestedTagsContainer.classList.add("hidden");
        
        el.aiSimilarityLoader.classList.add("hidden");
        el.aiSimilarityDefaultMsg.classList.remove("hidden");
        el.similarQuestionsContainer.classList.add("hidden");
        return;
    }
    
    el.aiTagsLoader.classList.remove("hidden");
    el.aiTagsDefaultMsg.classList.add("hidden");
    el.suggestedTagsContainer.classList.add("hidden");
    
    el.aiSimilarityLoader.classList.remove("hidden");
    el.aiSimilarityDefaultMsg.classList.add("hidden");
    el.similarQuestionsContainer.classList.add("hidden");
    
    try {
        const analysis = await apiFetch("/api/questions/analyze", {
            method: "POST",
            body: JSON.stringify({ text })
        });
        
        // 1. Render Recommended Tags
        renderRecommendedTags(analysis.suggested_tags);
        
        // 2. Render Similar Questions sidebar
        renderSimilarQuestionsSidebar(analysis.similar_questions);
        
    } catch (error) {
        el.aiTagsLoader.classList.add("hidden");
        el.aiSimilarityLoader.classList.add("hidden");
        showToast("Error processing real-time AI suggestions.", "error");
    }
}

function renderRecommendedTags(suggestedTags) {
    el.aiTagsLoader.classList.add("hidden");
    el.suggestedTagsContainer.classList.remove("hidden");
    el.suggestedTagsContainer.innerHTML = "";
    
    if (!suggestedTags || suggestedTags.length === 0) {
        el.suggestedTagsContainer.innerHTML = `<p class="text-dark text-center" style="font-size:0.8rem">No category tags mapped.</p>`;
        return;
    }
    
    // Find system vs custom tags to look up their properties
    suggestedTags.forEach(st => {
        const tagObj = state.tags.find(t => t.id === st.tag_id);
        const isSystem = tagObj ? tagObj.is_system : true;
        const pct = Math.round(st.similarity_score * 100);
        
        // Pre-select tags with score >= 32%
        const isPreselected = st.similarity_score >= 0.32;
        if (isPreselected) {
            state.selectedAnalysisTags.add(st.name);
        }
        
        const isSelected = state.selectedAnalysisTags.has(st.name);
        
        const row = document.createElement("div");
        row.className = `suggested-tag-row ${isSelected ? 'selected' : ''}`;
        row.dataset.tagName = st.name;
        
        row.innerHTML = `
            <div class="tag-label-block">
                <div class="tag-checkbox"></div>
                <span class="tag-name-text">${st.name}</span>
                <span class="tag-badge ${isSystem ? 'tag-system' : 'tag-custom'}">${isSystem ? 'system' : 'custom'}</span>
            </div>
            <div class="tag-match-score">
                <span class="match-percentage">${pct}%</span>
                <div class="match-bar-track">
                    <div class="match-bar-fill" style="width: ${Math.max(5, pct)}%"></div>
                </div>
            </div>
        `;
        
        row.addEventListener("click", () => {
            if (state.selectedAnalysisTags.has(st.name)) {
                state.selectedAnalysisTags.delete(st.name);
                row.classList.remove("selected");
            } else {
                state.selectedAnalysisTags.add(st.name);
                row.classList.add("selected");
            }
        });
        
        el.suggestedTagsContainer.appendChild(row);
    });
}

function renderSimilarQuestionsSidebar(similarQuestions) {
    el.aiSimilarityLoader.classList.add("hidden");
    el.similarQuestionsContainer.classList.remove("hidden");
    el.similarQuestionsContainer.innerHTML = "";
    
    // Filter questions above 25% match for sanity
    const matches = similarQuestions.filter(q => q.similarity_score >= 0.25);
    
    if (matches.length === 0) {
        el.similarQuestionsContainer.innerHTML = `
            <div class="empty-state" style="padding:1rem">
                <i class="fa-solid fa-square-check" style="font-size: 1.5rem"></i>
                <p style="font-size:0.8rem">No potential duplicates found. Text appears unique!</p>
            </div>
        `;
        return;
    }
    
    matches.forEach(mq => {
        const pct = Math.round(mq.similarity_score * 100);
        let matchClass = "sim-low";
        if (pct >= 80) matchClass = "sim-high";
        else if (pct >= 60) matchClass = "sim-medium";
        
        const miniCard = document.createElement("div");
        miniCard.className = "similar-q-mini";
        
        miniCard.innerHTML = `
            <div class="sim-q-header">
                <span class="sim-q-badge ${matchClass}">${pct}% Similar</span>
                <span style="font-size: 0.7rem; color: var(--text-dark)"><i class="fa-regular fa-user"></i> ${mq.username}</span>
            </div>
            <div class="sim-q-text">${escapeHtml(mq.text)}</div>
        `;
        
        el.similarQuestionsContainer.appendChild(miniCard);
    });
}

async function submitQuestion() {
    const text = el.questionTextarea.value.trim();
    if (text.length < 5) {
        showToast("Please enter a question with at least 5 characters.", "warning");
        return;
    }
    
    el.submitQuestionBtn.disabled = true;
    el.submitQuestionBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Saving...`;
    
    try {
        const requestBody = {
            text: text,
            tags: Array.from(state.selectedAnalysisTags)
        };
        
        await apiFetch("/api/questions", {
            method: "POST",
            body: JSON.stringify(requestBody)
        });
        
        showToast("Question posted and categorized successfully!", "success");
        // Back to Dashboard
        switchSection("dashboard");
    } catch (e) {
        showToast(e.message, "error");
    } finally {
        el.submitQuestionBtn.disabled = false;
        el.submitQuestionBtn.innerHTML = `<i class="fa-solid fa-paper-plane"></i> <span>Submit to Database</span>`;
    }
}

/* ==========================================================================
   SEMANTIC SEARCH FUNCTIONS
   ========================================================================== */
function resetSearchForm() {
    el.searchQueryInput.value = "";
    el.clearSearchBtn.classList.add("hidden");
    el.searchEmptyState.classList.remove("hidden");
    el.searchResultsLoader.classList.add("hidden");
    el.searchResultsFeed.innerHTML = "";
    el.searchResultsCount.textContent = "Search Results";
}

async function triggerSemanticSearch() {
    const query = el.searchQueryInput.value.trim();
    if (!query) {
        showToast("Please enter a search query.", "warning");
        return;
    }
    
    el.searchEmptyState.classList.add("hidden");
    el.searchResultsLoader.classList.remove("hidden");
    el.searchResultsFeed.innerHTML = "";
    
    const sliderVal = parseFloat(el.thresholdSlider.value);
    const threshold = sliderVal / 100.0;
    
    try {
        const results = await apiFetch(`/api/questions/search?query=${encodeURIComponent(query)}&threshold=${threshold}`);
        
        el.searchResultsLoader.classList.add("hidden");
        el.searchResultsCount.textContent = `Search Results (${results.length} found)`;
        
        if (results.length === 0) {
            el.searchResultsFeed.innerHTML = `
                <div class="empty-state">
                    <i class="fa-solid fa-circle-exclamation"></i>
                    <p>No questions matched your query at the ${sliderVal}% threshold. Try lowering the threshold or refining the terms.</p>
                </div>
            `;
        } else {
            renderQuestionsList(results, el.searchResultsFeed, true);
        }
    } catch (error) {
        el.searchResultsLoader.classList.add("hidden");
        showToast("Error processing semantic search.", "error");
    }
}

/* ==========================================================================
   MANAGE TAGS FUNCTIONS
   ========================================================================== */
async function fetchTagsCloud() {
    el.tagsListLoader.classList.remove("hidden");
    el.tagsGrid.classList.add("hidden");
    
    try {
        state.tags = await apiFetch("/api/tags");
        el.tagsListLoader.classList.add("hidden");
        el.tagsGrid.classList.remove("hidden");
        
        renderTagsGrid(state.tags);
    } catch (e) {
        el.tagsListLoader.classList.add("hidden");
        showToast("Error fetching tags list.", "error");
    }
}

function renderTagsGrid(tags) {
    el.tagsGrid.innerHTML = "";
    
    if (tags.length === 0) {
        el.tagsGrid.innerHTML = `<p class="text-muted text-center" style="grid-column:1/-1">No tags registered in the system.</p>`;
        return;
    }
    
    tags.forEach(t => {
        const card = document.createElement("div");
        card.className = "tag-card";
        
        const badgeClass = t.is_system ? "bg-system" : "bg-custom";
        const label = t.is_system ? "system" : "custom";
        
        card.innerHTML = `
            <div class="tag-card-header">
                <h3>${t.name}</h3>
                <span class="tag-type-badge ${badgeClass}">${label}</span>
            </div>
            <p title="${t.description || ''}">${t.description || 'No description provided.'}</p>
        `;
        
        el.tagsGrid.appendChild(card);
    });
}

async function createCustomTag(name, description) {
    const submitBtn = el.createTagForm.querySelector("button[type='submit']");
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Embedding & Saving...`;
    
    try {
        await apiFetch("/api/tags", {
            method: "POST",
            body: JSON.stringify({ name, description })
        });
        
        showToast(`Tag '${name}' added and indexed successfully!`, "success");
        el.createTagForm.reset();
        await fetchTagsCloud();
    } catch (e) {
        showToast(e.message, "error");
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = `<i class="fa-solid fa-tag"></i> Generate Embedding & Save`;
    }
}

/* ==========================================================================
   EVENT LISTENERS & BINDINGS
   ========================================================================== */
function setupEventListeners() {
    // Auth Toggles
    el.goToSignup.addEventListener("click", (e) => {
        e.preventDefault();
        el.loginForm.classList.add("hidden");
        el.signupForm.classList.remove("hidden");
        document.getElementById("auth-subtitle").textContent = "Register a new profile and unlock local similarity models";
    });
    
    el.goToLogin.addEventListener("click", (e) => {
        e.preventDefault();
        el.signupForm.classList.add("hidden");
        el.loginForm.classList.remove("hidden");
        document.getElementById("auth-subtitle").textContent = "Discover duplicates and organize study questions with local AI";
    });
    
    // Auth Submissions
    el.loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const username = document.getElementById("login-username").value.trim();
        const password = document.getElementById("login-password").value;
        await login(username, password);
    });
    
    el.signupForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const username = document.getElementById("signup-username").value.trim();
        const password = document.getElementById("signup-password").value;
        await signup(username, password);
    });
    
    // Logout
    el.logoutBtn.addEventListener("click", () => {
        logout();
    });
    
    // Sidebar Navigation
    el.navLinks.forEach(link => {
        link.addEventListener("click", (e) => {
            e.preventDefault();
            const section = link.dataset.section;
            switchSection(section);
        });
    });
    
    // Dashboard shortcut links
    document.querySelectorAll(".nav-shortcut").forEach(btn => {
        btn.addEventListener("click", () => {
            const target = btn.dataset.target;
            switchSection(target);
        });
    });
    
    // Add Question: Debounced Real-time analysis
    el.questionTextarea.addEventListener("input", () => {
        clearTimeout(state.analysisTimeout);
        state.analysisTimeout = setTimeout(() => {
            runRealtimeAnalysis();
        }, 700);
    });
    
    el.analyzeBtn.addEventListener("click", () => {
        clearTimeout(state.analysisTimeout);
        runRealtimeAnalysis();
    });
    
    el.submitQuestionBtn.addEventListener("click", () => {
        submitQuestion();
    });
    
    // Search: Slider controls
    el.thresholdSlider.addEventListener("input", (e) => {
        el.thresholdVal.textContent = `${e.target.value}%`;
    });
    
    el.thresholdSlider.addEventListener("change", () => {
        if (el.searchQueryInput.value.trim()) {
            triggerSemanticSearch();
        }
    });
    
    // Search button click
    el.searchBtn.addEventListener("click", () => {
        triggerSemanticSearch();
    });
    
    el.searchQueryInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            triggerSemanticSearch();
        }
    });
    
    // Search Clear Button logic
    el.searchQueryInput.addEventListener("input", (e) => {
        if (e.target.value.length > 0) {
            el.clearSearchBtn.classList.remove("hidden");
        } else {
            el.clearSearchBtn.classList.add("hidden");
        }
    });
    
    el.clearSearchBtn.addEventListener("click", () => {
        resetSearchForm();
    });
    
    // Create Tag Submit
    el.createTagForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const name = el.tagNameInput.value.trim();
        const description = el.tagDescInput.value.trim();
        await createCustomTag(name, description);
    });
}

/* ==========================================================================
   XSS PREVENTION UTILS
   ========================================================================== */
function escapeHtml(str) {
    if (!str) return "";
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function escapeAttribute(str) {
    if (!str) return "";
    return str
        .replace(/&/g, "&amp;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

/* ==========================================================================
   INITIALIZATION
   ========================================================================== */
window.addEventListener("DOMContentLoaded", () => {
    setupEventListeners();
    checkAuth();
});
