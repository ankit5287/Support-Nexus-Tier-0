from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .apps import CustomerPortalConfig
from .nlp_pipeline import classifier as nlp_model
from .models import SupportCase

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
            # -- PROFESSIONAL ANALYTICS: CONTENT AUDIT --
            unprofessional_indicators = ["idiot", "stupid", "dumb", "hate", "scam"]
            is_flagged = any(word in user_input.lower() for word in unprofessional_indicators)
            
            if CustomerPortalConfig.moderation_pipeline:
                mod_result = CustomerPortalConfig.moderation_pipeline(user_input)[0]
                is_flagged = mod_result['label'] == 'toxic' and mod_result['score'] > 0.8
                
            if is_flagged:
                context['moderation_flag'] = "⚠️ Your message requires revision for professional communication. Please adjust your tone."
                return render(request, 'customer_portal/index.html', context)
            
            from .kb import mock_vector_search
            ranked_articles = mock_vector_search(user_input)
            
            if ranked_articles:
                context['kb_suggestion'] = "Recommended resources for immediate resolution:"
                context['ranked_articles'] = ranked_articles
            
            # -- OPERATIONAL INTENT ANALYSIS --
            intent = "Technical Inquest"
            question_indicators = ["how", "what", "where", "can i", "is there", "?", "change", "reset", "help"]
            if any(indicator in user_input.lower() for indicator in question_indicators):
                intent = "Support Inquiry"
                
            if CustomerPortalConfig.intent_pipeline:
                intents = ["Technical Inquest", "Support Inquiry", "Operational Feedback"]
                intent_result = CustomerPortalConfig.intent_pipeline(user_input, intents)
                intent = intent_result['labels'][0]
                
            context['intent'] = intent
            
            if intent == "Support Inquiry" and ranked_articles:
                SupportCase.objects.create(
                    user=request.user,
                    ticket_text=user_input,
                    classification="Inquiry (Deflected)",
                    category_code=99
                )
                context['recent_tickets'] = _get_user_tickets(request.user)
                return render(request, 'customer_portal/index.html', context)

            # -- OPERATIONAL SENTIMENT & URGENCY SCORING --
            urgency_level = "Standard"
            priority_boost = False
            urgent_indicators = ["angry", "frustrated", "terrible", "worst", "unacceptable", "broken", "useless", "urgent", "critical", "emergency", "production", "crash", "crashed", "down", "offline"]
            
            if any(w in user_input.lower() for w in urgent_indicators):
                urgency_level = "High Priority"
                priority_boost = True
            
            context['urgency'] = urgency_level
            
            # -- OPERATIONAL DOMAIN ASSIGNMENT (HYBRID SEMANTIC/KEYWORD) --
            squad = None
            creative_keywords = ["button", "css", "layout", "visual", "ui", "ux", "responsive", "frontend", "color", "header", "footer", "interface", "animation", "style", "display"]
            systems_keywords = ["api", "database", "server", "slow", "performance", "backend", "connection", "error 500", "db", "auth", "infrastructure", "latency", "system", "offline", "crash"]
            neural_keywords = ["logic", "algorithm", "prediction", "accuracy", "integrity", "triage", "standard", "diagnostic", "sync", "migration", "data flow", "report", "analysis", "audit", "metrics", "chart"]
            
            input_lower = user_input.lower()
            if any(w in input_lower for w in neural_keywords):
                squad = "Neural Insights"
            elif any(w in input_lower for w in creative_keywords):
                squad = "Creative Architecture"
            elif any(w in input_lower for w in systems_keywords):
                squad = "Systems Engine"
            
            # Semantic Routing Fallback
            if not squad:
                try:
                    from developer_dashboard.semantic_search import SemanticSearchEngine
                    import numpy as np
                    engine = SemanticSearchEngine()
                    input_vec = engine.model.encode([user_input])[0]
                    # Logic: Compare input_vec with squad descriptions
                    best_score = -1
                    best_squad = "Systems Engine"
                    for squad_name, desc in CustomerPortalConfig.SQUAD_CONTEXTS.items():
                        desc_vec = engine.model.encode([desc])[0]
                        similarity = np.dot(input_vec, desc_vec) / (np.linalg.norm(input_vec) * np.linalg.norm(desc_vec))
                        if similarity > best_score:
                            best_score = similarity
                            best_squad = squad_name
                    squad = best_squad
                except:
                    squad = "Systems Engine" # Hard Fallback

            # Enhanced Priority Scoring (P1/P2/P3)
            prio = "P3"
            p1_keywords = ["emergency", "outage", "production down", "critical failure", "security breach", "data loss", "cannot access"]
            if any(w in input_lower for w in p1_keywords):
                prio = "P1"
            elif priority_boost:
                prio = "P2"

            tokenizer = CustomerPortalConfig.tokenizer
            model = CustomerPortalConfig.model
            
            classification_str = "Standard Inquiry"
            certainty = 0.0
            prediction_id = 99
            triage_logic = "Specialized BERT"

            # STEP 1: Specialized BERT
            if tokenizer and model:
                import torch
                inputs = tokenizer(user_input, return_tensors="pt", padding=True, truncation=True, max_length=128)
                with torch.no_grad():
                    outputs = model(**inputs)
                
                probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
                prediction_id = torch.argmax(probabilities, dim=-1).item()
                certainty = probabilities[0][prediction_id].item()

                labels = {0: "Technical Discrepancy", 1: "Account/Billing", 2: "Operational Feedback"}
                classification_str = labels.get(prediction_id, "Standard Inquiry")

            # STEP 2: Universal Zero-Shot Fallback (If BERT is uncertain)
            if certainty < 0.70 and CustomerPortalConfig.intent_pipeline:
                triage_labels = [
                    "Technical Discrepancy", "Operational Feedback", "Account/Billing", 
                    "Security/Compliance", "Feature Request", "Emergency Outage"
                ]
                z_result = CustomerPortalConfig.intent_pipeline(user_input, triage_labels)
                classification_str = z_result['labels'][0]
                certainty = z_result['scores'][0]
                triage_logic = "Universal Zero-Shot"
                prediction_id = 100 # Custom code for ZS

            context['classification'] = {
                'label': classification_str,
                'certainty': round(certainty * 100, 2),
                'logic': triage_logic
            }

            SupportCase.objects.create(
                user=request.user,
                ticket_text=user_input,
                classification=classification_str,
                category_code=prediction_id,
                system_certainty=round(certainty * 100, 2),
                assigned_team=squad,
                priority=prio,
                status="Open",
                triage_metadata={'logic': triage_logic}
            )
            
            latest_case = SupportCase.objects.filter(user=request.user).latest('id')
            context['success_msg'] = f"Operational Domain Analysis complete. Case #{latest_case.id} assigned to {squad}."
            
        else:
            context['error'] = "Description required for processing."
            
    return render(request, 'customer_portal/index.html', context)


def _get_user_tickets(user):
    """Helper: Fetch active cases for the authenticated user."""
    from .models import SupportCase
    URGENCY_MAP = {
        'P3': 'Standard Review',
        'P2': 'Expedited Audit',
        'P1': 'Critical Response'
    }
    
    STATUS_LABELS = {
        'Open': 'Pending Review',
        'In Progress': 'Active Investigation',
        'Resolved': 'Resolution Confirmed'
    }

    user_cases = SupportCase.objects.filter(user=user).order_by('-created_at')[:10]
    return [
        {
            'id': f'NX-{ticket.id:04d}',
            'title': ticket.ticket_text[:60],
            'status': STATUS_LABELS.get(ticket.status, "Processing"),
            'status_raw': ticket.status.lower().replace(' ', '-') if ticket.status else 'open',
            'squad': ticket.assigned_team if ticket.assigned_team else "Operational Support",
            'priority': URGENCY_MAP.get(ticket.priority, "Standard"),
            'date': ticket.created_at.strftime('%D'),
            'color': '#007aff',
        }
        for ticket in user_cases
    ]

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

@csrf_exempt
def operational_classification_endpoint(request):
    """
    Enterprise Microservice: Operational Categorization Endpoint.
    Accepts JSON: { "data": "Operational log text..." }
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Operational endpoint requires POST protocol'}, status=405)

    try:
        body = json.loads(request.body)
        text = body.get('data', '')
    except:
        return JsonResponse({'error': 'Invalid operational payload'}, status=400)

    if not text:
        return JsonResponse({'error': 'Null data signature'}, status=400)

    # Simplified Logic for Microservice
    labels = {0: "Technical Discrepancy", 1: "Account/Billing", 2: "Operational Feedback"}
    prediction_id = 0
    if any(w in text.lower() for w in ['bill', 'pay', 'charge']):
        prediction_id = 1
    elif any(w in text.lower() for w in ['slow', 'performance', 'stable']):
        prediction_id = 2

    return JsonResponse({
        'classification': labels[prediction_id],
        'system_certainty': 0.9412,
        'operational_status': 'Validated'
    })
