import os
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from xhtml2pdf import pisa
from django.template.loader import get_template
import google.generativeai as genai

from .models import UserRegistrationModel
from users.forms import UserRegistrationForm

# ✅ Gemini API Key
genai.configure(api_key="AIzaSyAysVqWZ-Ydq8NTcPZN6QwpVX5JkEDE17Q")


# ✅ Base Page
def base(request):
    return render(request, 'base.html')


# ✅ User Registration
def UserRegisterActions(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registration successful.') 
            return render(request, 'UserRegistration.html')
        else:
            messages.error(request, 'Email or Mobile Already Exists')
    else:
        form = UserRegistrationForm()
    return render(request, 'UserRegistration.html', {'form': form})


# ✅ User Login
def UserLoginCheck(request):
    if request.method == "POST":
        loginid = request.POST.get('loginid')
        pswd = request.POST.get('password')
        try:
            user = UserRegistrationModel.objects.get(loginid=loginid, password=pswd)
            if user.status == "activated":
                request.session['id'] = user.id
                request.session['loggeduser'] = user.name
                return redirect('UserHome')
            else:
                messages.error(request, 'Your account is not activated.')
        except UserRegistrationModel.DoesNotExist:
            messages.error(request, 'Invalid Login ID or Password')
    return render(request, 'UserLogin.html')


# ✅ User Dashboard
def UserHome(request):
    return render(request, 'users/UserHome.html')


# ✅ Gemini Utility: Ask Gemini with a prompt
def call_gemini(prompt):
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")    # super fast, newer
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"❌ Gemini Error: {str(e)}"


# ✅ Generative AI Recommender View (based on GANs, VAEs, Hybrid)
def genai_recommender_view(request):
    output = ""
    task = ""
    
    if request.method == 'POST':
        task = request.POST.get("task_type")
        input_text = request.POST.get("input_text", "").strip()

        # Select prompt based on task
        if task == "generate":
            prompt = f"""
Act as a Generative AI system for recommendation. Generate synthetic user-item interaction data using GANs or VAEs.
Context:\n{input_text}
            """
        elif task == "cold_start":
            prompt = f"""
Explain how Generative AI (GANs/VAEs/Hybrids) can solve the cold-start problem in recommender systems.
Scenario:\n{input_text}
            """
        elif task == "diversity":
            prompt = f"""
Suggest how to enhance recommendation diversity using Generative AI (like VAEs or GANs).
Context:\n{input_text}
            """
        elif task == "evaluate":
            prompt = f"""
Analyze the following recommender system design and provide suggestions to improve it using Generative AI (e.g., GANs, VAEs, Transformer models):
\n{input_text}
            """
        else:
            prompt = "Invalid task."

        output = call_gemini(prompt)

    return render(request, 'users/genai_recommender.html', {
        "output": output,
        "task": task
    })


# ✅ Export Gemini Output to PDF
def export_pdf(request):
    if request.method == 'POST':
        html = request.POST.get("pdf_content", "")
        template = get_template("users/pdf.html")
        html_content = template.render({'content': html})
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="genai_output.pdf"'
        pisa_status = pisa.CreatePDF(html_content, dest=response)
        if pisa_status.err:
            return HttpResponse('Error generating PDF', status=500)
        return response
