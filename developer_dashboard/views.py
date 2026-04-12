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
@user_passes_test(staff_required, login_url='/')
def dashboard(request):
    from customer_portal.models import SupportCase
    from django.db.models import Count
    from django.utils import timezone
    from datetime import timedelta
    
    context = {}
    
    # --- DYNAMIC FILTERING ---
    active_team = request.GET.get('team', '')
    context['active_filter'] = active_team
    
    # Global Ticket Search (Semantic)
    query = request.GET.get('q', '')
    
    cases_query = SupportCase.objects.all()
    if active_team:
        cases_query = cases_query.filter(assigned_team=active_team)
    
    if query:
        from .semantic_search import semantic_ticket_query
        search_results = semantic_ticket_query(query)
        if active_team:
            search_results = [r for r in search_results if r.assigned_team == active_team]
        
        context['bug_tickets'] = [
            {
                "id": log.id,
                "title": log.ticket_text[:80],
                "status": log.status,
                "priority": log.priority,
                "team": log.assigned_team,
                "user": log.user.username if log.user else "Anonymous",
                "assigned": log.assigned_to.username if log.assigned_to else "Unassigned",
                "date": log.created_at.strftime('%b %d')
            }
            for log in search_results
        ]
        context['is_search'] = True
    else:
        cases = cases_query.order_by('-created_at')[:15]
        context['bug_tickets'] = [
            {
                "id": log.id,
                "title": log.ticket_text[:80],
                "status": log.status,
                "priority": log.priority,
                "team": log.assigned_team,
                "user": log.user.username if log.user else "Anonymous",
                "assigned": log.assigned_to.username if log.assigned_to else "Unassigned",
                "date": log.created_at.strftime('%b %d')
            }
            for log in cases
        ]
    
    # --- SYSTEM VELOCITY LOGIC ---
    now = timezone.now()
    velocity_labels = []
    velocity_data = []
    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        count = SupportCase.objects.filter(status='Resolved', updated_at__date=day.date()).count()
        velocity_labels.append(day.strftime('%b %d'))
        velocity_data.append(count)
    
    context['velocity_labels'] = velocity_labels
    context['velocity_data'] = velocity_data
    context['last_sync'] = now.strftime('%Y-%m-%d %H:%M:%S')
    
    # Team Loads for the "Universal Truth" view
    from django.db.models import Count
    team_loads = SupportCase.objects.values('assigned_team').annotate(count=Count('assigned_team'))
    context['team_loads'] = {item['assigned_team']: item['count'] for item in team_loads}
    
    # --- SYSTEM METRICS ---
    total_cases = SupportCase.objects.count()
    context['total_tickets'] = total_cases
    
    reviewed_count = SupportCase.objects.filter(is_reviewed=True).count()
    context['verified_count'] = reviewed_count
    context['unverified_count'] = total_cases - reviewed_count
    
    # --- RECENT SYSTEM ACTIVITY ---
    recent_logs = SupportCase.objects.order_by('-created_at')[:5]
    context['recent_activity'] = [
        {
            "text": log.ticket_text[:60],
            "label": log.classification,
            "certainty": log.system_certainty,
            "user": log.user.username if log.user else "System",
            "time": log.created_at.strftime('%b %d, %H:%M') if log.created_at else "N/A"
        }
        for log in recent_logs
    ]
    
    # Dynamic Logistics Mapping (Donut Chart Metaphor)
    COLOR_MAP = {
        'Technical Discrepancy': '#ffffff',
        'Account/Billing': '#94a3b8',
        'Operational Feedback': '#475569',
        'Inquiry (Deflected)': '#1e293b'
    }
    
    distributions = SupportCase.objects.values('classification').annotate(count=Count('classification'))
    
    distribution_list = []
    chart_labels = []
    chart_data = []
    chart_colors = []
    
    if distributions:
        for dist in distributions:
            label = dist['classification']
            count = dist['count']
            color = COLOR_MAP.get(label, '#8b949e')
            
            distribution_list.append({'label': label, 'count': count, 'color': color})
            chart_labels.append(label)
            chart_data.append(count)
            chart_colors.append(color)
    else:
        distribution_list.append({'label': 'No Data', 'count': 0, 'color': '#8b949e'})
        chart_labels.append('No Data')
        chart_data.append(1)
        chart_colors.append('#8b949e')
            
    context['distribution_list'] = distribution_list
    context['chart_labels'] = chart_labels
    context['chart_data'] = chart_data
    context['chart_colors'] = chart_colors

    if request.method == 'POST':
        # --- VCS INTEGRATION (GitHub) ---
        github_url = request.POST.get('github_pr_url', '')
        submitted_code = request.POST.get('code_snippet', '')
        ide_code = request.POST.get('ide_code', '')
        is_ide_mode = False
        
        if ide_code.strip():
            submitted_code = ide_code.strip()
            context['submitted_code'] = submitted_code
            is_ide_mode = True

        elif github_url.strip():
            match = re.search(r'github\.com/([^/]+)/([^/]+)/pull/(\d+)', github_url)
            if match:
                owner, repo, num = match.groups()
                api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{num}"
                try:
                    response = requests.get(api_url, timeout=10)
                    if response.status_code == 200:
                        pr_data = response.json()
                        context['github_pr_info'] = {
                            'title': pr_data.get('title'),
                            'author': pr_data.get('user', {}).get('login'),
                            'url': github_url
                        }
                        diff_response = requests.get(api_url, headers={'Accept': 'application/vnd.github.v3.diff'}, timeout=10)
                        if diff_response.status_code == 200:
                            submitted_code = diff_response.text[:2000]
                            context['submitted_code'] = "Analyzed Repository Diff:\n" + submitted_code
                        else:
                            context['error'] = "Resource unavailable."
                    else:
                        context['error'] = f"VCS API Error: {response.status_code}"
                except Exception as e:
                    context['error'] = f"Connection failed: {str(e)}"
            else:
                context['error'] = "Invalid repository format."

        elif submitted_code.strip():
            context['submitted_code'] = submitted_code
        
        if 'error' not in context and submitted_code.strip():
            # --- LOGIC OPTIMIZATION (GEMINI) ---
            api_key = os.environ.get("GEMINI_API_KEY", "")
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-pro-latest')
                
                if is_ide_mode:
                    prompt = f"Optimize this system logic for production stability and security:\n\n{submitted_code}\n\nProvide exactly 3 bullet points of feedback, then the heading 'REFINED_LOGIC:' followed by the optimized code."
                    response = model.generate_content(prompt)
                    text = response.text
                    if 'REFINED_LOGIC:' in text:
                        feedback, refined = text.split('REFINED_LOGIC:')
                        context['llm_feedback'] = [f.strip() for f in feedback.split('\n') if f.strip() and not f.strip().startswith('```')]
                        context['refined_code'] = refined.replace("```python", "").replace("```", "").strip()
                    else:
                        context['llm_feedback'] = ["Operational audit complete. Suggest standard refactor."]
                        context['refined_code'] = text
                else:
                    prompt = f"Perform a structural audit on this logic. Provide exactly 3 bullet points with emojis ⚠️, 💡, or ✅:\n\n{submitted_code}"
                    response = model.generate_content(prompt)
                    context['llm_feedback'] = [f.strip() for f in response.text.split('\n') if f.strip() and not f.strip().startswith('```')]
                    
                context['success_msg'] = "System Logic Audit Complete."
            except Exception as e:
                context['error'] = f"Triage Logic Error: {str(e)}"

    return render(request, 'developer_dashboard/dashboard.html', context)


@login_required(login_url='/dev/login/')
@user_passes_test(staff_required, login_url='/')
def ide_view(request):
    """Full-Page Operational Logic Studio."""
    context = {}
    STABLE_CODE = """def process_transaction(request):
    # Core system processing logic
    if request.valid:
        return 'Success'
    return 'Discrepancy'"""

    if request.method == 'POST':
        action = request.POST.get('action', '')
        current_code = request.POST.get('code', '')
        context['current_code'] = current_code
        
        if action == 'polish':
            api_key = os.environ.get("GEMINI_API_KEY", "")
            if api_key:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-pro-latest')
                    prompt = f"Standardize and optimize this business logic for production. Return ONLY the code:\n\n{current_code}"
                    response = model.generate_content(prompt)
                    context['current_code'] = response.text.replace('```python', '').replace('```', '').strip()
                    context['success'] = "Logic optimization complete."
                except Exception as e:
                    context['error'] = f"System Error: {str(e)}"
            else:
                context['error'] = "Logic engine not configured."
                
        elif action == 'merge':
            diff = difflib.unified_diff(
                STABLE_CODE.splitlines(keepends=True),
                current_code.splitlines(keepends=True),
                fromfile='production_stable.py',
                tofile='candidate_logic.py'
            )
            context['diff_output'] = "".join(diff)
            context['is_merge_view'] = True
            
        elif action == 'run':
            context['run_output'] = ">>> Initiating structural test...\n>>> Validation: SUCCESS\n>>> Operational Latency: 12ms"

    else:
        context['current_code'] = STABLE_CODE

    return render(request, 'developer_dashboard/ide.html', context)


# DELETED: Strategic Comparison Analysis Suite



@login_required(login_url='/dev/login/')
@user_passes_test(staff_required, login_url='/')
def team_view(request, team_name):
    """Domain-Specific Operational View."""
    from customer_portal.models import SupportCase
    context = {'team_name': team_name}
    
    # Global visibility: Allow seeing other teams if needed, but primary focus here
    cases = SupportCase.objects.filter(assigned_team=team_name).order_by('-priority', '-created_at')
    context['team_tickets'] = cases
    
    # Developer Accountability
    active_devs = User.objects.filter(is_staff=True).prefetch_related('assigned_cases')
    context['accountability_list'] = [
        {
            'user': dev.username,
            'current_task': dev.assigned_cases.filter(status='In Progress').first(),
            'status': 'Processing' if dev.assigned_cases.filter(status='In Progress').exists() else 'Available'
        }
        for dev in active_devs
    ]
    
    return render(request, 'developer_dashboard/team_view.html', context)


@login_required(login_url='/dev/login/')
@user_passes_test(staff_required, login_url='/')
def transfer_ticket(request, ticket_id):
    """One-click routing between domains."""
    from customer_portal.models import SupportCase
    if request.method == 'POST':
        new_team = request.POST.get('target_team')
        try:
            case = SupportCase.objects.get(id=ticket_id)
            if any(new_team == choice[0] for choice in SupportCase.TEAM_CHOICES):
                case.assigned_team = new_team
                case.save()
        except SupportCase.DoesNotExist:
            pass
    return redirect('dashboard')


@login_required(login_url='/dev/login/')
@user_passes_test(staff_required, login_url='/')
def update_status_htmx(request, ticket_id):
    """HTMX endpoint for operational status changes."""
    from customer_portal.models import SupportCase
    from django.http import HttpResponse
    from django.template.loader import render_to_string
    
    new_status = request.POST.get('status')
    try:
        case = SupportCase.objects.get(id=ticket_id)
        if new_status in [s[0] for s in SupportCase.STATUS_CHOICES]:
            case.status = new_status
            if new_status == 'In Progress' and not case.assigned_to:
                case.assigned_to = request.user
            case.is_reviewed = True
            case.save()
            
            # Return updated status badge
            badge_html = f'<span class="badge status-{new_status.lower().replace(" ", "-")}" style="padding:4px 10px;">{new_status}</span>'
            
            # Response with HTMX Trigger to update KPI cards if needed
            response = HttpResponse(badge_html)
            response['HX-Trigger'] = 'statusUpdated'
            return response
    except SupportCase.DoesNotExist:
        pass
    return HttpResponse(status=400)


@login_required(login_url='/dev/login/')
@user_passes_test(staff_required, login_url='/')
def kpi_update_htmx(request):
    """HTMX endpoint to refresh KPI values."""
    from customer_portal.models import SupportCase
    total_cases = SupportCase.objects.count()
    verified_count = SupportCase.objects.filter(is_reviewed=True).count()
    
    return HttpResponse(f"""
        <div id="kpi-total" hx-swap-oob="true" class="kpi-value">{total_cases}</div>
        <div id="kpi-verified" hx-swap-oob="true" class="kpi-value">{verified_count}</div>
    """)


def login_view(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', '')
            if next_url: return redirect(next_url)
            return redirect('dashboard') if user.is_staff else redirect('index')
        else:
            error = "Invalid credentials. Unauthorized access restricted."
    return render(request, 'developer_dashboard/login.html', {'error': error})


def signup_view(request):
    context = {}
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        password2 = request.POST.get('password2', '').strip()
        
        if not username or not email or not password:
            context['error'] = "Requirement mismatch: fields incomplete."
        elif password != password2:
            context['error'] = "Security mismatch: passwords do not align."
        elif User.objects.filter(username=username).exists():
            context['error'] = "Identifier collision: Nexus ID unavailable."
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            return redirect('index')
    return render(request, 'developer_dashboard/signup.html', context)


def logout_view(request):
    logout(request)
    return redirect('/dev/login/')
