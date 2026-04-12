from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
import requests
import re
import os
import difflib


def staff_required(user):
    return user.is_staff


@login_required(login_url='/dev/login/')
@user_passes_test(staff_required, login_url='/support/')
def dashboard(request):
    from customer_portal.models import AITrainingLog
    from django.db.models import Count
    
    context = {}
    
    # --- REAL BUG TICKETS FROM DATABASE (Squad-Filtered) ---
    # In a real app, we'd check request.user.groups, but for this demo 
    # we'll assume a session-based or profile-based squad assignment.
    # Defaulting admin to 'Frontend' for demonstration.
    user_squad = getattr(request.user, 'squad', 'Frontend') 
    
    bug_logs = AITrainingLog.objects.filter(assigned_team=user_squad, status='Open').order_by('-created_at')[:10]
    context['bug_tickets'] = [
        {
            "id": log.id,
            "title": log.ticket_text[:80],
            "status": log.status,
            "priority": log.priority,
            "user": log.user.username if log.user else "Anonymous",
            "date": log.created_at.strftime('%b %d, %H:%M') if log.created_at else "N/A"
        }
        for log in bug_logs
    ]
    context['user_squad'] = user_squad
    
    # --- REAL MODERATION STATS ---
    total_tickets = AITrainingLog.objects.count()
    context['total_tickets'] = total_tickets if total_tickets > 0 else 0
    
    verified_count = AITrainingLog.objects.filter(is_verified=True).count()
    context['verified_count'] = verified_count
    context['unverified_count'] = total_tickets - verified_count
    
    # --- REAL RECENT ACTIVITY LOG ---
    recent_logs = AITrainingLog.objects.order_by('-created_at')[:5]
    context['recent_activity'] = [
        {
            "text": log.ticket_text[:60],
            "label": log.predicted_label,
            "confidence": log.confidence,
            "user": log.user.username if log.user else "API",
            "time": log.created_at.strftime('%b %d, %H:%M') if log.created_at else "N/A"
        }
        for log in recent_logs
    ]
    
    # Dynamic Analytics Mapping
    COLOR_MAP = {
        'Bug Report': '#f85149',
        'Billing Issue': '#58a6ff',
        'Praise': '#3fb950',
        'Question (Deflected)': '#a371f7'
    }
    
    distributions = AITrainingLog.objects.values('predicted_label').annotate(count=Count('predicted_label'))
    
    distribution_list = []
    chart_labels = []
    chart_data = []
    chart_colors = []
    
    if distributions:
        for dist in distributions:
            label = dist['predicted_label']
            count = dist['count']
            color = COLOR_MAP.get(label, '#8b949e')
            
            distribution_list.append({'label': label, 'count': count, 'color': color})
            chart_labels.append(label)
            chart_data.append(count)
            chart_colors.append(color)
    else:
        # Show zeros when DB is empty - no fake data
        distribution_list.append({'label': 'No Data', 'count': 0, 'color': '#8b949e'})
        chart_labels.append('No Data')
        chart_data.append(1)
        chart_colors.append('#8b949e')
            
    context['distribution_list'] = distribution_list
    context['chart_labels'] = chart_labels
    context['chart_data'] = chart_data
    context['chart_colors'] = chart_colors

    if request.method == 'POST':
        # --- GITHUB PR INTEGRATION ---
        github_url = request.POST.get('github_pr_url', '')
        submitted_code = request.POST.get('code_snippet', '')
        ide_code = request.POST.get('ide_code', '')
        is_ide_mode = False
        
        if ide_code.strip():
            # --- LIVE IDE (VS CODE) INTEGRATION ---
            submitted_code = ide_code.strip()
            context['submitted_code'] = submitted_code
            is_ide_mode = True

        elif github_url.strip():
            # Parse URL: https://github.com/owner/repo/pull/num
            match = re.search(r'github\.com/([^/]+)/([^/]+)/pull/(\d+)', github_url)
            if match:
                owner, repo, num = match.groups()
                api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{num}"
                
                try:
                    # 1. Fetch PR Metadata
                    response = requests.get(api_url, timeout=10)
                    if response.status_code == 200:
                        pr_data = response.json()
                        context['github_pr_info'] = {
                            'title': pr_data.get('title'),
                            'author': pr_data.get('user', {}).get('login'),
                            'url': github_url
                        }
                        
                        # 2. Fetch the Diff for analysis
                        diff_response = requests.get(api_url, headers={'Accept': 'application/vnd.github.v3.diff'}, timeout=10)
                        if diff_response.status_code == 200:
                            submitted_code = diff_response.text[:2000]
                            context['submitted_code'] = "Analyzed GitHub PR Diff:\n" + submitted_code
                        else:
                            context['error'] = "Could not fetch PR diff."
                    else:
                        context['error'] = f"GitHub API Error: {response.status_code}. Is the repo public?"
                except Exception as e:
                    context['error'] = f"Connection error: {str(e)}"
            else:
                context['error'] = "Invalid GitHub PR URL format. Use: https://github.com/owner/repo/pull/123"

        # --- EXISTING MANUAL REVIEW ---
        elif submitted_code.strip():
            context['submitted_code'] = submitted_code
        
        if 'error' not in context and submitted_code.strip():
            try:
                import google.generativeai as genai
                GEMINI_AVAILABLE = True
            except ImportError:
                GEMINI_AVAILABLE = False
                
            api_key = os.environ.get("GEMINI_API_KEY", "")
            
            if not GEMINI_AVAILABLE:
                context['error'] = "google-generativeai module is not installed."
            elif not api_key:
                context['error'] = "GEMINI_API_KEY environment variable is not set. Real AI review cannot proceed."
            else:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-pro-latest')
                    
                    if is_ide_mode:
                        prompt = f"""You are an expert Code Reviewer. Analyze this code:
```
{submitted_code}
```
Provide two things:
1. A brief list of 3 bullet points reviewing the code (focus on Security, Optimization, Style). Prefix emojis like ⚠️ or ✅.
2. Under exactly the heading 'REFINED_CODE:', provide the optimized version of the code. Only output the python code inside ```python blocks.
"""
                        response = model.generate_content(prompt)
                        text = response.text
                        if 'REFINED_CODE:' in text:
                            feedback, refined = text.split('REFINED_CODE:')
                            context['llm_feedback'] = [f.strip() for f in feedback.split('\n') if f.strip() and not f.strip().startswith('```')]
                            context['refined_code'] = refined.replace("```python", "").replace("```", "").strip()
                        else:
                            context['llm_feedback'] = ["✅ Code parsed, but AI could not generate a clean block."]
                            context['refined_code'] = text
                    else:
                        prompt = f"Review this code snippet. Provide exactly 3 bullet points with emojis ⚠️, 💡, or ✅:\n```\n{submitted_code}\n```"
                        response = model.generate_content(prompt)
                        context['llm_feedback'] = [f.strip() for f in response.text.split('\n') if f.strip() and not f.strip().startswith('```')]
                        
                    context['success_msg'] = "Gemini Code Review Complete."
                except Exception as e:
                    context['error'] = f"Gemini API Error: {str(e)}"

        elif not github_url.strip() and not submitted_code.strip():
            context['error'] = "Please submit a GitHub PR URL or paste a code snippet."

    return render(request, 'developer_dashboard/dashboard.html', context)


@login_required(login_url='/dev/login/')
@user_passes_test(staff_required, login_url='/support/')
def ide_view(request):
    """
    Phase 4: Pro-Grade Full-Page IDE
    Features syntax highlighting (UI), AI Polish, and Merge Diff.
    """
    context = {}
    
    # Stable 'Main Branch' version of a key file for diffing
    STABLE_CODE = """def classify_ticket(text):
    # Standard linear classification
    if 'error' in text:
        return 'Bug'
    return 'Question'"""

    if request.method == 'POST':
        action = request.POST.get('action', '')
        current_code = request.POST.get('code', '')
        context['current_code'] = current_code
        
        if action == 'polish':
            # AI Polish Logic (Gemini)
            api_key = os.environ.get("GEMINI_API_KEY", "")
            if api_key:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-pro-latest')
                    prompt = f"Optimize and polish this code for production. Return ONLY the code:\n\n{current_code}"
                    response = model.generate_content(prompt)
                    context['current_code'] = response.text.replace('```python', '').replace('```', '').strip()
                    context['success'] = "AI Polish complete!"
                except Exception as e:
                    context['error'] = f"Gemini Error: {str(e)}"
            else:
                context['error'] = "GEMINI_API_KEY not configured."
                
        elif action == 'merge':
            # Merge to Main -> Generate Diff
            diff = difflib.unified_diff(
                STABLE_CODE.splitlines(keepends=True),
                current_code.splitlines(keepends=True),
                fromfile='main_branch.py',
                tofile='current_squad_feature.py'
            )
            context['diff_output'] = "".join(diff)
            context['is_merge_view'] = True
            
        elif action == 'run':
            # Simulated Debug/Run
            context['run_output'] = ">>> Running code...\n>>> Triage Logic Initialized.\n>>> Result: VALID\n>>> Execution finished in 0.04s"

    else:
        # Default code in editor
        context['current_code'] = STABLE_CODE

    return render(request, 'developer_dashboard/ide.html', context)


@login_required(login_url='/dev/login/')
@user_passes_test(staff_required, login_url='/support/')
def logic_lab(request):
    """
    Pillar 3: A/B Test Outcome Prediction
    Uses Gemini to predict which of two support flow strategies will be most effective.
    Saves every prediction to the database.
    """
    from .models import ABTestPrediction
    
    context = {}
    
    # Load past predictions for this user
    context['past_predictions'] = ABTestPrediction.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    if request.method == 'POST':
        flow_a = request.POST.get('flow_a', '')
        flow_b = request.POST.get('flow_b', '')
        
        if flow_a and flow_b:
            api_key = os.environ.get("GEMINI_API_KEY", "")
            if api_key:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-pro-latest')
                    
                    prompt = f"""You are an A/B Testing Data Scientist. Compare these two Nexus Quantum support strategies:
STRATEGY A: {flow_a}
STRATEGY B: {flow_b}

Provide:
1. Winner: (A or B)
2. Confidence Score: (0-100%)
3. Reason: (Brief explanation on why one would improve Resolution Accuracy or Customer Satisfaction)
"""
                    response = model.generate_content(prompt)
                    result_text = response.text
                    context['prediction_result'] = result_text
                    
                    # --- PERSIST TO DATABASE ---
                    ABTestPrediction.objects.create(
                        user=request.user,
                        strategy_a=flow_a,
                        strategy_b=flow_b,
                        prediction_result=result_text
                    )
                    
                    # Refresh past predictions
                    context['past_predictions'] = ABTestPrediction.objects.filter(user=request.user).order_by('-created_at')[:5]
                    
                except Exception as e:
                    context['error'] = f"Prediction Error: {str(e)}"
            else:
                context['error'] = "GEMINI_API_KEY not configured."
                
    return render(request, 'developer_dashboard/logic_lab.html', context)


def login_view(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Smart redirect: Staff -> Dev Dashboard, Customer -> Support Hub
            next_url = request.GET.get('next', '')
            if next_url:
                return redirect(next_url)
            if user.is_staff:
                return redirect('dashboard')
            else:
                return redirect('index')
        else:
            error = "Invalid Nexus ID or password. Please try again."
    return render(request, 'developer_dashboard/login.html', {'error': error})


def signup_view(request):
    context = {}
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        password2 = request.POST.get('password2', '').strip()
        
        if not username or not email or not password:
            context['error'] = "All fields are required."
        elif password != password2:
            context['error'] = "Passwords do not match."
        elif len(password) < 6:
            context['error'] = "Password must be at least 6 characters."
        elif User.objects.filter(username=username).exists():
            context['error'] = f"Nexus ID '{username}' is already taken."
        elif User.objects.filter(email=email).exists():
            context['error'] = "An account with this email already exists."
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            return redirect('index')
    
    return render(request, 'developer_dashboard/signup.html', context)


def logout_view(request):
    logout(request)
    return redirect('/dev/login/')
