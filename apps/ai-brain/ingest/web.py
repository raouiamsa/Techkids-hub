import requests
import json
import re
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from .shared import EMBEDDINGS, CHROMA_PERSIST_DIR
from .neo4j_store import get_neo4j_store
from .ingest_config import CHUNK_SIZE, CHUNK_OVERLAP

def report_progress(source_id: str, percent: int):
    """Communique la progression de l'indexation Web au Hub NestJS."""
    try:
        url = f"http://localhost:3000/api/ai/content-sources/{source_id}/progress"
        requests.patch(url, json={"progressPercent": percent})
    except:
        pass

def process_webpage(
    url: str,
    source_id: str,
    title: str | None = None,
    domain: str | None = None,
    source_metadata: dict | None = None,
):
    """
    Scrape, nettoie et indexe le contenu d'un site web.
    Ajoute les métadonnées nécessaires pour les citations (Titre du site).
    """
    print(f" Archiviste : Scraping de la page Web : {url}")
    report_progress(source_id, 20) # Début du chargement

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # 1. Récupération du contenu HTML
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        report_progress(source_id, 50) # Page récupérée
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 2. Extraction du titre pour les citations futures
        page_title = title or (soup.title.string.strip() if soup.title else "Site Web")
        
        # 3. Nettoyage du HTML (on retire le superflu)
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe"]):
            tag.extract()
            
        text = soup.get_text(separator=' ', strip=True)
        text = re.sub(r"\s+", " ", text).strip()

        # Certains sites (docs modernes) rendent le contenu côté JS.
        # On tente une extraction ciblée des paragraphes avant d'abandonner.
        if len(text) < 120:
            paragraph_candidates = [
                node.get_text(" ", strip=True)
                for node in soup.select("main p, article p, p, li")
            ]
            paragraph_text = " ".join(
                chunk for chunk in paragraph_candidates if len(chunk) > 30
            ).strip()
            text = re.sub(r"\s+", " ", paragraph_text).strip() or text

        if len(text) < 120:
            print(f" Contenu web insuffisant pour indexation: {url}")
            report_progress(source_id, 0)
            return False
        
        # 4. Création du document avec métadonnées de citation
        doc = Document(
            page_content=text, 
            metadata={
                "course_id": source_id, 
                "source_name": page_title, #  Pour les citations (ex: "Source: Wikipédia")
                "source_url": url,
                "type": "webpage"
            }
        )
        
        report_progress(source_id, 80) # Nettoyage terminé
        
        # 5. Découpage et Vectorisation
        splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        docs = splitter.split_documents([doc])
        docs = [chunk for chunk in docs if chunk.page_content and chunk.page_content.strip()]

        if not docs:
            print(f" Aucun segment valide extrait pour: {url}")
            report_progress(source_id, 0)
            return False

        for index, chunk in enumerate(docs):
            chunk.metadata["doc_id"] = f"{source_id}::web::{index:04d}"
            if domain:
                chunk.metadata["domain"] = domain
        
        Chroma.from_documents(documents=docs, embedding=EMBEDDINGS, persist_directory=CHROMA_PERSIST_DIR)
        get_neo4j_store().index_documents(
            resource_id=source_id,
            source_type="web",
            title=page_title,
            domain=domain,
            source_path_or_url=url,
            documents=docs,
        )
        
        report_progress(source_id, 100) # Terminé
        print(f" Page Web '{page_title}' indexée ({len(docs)} segments).")
        return True
        
    except Exception as e:
        print(f" Erreur lors de l'analyse du site Web : {e}")
        report_progress(source_id, 0) # Signalement d'erreur
        return False