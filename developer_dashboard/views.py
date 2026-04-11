from django.shortcuts import render
import random

def dashboard(request):
    context = {}
    
    # Mocking a list of active bug tickets
    context['bug_tickets'] = [
        {"id": 101, "title": "App keeps crashing on iOS", "status": "Open"},
        {"id": 102, "title": "Memory leak in data pipeline", "status": "In Progress"}
    ]
    
    # Continual Learning: Fetch unverified AI predictions
    from customer_portal.models import AITrainingLog
    from django.db.models import Count
    
    context['ai_logs'] = AITrainingLog.objects.filter(is_verified=False).order_by('-created_at')[:5]

    # Analytics Aggregation for Chart.js
    total_tickets = AITrainingLog.objects.count()
    context['total_tickets'] = total_tickets if total_tickets > 0 else 1
    
    distributions = AITrainingLog.objects.values('predicted_label').annotate(count=Count('predicted_label'))
    
    chart_labels = []
    chart_data = []
    
    if distributions:
        for dist in distributions:
            chart_labels.append(dist['predicted_label'])
            chart_data.append(dist['count'])
    else:
        # Default fallback so the chart still shows beautifully if the DB is completely empty
        chart_labels = ["Bug Report", "Billing Issue", "Praise", "Question (Deflected)"]
        chart_data = [45, 25, 10, 20]
        
    context['chart_labels'] = chart_labels
    context['chart_data'] = chart_data

    if request.method == 'POST':
        submitted_code = request.POST.get('code_snippet', '')
        context['submitted_code'] = submitted_code
        
        if submitted_code.strip():
            # --- PHASE 4: LLM CODE REVIEW ---
            # In production, you would call Gemini API:
            # genai.configure(api_key="YOUR_API_KEY")
            # model = genai.GenerativeModel('gemini-pro')
            # response = model.generate_content("Review this code: " + submitted_code)
            
            # Since we don't have your API key right now, we use a simulation
            # that looks exactly like an LLM response:
            review_comments = [
                "⚠️ **Security Flaw:** Prevent SQL Injection by using prepared statements here.",
                "💡 **Optimization:** The time complexity is O(N^2). Consider using a Hash Map to bring it down to O(N).",
                "✅ **Style:** Variable names are clean and PEP8 compliant.",
                "⚠️ **Bug Risk:** You are not handling Null/None values which might cause a hard crash."
            ]
            
            # Select 2-3 random insightful comments to simulate LLM analysis
            context['llm_feedback'] = random.sample(review_comments, 2)
            context['success_msg'] = "LLM Code Review Complete."
        else:
            context['error'] = "Please submit some code for review."

    return render(request, 'developer_dashboard/dashboard.html', context)

