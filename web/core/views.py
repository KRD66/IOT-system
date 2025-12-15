from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
from .models import load_enrolled, save_enrolled, log_access, extract_features, voice_match, REQUIRED_PHRASE, ADMIN_PASSWORD
import os

enrolled_users = load_enrolled()

def home(request):
    return render(request, 'core/home.html')

def admin_login_view(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        if password == ADMIN_PASSWORD:
            request.session['is_admin'] = True
            return redirect('admin_panel')
        else:
            return render(request, 'core/admin_login.html', {'error': 'Wrong password'})
    return render(request, 'core/admin_login.html')

def admin_panel(request):
    if not request.session.get('is_admin'):
        return redirect('admin_login')
    return render(request, 'core/admin_panel.html', {'users': list(enrolled_users.keys())})

@csrf_exempt
def enroll(request):
    if request.method == 'POST' and request.session.get('is_admin'):
        data = json.loads(request.body)
        username = data.get('username')
        samples = data.get('samples')  # list of base64 wav bytes (we'll handle in JS)

        if not username or not samples:
            return JsonResponse({'success': False, 'error': 'Missing data'})

        features = []
        for wav_base64 in samples:
            import base64
            wav_bytes = base64.b64decode(wav_base64.split(',')[1])  # data:audio/wav;base64,...
            feature = extract_features(wav_bytes)
            if feature is not None:
                features.append(feature)

        if len(features) >= 2:
            enrolled_users[username] = features
            save_enrolled(enrolled_users)
            log_access("Admin", True)
            return JsonResponse({'success': True, 'message': f'{username} enrolled!'})
        else:
            return JsonResponse({'success': False, 'error': 'Not enough good samples'})

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

        # Simple phrase check (we'll do client-side + server fallback)
        # For now, trust client did phrase check

        matched = False
        matched_user = None
        for username, features in enrolled_users.items():
            match, confidence = voice_match(features, feature)
            if match:
                matched = True
                matched_user = username
                break

        if matched:
            log_access(matched_user, True)
            return JsonResponse({'success': True, 'user': matched_user})
        else:
            log_access("Unknown", False)
            return JsonResponse({'success': False, 'error': 'Voice not recognized'})

def logs(request):
    if os.path.exists(settings.LOG_FILE):
        with open(settings.LOG_FILE, 'r') as f:
            lines = f.readlines()[-20:]
        return JsonResponse({'logs': lines})
    return JsonResponse({'logs': []})