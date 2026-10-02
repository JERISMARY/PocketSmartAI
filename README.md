# 💡 PocketSmart AI

> **Your Smart Budget & Recommendation Assistant**

PocketSmart AI is a GenAI-powered budget planning application built with **Python + FastAPI + Google Gemini**. It helps users plan home interiors, parties, and jewelry purchases within their budget — generating structured, AI-driven recommendations instantly.

---

## ✨ Features

- **🏠 Home Interior Planner** — Budget-aware recommendations for lighting, furniture, fans, curtains, and decor
- **🎉 Party & Event Planner** — Allocates budget across food, venue, decoration, entertainment, and accommodation
- **💎 Jewelry Planner** — Matches jewelry to occasion, style, and outfit (with optional image upload)
- **📸 Outfit Image Analysis** — Upload a photo; Gemini analyzes outfit colors and style to recommend matching jewelry
- **🔒 Secure Authentication** — JWT + bcrypt hashing; no plain-text passwords ever stored
- **📋 Recommendation History** — All plans saved per-user; full detail view with budget breakdown
- **💰 Budget Math in Python** — AI provides recommendations; Python calculates all totals
- **⚡ Quota Protection** — Disables submit button after click; detects and displays quota exceeded errors gracefully

---

## 🏗️ Architecture

```
USER INPUT → FastAPI Validation → Planner Service
         → Gemini Prompt → Gemini API
         → JSON Parsing → Pydantic Validation
         → Python Budget Math → Save History
         → Structured Response → Frontend Rendering
```

---

## 📁 Project Structure

```
PocketSmartAI/
├── app/
│   ├── main.py                  # FastAPI application entry
│   ├── config.py                # Centralized settings (from .env)
│   ├── routes/
│   │   ├── auth.py              # Register, Login, Logout
│   │   ├── home.py              # Index, Dashboard, Health
│   │   ├── home_planner.py      # Home Interior planner
│   │   ├── party.py             # Party/Event planner
│   │   ├── jewelry.py           # Jewelry planner (multimodal)
│   │   └── history.py           # Recommendation history
│   ├── services/
│   │   ├── gemini_utils.py      # Centralized Gemini service
│   │   └── recommendation_service.py  # Orchestration + budget calc
│   ├── models/
│   │   ├── user.py              # User schemas + in-memory store
│   │   ├── planner.py           # Planner input schemas
│   │   └── recommendation.py   # Result schemas + history store
│   ├── auth/
│   │   ├── jwt.py               # JWT creation/decoding
│   │   └── security.py          # bcrypt hashing
│   ├── templates/               # Jinja2 HTML templates
│   └── static/                  # CSS + JS
├── tests/
│   └── test_app.py              # Full test suite
├── .env                         # Your secrets (never commit)
├── .env.example                 # Template without secrets
├── requirements.txt
├── run.py                       # Start server with python run.py
└── README.md
```

---

## 🛠️ Technologies

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, FastAPI, Uvicorn |
| AI | Google Gemini (via `google-generativeai`) |
| Auth | JWT (`python-jose`), bcrypt (`passlib`) |
| Templates | Jinja2 |
| Validation | Pydantic v2 |
| Config | pydantic-settings + `.env` |
| Frontend | HTML5, Vanilla CSS, Vanilla JavaScript |
| Testing | pytest, httpx |

---

## 🚀 Installation & Setup

### 1. Prerequisites

- Python 3.10 or higher
- A Google Gemini API key ([Get one here](https://aistudio.google.com/app/apikey))

### 2. Clone / Download the Project

```bash
# Navigate to your project folder
cd PocketSmartAI
```

### 3. Create a Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Copy the example file and fill in your keys:

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Then open `.env` and set:

```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash
SECRET_KEY=your_very_long_random_secret_key_minimum_32_chars
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

> ⚠️ **Never commit `.env` to version control.** It is already in `.gitignore`.

### 6. Run the Application

```bash
# Option A — Simple
python run.py

# Option B — Uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open your browser at: **http://localhost:8000**

---

## 🔑 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Your Google Gemini API key | *(required)* |
| `GEMINI_MODEL` | Gemini model to use | `gemini-1.5-flash` |
| `SECRET_KEY` | JWT signing secret (min 32 chars) | *(auto-generated, change this)* |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT expiry in minutes | `60` |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins | `http://localhost:8000` |

---

## 📡 API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/` | Home page | No |
| GET | `/dashboard` | User dashboard | ✅ Yes |
| GET | `/login` | Login page | No |
| POST | `/login` | Submit login | No |
| GET | `/register` | Register page | No |
| POST | `/register` | Submit registration | No |
| GET | `/logout` | Logout + clear cookie | No |
| GET | `/session-info` | Current session details | No |
| GET | `/home-planner` | Home planner page | ✅ Yes |
| POST | `/generate-home` | Generate home recommendations | ✅ Yes |
| GET | `/party-planner` | Party planner page | ✅ Yes |
| POST | `/generate-party` | Generate event recommendations | ✅ Yes |
| GET | `/jewelry-planner` | Jewelry planner page | ✅ Yes |
| POST | `/generate-jewelry` | Generate jewelry recommendations | ✅ Yes |
| GET | `/history` | History page | ✅ Yes |
| GET | `/history/{id}` | Get single history entry | ✅ Yes |
| GET | `/health` | Health check | No |
| GET | `/api/gemini-status` | Test Gemini connectivity | ✅ Yes |
| GET | `/docs` | Swagger API docs | No |
| GET | `/redoc` | ReDoc API docs | No |

---

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test class
pytest tests/test_app.py::TestAuth -v

# Run with coverage
pip install pytest-cov
pytest tests/ --cov=app --cov-report=term-missing
```

> **Note:** Tests that call `/generate-home`, `/generate-party`, or `/generate-jewelry` with valid data will make real Gemini API calls. The test suite primarily tests validation errors and auth flows to avoid unnecessary API usage.

---

## 🛒 Platform Data Disclaimer

PocketSmart AI does **not** have real-time access to:
- Amazon India
- Flipkart
- IKEA
- Tanishq / Malabar Gold / CaratLane
- Swiggy / Zomato / Swiggy Genie
- OYO / hotel booking platforms

**All prices shown are AI-estimated demo prices** and are clearly labeled as **"Estimated Price"** in the UI.

The AI references these platforms by name for context (e.g., "you can find this on Amazon India for approximately ₹X"), but does not fetch live data from them.

---

## 🔒 Security Notes

- Passwords are hashed with **bcrypt** — never stored in plain text
- JWTs are stored in **HttpOnly cookies** — not accessible by JavaScript
- API keys are **never exposed** in HTML, JS, or API responses
- Gemini API calls are quota-protected — no unlimited retries
- User history is **user-scoped** — no cross-user access possible

---

## 🚧 Known Limitations (Demo Version)

- **In-memory storage** — User data and history are lost on server restart. Replace with SQLite/PostgreSQL for production.
- **No email verification** — Registration is immediate.
- **Single-server sessions** — JWT cookies won't work across multiple server instances without a shared secret.

---

## 🔮 Future Enhancements

- [ ] SQLite / PostgreSQL database for persistence
- [ ] Real Amazon/Flipkart product APIs via RapidAPI
- [ ] PDF export of recommendations
- [ ] Email/WhatsApp share of plans
- [ ] Budget comparison between plans
- [ ] Currency conversion (USD, GBP)
- [ ] Multiple AI model support
- [ ] Admin dashboard

---

## 👨‍💻 Tech Stack Details

- **FastAPI** — Modern Python web framework with automatic OpenAPI docs
- **Gemini AI** — Google's multimodal AI for text + image understanding
- **Jinja2** — Server-side HTML templating
- **python-jose** — JWT encoding/decoding
- **passlib[bcrypt]** — Password hashing
- **pydantic-settings** — Environment variable management

---

*Built for learning and demonstration purposes. Not intended for financial advice.*
