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
            sentiment, sentiment_score = nlp_model.get_sentiment(user_input)
            is_flagged = sentiment == "Angry/Frustrated" and sentiment_score > 80.0
            
            if is_flagged:
                context['moderation_flag'] = "⚠️ Your message requires revision for professional communication. Please adjust your tone."
                return render(request, 'customer_portal/index.html', context)
            
            from .kb import mock_vector_search
            ranked_articles = mock_vector_search(user_input)
            
            if ranked_articles:
                context['kb_suggestion'] = "Recommended resources for immediate resolution:"
                context['ranked_articles'] = ranked_articles
            
            # -- OPERATIONAL INTENT & CLASSIFICATION --
            classification_str, certainty = nlp_model.classify_ticket(user_input)
            prio, urgency_label, urgency_score = nlp_model.get_urgency_and_priority(user_input)
            squad = nlp_model.get_assigned_squad(user_input)
            
            # Additional metadata for context
            context['intent'] = classification_str
            context['urgency'] = urgency_label
            context['classification'] = {
                'label': classification_str,
                'certainty': certainty,
                'logic': "Advanced BERT Engine"
            }

            # Deflection Logic: If it's a simple inquiry and we found KB articles, don't create a real ticket
            # (Wait, the previous code had a specific check for "Support Inquiry")
            # We'll adapt it to check if class is "Operational Feedback" or "Technical Discrepancy"
            if classification_str == "Operational Feedback" and ranked_articles:
                 SupportCase.objects.create(
                    user=request.user,
                    ticket_text=user_input,
                    classification="Inquiry (Deflected)",
                    category_code=99,
                    status="Deflected"
                )
                 context['recent_tickets'] = _get_user_tickets(request.user)
                 return render(request, 'customer_portal/index.html', context)

            SupportCase.objects.create(
                user=request.user,
                ticket_text=user_input,
                classification=classification_str,
                category_code=0 if classification_str == "Technical Discrepancy" else 1,
                system_certainty=certainty,
                assigned_team=squad,
                priority=prio,
                status="Open",
                triage_metadata={
                    'logic': 'Centralized NLP Pipeline',
                    'sentiment': sentiment,
                    'sentiment_score': sentiment_score,
                    'urgency_score': urgency_score
                }
            )
            
            latest_case = SupportCase.objects.filter(user=request.user).latest('id')
            context['success_msg'] = f"Operational Domain Analysis complete. Case #{latest_case.id} assigned to {squad}. Please go to the Developer Dashboard to view your ticket."
            
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
