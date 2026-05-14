SERVICE_MAP = {
    "workbench": "http://workbench:8000",
    "tes": "http://tes:8081",
    "toolserver": "http://toolserver:9090",
    "model-registry": "http://model-registry:8095",
    "rag": "http://rag:8096",
}


def resolve_service(service: str) -> str | None:
    return SERVICE_MAP.get(service)