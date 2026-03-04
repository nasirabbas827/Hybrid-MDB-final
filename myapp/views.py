from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.conf import settings

import os
import joblib
import csv

# ────────────────────────────────────────────────
# IMPORTS — MODELS & FORMS
# ────────────────────────────────────────────────
from .forms import (
    UserRegisterForm,
    LoginForm,
    UpdateProfileForm,
    MDBPostForm,
    GlobalKeywordForm,
)
from .models import (
    UserRegister,
    GlobalKeyword,
    MDBMessage,
    ModelPerformance,
    Review,
    Dataset,
)

# =============================================================================
#                           HELPER FUNCTIONS
# =============================================================================

def load_latest_models():
    """
    Loads the most recently trained vectorizer + logistic regression model.
    Returns (None, None) if no models exist or files are missing.
    """
    latest_dataset = Dataset.objects.order_by('-uploaded_at').first()
    if not latest_dataset:
        return None, None

    model_dir = os.path.join(settings.MEDIA_ROOT, "trained_models")
    vec_path = os.path.join(model_dir, f"vectorizer_{latest_dataset.id}.pkl")
    lr_path  = os.path.join(model_dir, f"logistic_regression_{latest_dataset.id}.pkl")

    if not all(os.path.exists(p) for p in [vec_path, lr_path]):
        return None, None

    try:
        vectorizer = joblib.load(vec_path)
        lr_model   = joblib.load(lr_path)
        return vectorizer, lr_model
    except Exception:
        return None, None


def get_current_user(request, required_role=None):
    """
    Helper: Retrieve currently logged-in user from session.
    Returns user object or redirects with error message.
    """
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Session expired. Please log in again.")
        return None, redirect('login')

    try:
        user = UserRegister.objects.get(id=user_id)
    except UserRegister.DoesNotExist:
        messages.error(request, "User account not found. Please log in again.")
        return None, redirect('login')

    if required_role and user.role != required_role:
        messages.error(request, f"Only {required_role}s can access this page.")
        return None, redirect('login')

    return user, None


# =============================================================================
#                           PUBLIC VIEWS
# =============================================================================

def index(request):
    """Landing / home page"""
    return render(request, 'index.html')


def register(request):
    """
    User registration (student or teacher).
    WARNING: Stores password in plain text → only for prototype!
    """
    if request.method == 'POST':
        form = UserRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            # Plain-text password (NOT secure — prototype only)
            user.password = form.cleaned_data['password']
            user.status = 'active'
            user.save()

            messages.success(request, "Registration successful. Please login.")
            return redirect('login')
    else:
        form = UserRegisterForm()

    return render(request, 'register.html', {'form': form})


def login(request):
    """
    Login using email + password + role.
    Uses plain-text password comparison (prototype only).
    """
    form = LoginForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        email    = form.cleaned_data['email']
        password = form.cleaned_data['password']
        role     = form.cleaned_data['role']

        try:
            user = UserRegister.objects.get(email=email, role=role)
        except UserRegister.DoesNotExist:
            messages.error(request, "Invalid credentials.")
            return redirect('login')

        if user.password == password:
            if user.status == 'active':
                # Set session
                request.session['user_id']   = user.id
                request.session['user_name'] = user.full_name
                request.session['user_role'] = user.role

                # Role-based redirection
                if user.role == 'teacher':
                    return redirect('teacher_dashboard')
                elif user.role == 'student':
                    return redirect('student_dashboard')
            else:
                messages.error(request, "Your account is inactive. Contact admin.")
        else:
            messages.error(request, "Invalid credentials.")

    return render(request, 'login.html', {'form': form})


def logout(request):
    """Clear session and log out user"""
    request.session.flush()
    messages.success(request, "Logged out successfully.")
    return redirect('index')


# =============================================================================
#                           STUDENT VIEWS
# =============================================================================

def student_dashboard(request):
    """Student dashboard — post messages & see own history"""
    user, redirect_resp = get_current_user(request, required_role='student')
    if redirect_resp:
        return redirect_resp

    if request.method == 'POST':
        form = MDBPostForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.posted_by = user
            message.save()
            messages.success(request, "Message posted successfully.")
            return redirect('student_dashboard')
    else:
        form = MDBPostForm()

    messages_list = MDBMessage.objects.filter(posted_by=user).order_by('-created_at')
    total_messages = messages_list.count()

    context = {
        'full_name': user.full_name,
        'form': form,
        'messages_list': messages_list,
        'total_messages': total_messages,
    }
    return render(request, 'student_dashboard.html', context)


# =============================================================================
#                           TEACHER VIEWS
# =============================================================================

def teacher_dashboard(request):
    """
    Teacher main dashboard:
      • Shows recent model performances
      • Recent messages + keyword vs AI classification comparison
      • Allows teachers to correct AI predictions
    """
    user, redirect_resp = get_current_user(request, required_role='teacher')
    if redirect_resp:
        return redirect_resp

    # ─── GET: Display dashboard ───────────────────────────────────────
    if request.method == 'GET':
        performances = ModelPerformance.objects.order_by('-trained_at')

        # Latest keyword set
        keywords = GlobalKeyword.objects.order_by('-created_at').first()

        # Recent messages (last 50)
        messages_qs = MDBMessage.objects.order_by('-created_at')[:50]

        comparison_data = []
        for msg in messages_qs:
            if not keywords:
                keyword_label = 'non_academic'
            else:
                academic_words = [w.strip().lower() for w in keywords.academic_keywords.split(',') if w.strip()]
                keyword_label = 'academic' if any(w in msg.content.lower() for w in academic_words) else 'non_academic'

            # Placeholder — replace with real model inference
            ai_prediction = 'academic'

            comparison_data.append({
                'message': msg,
                'keyword_label': keyword_label,
                'ai_label': ai_prediction,
                'misclassified': keyword_label != ai_prediction,
            })

        context = {
            'full_name': request.session.get('user_name', user.full_name),
            'performances': performances,
            'comparison_data': comparison_data,
        }
        return render(request, 'teacher_dashboard.html', context)

    # ─── POST: Save teacher corrections ───────────────────────────────
    if request.method == 'POST':
        saved_count = 0

        for key, corrected_label in request.POST.items():
            if not key.startswith('label_'):
                continue

            try:
                message_id = int(key.removeprefix('label_'))
                message_obj = MDBMessage.objects.get(id=message_id)

                if corrected_label not in ('academic', 'non_academic'):
                    continue

                comment = request.POST.get(f"comment_{message_id}", '').strip() or None

                Review.objects.update_or_create(
                    message=message_obj,
                    reviewer=user,
                    defaults={
                        'corrected_label': corrected_label,
                        'comment': comment,
                    }
                )
                saved_count += 1

            except (ValueError, MDBMessage.DoesNotExist):
                continue

        if saved_count > 0:
            messages.success(request, f"Saved {saved_count} correction(s).")
        else:
            messages.warning(request, "No valid corrections were submitted.")

        return redirect('teacher_dashboard')

    return redirect('teacher_dashboard')


def teacher_mdb_messages(request):
    """
    Paginated view of all MDB messages.
    Supports:
      • Search
      • Toggle between keyword-based vs AI-based labeling
    """
    user, redirect_resp = get_current_user(request, required_role='teacher')
    if redirect_resp:
        return redirect_resp

    mode = request.POST.get('mode', 'ai') if request.method == 'POST' else 'ai'
    query = request.POST.get('q', '').strip() if request.method == 'POST' else ''

    messages_qs = MDBMessage.objects.select_related('posted_by').order_by('-created_at')
    if query:
        messages_qs = messages_qs.filter(content__icontains=query)

    paginator = Paginator(messages_qs, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # ─── Keyword classification ───────────────────────────────
    latest_gk = GlobalKeyword.objects.order_by('-created_at').first()
    academic_keywords   = [k.strip().lower() for k in (latest_gk.academic_keywords.split(',')   if latest_gk else [])]
    non_academic_keywords = [k.strip().lower() for k in (latest_gk.non_academic_keywords.split(',') if latest_gk else [])]

    # ─── AI model classification ──────────────────────────────
    vectorizer, lr_model = load_latest_models()
    models_available = bool(vectorizer and lr_model)

    # ─── Prepare display data ─────────────────────────────────
    messages_data = []
    for msg in page_obj:
        content_lower = msg.content.lower()

        # Keyword-based label
        academic_count   = sum(1 for kw in academic_keywords   if kw in content_lower)
        non_academic_count = sum(1 for kw in non_academic_keywords if kw in content_lower)

        if academic_count > non_academic_count:
            keyword_label = 'academic'
        elif non_academic_count > academic_count:
            keyword_label = 'non_academic'
        else:
            keyword_label = 'unlabeled'

        # AI-based label
        ai_label = lr_model.predict(vectorizer.transform([msg.content]))[0] if models_available else 'unlabeled'

        selected_label = ai_label if mode == 'ai' else keyword_label

        messages_data.append({
            'msg': msg,
            'keyword_label': keyword_label,
            'ai_label': ai_label,
            'selected_label': selected_label,
        })

    context = {
        'messages_data': messages_data,
        'query': query,
        'total_messages': MDBMessage.objects.count(),
        'mode': mode,
        'models_available': models_available,
        'page_obj': page_obj,           # for pagination controls
    }

    return render(request, 'teacher_mdb_messages.html', context)


def teacher_mdb_messages_export_csv(request):
    """
    Export filtered MDB messages to CSV (all matching records — no pagination).
    Uses same filtering & labeling logic as teacher_mdb_messages view.
    """
    user, redirect_resp = get_current_user(request, required_role='teacher')
    if redirect_resp:
        return redirect_resp

    query = request.GET.get('q', '').strip()
    mode  = request.GET.get('mode', 'ai')

    messages_qs = MDBMessage.objects.select_related('posted_by').order_by('-created_at')
    if query:
        messages_qs = messages_qs.filter(content__icontains=query)

    latest_gk = GlobalKeyword.objects.order_by('-created_at').first()
    academic_keywords   = [k.strip().lower() for k in (latest_gk.academic_keywords.split(',')   if latest_gk else [])]
    non_academic_keywords = [k.strip().lower() for k in (latest_gk.non_academic_keywords.split(',') if latest_gk else [])]

    vectorizer, lr_model = load_latest_models()
    models_available = bool(vectorizer and lr_model)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="mdb_messages_filtered.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Message', 'Selected Label', 'Keyword Label',
        'AI Label', 'Posted By', 'Created At'
    ])

    for msg in messages_qs:
        content_lower = msg.content.lower()

        academic_count   = sum(1 for kw in academic_keywords   if kw in content_lower)
        non_academic_count = sum(1 for kw in non_academic_keywords if kw in content_lower)

        keyword_label = 'academic' if academic_count > non_academic_count else \
                        'non_academic' if non_academic_count > academic_count else 'unlabeled'

        ai_label = lr_model.predict(vectorizer.transform([msg.content]))[0] if models_available else 'unlabeled'

        selected_label = ai_label if mode == 'ai' else keyword_label

        posted_by_name = msg.posted_by.full_name if msg.posted_by else '—'

        writer.writerow([
            msg.id,
            msg.content.replace('\n', ' ').replace('\r', ''),
            selected_label,
            keyword_label,
            ai_label,
            posted_by_name,
            msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])

    return response


# =============================================================================
#                           PROFILE & KEYWORDS
# =============================================================================

def update_profile(request):
    """Update own profile (any logged-in user)"""
    if not request.session.get('user_id'):
        messages.error(request, "Please login first.")
        return redirect('login')

    user = get_object_or_404(UserRegister, id=request.session['user_id'])

    if request.method == 'POST':
        form = UpdateProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('update_profile')
    else:
        form = UpdateProfileForm(instance=user)

    return render(request, 'update_profile.html', {
        'form': form,
        'user': user
    })


def manage_keywords(request):
    """
    Manage global academic/non-academic keyword lists.
    Usually restricted to teachers/admins.
    """
    # You may want to add role check here (teacher/admin only)

    # Get most recent keyword record
    gk = GlobalKeyword.objects.order_by('-created_at').first()

    if request.method == 'POST':
        form = GlobalKeywordForm(request.POST, instance=gk)
        if form.is_valid():
            form.save()
            messages.success(request, "Keywords saved successfully.")
            return redirect('manage_keywords')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = GlobalKeywordForm(instance=gk)

    context = {
        'form': form,
        'latest_keywords': gk,
    }
    return render(request, 'manage_keywords.html', context)