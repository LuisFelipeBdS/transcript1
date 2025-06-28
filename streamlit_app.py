import streamlit as st
import google.generativeai as genai
import json
import time
from datetime import datetime
import re

# Configure the page
st.set_page_config(
    page_title="Medical Diagnosis Helper",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .diagnosis-item {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 5px;
        border-left: 4px solid #1f77b4;
    }
    .follow-up-question {
        background-color: #e8f4fd;
        padding: 8px;
        border-radius: 5px;
        margin-bottom: 5px;
        border-left: 3px solid #3498db;
    }
    .conduct-suggestion {
        background-color: #f0fff0;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #28a745;
    }
    .stProgress > div > div > div > div {
        background-color: #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'consultation_data' not in st.session_state:
    st.session_state.consultation_data = []
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'current_diagnoses' not in st.session_state:
    st.session_state.current_diagnoses = []
if 'follow_up_questions' not in st.session_state:
    st.session_state.follow_up_questions = []
if 'suggested_conduct' not in st.session_state:
    st.session_state.suggested_conduct = ""
if 'suggested_followup' not in st.session_state:
    st.session_state.suggested_followup = ""

def configure_gemini(api_key):
    """Configure Gemini AI with the provided API key"""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        return model
    except Exception as e:
        st.error(f"Error configuring Gemini AI: {str(e)}")
        return None

def get_ai_analysis(consultation_data, model):
    """Get AI analysis for diagnoses, follow-up questions, and conduct suggestions"""
    
    # Prepare the consultation history
    consultation_text = "\n".join([f"Input {i+1}: {data}" for i, data in enumerate(consultation_data)])
    
    prompt = f"""
As a medical AI assistant, analyze the following consultation data and provide:

Consultation Data:
{consultation_text}

Please provide your response in the following JSON format:
{{
    "diagnoses": [
        {{"condition": "Diagnosis 1", "probability": 85}},
        {{"condition": "Diagnosis 2", "probability": 70}},
        {{"condition": "Diagnosis 3", "probability": 45}},
        {{"condition": "Diagnosis 4", "probability": 30}}
    ],
    "follow_up_questions": [
        "Question 1 to gather more information",
        "Question 2 to clarify symptoms",
        "Question 3 to understand duration"
    ],
    "suggested_conduct": "Immediate actions and treatment recommendations",
    "suggested_followup": "Recommended examinations, tests, and follow-up appointments"
}}

Important:
- Diagnoses should be ranked by probability (highest first)
- Probabilities should be realistic and sum to reasonable medical uncertainty
- Follow-up questions should be specific and relevant to the current information
- Conduct suggestions should be immediate, actionable medical advice
- Follow-up should include specific tests, examinations, or specialist referrals
- Keep medical advice general and emphasize the need for proper medical evaluation
"""

    try:
        response = model.generate_content(prompt)
        
        # Extract JSON from response
        response_text = response.text
        
        # Find JSON in the response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            analysis = json.loads(json_str)
            return analysis
        else:
            st.error("Could not parse AI response. Please try again.")
            return None
            
    except json.JSONDecodeError as e:
        st.error(f"Error parsing AI response: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error getting AI analysis: {str(e)}")
        return None

def display_probability_bars(diagnoses):
    """Display diagnosis probabilities as progress bars"""
    st.markdown('<div class="section-header">🎯 Possible Diagnoses</div>', unsafe_allow_html=True)
    
    for i, diagnosis in enumerate(diagnoses):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f'<div class="diagnosis-item"><strong>{diagnosis["condition"]}</strong></div>', 
                       unsafe_allow_html=True)
            st.progress(diagnosis["probability"] / 100)
        
        with col2:
            st.metric("Probability", f"{diagnosis['probability']}%")

def display_follow_up_questions(questions):
    """Display suggested follow-up questions"""
    st.markdown('<div class="section-header">❓ Suggested Follow-up Questions</div>', unsafe_allow_html=True)
    
    for i, question in enumerate(questions):
        st.markdown(f'<div class="follow-up-question"><strong>Q{i+1}:</strong> {question}</div>', 
                   unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<div class="main-header">🏥 Medical Diagnosis Helper</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar for API key configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        api_key = st.text_input("Gemini API Key", type="password", value=st.session_state.api_key)
        
        if api_key:
            st.session_state.api_key = api_key
            st.success("✅ API Key configured")
        else:
            st.warning("🔑 Please enter your Gemini API key")
        
        st.markdown("---")
        st.header("📋 Consultation History")
        
        if st.session_state.consultation_data:
            for i, data in enumerate(st.session_state.consultation_data):
                with st.expander(f"Input {i+1}"):
                    st.write(data)
        else:
            st.info("No consultation data yet")
        
        if st.button("🗑️ Clear Session", type="secondary"):
            st.session_state.consultation_data = []
            st.session_state.current_diagnoses = []
            st.session_state.follow_up_questions = []
            st.session_state.suggested_conduct = ""
            st.session_state.suggested_followup = ""
            st.rerun()

    # Main content area
    if not st.session_state.api_key:
        st.warning("🔑 Please configure your Gemini API key in the sidebar to begin.")
        st.info("You can get a free Gemini API key from Google AI Studio: https://makersuite.google.com/")
        return

    # Configure Gemini
    model = configure_gemini(st.session_state.api_key)
    if not model:
        return

    # Input section
    st.markdown('<div class="section-header">📝 Medical Data Input</div>', unsafe_allow_html=True)
    
    # Text input for medical data
    medical_input = st.text_area(
        "Enter medical consultation data:",
        placeholder="Enter patient symptoms, vital signs, physical examination findings, medical history, etc.",
        height=150,
        key="medical_input"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("➕ Add Data", type="primary"):
            if medical_input.strip():
                st.session_state.consultation_data.append(medical_input.strip())
                
                # Get AI analysis
                with st.spinner("🤖 Analyzing data with AI..."):
                    analysis = get_ai_analysis(st.session_state.consultation_data, model)
                    
                    if analysis:
                        st.session_state.current_diagnoses = analysis.get("diagnoses", [])
                        st.session_state.follow_up_questions = analysis.get("follow_up_questions", [])
                        st.session_state.suggested_conduct = analysis.get("suggested_conduct", "")
                        st.session_state.suggested_followup = analysis.get("suggested_followup", "")
                
                # Clear input and rerun
                st.session_state.medical_input = ""
                st.rerun()
            else:
                st.error("Please enter some medical data before adding.")

    # Display results if we have consultation data
    if st.session_state.consultation_data:
        
        # Create two main columns
        left_col, right_col = st.columns([1, 1])
        
        with left_col:
            # Follow-up questions section
            if st.session_state.follow_up_questions:
                display_follow_up_questions(st.session_state.follow_up_questions)
        
        with right_col:
            # Diagnoses section
            if st.session_state.current_diagnoses:
                display_probability_bars(st.session_state.current_diagnoses)
        
        # Full-width sections for conduct and follow-up
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="section-header">🩺 Suggested Conduct</div>', unsafe_allow_html=True)
            if st.session_state.suggested_conduct:
                st.markdown(f'<div class="conduct-suggestion">{st.session_state.suggested_conduct}</div>', 
                           unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="section-header">📋 Suggested Follow-up</div>', unsafe_allow_html=True)
            if st.session_state.suggested_followup:
                st.markdown(f'<div class="conduct-suggestion">{st.session_state.suggested_followup}</div>', 
                           unsafe_allow_html=True)
    
    # Footer disclaimer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.9rem; margin-top: 2rem;'>
        ⚠️ <strong>Medical Disclaimer:</strong> This tool is for educational and assistance purposes only. 
        It should not replace professional medical judgment or consultation. 
        Always verify recommendations with proper medical evaluation and current clinical guidelines.
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 