
from django.shortcuts import render

from users.forms import  UserRegistrationForm
from django.shortcuts import render, redirect
from django.contrib import messages

from .models import UserRegistrationModel
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import UserRegistrationModel


def base(request):
    return render(request,'base.html')



def UserRegisterActions(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'You have been successfully registered') 
            return render(request,'UserRegistration.html')
        else:
            messages.error(request, 'Email or Mobile Already Exists')
    else:
        form = UserRegistrationForm()
    return render(request, 'UserRegistration.html', {'form': form})


def UserLoginCheck(request):
    if request.method == "POST":
        loginid = request.POST.get('loginid')
        pswd = request.POST.get('password')  # Corrected key to match the form input name
        try:
            user = UserRegistrationModel.objects.get(loginid=loginid, password=pswd)
            if user.status == "activated":
                request.session['id'] = user.id
                request.session['loggeduser'] = user.name
                return redirect('UserHome')  # Redirect to User Home after successful login
            else:
                messages.error(request, 'Your account is not activated.')
        except UserRegistrationModel.DoesNotExist:
            messages.error(request, 'Invalid Login ID or Password')
    return render(request, 'UserLogin.html')  # Ensure this is the correct template name


def UserHome(request):
    return render(request, 'users/UserHome.html')


import os
import re
import zlib
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
import google.generativeai as genai
from dotenv import load_dotenv

# Load .env variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY", "AIzaSyAysVqWZ-Ydq8NTcPZN6QwpVX5JkEDE17Q"))

# 🛠 Corrected encoding functions
def plantuml_encode(text):
    deflate = zlib.compressobj(level=9, method=zlib.DEFLATED, wbits=-15)
    compressed = deflate.compress(text.encode('utf-8')) + deflate.flush()
    return encode_plantuml_base64(compressed)

def encode_plantuml_base64(data):
    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
    result = ""
    i = 0
    while i < len(data):
        b1 = data[i]
        b2 = data[i+1] if i+1 < len(data) else 0
        b3 = data[i+2] if i+2 < len(data) else 0
        i += 3

        c1 = b1 >> 2
        c2 = ((b1 & 0x3) << 4) | (b2 >> 4)
        c3 = ((b2 & 0xF) << 2) | (b3 >> 6)
        c4 = b3 & 0x3F

        result += alphabet[c1 & 0x3F] + alphabet[c2 & 0x3F] + alphabet[c3 & 0x3F] + alphabet[c4 & 0x3F]
    return result

# 🧠 Gemini to generate PlantUML
def generate_diagram_code(prompt):
    try:
        model = genai.GenerativeModel("models/gemini-2.0-flash")
        system_prompt = (
            "You are a PlantUML diagram generator.\n"
            "Return ONLY PlantUML code enclosed with @startuml and @enduml.\n"
            "No markdown, no extra formatting.\n"
            f"{prompt}"
        )
        response = model.generate_content(system_prompt)
        text = response.text.strip()

        if not (text.startswith("@startuml") and text.endswith("@enduml")):
            return None, "⚠️ Invalid format: Missing @startuml or @enduml"

        return text, None
    except Exception as e:
        return None, f"❌ Gemini Error: {str(e)}"


def code_to_diagram_view(request):
    ai_response = ""
    diagram_url = ""
    uploaded_code_filename = None

    if request.method == 'POST':
        query = request.POST.get('query', '').strip()
        uploaded_file = request.FILES.get('code_file')

        try:
            prompt = query
            if uploaded_file:
                fs = FileSystemStorage()
                filename = fs.save(uploaded_file.name, uploaded_file)
                uploaded_code_filename = fs.url(filename)
                with open(fs.path(filename), 'r', encoding='utf-8') as f:
                    file_text = f.read()
                    prompt += "\n" + file_text

            plantuml_code, error = generate_diagram_code(prompt)

            if plantuml_code:
                encoded = plantuml_encode(plantuml_code)
                diagram_url = f"https://www.plantuml.com/plantuml/png/{encoded}"
            else:
                ai_response = error

        except Exception as e:
            ai_response = f"❌ Error: {str(e)}"

    return render(request, 'users/generate.html', {
        'ai_response': ai_response,
        'diagram_url': diagram_url,
        'uploaded_code_filename': uploaded_code_filename,
    })
