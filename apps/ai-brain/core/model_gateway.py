import os
import requests
from dotenv import load_dotenv

load_dotenv()

class ModelGateway:
    """
    Passerelle centralisee pour appeler les modeles d'IA.
    Prend en charge le modele Fine-Tune local (Ollama) valide lors du Benchmarking.
    """
    def __init__(self):
        self.nvidia_key = os.getenv("NVIDIA_API_KEY")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.google_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        
        # URL par défaut pour Ollama local (où tournera le Llama 3.1 Fine-Tuné)
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    def invoke(self, model_id, provider, sys_prompt, user_input, format_json=False):
        """
        Route la requete vers le fournisseur specifie dans la SELECTION_MATRIX.
        `format_json` permet de forcer la sortie JSON si l'API le supporte.
        """
        provider = provider.lower()
        if provider == "ollama" or provider == "local":
            return self._invoke_ollama(model_id, sys_prompt, user_input, format_json)
        elif provider == "nvidia":
            return self._invoke_nvidia(model_id, sys_prompt, user_input)
        elif provider == "openrouter":
            return self._invoke_openrouter(model_id, sys_prompt, user_input)
        elif provider == "groq":
            return self._invoke_groq(model_id, sys_prompt, user_input)
        elif provider == "google":
            return self._invoke_google(model_id, sys_prompt, user_input)
        else:
            raise ValueError(f"Provider inconnu: {provider}")

    def _invoke_ollama(self, model_id, sys_prompt, user_input, format_json):
        """
        Appel vers le serveur Ollama local contenant le modèle fine-tuné (Llama 3.1).
        Respecte la température définie lors du Benchmarking.
        """
        url = f"{self.ollama_base_url}/api/chat"
        
        payload = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_input}
            ],
            "stream": False,
            "options": {
                "temperature": 0.2,
                "top_p": 0.9,
                "num_ctx": 8192
            }
        }
        
        if format_json:
            payload["format"] = "json"

        try:
            # Timeout plus long car l'inférence locale peut prendre du temps
            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()
            return response.json()["message"]["content"]
        except Exception as e:
            print(f"[ERREUR] Impossible de contacter Ollama local ({model_id}): {e}")
            return "ERROR_GENERATION_LOCAL"

    def _invoke_groq(self, model_id, sys_prompt, user_input):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.groq_key}", "Content-Type": "application/json"}
        payload = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_input}
            ],
            "temperature": 0.2, "max_tokens": 4096, "stream": False
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Erreur API Groq ({model_id}): {e}")
            return "ERROR_GENERATION_GROQ"

    def _invoke_google(self, model_id, sys_prompt, user_input):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={self.google_key}"
        headers = {"Content-Type": "application/json"}
        combined_prompt = f"{sys_prompt}\n\nInstruction utilisateur: {user_input}"
        payload = {
            "contents": [{"parts": [{"text": combined_prompt}]}],
            "generationConfig": {"temperature": 0.15, "maxOutputTokens": 2048}
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=90)
            response.raise_for_status()
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            print(f"Erreur API Google ({model_id}): {e}")
            return "ERROR_GENERATION_GOOGLE"

    def _invoke_nvidia(self, model_id, sys_prompt, user_input):
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.nvidia_key}", "Accept": "application/json"}
        temp, max_tk = (1.0, 4096) if "kimi" in model_id.lower() or "thinking" in model_id.lower() else (0.15, 2048)
        payload = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_input}
            ],
            "max_tokens": max_tk, "temperature": temp, "stream": False
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Erreur API NVIDIA ({model_id}): {e}")
            return "ERROR_GENERATION_NVIDIA"

    def _invoke_openrouter(self, model_id, sys_prompt, user_input):
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.openrouter_key}", "HTTP-Referer": "https://techkids-hub.com", "X-Title": "Benchmark AI"}
        payload = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_input}
            ],
            "temperature": 0.2, "stream": False
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Erreur API OpenRouter ({model_id}): {e}")
            return "ERROR_GENERATION_OPENROUTER"