# 🚀 Support Nexus: AI-Powered Support Platform

This document serves as the handoff and roadmap for the next development session.

## 🌟 Current State
The project is an enterprise-grade AI support platform building on a Django backend with a BERT-based ticket classification pipeline. 

### Recent Achievements: **Developer Dashboard Refinement**
In the last session, we simplified the Developer Dashboard to focus on high-priority bug tracking and automated LLM code review.

- **Automated Ticket Analytics:** Real-time distribution charts showing how the AI classifies incoming support requests.
- **Bug Tracking Workspace:** A dedicated view for engineers to track active high-priority issues.
- **LLM Code Reviewer:** A functional simulation of a Google Gemini-powered code reviewer that analyzes pull request snippets for security and performance vulnerabilities.
- **Microservices API:** A robust REST implementation that allows external systems to tap into the classification pipeline.

---

## 🛠 Technical Stack
- **Backend:** Django 6.x
- **Frontend:** Vanilla CSS (Premium Dark Mode Aesthetics)
- **ML/AI:** PyTorch, Transformers (BERT), REST API Microservices
- **Database:** SQLite

---

## 🎯 Next Feature Roadmap
Choose one of these for the next session to continue the enterprise narrative:

### 1. ⚡ Priority & Urgency Scoring
- **Concept:** Auto-assign "P1/P2/P3" levels using ML or keyword-based urgency detection.
- **Value:** Helps support teams focus on critical bugs first.
- **Work:** Update model, add priority tags to the dashboard, and color-code high-urgency items.

### 2. 🌍 Multi-language & Sentiment Analysis
- **Concept:** Automatically translate incoming tickets from other languages and detect customer sentiment (Angry vs. Happy).
- **Value:** Expands the platform's reach to global enterprises.
- **Work:** Integrate a translation API and update the moderation pipeline.

### 3. 🔔 Enterprise Notifications
- **Concept:** Send Slack or Email alerts when a low-confidence or high-priority ticket lands.
- **Value:** Real-time visibility for critical engineering issues.
- **Work:** Add a notification service (simulated or real Slack webhook).

### 4. 🧠 Real Gemini Integration for Code Review
- **Concept:** Replace the simulated LLM Code Reviewer in the Dev Dashboard with real API calls to Google's Gemini.
- **Value:** Moves from simulation to a live, functional AI feature.
- **Work:** Configure `google-generativeai` and wire up the `dashboard` view.

---

## 🚀 How to Run
1. Ensure dependencies are installed: `pip install djangorestframework torch transformers`
2. Run migrations: `python manage.py migrate`
3. Start server: `python manage.py runserver`
4. Access:
   - **Customer Portal:** `http://127.0.0.1:8000/`
   - **Dev Dashboard:** `http://127.0.0.1:8000/dev/` (Login: `admin` / `admin123`)
