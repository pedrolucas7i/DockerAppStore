import json
import re

# Carrega seu arquivo JSON
with open('dockers.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

def normalize_name(name):
    # Remove tudo que não for letra ou número
    name = re.sub(r'[^\w\s]', '', name)
    return name.lower().replace(' ', '')

# Adiciona campo 'icon_url' com base no nome do app
for category, apps in data.items():
    for app in apps:
        icon_name = normalize_name(app['name'])
        app['icon_url'] = f"https://cdn.simpleicons.org/{icon_name}"

# Salva o JSON atualizado
with open('dockers.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("JSON atualizado com os ícones salvos em dockers_with_icons.json")
