import streamlit as st
import google.generativeai as genai
import json
import time
from datetime import datetime
import re

# Configure the page
st.set_page_config(
    page_title="Auxílio de Diagnóstico (ALPHA)",
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
if 'input_key' not in st.session_state:
    st.session_state.input_key = 0

def configure_gemini(api_key):
    """Configure Gemini AI with the provided API key"""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
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
    "suggested_conduct": "Immediate actions and treatment recommendations, in Brazilian Portuguese",
    "suggested_followup": "Recommended examinations, tests, and follow-up appointments, in Brazilian Portuguese"
}}

Important:
- Diagnoses should be ranked by probability (highest first) and must be in Brazilian Portuguese
- Probabilities should be realistic and sum to reasonable medical uncertainty
- Follow-up questions should be specific and relevant to the current information
- Conduct suggestions should be immediate, actionable medical advice
- Follow-up should include specific tests, examinations, or specialist referrals
- Keep medical advice general and emphasize the need for proper medical evaluation
"""

    try:
        st.write("🔍 Debug: Mandando request...")
        response = model.generate_content(prompt)
        
        # Extract JSON from response
        response_text = response.text
        st.write("🔍 Debug: Resposta recebida")
        st.write("🔍 Debug: Preview da resposta:", response_text[:200] + "..." if len(response_text) > 200 else response_text)
        
        # Find JSON in the response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            st.write("🔍 Debug: Found JSON in response")
            analysis = json.loads(json_str)
            st.write("🔍 Debug: Successfully parsed JSON")
            return analysis
        else:
            st.error("Could not parse AI response. Please try again.")
            st.write("🔍 Debug: No JSON found in response")
            return None
            
    except json.JSONDecodeError as e:
        st.error(f"Error parsing AI response: {str(e)}")
        st.write("🔍 Debug: JSON decode error")
        return None
    except Exception as e:
        st.error(f"Error getting AI analysis: {str(e)}")
        st.write(f"🔍 Debug: General error: {str(e)}")
        return None

def display_probability_bars(diagnoses):
    """Display diagnosis probabilities as progress bars"""
    st.markdown('<div class="section-header">🎯 Possíveis Diagnósticos</div>', unsafe_allow_html=True)
    
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
    st.markdown('<div class="section-header">❓ Perguntas sugeridas</div>', unsafe_allow_html=True)
    
    for i, question in enumerate(questions):
        st.markdown(f'<div class="follow-up-question"><strong>Q{i+1}:</strong> {question}</div>', 
                   unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<div class="main-header">🏥 Auxílio de Diagnóstico (ALPHA)</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar for API key configuration
    with st.sidebar:
        st.header("⚙️ Configurações")
        api_key = st.text_input("Chave API", type="password", value=st.session_state.api_key)
        
        if api_key:
            st.session_state.api_key = api_key
            st.success("✅ Chave API Aceita")
        else:
            st.warning("🔑 Chave API")
        
        st.markdown("---")
        st.header("📋 Histórico da Consulta")
        
        if st.session_state.consultation_data:
            for i, data in enumerate(st.session_state.consultation_data):
                with st.expander(f"Input {i+1}"):
                    st.write(data)
        else:
            st.info("Sem informações até o momento")
        
        if st.button("🗑️ Clear Session", type="secondary"):
            st.session_state.consultation_data = []
            st.session_state.current_diagnoses = []
            st.session_state.follow_up_questions = []
            st.session_state.suggested_conduct = ""
            st.session_state.suggested_followup = ""
            st.session_state.input_key += 1
            st.rerun()

    # Main content area
    if not st.session_state.api_key:
        st.warning("🔑 Configure a chave API ao lado para inicial.")
        st.info("Sistema em ALPHA, sujeito à mudanças")
        return

    # Configure Gemini
    model = configure_gemini(st.session_state.api_key)
    if not model:
        return

    # Input section
    st.markdown('<div class="section-header">📝 Informações do Caso Clínico</div>', unsafe_allow_html=True)
    
    # Text input for medical data
    medical_input = st.text_area(
        "Insira dados acerca do caso clínico:",
        placeholder="Sintomas, sinais vitais, exame físico, histórico médico, etc.",
        height=150,
        key=f"medical_input_{st.session_state.input_key}"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("➕ Processar", type="primary"):
            if medical_input.strip():
                st.session_state.consultation_data.append(medical_input.strip())
                
                # Get AI analysis
                with st.spinner("🤖 Analizando informações com a IA..."):
                    analysis = get_ai_analysis(st.session_state.consultation_data, model)
                    
                    if analysis:
                        st.session_state.current_diagnoses = analysis.get("diagnoses", [])
                        st.session_state.follow_up_questions = analysis.get("follow_up_questions", [])
                        st.session_state.suggested_conduct = analysis.get("suggested_conduct", "")
                        st.session_state.suggested_followup = analysis.get("suggested_followup", "")
                
                # Clear input by incrementing key and rerun
                st.session_state.input_key += 1
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
            st.markdown('<div class="section-header">🩺 Conduta SUGERIDA</div>', unsafe_allow_html=True)
            if st.session_state.suggested_conduct:
                st.markdown(f'<div class="conduct-suggestion">{st.session_state.suggested_conduct}</div>', 
                           unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="section-header">📋 Seguimento SUGERIDO</div>', unsafe_allow_html=True)
            if st.session_state.suggested_followup:
                st.markdown(f'<div class="conduct-suggestion">{st.session_state.suggested_followup}</div>', 
                           unsafe_allow_html=True)
    
    # Footer disclaimer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.9rem; margin-top: 2rem;'>
        ⚠️ <strong>Informação Legal:</strong> Essa ferramenta, no estado atual, está em desenvolvimento. 
        Ela não deve nem pode substituir uma consulta médica completa, nem o discernimento do profissional médico. 
        Sempre verifique as informações e as valide com as guidelines mais atualizadas.
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 