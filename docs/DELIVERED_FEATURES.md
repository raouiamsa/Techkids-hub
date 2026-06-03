# État de livraison — TechKids Hub (synthèse)

Oui. À partir du workspace, le projet n’est pas juste un module IA: c’est bien une plateforme full‑stack TechKids Hub avec une couche pédagogique, une couche métier et une couche IA.

## Ce qui est déjà livré par rapport au cahier des charges

- **Plateforme web**: interface cours, dashboard enseignant et Virtual Lab.
  - Voir: [apps/web/src/app/courses/[courseId]/components/VirtualLab.tsx](apps/web/src/app/courses/[courseId]/components/VirtualLab.tsx) et pages dashboard.
- **Passerelle métier (API Gateway)**: centralise auth, ingestion, génération, rectification et publication.
  - Voir: [apps/api-gateway/src/app/ai/ai.controller.ts](apps/api-gateway/src/app/ai/ai.controller.ts)
- **Virtual Lab — temps réel**: join-lab, code-draft, ask-tutor, run-code, simulate-circuit via WebSocket.
  - Voir: [apps/virtual-lab-service/src/app/virtual-lab.gateway.ts](apps/virtual-lab-service/src/app/virtual-lab.gateway.ts)
- **Cœur IA (service IA)**: endpoints FastAPI pour génération, tutorat socratique, scoring, etc.
  - Voir: [apps/ai-brain/main.py](apps/ai-brain/main.py)
- **Base de données / modèle**: Prisma schema couvrant utilisateurs, profils, cours, modules, exercices, inscriptions, progression, sources et brouillons.
  - Voir: [libs/database/prisma/schema.prisma](libs/database/prisma/schema.prisma)
- **Authentification & rôles**: module d'authentification présent et intégré.
- **Messagerie inter‑services**: événements structurés pour orchestrer ingestion, publication, suivi et Virtual Lab.
  - Voir: [libs/messaging/src/lib/messaging.constants.ts](libs/messaging/src/lib/messaging.constants.ts)

## Mapping rapide au cahier des charges

- **Authentification sécurisée, rôles et profils**: implémentés.
- **Parcours apprenant, inscriptions, progression**: implémentés via Prisma et API.
- **Virtual Lab (exécution de code + assistance IA)**: fonctionnel en temps réel.
- **Portail enseignant (ingestion → génération → rectification → publication)**: endpoints et workflows en place.
- **Suivi parental & supervision**: entités et vues présentes (dashboard, logs, rôles admin).
- **Génération IA et pipeline de contenu**: pipeline multi‑agents et scripts de benchmarking (COMP2 etc.) présents.
- **Architecture**: monorepo Nx, services Next.js / NestJS / FastAPI, Prisma, RabbitMQ/WebSocket.

## Ce que le workspace montre aussi — au‑delà de l'IA

- Le projet est structuré comme un vrai produit, pas seulement un prototype IA: cycle métier complet (création de cours, ingestion, brouillon IA, validation, publication, suivi élève).
- Architecture et base technique prêtes pour déploiement et évolution (monorepo, CI à prévoir, conteneurisation possible).

## Fichiers clés à consulter rapidement

- Interface web / Virtual Lab: [apps/web/src/app/courses/[courseId]/components/VirtualLab.tsx](apps/web/src/app/courses/[courseId]/components/VirtualLab.tsx)
- Gateway / API métier: [apps/api-gateway/src/app/ai/ai.controller.ts](apps/api-gateway/src/app/ai/ai.controller.ts)
- Virtual Lab realtime: [apps/virtual-lab-service/src/app/virtual-lab.gateway.ts](apps/virtual-lab-service/src/app/virtual-lab.gateway.ts)
- Service IA: [apps/ai-brain/main.py](apps/ai-brain/main.py)
- Modèle de données: [libs/database/prisma/schema.prisma](libs/database/prisma/schema.prisma)
- Messagerie/events: [libs/messaging/src/lib/messaging.constants.ts](libs/messaging/src/lib/messaging.constants.ts)
- Benchmarking IA (local-first, Ollama): [apps/ai-brain/benchmarking/comp2_agents_llm_comparaison.py](apps/ai-brain/benchmarking/comp2_agents_llm_comparaison.py)

## Recommandations rapides

- Garder le Chapitre 3 (conception) séparé des traces d'expérimentation (commit hashes, seeds, prompts versionnées) — ces éléments pratiques doivent aller dans Chapitre 5 / Annexe C.
- Documenter la procédure locale de benchmark (Ollama local, Chroma/Neo4j si nécessaire) dans `docs/` si vous prévoyez de reproduire les runs.

---
_Fichier généré automatiquement pour garder trace de l'état livré — mettre à jour quand on ajoute des fonctionnalités majeures ou qu'on déplace des responsabilités entre services._
