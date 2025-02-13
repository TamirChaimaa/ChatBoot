from flask import Flask, render_template, request, jsonify
import openai
import os
from PyPDF2 import PdfReader
from docx import Document  # Assurez-vous d'avoir la bibliothèque python-docx installée

app = Flask(__name__)

# Configuration de l'API OpenAI avec la clé API depuis une variable d'environnement


def load_documents():
    """
    Charger les documents dynamiquement depuis le dossier 'documents'.
    """
    documents = []
    documents_path = "documents"

    if not os.path.exists(documents_path):
        return ["Le dossier 'documents' est introuvable."]

    # Charger les fichiers TXT
    for file in os.listdir(documents_path):
        file_path = os.path.join(documents_path, file)
        if file.endswith(".txt"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    documents.extend([line.strip() for line in f if line.strip()])
            except Exception as e:
                documents.append(f"Erreur de lecture du fichier TXT {file}: {e}")

    # Charger les fichiers PDF
    for file in os.listdir(documents_path):
        file_path = os.path.join(documents_path, file)
        if file.endswith(".pdf"):
            try:
                reader = PdfReader(file_path)
                for page in reader.pages:
                    text = page.extract_text().strip()
                    if text:
                        documents.append(text)
            except Exception as e:
                documents.append(f"Erreur de lecture du fichier PDF {file}: {e}")

    # Charger les fichiers Word
    for file in os.listdir(documents_path):
        file_path = os.path.join(documents_path, file)
        if file.endswith(".docx"):
            try:
                doc = Document(file_path)
                for paragraph in doc.paragraphs:
                    if paragraph.text.strip():
                        documents.append(paragraph.text.strip())
            except Exception as e:
                documents.append(f"Erreur de lecture du fichier Word {file}: {e}")

    return documents

def search_documents(user_input):
    """
    Rechercher des documents pertinents.
    """
    documents = load_documents()
    results = [doc for doc in documents if any(word.lower() in doc.lower() for word in user_input.split())]
    return results if results else ["Aucun document pertinent trouvé."]

def get_chatbot_response(user_input):
    """
    Envoyer un message à GPT avec des documents contextuels.
    """
    # Rechercher des documents pertinents
    relevant_docs = search_documents(user_input)
    context = "\n".join(relevant_docs[:5]) if relevant_docs else "Aucun contexte disponible."

    # Construire le message pour GPT
    messages = [
        {"role": "system", "content": "Tu es un assistant expert en formation et coaching. Utilise les informations fournies pour donner des réponses précises et personnalisées."},
        {"role": "assistant", "content": f"Contexte pertinent :\n{context}"},
        {"role": "user", "content": user_input}
    ]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Assurez-vous d'utiliser le bon modèle, "gpt-4" ou autre.
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        return response['choices'][0]['message']['content']

    except Exception as e:
        return f"Une erreur est survenue lors de l'appel à l'API OpenAI : {e}"

@app.route('/')
def index():
    """
    Affiche la page HTML principale.
    """
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """
    Endpoint pour gérer les requêtes du chatbot.
    """
    try:
        user_input = request.json.get('message', '')
        if not user_input:
            return jsonify({"response": "Aucun message n'a été fourni."})
        
        response = get_chatbot_response(user_input)
        return jsonify({"response": response})

    except Exception as e:
        return jsonify({"response": f"Une erreur est survenue : {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
