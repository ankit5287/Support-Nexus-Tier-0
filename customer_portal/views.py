from django.shortcuts import render
from .apps import CustomerPortalConfig

def index(request):
    context = {}
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
                from .models import AITrainingLog
                AITrainingLog.objects.create(
                    ticket_text=user_input,
                    predicted_label="Question (Deflected)",
                    predicted_id=99
                )
                return render(request, 'customer_portal/index.html', context)

            # -- PHASE 1: TICKET CLASSIFICATION (Original Logic) --
            tokenizer = CustomerPortalConfig.tokenizer
            model = CustomerPortalConfig.model

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
                
                # --- PHASE 5: CONTINUOUS LEARNING PIPELINE ---
                # Save the interaction to the database for future learning
                from .models import AITrainingLog
                AITrainingLog.objects.create(
                    ticket_text=user_input,
                    predicted_label=predicted_label_str,
                    predicted_id=prediction_id
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
                    'confidence': 85.0, # Simulated confidence
                    'id': simulated_id
                }
                
                # --- PHASE 5: CONTINUOUS LEARNING PIPELINE (Simulation Backup) ---
                from .models import AITrainingLog
                AITrainingLog.objects.create(
                    ticket_text=user_input,
                    predicted_label=simulated_label,
                    predicted_id=simulated_id
                )
        else:
            context['error'] = "Please enter some text."
            
    return render(request, 'customer_portal/index.html', context)

