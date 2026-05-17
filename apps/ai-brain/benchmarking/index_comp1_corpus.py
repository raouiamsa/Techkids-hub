import argparse
import json
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
AI_BRAIN_DIR = PROJECT_ROOT / "apps" / "ai-brain"
sys.path.append(str(AI_BRAIN_DIR))


RESOURCE_MANIFEST_PATH = AI_BRAIN_DIR / "benchmarking" / "dataset" / "sprint4_comp1_resources.json"


def load_manifest() -> list[dict]:
    if not RESOURCE_MANIFEST_PATH.exists():
        raise FileNotFoundError(
            f"Manifeste introuvable: {RESOURCE_MANIFEST_PATH}"
        )

    with open(RESOURCE_MANIFEST_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def index_corpus(dry_run: bool = False) -> None:
    resources = load_manifest()
    ingest_source = None

    if not dry_run:
        from ingest import ingest_source as ingest_source_fn

        ingest_source = ingest_source_fn

    print("=" * 60)
    print("COMP 1 CORPUS INDEXER")
    print("=" * 60)
    print(f"Ressources trouvées: {len(resources)}")

    indexed = 0
    skipped = 0

    for resource in resources:
        resource_id = resource.get("resource_id", "unknown")
        source_type = str(resource.get("source_type", "")).upper()
        path_or_url = resource.get("path_or_url", "")
        status = str(resource.get("status", "todo")).lower()
        title = resource.get("title")
        domain = resource.get("domain")

        if status == "todo" or not path_or_url:
            print(f"- skip {resource_id}: status={status}, source vide")
            skipped += 1
            continue

        print(f"- index {resource_id} ({source_type}) -> {path_or_url}")

        if dry_run:
            indexed += 1
            continue

        try:
            result = ingest_source(
                source_type,
                path_or_url,
                resource_id,
                title=title,
                domain=domain,
                metadata=resource,
            )
            if result is False:
                print(f"- skip {resource_id}: ingestion échouée")
                skipped += 1
                continue
            indexed += 1
        except Exception as exc:
            print(f"- skip {resource_id}: erreur d'ingestion ({exc})")
            skipped += 1

    print("=" * 60)
    print(f"Indexation terminée: {indexed} traitées, {skipped} ignorées")


def main() -> None:
    parser = argparse.ArgumentParser(description="Indexer le corpus COMP 1 depuis le manifeste.")
    parser.add_argument("--dry-run", action="store_true", help="Afficher les ressources sans les ingérer")
    args = parser.parse_args()

    index_corpus(dry_run=args.dry_run)


if __name__ == "__main__":
    main()