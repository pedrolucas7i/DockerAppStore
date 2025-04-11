import requests
import json

DOCKER_HUB_SEARCH_URL = "https://hub.docker.com/api/search/v4?badges=official&size=200&type=image"
DOCKER_JSON_FILE = "dockers.json"

def fetch_app_names():
    """Busca os nomes dos apps oficiais do Docker Hub."""
    app_list = []
    next_url = DOCKER_HUB_SEARCH_URL

    while next_url:
        try:
            response = requests.get(next_url)
            response.raise_for_status()
            data = response.json()

            results = data.get('results', [])
            for app in results:
                app_list.append({
                    "name": app.get("name", "unknown"),
                    "namespace": app.get("namespace", "library"),  # Pode servir como pseudo-categoria
                    "description": app.get("short_description", "")
                })

            next_url = data.get('next')
        except requests.exceptions.RequestException as e:
            print(f"Erro ao buscar dados: {e}")
            break

    return app_list

apps = fetch_app_names()

# Salva apenas os nomes e pseudo-categorias
with open(DOCKER_JSON_FILE, 'w', encoding='utf-8') as f:
    json.dump(apps, f, indent=2, ensure_ascii=False)

print(f"{len(apps)} apps salvos em docker_app_names.json")
