import os
import json
import asyncio
import aiohttp
import aio_pika
import uvicorn
import json_repair
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from ingest import ingest_source
from agents import create_course_graph

# --- Configuration du Worker (RabbitMQ) ---
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://techkids:techkids@localhost:5672/")
QUEUE_NAME   = "techkids_main_queue"
EVENT_NAME   = "source.indexing.requested"
API_WEBHOOK  = "http://localhost:3000/api/ai/content-sources"

# Clé secrète pour authentifier le Cerveau auprès de NestJS
INTERNAL_SECRET = os.getenv("INTERNAL_AI_SECRET", "votre-secret-pfe-2026")

# --- Fonctions du Worker (Tâches en arrière-plan) ---

async def notify_gateway(source_id: str, status: str):
    """Notifie NestJS de la fin ou de l'échec de l'indexation avec authentification."""
    url = f"{API_WEBHOOK}/{source_id}/status"
    async with aiohttp.ClientSession() as session:
        try:
            #  SÉCURITÉ : On ajoute le secret attendu par NestJS
            headers = {"x-ai-secret": INTERNAL_SECRET}
            async with session.patch(url, json={"status": status}, headers=headers) as resp:
                if resp.status == 200:
                    print(f" Webhook notifié : source {source_id} -> {status}")
                else:
                    print(f" Webhook erreur {resp.status} pour {source_id}")
        except Exception as e:
            print(f" Erreur lors de la notification du statut : {e}")

async def process_rabbitmq_message(message: aio_pika.IncomingMessage):
    """Traite les messages de RabbitMQ pour lancer l'ingestion asynchrone."""
    async with message.process():
        try:
            payload = json.loads(message.body.decode())
            # NestJS encapsule souvent les données dans 'data'
            data = payload.get("data", payload)
            pattern = payload.get("pattern")

            if pattern != EVENT_NAME:
                return

            source_id   = data.get("sourceId")
            source_type = data.get("type", "PDF")
            file_path   = data.get("filePath")
            url         = data.get("url")
            
            if not source_id:
                print(" Message ignoré : sourceId manquant.")
                return

            print(f" Background : Début indexation pour {source_id} ({source_type})...")
            # Détermination du chemin (Fichier local pour PDF, URL pour le reste)
            source_path = file_path if source_type.upper() == "PDF" else url
            
            # Offload vers un thread pour ne pas bloquer l'Event Loop asynchrone
            await asyncio.to_thread(ingest_source, source_type, source_path, str(source_id))

            print(f" Background : Indexation terminée pour {source_id}")
            await notify_gateway(str(source_id), "READY")

        except Exception as e:
            print(f" Background Error : {e}")
            try:
                # Tentative de notification d'erreur si l'ID est disponible
                body_err = json.loads(message.body.decode())
                sid = body_err.get("data", {}).get("sourceId")
                if sid: await notify_gateway(str(sid), "ERROR")
            except: pass

async def start_background_worker():
    """Écoute continue de la file RabbitMQ."""
    print(" Worker RabbitMQ en attente de tâches d'indexation...")
    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        async with connection:
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=1)
            queue = await channel.declare_queue(QUEUE_NAME, durable=True)
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    await process_rabbitmq_message(message)
    except Exception as e:
        print(f" Connexion au Worker impossible : {e}")

# --- Gestion du cycle de vie (FastAPI Lifespan) ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Lancement du Worker RabbitMQ au démarrage de l'API
    worker_task = asyncio.create_task(start_background_worker())
    yield
    # Arrêt propre lors de la fermeture
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        print("Worker arrêté proprement.")

# --- Configuration de l'API ---

app = FastAPI(title="TechKids Hub - AI Brain", lifespan=lifespan)

# --- Modèles de données (Pydantic) ---

class CourseRequest(BaseModel):
    input_request: str
    course_ids: List[str]
    age_group: int
    level: str = "BEGINNER"
    teacher_feedback: Optional[str] = ""
    include_code_exercises: bool = False
    draft_id: Optional[str] = None
    programming_language: Optional[str] = "Python"
    internal_secret: Optional[str] = "" #  Passé par le Gateway NestJS
    existing_content: Optional[str] = None
    existing_syllabus: Optional[str] = None

class SyllabusRequest(BaseModel):
    input_request: str
    course_ids: List[str]
    age_group: int
    level: str = "BEGINNER"
    programming_language: Optional[str] = "Python"
    teacher_notes: Optional[str] = ""

class PracticeRequest(BaseModel):
    concept: str
    age_group: int
    level: str = "BEGINNER"
    student_mistake: Optional[str] = ""
    is_success: bool = False
    language: str = "fr"

class IndexCourseRequest(BaseModel):
    course_id: str
    content: str
    title: Optional[str] = "Untitled Course"
    student_mistake: Optional[str] = ""
    is_success: bool = False
    language: str = "Python"

class TutorRequest(BaseModel):
    code: str
    question: str
    language: str = "python"
    exercise_instructions: str = ""

class GradeCodeRequest(BaseModel):
    student_code: str
    execution_output: str
    instructions: str
    teacher_solution: Optional[str] = ""

# --- Points d'Entrée (Endpoints) ---

@app.get("/")
def root():
    return {"status": "online", "engine": "Sophie Chen 2.1"}

@app.post("/generate")
async def api_generate(req: CourseRequest):
    """Génération de cours riche via LangGraph (Sophie Chen)."""
    try:
        graph = create_course_graph()
        initial_state = {
            "input_request": req.input_request,
            "course_ids": req.course_ids,
            "age_group": req.age_group,
            "level": req.level,
            "teacher_feedback": req.teacher_feedback,
            "include_code_exercises": req.include_code_exercises,
            "draft_id": req.draft_id,
            "iterations": 0,
            "source_documents": [],
            "programming_language": req.programming_language,
            "internal_secret": req.internal_secret or INTERNAL_SECRET,
            "content": [req.existing_content] if req.existing_content else [],
            "syllabus": req.existing_syllabus or "",
        }
        
        # Invocation du graphe d'agents (bloquant, donc on l'isole en thread)
        result = await asyncio.to_thread(graph.invoke, initial_state)
        
        return {
            "status": "success",
            "syllabus": result.get("syllabus"),
            "content": result.get("content", [])[-1] if result.get("content") else "",
            "placement_bank": result.get("placement_bank"),
            "certification_bank": result.get("certification_bank"),
            "final_project": result.get("final_project"),
            "ai_score": result.get("ai_score", 0),
            "sources": result.get("source_documents", [])
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur Génération : {str(e)}")

@app.post("/generate-syllabus")
async def api_generate_syllabus(req: SyllabusRequest):
    """Génère uniquement le syllabus (Architecte seul)."""
    try:
        from agents.architect import architect_node
        state = {
            "input_request": req.input_request,
            "course_ids": req.course_ids,
            "age_group": req.age_group,
            "level": req.level,
            "programming_language": req.programming_language,
            "teacher_feedback": req.teacher_notes or "",
            "syllabus": "",
            "content": [],
            "iterations": 0,
        }
        result = await asyncio.to_thread(architect_node, state)
        return {"status": "success", "syllabus": result.get("syllabus")}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-practice")
async def api_generate_practice(req: PracticeRequest):
    """Génération d'un Mini-Module Practice More (Adaptive Learning)."""
    try:
        from agents.practice import generate_practice_module
        module = await asyncio.to_thread(
            generate_practice_module,
            req.concept,
            req.age_group,
            req.level,
            req.student_mistake,
            req.is_success,
            req.language
        )
        return {"status": "success", "module": module}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/index-course")
async def api_index_course(req: IndexCourseRequest):
    """Indexe un cours approuvé dans ChromaDB pour le Tuteur RAG."""
    try:
        from core.rag_manager import RAGManager
        rag = RAGManager()
        success = await asyncio.to_thread(
            rag.index_course,
            req.course_id,
            req.content,
            req.title
        )
        return {"status": "success", "indexed": success}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/index-course")
async def api_index_course(req: IndexCourseRequest):
    """Indexe un cours approuvé dans ChromaDB pour le Tuteur RAG."""
    try:
        from core.rag_manager import RAGManager
        rag = RAGManager()
        success = await asyncio.to_thread(
            rag.index_course,
            req.course_id,
            req.content,
            req.title
        )
        return {"status": "success", "indexed": success}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/grade-code")
async def api_grade_code(req: GradeCodeRequest):
    """Évalue le code de l'élève à l'aide de l'IA Socratique."""
    try:
        from core.model_gateway import ModelGateway
        
        prompt = f"""
Tu es un professeur de programmation expert. Évalue le code de l'étudiant.
Instructions de l'exercice :
{req.instructions}

Code de l'étudiant :
{req.student_code}

Sortie console / exécution (peut contenir des erreurs ou la sortie standard) :
{req.execution_output}

Analyse si le code répond à l'énoncé de manière logique. Si l'exercice demande d'écrire un algorithme ou du code Arduino (comme faire clignoter une LED), prends en compte les fonctions utilisées.
Le score doit être un entier entre 0 et 100.
Donne un feedback court, positif et constructif pour l'enfant.
Retourne UNIQUEMENT un objet JSON valide avec la structure exacte suivante, sans aucun texte autour ni bloc markdown :
{{"score": 80, "feedback": "Bravo, mais tu as oublié le delay!"}}
"""
        gateway = ModelGateway()
        response = await asyncio.to_thread(
            gateway.invoke,
            "gemini-1.5-flash",
            "google",
            prompt,
            "Analyse le code et retourne un JSON."
        )
        
        import json_repair
        try:
            parsed = json_repair.loads(response)
        except Exception:
            parsed = {"score": 50, "feedback": "L'IA n'a pas pu analyser précisément, mais bel effort !"}
            
        # S'assurer que le score est un entier
        score = int(parsed.get("score", 0)) if str(parsed.get("score", "0")).isdigit() else 0
        return {"score": score, "feedback": parsed.get("feedback", "")}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/simulate-circuit")
async def api_simulate_circuit(req: dict):
    """Simulateur de circuit électronique."""
    try:
        from core.circuit_simulator import CircuitSimulator, CircuitRequest
        # Parsing manuel pour être souple
        circuit_req = CircuitRequest(**req)
        simulator = CircuitSimulator()
        result = await asyncio.to_thread(simulator.simulate, circuit_req)
        
        # Socratic AI Integration !
        if result.get("led_status") == "EXPLODED":
            from core.model_gateway import ModelGateway
            from core.rag_manager import RAGManager
            
            # Recherche du contexte dans le cours
            rag = RAGManager()
            context = await asyncio.to_thread(rag.search_context, "LED grillée résistance surintensité", top_k=1)
            
            context_prompt = f"\n\n--- CONTEXTE DU COURS OFFICIEL ---\n{context}\n--------------------------------\n" if context else ""
            prompt = f"""
### SYSTEM ROLE
Tu es un tuteur expert en ingénierie et pédagogie Socratique pour enfants. 
Ton objectif est de guider l'élève vers la découverte de l'erreur sans jamais lui donner la solution.

### INPUT DATA
- Objectif du cours : {context_prompt}
- Données Physiques (PySpice) : {result}

### ANALYSE PROTOCOL (Interne)
Avant de répondre, analyse les points suivants :
1. **Intégrité Physique** : Est-ce que le courant (mA) ou la tension (V) dépasse les limites des composants ?
2. **Écart Pédagogique** : Quelle est la différence entre le branchement actuel et l'objectif du circuit ?

### RÉPONSE AU PETIT INGÉNIEUR
Rédige une réponse courte (max 3 phrases) en suivant ces règles :
- **Langue** : Un mélange fluide de Français et de Tunisien (Darija).
- **Ton** : Enthousiaste, valorisant ("Ya Batal", "Ya Engenieur").
- **Stratégie** : Pose une question qui force l'enfant à regarder ses composants (ex: as-tu oublié une résistance ?).
- **Exemple de style** : "يا بطل، التركيب متاعك طيارة! أما ثبت في الـ LED، حسب الـ Simulator تعدالها {result.get('current_mA')}mA... ما فماش حاجة تنقص في قوة الكهرباء باش ما تتحرقش؟"
"""
            
            """prompt = (
                "Tu es un tuteur bienveillant d'électronique pour enfants. "
                "L'enfant vient de lancer une simulation de circuit. "
                "Le moteur physique (PySpice) a détecté un court-circuit ou une surintensité "
                f"({result.get('current_mA', 'trop élevé')} mA). La LED a grillé.\n"
                f"{context_prompt}"
                "En te basant strictement sur le CONTEXTE DU COURS s'il est fourni, "
                "dis-lui que son programme Arduino fonctionne bien, mais qu'il a oublié de protéger la LED. "
                "Guide-le pour qu'il ajoute une résistance, mais NE LUI DONNE PAS LA SOLUTION directement. "
                "Fais-le réfléchir avec une question. Parle en français ou tunisien."
            )"""
            
            # Appel asynchrone à Gemini via le ModelGateway
            gateway = ModelGateway()
            ai_message = await asyncio.to_thread(
                gateway.invoke,
                "gemini-1.5-flash", 
                "google", 
                prompt, 
                "Analyse ce résultat et donne moi le retour."
            )
            if "ERROR_" in ai_message:
                ai_message = "Oups, j'ai eu un petit problème de connexion !  Mais attention, ton circuit a un problème : ta LED a grillé car il y a eu trop de courant. As-tu pensé à ajouter une résistance ?"
            result["message"] = ai_message
        elif result.get("led_status") == "ON":
            result["message"] = "Super ! La LED s'allume correctement sans brûler."
        else:
            result["message"] = "Le circuit est ouvert, la LED est éteinte."
            
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)