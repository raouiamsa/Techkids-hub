from .ingest_config import write_ingest_manifest

def ingest_source(
    source_type: str,
    source_path_or_url: str,
    course_id: str,
    title: str | None = None,
    domain: str | None = None,
    metadata: dict | None = None,
):
    """Routeur principal pour l'ingestion automatique."""
    source_type = source_type.upper()
    result = None
    
    if source_type == "PDF":
        from .pdf import process_pdf
        result = process_pdf(source_path_or_url, course_id, title=title, domain=domain, source_metadata=metadata)
    elif source_type in ["YOUTUBE", "VIDEO"]:
        from .youtube import process_youtube
        result = process_youtube(source_path_or_url, course_id, title=title, domain=domain, source_metadata=metadata)
    elif source_type in ["WEB", "WEBPAGE"]:
        from .web import process_webpage
        result = process_webpage(source_path_or_url, course_id, title=title, domain=domain, source_metadata=metadata)
    else:
        print(f" Type de source '{source_type}' non supporté.")
        return False

    # In this codebase, some ingestion functions return None on success.
    success = result is not False
    write_ingest_manifest(
        source_id=course_id,
        source_type=source_type,
        source_path_or_url=source_path_or_url,
        success=success,
    )
    return result