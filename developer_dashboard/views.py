from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
import random
import requests
import re

@login_required(login_url='/dev/login/')
def dashboard(request):
    from customer_portal.models import AITrainingLog
    from django.db.models import Count
    
    context = {}
    
    # Mocking a list of active bug tickets
    context['bug_tickets'] = [
        {"id": 101, "title": "App keeps crashing on iOS", "status": "Open"},
        {"id": 102, "title": "Memory leak in data pipeline", "status": "In Progress"}
    ]
    
    # Dynamic Analytics Mapping
    COLOR_MAP = {
        'Bug Report': '#f85149',
        'Billing Issue': '#58a6ff',
        'Praise': '#3fb950',
        'Question (Deflected)': '#a371f7'
    }
    
    total_tickets = AITrainingLog.objects.count()
    context['total_tickets'] = total_tickets if total_tickets > 0 else 1
    
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
        fallback_data = [
            ('Bug Report', 45, '#f85149'),
            ('Billing Issue', 25, '#58a6ff'),
            ('Praise', 10, '#3fb950'),
            ('Question (Deflected)', 20, '#a371f7')
        ]
        for label, count, color in fallback_data:
            distribution_list.append({'label': label, 'count': count, 'color': color})
            chart_labels.append(label)
            chart_data.append(count)
            chart_colors.append(color)
            
    context['distribution_list'] = distribution_list
    context['chart_labels'] = chart_labels
    context['chart_data'] = chart_data
    context['chart_colors'] = chart_colors

    if request.method == 'POST':
        # --- NEW GITHUB PR INTEGRATION ---
        github_url = request.POST.get('github_pr_url', '')
        submitted_code = request.POST.get('code_snippet', '')
        
        if github_url.strip():
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
                            # Use the first 2000 chars of diff for simulation
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
            # LLM Code Review Simulation
            review_comments = [
                "⚠️ **Security Flaw:** Prevent SQL Injection by using prepared statements here.",
                "💡 **Optimization:** The time complexity is O(N^2). Consider using a Hash Map to bring it down to O(N).",
                "✅ **Style:** Variable names are clean and PEP8 compliant.",
                "⚠️ **Bug Risk:** You are not handling Null/None values which might cause a hard crash.",
                "💡 **Maintainability:** Consider splitting this function into smaller, more focused components.",
                "✅ **Documentation:** Good use of docstrings to explain the function's purpose."
            ]
            
            # Select 3 random comments for a "proper" review feel
            context['llm_feedback'] = random.sample(review_comments, 3)
            context['success_msg'] = "LLM Code Review Complete."
        elif not github_url.strip() and not submitted_code.strip():
            context['error'] = "Please submit a GitHub PR URL or paste a code snippet."

    return render(request, 'developer_dashboard/dashboard.html', context)


def login_view(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            error = "Invalid credentials. Please try again."
    return render(request, 'developer_dashboard/login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('/dev/login/')
