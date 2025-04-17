import google.generativeai as genai
import streamlit as st
import pandas as pd
import time
from datetime import datetime
import os
from fpdf import FPDF

API_KEY = "API KEY"
genai.configure(api_key=API_KEY)

if "chat" not in st.session_state:
    model = genai.GenerativeModel("gemini-1.5-pro")
    st.session_state["chat"] = model.start_chat()
    st.session_state["assessment_done"] = False
    st.session_state["submitted"] = False

st.title("Mental Health Assessment")
choice = st.radio("Choose an option:", ["Mental Health Assessment", "Chat with AI"])

if choice == "Mental Health Assessment":
    st.header("Mental Health Assessment")

    if st.session_state["assessment_done"]:
        st.warning("You have already completed the assessment.")
    else:
        if "personal_info_submitted" not in st.session_state:
            st.session_state["personal_info_submitted"] = False

        if not st.session_state["personal_info_submitted"]:
            name = st.text_input("Enter Your Name")
            Age = st.text_input("Enter Your Age")
            Gender = st.selectbox("Select Your Gender", ["Male", "Female", "Other", "Prefer not to say"])
            PhoneNumber = st.text_input("Enter Your Mobile Number")
            Email = st.text_input("Enter your Email Address")
            Occupation = st.text_input("Enter Your Occupation")

            if st.button("Submit Personal Info"):
                if name and Age and PhoneNumber and Email and Occupation:
                    st.session_state["personal_info_submitted"] = True
                    st.session_state["personal_info"] = {
                        "name": name,
                        "Age": Age,
                        "Gender": Gender,
                        "PhoneNumber": PhoneNumber,
                        "Email": Email,
                        "Occupation": Occupation
                    }
                else:
                    st.warning("Please fill in all fields before proceeding.")
        else:
            name = st.session_state["personal_info"]["name"]
            Age = st.session_state["personal_info"]["Age"]
            Gender = st.session_state["personal_info"]["Gender"]
            PhoneNumber = st.session_state["personal_info"]["PhoneNumber"]
            Email = st.session_state["personal_info"]["Email"]
            Occupation = st.session_state["personal_info"]["Occupation"]

            st.subheader("Assessment Questions")

            questions = [
                "How often do you feel anxious or worried?",
                "Do you have trouble sleeping at night?",
                "Have you been feeling sad or hopeless lately?",
                "Do you find it hard to focus or concentrate?",
                "Do you feel overwhelmed by your daily tasks?",
                "How often do you have mood swings?",
                "Are you still interested in activities you once enjoyed?",
                "Do you feel physically exhausted or tired often?",
                "Do you feel socially withdrawn or lonely?",
            ]

            responses = {}
            rating_map = {"Never": 1, "Rarely": 3, "Sometimes": 5, "Often": 7, "Always": 8}

            for question in questions:
                responses[question] = st.radio(question, ["Never", "Rarely", "Sometimes", "Often", "Always"], index=2)

            if st.button("Submit"):
                st.session_state["assessment_done"] = True
                st.session_state["submitted"] = True
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                with st.spinner("Processing your request..."):
                    time.sleep(2)
                    st.empty()

                    total_score = sum(rating_map[responses[q]] for q in responses)

                    if total_score <= 15:
                        mental_health_status = "Good Mental Health"
                    elif total_score <= 20:
                        mental_health_status = "Mild Concerns"
                    elif total_score <= 50:
                        mental_health_status = "Moderate Concerns"
                    else:
                        mental_health_status = "Severe concerns - Get Consultation"

                    responses_text = "\n".join([f"{q}: {responses[q]}" for q in responses])

                    assessment_prompt = f"""
You are a mental health expert AI designed to analyze psychological survey data.

Below are the responses from an individual named {name} to a mental health questionnaire. 

Please provide:
1. **Mental Health Summary** – A brief overview of their current mental state.
2. **Identified Symptoms** – List any psychological symptoms or patterns seen in the responses.
3. **Condition Prediction** – A potential condition they may be showing signs of (e.g., mild anxiety, moderate depression), if any.
4. **Detailed Analysis** – Breakdown of each area (anxiety, mood, focus, sleep, etc.) based on the answers.
5. **Recommendations** – Next steps like lifestyle changes, professional help, stress management, etc.
6. **Precautionary Measures** – Any red flags that should be closely monitored.
also **Analyse the person's response taking into {Occupation} and {Gender} and the {Age}

Respond in a structured and professional format. Here are the responses:

{responses_text}
"""
                    try:
                        chat = st.session_state["chat"]
                        ai_response = chat.send_message(assessment_prompt)
                        st.subheader("Your Mental Health Assessment:")
                        st.write(ai_response.text)
                        
                        st.session_state["ai_response_text"] = ai_response.text

                        pdf = FPDF()
                        pdf.add_page()
                        pdf.set_font("Arial", size=12)
                        for line in ai_response.text.split("\n"):
                            pdf.multi_cell(0, 10, line)
                        pdf_output = f"{name.replace(' ', '_')}_mental_health_assessment.pdf"
                        pdf.output(pdf_output)

                        with open(pdf_output, "rb") as file:
                            st.download_button("Download Assessment as PDF", file, file_name=pdf_output)
                    
                    except Exception as e:
                        st.error(f"Error: {e}")

                    data = {
                        "Timestamp": [timestamp],
                        "Name": [name],
                        "Age": [Age],
                        "Gender": [Gender],
                        "Phone Number": [PhoneNumber],
                        "Email": [Email],
                        "Mental Health Status": [mental_health_status],
                        "Anxiety Issues": [responses["How often do you feel anxious or worried?"]],
                        "Sleep Issues": [responses["Do you have trouble sleeping at night?"]],
                        "Hopelessness": [responses["Have you been feeling sad or hopeless lately?"]],
                        "LackOfFocus": [responses["Do you find it hard to focus or concentrate?"]],
                        "Overwhelming Issues": [responses["Do you feel overwhelmed by your daily tasks?"]],
                        "Mood Swings": [responses["How often do you have mood swings?"]],
                        "Interest Loss": [responses["Are you still interested in activities you once enjoyed?"]],
                        "Fatigue Issues": [responses["Do you feel physically exhausted or tired often?"]],
                        "Social Withdrawal": [responses["Do you feel socially withdrawn or lonely?"]],
                    }

                    df = pd.DataFrame(data)
                    file_exists = os.path.isfile("mental_health_responses.csv")
                    df.to_csv("mental_health_responses.csv", mode='a', index=False, header=not file_exists or os.path.getsize("mental_health_responses.csv") == 0)

                    st.session_state["csv_initialized"] = True
                    st.success("Responses saved successfully!")

elif choice == "Chat with AI":
    st.header("Chat with AI")

    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    for message in st.session_state["messages"]:
        with st.chat_message(message["participant"]):
            st.write(message["content"])

    user_input = st.chat_input("Ask something about mental well-being...")

    def is_mental_health_related(text):
        keywords = [
            "mental", "health", "stress", "anxiety", "depression", "therapy", "well-being",
            "emotion", "feeling", "sad", "happy", "mood", "panic", "counsel", "therapist",
            "overwhelm", "mind", "psychology", "burnout", "trauma", "motivation", "hello", "hi",
            "support", "self-care", "mental illness", "psychiatrist", "disorder", "grief", "lonely",
            "isolation", "crying", "worry", "fear", "hope", "healing", "distress", "talk", "cope",
            "relaxation", "mental state", "bipolar", "schizophrenia", "diagnosis", "cognitive",
            "counseling", "mood swings", "inner peace", "suicidal", "mental clarity", "mindfulness"
        ]
        return any(word in text.lower() for word in keywords)

    if user_input:
        st.session_state["messages"].append({"participant": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        if not is_mental_health_related(user_input):
            with st.chat_message("ai"):
                warning_message = (
                    "I'm here to help with **mental health-related queries** only. "
                    "Please ask something related to mental well-being."
                )
                st.write(warning_message)
                st.session_state["messages"].append({"participant": "ai", "content": warning_message})
        else:
            with st.chat_message("ai"):
                st.write("Loading...")
                try:
                    chat = st.session_state["chat"]
                    prompt = f"You are a mental health expert. Answer strictly related to mental well-being.\n\nUser: {user_input}"
                    ai_reply = chat.send_message(prompt)
                    st.session_state["messages"].append({"participant": "ai", "content": ai_reply.text})

                    st.empty()
                    st.write(ai_reply.text)
                except Exception as err:
                    st.error(f"Problem Encountered: {err}")
