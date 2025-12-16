from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import os 
import json
from .models import load_enrolled, save_enrolled, log_access, extract_features, voice_match, REQUIRED_PHRASE, ADMIN_PASSWORD, get_user_entry_count

enrolled_users = load_enrolled()

def home(request):
    return render(request, 'core/home.html')

def admin_login_view(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        if password == ADMIN_PASSWORD:
            request.session['is_admin'] = True
            return redirect('admin_dashboard')
        else:
            return render(request, 'core/admin_login.html', {'error': 'Wrong password'})
    return render(request, 'core/admin_login.html')
from .models import get_user_entry_count  

def admin_dashboard(request):
    if not request.session.get('is_admin'):
        return redirect('admin_login')
    
    enrolled_users = load_enrolled()
    total_logs = 0
    successful_entries = 0
    
    if os.path.exists(settings.LOG_FILE):
        with open(settings.LOG_FILE, 'r') as f:
            lines = f.readlines()
            total_logs = len(lines)
            successful_entries = sum(1 for line in lines if 'GRANTED' in line)
    
    return render(request, 'core/admin_dashboard.html', {
        'users': enrolled_users,
        'total_logs': total_logs,
        'successful_entries': successful_entries
    })
def logout(request):
    request.session.flush()
    return redirect('home')

@csrf_exempt
def enroll(request):
    if request.method == 'POST' and request.session.get('is_admin'):
        data = json.loads(request.body)
        username = data.get('username')
        full_name = data.get('full_name')
        email = data.get('email')
        role = data.get('role')
        samples = data.get('samples')

        if not all([username, full_name, email, role, samples]):
            return JsonResponse({'success': False, 'error': 'Missing data'})

        features = []
        for i, wav_base64 in enumerate(samples):
            try:
                import base64
                wav_bytes = base64.b64decode(wav_base64.split(',')[1])
                feature = extract_features(wav_bytes)
                if feature is not None:
                    features.append(feature)
                else:
                    print(f"Sample {i+1} failed to embed")
            except Exception as e:
                print(f"Sample {i+1} error: {e}")

        if len(features) >= 1:  # Allow 1 for testing; change to 2 later
            enrolled_users[username] = {
                'details': {'full_name': full_name, 'email': email, 'role': role},
                'features': features
            }
            save_enrolled(enrolled_users)
            log_access("Admin", True)
            return JsonResponse({'success': True, 'message': f'{username} enrolled with {len(features)} good samples!'})
        else:
            return JsonResponse({'success': False, 'error': 'Not enough good samples. Speak clearly and loudly for 5–10 seconds.'})

    return JsonResponse({'error': 'Invalid request'})
@csrf_exempt
def unlock(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        wav_base64 = data.get('audio')
        if not wav_base64:
            return JsonResponse({'success': False, 'error': 'No audio'})

        import base64
        wav_bytes = base64.b64decode(wav_base64.split(',')[1])
        feature = extract_features(wav_bytes)

        matched = False
        matched_user = None
        matched_details = {}
        for username, user_data in enrolled_users.items():
            match, confidence = voice_match(user_data['features'], feature)
            if match:
                matched = True
                matched_user = username
                matched_details = user_data['details']
                break

        if matched:
            log_access(matched_user, True)
            entry_count = get_user_entry_count(matched_user)
            return JsonResponse({
                'success': True,
                'user': matched_user,
                'details': matched_details,
                'entry_count': entry_count
            })
        else:
            log_access("Unknown", False)
            return JsonResponse({'success': False, 'error': 'Voice not recognized'})

def logs(request):
    if os.path.exists(settings.LOG_FILE):
        with open(settings.LOG_FILE, 'r') as f:
            lines = f.readlines()[-20:]
        return JsonResponse({'logs': lines})
    return JsonResponse({'logs': []})

def unlock_page(request):
    return render(request, 'core/unlock_page.html')
