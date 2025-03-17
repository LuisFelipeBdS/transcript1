import streamlit as st
import os
import tempfile
from openai import OpenAI
import time

# Set page configuration
st.set_page_config(
    page_title="Class Notes Generator",
    page_icon="📝",
    layout="wide"
)

# Main title
st.title("🎓 Class Notes Generator")
st.markdown("Upload an audio recording of your class to generate comprehensive notes and study materials.")

# Sidebar for API Key
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Enter your OpenAI API Key", type="password")
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    This app helps students:
    1. Transcribe class recordings from Brazilian Portuguese
    2. Generate detailed study notes
    3. Identify key concepts and potential test questions
    """)

# Initialize the OpenAI client
@st.cache_resource
def get_openai_client(api_key):
    return OpenAI(api_key=api_key)

# Function to transcribe audio using Whisper API
def transcribe_audio(client, audio_file_path):
    with open(audio_file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-1",
            language="pt"  # Brazilian Portuguese
        )
    return transcript.text

# Function to generate study notes using GPT
def generate_notes(client, transcript):
    prompt = f"""
    A seguir está a transcrição de uma aula em português brasileiro. 
    Por favor, gere notas de estudo detalhadas baseadas nesta aula, incluindo:
    
    1. Resumo geral da aula
    2. Conceitos principais e definições
    3. Pontos mais importantes que o professor enfatizou
    4. Como este assunto provavelmente seria cobrado em uma prova
    5. Possíveis questões que o professor poderia fazer sobre este conteúdo
    6. Ao final, faça um comentário geral sobre o que o professor quis passar com a aula, algo como uma ideia geral
    
    Transcrição:
    {transcript}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Você é um assistente acadêmico especializado em criar materiais de estudo detalhados a partir de transcrições de aulas."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    
    return response.choices[0].message.content

# Main application flow
def main():
    if not api_key:
        st.warning("Por favor, insira sua chave da API OpenAI na barra lateral para começar.")
        return
    
    try:
        client = get_openai_client(api_key)
    except Exception as e:
        st.error(f"Erro ao configurar o cliente OpenAI: {e}")
        return
    
    # File uploader
    uploaded_file = st.file_uploader("Faça upload do arquivo de áudio da aula", type=['mp3', 'wav', 'ogg', 'm4a'])
    
    if uploaded_file:
        # Display audio player
        st.audio(uploaded_file, format='audio/ogg')
        
        # Process button
        if st.button("Processar Áudio e Gerar Notas"):
            with st.spinner("Processando o áudio..."):
                # Save the uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    audio_path = tmp_file.name
                
                try:
                    # Step 1: Transcribe
                    with st.status("Transcrevendo o áudio...") as status:
                        transcript = transcribe_audio(client, audio_path)
                        status.update(label="Transcrição completa!", state="complete")
                    
                    # Step 2: Generate notes
                    with st.status("Gerando notas detalhadas...") as status:
                        notes = generate_notes(client, transcript)
                        status.update(label="Notas geradas com sucesso!", state="complete")
                    
                    # Delete the temporary file
                    os.unlink(audio_path)
                    
                    # Display results in tabs
                    tab1, tab2 = st.tabs(["Notas de Estudo", "Transcrição Original"])
                    
                    with tab1:
                        st.markdown(notes)
                        
                        # Download button for notes
                        st.download_button(
                            label="Download das Notas",
                            data=notes,
                            file_name="notas_de_aula.md",
                            mime="text/markdown"
                        )
                    
                    with tab2:
                        st.markdown("### Transcrição Completa")
                        st.text_area("", transcript, height=400)
                        
                        # Download button for transcript
                        st.download_button(
                            label="Download da Transcrição",
                            data=transcript,
                            file_name="transcricao.txt",
                            mime="text/plain"
                        )
                
                except Exception as e:
                    st.error(f"Ocorreu um erro: {str(e)}")
    
    # Sample of what the app does
    with st.expander("Como usar este aplicativo"):
        st.markdown("""
        **Passo a passo:**
        1. Insira sua chave da API OpenAI na barra lateral
        2. Faça upload do arquivo de áudio da sua aula
        3. Clique em "Processar Áudio e Gerar Notas"
        4. Aguarde enquanto o aplicativo:
           - Transcreve o áudio usando OpenAI Whisper
           - Analisa o conteúdo e gera notas detalhadas
        5. Baixe as notas e a transcrição para usar em seus estudos
        
        **Observação:** Certifique-se de ter autorização do professor para gravar a aula.
        """)

if __name__ == "__main__":
    main()