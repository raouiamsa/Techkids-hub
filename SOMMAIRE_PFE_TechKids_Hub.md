# SOMMAIRE

## Introduction générale

## Dédicace

## Remerciements

## Liste des figures et tableaux

## Introduction générale

## Chapitre 1 : Cadre Général du Projet

### Introduction

### 1.1 Présentation de l'organisme d'accueil
- 1.1.1 Fiche d'identité
- 1.1.2 Services et activités
- 1.1.3 Secteur d'activité

### 1.2 Problématique et motivation
- 1.2.1 Contexte du projet
- 1.2.2 Problématique
- 1.2.3 Objectifs du projet

### 1.3 Solution proposée : TechKids Hub
- 1.3.1 Vision et concept "Phygital"
- 1.3.2 Architecture microservices
- 1.3.3 Les différentiateurs clés

### 1.4 Méthodologie de travail
- 1.4.1 Méthodologie Agile Scrum
  - 1.4.1.1 Principes fondamentaux
  - 1.4.1.2 Organisation en sprints
  - 1.4.1.3 Artifacts Scrum (Product Backlog, Sprint Backlog, Burndown Chart)
- 1.4.2 Cycle de vie GenAI pour les composants IA
  - 1.4.2.1 Phase d'ingestion et indexation
  - 1.4.2.2 Phase d'implémentation des modèles
  - 1.4.2.3 Phase de validation et déploiement

### 1.5 Planification du projet
- 1.5.1 Découpage en Releases
  - 1.5.1.1 Release 1 : Développement Web
  - 1.5.1.2 Release 2 : Phase IA
- 1.5.2 Diagramme de Gantt
- 1.5.3 Gestion des risques

### Conclusion du chapitre

---

## Chapitre 2 : Étude de l'Existant et Analyse des Besoins

### Introduction

### 2.1 Étude de l'existant
- 2.1.1 Analyse des solutions existantes
  - 2.1.1.1 Plateformes e-learning pour enfants
  - 2.1.1.2 Kits éducatifs électroniques
  - 2.1.1.3 Laboratoires virtuels
- 2.1.2 Tableau comparatif
- 2.1.3 Critique de l'existant

### 2.2 Analyse des besoins
- 2.2.1 Besoins fonctionnels
  - 2.2.1.1 Gestion des utilisateurs et rôles
  - 2.2.1.2 Module E-Commerce (achat/location de kits)
  - 2.2.1.3 Module Edu-Tracker (LMS)
  - 2.2.1.4 Module Virtual Lab (simulation)
  - 2.2.1.5 Module Génération de contenu IA
  - 2.2.1.6 Tuteur IA Socratique
- 2.2.2 Besoins non fonctionnels
  - 2.2.2.1 Performance et scalabilité
  - 2.2.2.2 Sécurité
  - 2.2.2.3 Disponibilité
  - 2.2.2.4 Maintenabilité

### 2.3 Spécifications des composants IA
- 2.3.1 Système de recommandation de kits
- 2.3.2 Détection des difficultés des élèves
- 2.3.3 Génération de contenu pédagogique
- 2.3.4 Tutorat Socratique

### Conclusion du chapitre

---

## Chapitre 3 : Conception et Architecture du Système

### Introduction

### 3.1 Architecture globale
- 3.1.1 Vue d'ensemble de l'architecture microservices
- 3.1.2 API Gateway et authentification
- 3.1.3 Communication inter-services
  - 3.1.3.1 REST API
  - 3.1.3.2 WebSocket pour le Virtual Lab
  - 3.1.3.3 Message Queue (RabbitMQ/Redis Streams)

### 3.2 Stack technique
- 3.2.1 Frontend
  - 3.2.1.1 Next.js 14 (App Router)
  - 3.2.1.2 Tailwind CSS + shadcn/ui
  - 3.2.1.3 Socket.io-client
- 3.2.2 Backend
  - 3.2.2.1 NestJS (TypeScript)
  - 3.2.2.2 Prisma ORM
  - 3.2.2.3 PostgreSQL et Redis
- 3.2.3 Service IA
  - 3.2.3.1 FastAPI (Python)
  - 3.2.3.2 LangChain et LangGraph
  - 3.2.3.3 ChromaDB et Neo4j

### 3.3 Conception de la base de données
- 3.3.1 Modèle conceptuel (MCD)
- 3.3.2 Schéma relationnel
- 3.3.3 Modèles Prisma détaillés
  - 3.3.3.1 Domaine Utilisateurs et Authentification
  - 3.3.3.2 Domaine E-Commerce (Kit, PhysicalItem, Order, Rental)
  - 3.3.3.3 Domaine Pédagogique (Course, Module, Exercise, Progression)
  - 3.3.3.4 Domaine Contenu IA (ContentSource, GeneratedDraft)

### 3.4 Conception détaillée par module
- 3.4.1 Module E-Commerce
  - 3.4.1.1 Diagramme de cas d'utilisation
  - 3.4.1.2 Diagramme de séquence (achat/location)
- 3.4.2 Module Edu-Tracker
  - 3.4.2.1 Diagramme de cas d'utilisation
  - 3.4.2.2 Flux de progression estudiante
- 3.4.3 Module Virtual Lab
  - 3.4.3.1 Architecture temps réel
  - 3.4.3.2 Flux WebSocket
- 3.4.4 Module Génération de Contenu
  - 3.4.4.1 Pipeline de traitement
  - 3.4.4.2 Workflow multi-agents (LangGraph)

### 3.5 Architecture des composants IA
- 3.5.1 Architecture RAG Hybride
- 3.5.2 Graphe de connaissances pédagogique
- 3.5.3 Modèles et fine-tuning (COMP 1-5)

### Conclusion du chapitre

---

## Chapitre 4 : Mise en Œuvre - Release 1 (Développement Web)

### Introduction

### 4.1 Infrastructure et configuration
- 4.1.1 Setup du Monorepo (Nx)
- 4.1.2 Configuration Docker Compose
- 4.1.3 CI/CD pipeline

### 4.2 Sprint 1 : Fondation et Authentification
- 4.2.1 Backlog du Sprint
- 4.2.2 Implémentation
  - 4.2.2.1 Modèles User et Profile (Prisma)
  - 4.2.2.2 Module Auth (JWT, Guards)
  - 4.2.2.3 API Endpoints
- 4.2.3 Revue de sprint

### 4.3 Sprint 2 : Module E-Commerce
- 4.3.1 Backlog du Sprint
- 4.3.2 Analyse et conception
- 4.3.3 Réalisation
  - 4.3.3.1 Gestion des kits et du stock
  - 4.3.3.2 Processus de commande et location
  - 4.3.3.3 Génération et gestion des QR codes
- 4.3.4 Revue de sprint

### 4.4 Sprint 3 : Module Edu-Tracker
- 4.4.1 Backlog du Sprint
- 4.4.2 Analyse et conception
- 4.4.3 Réalisation
  - 4.4.3.1 Gestion des cours et modules
  - 4.4.3.2 Système d'exercices
  - 4.4.3.3 Suivi de progression
- 4.4.4 Revue de sprint

### 4.5 Sprint 4 : Dashboard Parent et Enseignant
- 4.5.1 Backlog du Sprint
- 4.5.2 Réalisation
  - 4.5.2.1 Interface Parent (progression enfants)
  - 4.5.2.2 Interface Enseignant (gestion cours)
  - 4.5.2.3 Visualisation des analytics
- 4.5.3 Revue de sprint

### 4.6 Sprint 5 : Intégration et Tests
- 4.6.1 Backlog du Sprint
- 4.6.2 Tests d'intégration
- 4.6.3 Revue de sprint

### Conclusion du chapitre

---

## Chapitre 5 : Mise en Œuvre - Release 2 (Phase IA)

### Introduction

### 5.1 Infrastructure IA
- 5.1.1 Setup du service FastAPI
- 5.1.2 Configuration du Cerveau Vectoriel (ChromaDB + Neo4j)
- 5.1.3 Intégration avec l'API Gateway

### 5.2 Sprint 6 : Système de Recommandation (PFE 1)
- 5.2.1 Backlog du Sprint
- 5.2.2 Implémentation
  - 5.2.2.1 Collecte et préparation des données
  - 5.2.2.2 Algorithme SVD (Filtrage Collaboratif)
  - 5.2.2.3 Évaluation (RMSE, Precision@K)
- 5.2.3 Revue de sprint

### 5.3 Sprint 7 : Détection des Difficultés (PFE 2)
- 5.3.1 Backlog du Sprint
- 5.3.2 Implémentation
  - 5.3.2.1 Feature Engineering
  - 5.3.2.2 Modèle Random Forest/XGBoost
  - 5.3.2.3 Évaluation (F1-Score, Matrice de confusion)
- 5.3.3 Revue de sprint

### 5.4 Sprint 8 : Génération de Contenu Pédagogique (PFE 4)
- 5.4.1 Backlog du Sprint
- 5.4.2 Implémentation
  - 5.4.2.1 Pipeline d'extraction (PDF, YouTube, Web)
  - 5.4.2.2 Workflow Multi-Agents "Le Conseil"
  - 5.4.2.3 Validation humaine (Human-in-the-loop)
- 5.4.3 Méthodologie COMP 1-5
  - 5.4.3.1 COMP 1 : Stratégie de récupération
  - 5.4.3.2 COMP 2 : Sélection du modèle LLM
  - 5.4.3.3 COMP 3 : Structure du graphe de connaissances
  - 5.4.3.4 COMP 4 : Fine-tuning QLoRA
  - 5.4.3.5 COMP 5 : Test d'intégration
- 5.4.4 Revue de sprint

### 5.5 Sprint 9 : Virtual Lab et Tuteur IA (PFE 3)
- 5.5.1 Backlog du Sprint
- 5.5.2 Réalisation
  - 5.5.2.1 Gateway WebSocket temps réel
  - 5.5.2.2 Interface de simulation
  - 5.5.2.3 Tuteur Socratique (RAG + LLM)
  - 5.5.2.4 Validation automatique des exercices
- 5.5.3 Revue de sprint

### 5.6 Sprint 10 : Intégration Finale et Déploiement
- 5.6.1 Backlog du Sprint
- 5.6.2 Tests E2E
- 5.6.3 Déploiement et monitoring

### Conclusion du chapitre

---

## Chapitre 6 : Résultats et Évaluation

### Introduction

### 6.1 Évaluation des composants IA
- 6.1.1 Système de recommandation
  - 6.1.1.1 Résultats RMSE et Precision@K
  - 6.1.1.2 Analyse qualitative
- 6.1.2 Détection des difficultés
  - 6.1.2.1 Résultats F1-Score
  - 6.1.2.2 Matrice de confusion
- 6.1.3 Génération de contenu
  - 6.1.3.1 Scores BLEU/ROUGE
  - 6.1.3.2 Évaluation humaine (1-5)
- 6.1.4 Tuteur Socratique
  - 6.1.4.1 Taux d'hallucination
  - 6.1.4.2 Précision des citations

### 6.2 Comparaison avec l'état de l'art
- 6.2.1 Tableau comparatif des solutions
- 6.2.2 Analyse des forces et faiblesses

### 6.3 Démonstration fonctionnelle
- 6.3.1 Scénarios de test
- 6.3.2 Captures d'écran

### Conclusion du chapitre

---

## Conclusion générale

## Références et bibliographie

## Annexes
- Annexe A : Manuel d'utilisation
- Annexe B : Schéma Prisma complet
- Annexe C : Documentation API
- Annexe D : Code source (extraits)