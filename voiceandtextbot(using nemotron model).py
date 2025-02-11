import streamlit as st
import requests
import json
import csv
import speech_recognition as sr
import pyttsx3
import os
# Set API configuration
API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"  # Replace with your actual model's API endpoint
API_KEY = "Place your api key here"  # Replace with your actual API key

# List of fields to extract
fields = { 
  'loan_amount': None,
    'promotion_applied': None,
    'loan_purpose': None,
    'how_heard': None,
    'first_name': None,
   'last_name': None,
    'membership_status': None,
    'account_number': None,
    'telephone': None,
    'email': None,
    'date_of_birth': None,
    'marital_status': None,
    'whatsapp_opt_in': None,
    'employer_name': None,
    'self_employed': None,
    'primary_income': None,
    'additional_income': None,
    'total_income': None,
    'commitments': [],
    'declaration': None,
    'uploaded_ids': [],
    'uploaded_documents': [],
    'reference1_name': None,
    'reference1_relation': None,
    'reference1_address': None,
    'reference1_contact': None,
    'reference1_occupation': None,
    'reference2_name': None,
    'reference2_relation': None,
    'reference2_address': None,
    'reference2_contact': None,
    'reference2_occupation': None
}

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "extracted_fields" not in st.session_state:
    st.session_state.extracted_fields = fields.copy()
if "voice_input" not in st.session_state:
    st.session_state.voice_input = ""
# Save data to CSV function

def save_to_csv(data):
    file_name = r"Give your csv file path here"
    
    # Check if the file already exists
    file_exists = os.path.exists(file_name)
    
    with open(file_name, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fields.keys())
        
        # Write header only if the file is new
        if not file_exists:
            writer.writeheader()
        
        # Write the data (values only)
        writer.writerow(data)

def speak_text(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def get_audio_input():
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            st.write("Listening...")
            recognizer.adjust_for_ambient_noise(source, duration=0.2)
            audio = recognizer.listen(source)
            text = recognizer.recognize_google(audio).lower()
            return text
    except sr.RequestError as e:
        st.error(f"API Error: {e}")
    except sr.UnknownValueError:
        st.warning("Could not understand the audio.")
    return ""

# Extract fields function
def extract_fields_from_chat(chat_history):
    chat_history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history])
    fields_to_extract = ", ".join(fields.keys())
    prompt = (
        f"Extract the following fields from this chat history and return them as a single dictionary in valid JSON format. "
        f"The output must contain all fields with their corresponding values. If a field is not mentioned, set its value to null.\n\n"
        f"Fields to extract: {fields_to_extract}\n\n"
        f"Chat History:\n{chat_history_text}"
        f"Dont give here is the ... line just the list is enough"
        f"also make sure the list is not present within '`' marks"
        f"just give the list with a single dictionary nothing else"
        f"dont give the dictionary inside '```' just give the dictionary"
    )

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "nvidia/llama-3.1-nemotron-70b-instruct",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 1000,
        "stream": False
    }

    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        try:
            response_data = response.json()
            #st.write("**Raw API Response:**", response_data)

            # Extract content string
            extracted_string = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
            #st.write("1",extracted_string)
            # Remove any surrounding code block formatting (```)
            exstr=""
            for i in range(len(extracted_string)):
                if extracted_string[i]=="{":
                    exstr = extracted_string[i:]
            extracted_string = exstr.strip("```")
            #st.write("2",extracted_string)
            # Parse JSON string into a dictionary
            extracted_data = json.loads(extracted_string)
            return extracted_data
        except (KeyError, json.JSONDecodeError):
            st.error("Failed to parse JSON from response.")
            return {}
    else:
        st.error(f"Error {response.status_code}: {response.text}")
        return {}

# Streamlit UI
st.title("Field Extraction Chatbot 🤖")
st.write("A chatbot that identifies key fields from your prompts and stores them in a CSV file.")

#user_input = st.text_input("Your Message:", placeholder="Enter your message or type 'end' to finish.")
user_input = st.text_input("Your Message (or use the microphone):", placeholder="Type your message here.")

# Use microphone button
if st.button("Use Microphone"):
    st.session_state.voice_input = get_audio_input()
    if st.session_state.voice_input:
        st.write(f"Did you say: {st.session_state.voice_input}")

# Combine text and voice input
if st.session_state.voice_input and not user_input:
    user_input = st.session_state.voice_input

if st.button("Send"):
    if user_input:
        # Check if chat history exists, else initialize it
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        # Add system message to guide the model
        if len(st.session_state.chat_history) == 0:
            st.session_state.chat_history.append({
                "role": "system",
                "content": "You are a helpful assistant. Please respond concisely in a single short paragraph."
            })

        # Append user input to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Send user input to the model for a response
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "nvidia/llama-3.1-nemotron-70b-instruct",  # Replace with your model name
            "messages": st.session_state.chat_history,
            "temperature": 0.7,
            "max_tokens": 500,
            "stream": False
        }
        response = requests.post(API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            response_data = response.json()
            
            bot_response = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Append bot response to chat history
            st.session_state.chat_history.append({"role": "assistant", "content": bot_response})
            
            # Display chat history
            st.write(f"**Bot:** {bot_response}")
            speak_text(bot_response)
            
            # Extract features
            # Extract features
            extracted_data = extract_fields_from_chat(st.session_state.chat_history)
            #st.write("check",extracted_data)
            if extracted_data:  # Ensure extracted_data is a dictionary
                for key, value in extracted_data.items():  # extracted_data should now be a single dictionary
                    if value is not None:  # Only update if the value is not null
                        st.session_state.extracted_fields[key] = value
                st.write("Updated Extracted Fields:", st.session_state.extracted_fields)


            # Check for missing fields
            #st.write("hello",st.session_state.extracted_fields)
            missing_fields = [key for key, value in st.session_state.extracted_fields.items() if value is None]
            if missing_fields:
                next_field = missing_fields[0]
                st.write(f"**Bot:** Could you please provide your {next_field.replace('_', ' ')}?")
                speak_text(f"Could you please provide your {next_field.replace('_', ' ')}?")
            else:
                st.success("All features have been extracted. Thank you!")
                save_to_csv(st.session_state.extracted_fields)
                st.stop()

        else:
            st.error(f"Error {response.status_code}: {response.text}")
    else:
        st.warning("Please enter a message.")
