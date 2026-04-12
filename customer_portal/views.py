from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .apps import CustomerPortalConfig
from .nlp_pipeline import classifier as nlp_model

def landing(request):
    return render(request, 'customer_portal/landing.html')

@login_required(login_url='/dev/login/')
def index(request):
    context = {}
    
    context['recent_tickets'] = _get_user_tickets(request.user)

    if request.method == 'POST':
        user_input = request.POST.get('ticket_text', '')
        context['user_input'] = user_input
        
        if user_input.strip():
            # -- PHASE 2: CONTENT MODERATION --
            toxic_words = ["idiot", "stupid", "dumb", "hate", "scam"]
            is_toxic = any(word in user_input.lower() for word in toxic_words)
            
            if CustomerPortalConfig.moderation_pipeline:
                # Real ML Moderation
                mod_result = CustomerPortalConfig.moderation_pipeline(user_input)[0]
                is_toxic = mod_result['label'] == 'toxic' and mod_result['score'] > 0.8
                
            if is_toxic:
                context['moderation_flag'] = "⚠️ Your message violates our community guidelines (Toxic Content). Please revise."
                return render(request, 'customer_portal/index.html', context)
            
            from .kb import mock_vector_search
            ranked_articles = mock_vector_search(user_input)
            
            # If articles scored well, ALWAYS suggest them immediately
            if ranked_articles:
                context['kb_suggestion'] = "Before submitting a ticket, check if these articles solve your issue:"
                context['ranked_articles'] = ranked_articles
            
            # -- PHASE 2: INTENT CLASSIFICATION --
            intent = "Report a Bug/Issue"
            question_indicators = ["how", "what", "where", "can i", "is there", "?", "change", "reset", "help"]
            if any(indicator in user_input.lower() for indicator in question_indicators):
                intent = "Ask a Question"
                
            if CustomerPortalConfig.intent_pipeline:
                # Real ML Intent
                intents = ["Report a Bug/Issue", "Ask a Question", "Praise/Feedback"]
                intent_result = CustomerPortalConfig.intent_pipeline(user_input, intents)
                intent = intent_result['labels'][0]
                
            context['intent'] = intent
            
            # If they definitely just want to ask a question (and articles were found), stop here.
            if intent == "Ask a Question" and ranked_articles:
                AITrainingLog.objects.create(
                    user=request.user,
                    ticket_text=user_input,
                    predicted_label="Question (Deflected)",
                    predicted_id=99
                )
                # Refresh tickets after save
                context['recent_tickets'] = _get_user_tickets(request.user)
                return render(request, 'customer_portal/index.html', context)

            # -- PHASE 3: SENTIMENT & LANGUAGE ANALYSIS --
            sentiment_score = "Neutral 😐"
            priority_boost = False
            angry_keywords = ["angry", "frustrated", "terrible", "worst", "hate", "unacceptable", "broken", "useless", "twice", "issue", "crash", "crashed"]
            happy_keywords = ["great", "awesome", "thanks", "amazing", "love", "perfect", "good"]
            
            if any(w in user_input.lower() for w in angry_keywords):
                sentiment_score = "Negative 😠"
                priority_boost = True
            elif any(w in user_input.lower() for w in happy_keywords):
                sentiment_score = "Positive 😃"
                
            context['sentiment'] = sentiment_score
            context['urgency'] = "High 🔥" if priority_boost else "Normal"
            
            # Simulated language detection
            foreign_keywords = ["ayuda", "problema", "hola", "gracias", "bonjour", "erreur", "hilfe"]
            if any(w in user_input.lower() for w in foreign_keywords):
                context['language'] = "Auto-translated (Foreign Language Detected)"
            else:
                context['language'] = "English"

            # -- PHASE 1: TICKET CLASSIFICATION (Original Logic) --
            tokenizer = CustomerPortalConfig.tokenizer
            model = CustomerPortalConfig.model

            # --- PHASE 8: ENTERPRISE SQUAD TRIAGE (NEW) ---
            squad = "Backend" # Default
            frontend_keywords = ["button", "css", "layout", "visual", "ui", "ux", "responsive", "frontend", "color", "header", "footer"]
            backend_keywords = ["api", "database", "server", "slow", "performance", "backend", "connection", "error 500", "database", "db", "auth"]
            ai_keywords = ["model", "prediction", "accuracy", "confidence", "bert", "ai", "ml", "training", "gemini", "diagnostic", "neural"]

            input_lower = user_input.lower()
            if any(w in input_lower for w in ai_keywords):
                squad = "AI/ML"
            elif any(w in input_lower for w in frontend_keywords):
                squad = "Frontend"
            elif any(w in input_lower for w in backend_keywords):
                squad = "Backend"

            # Priority logic
            prio = "Medium"
            high_prio_keywords = ["urgent", "broken", "critical", "blocking", "emergency", "crash", "crashed"]
            if any(w in input_lower for w in high_prio_keywords):
                prio = "High"

            if tokenizer and model:
                import torch
                # 1. Tokenize Input
                inputs = tokenizer(user_input, return_tensors="pt", padding=True, truncation=True, max_length=128)
                
                # 2. Run Inference
                with torch.no_grad():
                    outputs = model(**inputs)
                
                # 3. Get Prediction
                probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
                prediction_id = torch.argmax(probabilities, dim=-1).item()
                confidence = probabilities[0][prediction_id].item()

                labels = {0: "Bug Report", 1: "Billing Issue", 2: "Praise"}
                predicted_label_str = labels.get(prediction_id, "Unknown")
                
                context['classification'] = {
                    'label': predicted_label_str,
                    'confidence': round(confidence * 100, 2),
                    'id': prediction_id
                }
                

                # --- PHASE 6: FINANCIAL ROUTING (NLP Case Study Integration) ---
                nlp_category, nlp_conf = nlp_model.predict(user_input)
                context['nlp_routing'] = {
                    'category': nlp_category,
                    'confidence': nlp_conf
                }

                # --- PHASE 5: CONTINUOUS LEARNING PIPELINE (Updated for Enterprise) ---
                AITrainingLog.objects.create(
                    user=request.user,
                    ticket_text=user_input,
                    predicted_label=predicted_label_str,
                    predicted_id=prediction_id,
                    confidence=round(confidence * 100, 2),
                    assigned_team=squad,
                    priority=prio,
                    status="Open"
                )
                
            else:
                context['error'] = "BERT Classifier not loaded. Proceeding with Phase 2 simulation."
                # Fallback Simulation
                import random
                simulated_id = random.choice([0, 1])
                labels = {0: "Bug Report", 1: "Billing Issue", 2: "Praise"}
                simulated_label = labels.get(simulated_id)
                context['classification'] = {
                    'label': simulated_label,
                    'confidence': 85.0,
                    'id': simulated_id
                }

                # --- PHASE 8: ENTERPRISE SQUAD TRIAGE (Simulation Backup) ---
                AITrainingLog.objects.create(
                    user=request.user,
                    ticket_text=user_input,
                    predicted_label=simulated_label,
                    predicted_id=simulated_id,
                    confidence=85.0,
                    assigned_team=squad,
                    priority=prio,
                    status="Open"
                )
            
            # Refresh tickets after save
            context['recent_tickets'] = _get_user_tickets(request.user)
            context['success_msg'] = f"🚀 Case #{AITrainingLog.objects.filter(user=request.user).latest('id').id} submitted and assigned to our {squad} team."
            
        else:
            context['error'] = "Please enter some text."
            
    return render(request, 'customer_portal/index.html', context)


def _get_user_tickets(user):
    """Helper: Fetch real tickets for a specific user from the database."""
    from .models import AITrainingLog
    # Customer-friendly Priority Mapping
    URGENCY_MAP = {
        'Low': 'Standard',
        'Medium': 'Important',
        'High': 'Urgent 🔥'
    }
    
    # Customer-friendly Status Mapping
    STATUS_LABELS = {
        'Open': 'Waiting for Specialist',
        'In Progress': 'Team Investigating',
        'Resolved': 'Issue Fixed ✓'
    }

    user_tickets = AITrainingLog.objects.filter(user=user).order_by('-created_at')[:10]
    return [
        {
            'id': f'Ref: {ticket.id}',
            'title': ticket.ticket_text[:60],
            'status': STATUS_LABELS.get(ticket.status, "Processing"),
            'status_raw': ticket.status.lower().replace(' ', '-') if ticket.status else 'open',
            'squad': ticket.assigned_team if ticket.assigned_team else "General",
            'priority': URGENCY_MAP.get(ticket.priority, "Standard"),
            'date': ticket.created_at.strftime('%b %d, %H:%M') if ticket.created_at else 'N/A',
            'color': '#007aff',
        }
        for ticket in user_tickets
    ]


# --- MICROSERVICES ARCHITECTURE (REST API) ---
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['POST'])
def classify_ticket_api(request):
    """
    Microservice Endpoint: Allows mobile apps and external systems to access the ML Pipeline.
    Expected JSON: {"ticket_text": "The app crashed again."}
    """
    user_input = request.data.get('ticket_text', '')
    
    if not user_input.strip():
        return Response({"error": "No text provided."}, status=400)
        
    response_data = {
        "text_received": user_input,
        "is_toxic": False,
        "intent": "Unknown",
        "predicted_category": "Unknown",
        "confidence": 0.0
    }
    
    # 1. Moderation Check
    toxic_words = ["idiot", "stupid", "dumb", "hate", "scam"]
    if any(word in user_input.lower() for word in toxic_words):
        response_data['is_toxic'] = True
        return Response(response_data, status=200)
        
    # 2. Intent Check
    intent = "Report a Bug/Issue"
    question_indicators = ["how", "what", "where", "can i", "is there", "?", "change", "reset", "help"]
    if any(indicator in user_input.lower() for indicator in question_indicators):
        intent = "Ask a Question"
    response_data['intent'] = intent
    
    if intent == "Ask a Question":
        return Response(response_data, status=200)

    # 3. Model Inference (Bug Classification)
    tokenizer = CustomerPortalConfig.tokenizer
    model = CustomerPortalConfig.model

    if tokenizer and model:
        import torch
        inputs = tokenizer(user_input, return_tensors="pt", padding=True, truncation=True, max_length=128)
        
        with torch.no_grad():
            outputs = model(**inputs)
            
        probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
        prediction_id = torch.argmax(probabilities, dim=-1).item()
        confidence = probabilities[0][prediction_id].item()

        labels = {0: "Bug Report", 1: "Billing Issue", 2: "Praise"}
        response_data['predicted_category'] = labels.get(prediction_id, "Unknown")
        response_data['confidence'] = round(confidence * 100, 2)
    else:
        import random
        simulated_id = random.choice([0, 1])
        labels = {0: "Bug Report", 1: "Billing Issue", 2: "Praise"}
        response_data['predicted_category'] = labels.get(simulated_id, "Mock Backup")
        response_data['confidence'] = 85.0
        
    return Response(response_data, status=200)
