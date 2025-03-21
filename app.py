import streamlit as st
import openai
import os
import random
import json
from dotenv import load_dotenv

# Load environment variables (create a .env file with your OPENAI_API_KEY)
load_dotenv()

# Get API Key from environment or secrets
api_key = os.getenv("NGC_API_KEY") or st.secrets.get("NGC_API_KEY")

# Initialize the OpenAI client
client = openai.OpenAI(
    base_url = "https://integrate.api.nvidia.com/v1",
    api_key = api_key
)

# Set up the Streamlit app
st.title("Caregiver Copilot")

def process_user_input(user_input):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Display user message
    if len(st.session_state.messages) > 2:
        with st.chat_message("user"):
            st.write(user_input)
    
    # Display assistant thinking
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        
        try:
            # Call OpenAI API
            response = client.chat.completions.create(
                model="nvidia/llama-3.3-nemotron-super-49b-v1",
                messages=[
                    {"role": m["role"], "content": m["content"]} 
                    for m in st.session_state.messages
                ]
            )
            
            # Get assistant response
            assistant_response = response.choices[0].message.content

            # Remove thinking content
            assistant_response = assistant_response.split('</think>')[1].strip()
            
            # Update placeholder with assistant response
            message_placeholder.markdown(assistant_response)
            
            # Add assistant response to history
            st.session_state.messages.append({"role": "assistant", "content": assistant_response})
        
        except Exception as e:
            message_placeholder.markdown(f"Error: {str(e)}")

    # If this is the first reply, add a second reply inviting to ask follow-up questions
    if len(st.session_state.messages) == 3:
        message = {"role": "assistant", "content": "Is there anything else I could help you with?"}
        st.session_state.messages.append(message)
        with st.chat_message(message["role"]):
            st.write(message["content"])

# Modified patient selection logic
if "patient_note" not in st.session_state:
    st.markdown("## For which patient should I provide support?")
    
    if 'patient_notes' not in st.session_state:
        with open('data/pmc_notes_100.json') as f:
            patient_notes = json.load(f)
            st.session_state.patient_notes = random.sample(patient_notes, k=3)
    
    # Create columns for better layout of patient selection buttons
    cols = st.columns(3)
    
    # Display patient selection buttons
    for i, note in enumerate(st.session_state.patient_notes):
        # Get a brief snippet of the patient note to show in the button
        snippet = note[:300] + "..." if len(note) > 300 else note
        
        # Alternate between columns
        col = cols[i % 3]
        
        # Create button for this patient
        if col.button(f"Select Patient {i+1}", key=f"patient_{i}"):
            st.session_state.patient_note = note
            
            # Force a rerun to update the UI
            st.rerun()

        # Display the snippet in a detail/summary tag
        col.markdown(f"""
        <details>
            <summary>{snippet}</summary>
            <p>{note[300:]}</p>
        </details>
        """, unsafe_allow_html=True)
else:

    # Display the snippet in a detail/summary tag
    st.markdown(f"""
    <details>
        <summary>{st.session_state.patient_note[0:300]}...</summary>
        <p>{st.session_state.patient_note[300:]}</p>
    </details>
    """, unsafe_allow_html=True)

    # Only initialize session state for message history when patient is selected
    if "messages" not in st.session_state:
        prompt_template = open('./prompt.md').read()
        prompt = prompt_template.replace('{PATIENT_NOTE}', st.session_state.patient_note)
        st.session_state.messages = [
            {"role":"system","content":"detailed thinking on"}
        ]

        process_user_input(prompt)

    else:

        # Display chat messages only when a patient is selected
        for message in st.session_state.messages[2:]:
            if message['role'] == 'system':
                continue
            with st.chat_message(message["role"]):
                st.write(message["content"])

    # Chat input area - only show when a patient is selected
    user_input = st.chat_input("Do you have another question?")

    # Process user input
    if user_input:
        process_user_input(user_input)