from flask import Flask, render_template, request
import socket
import json
import os

app = Flask(__name__)

# Dicionário para armazenar as portas já geradas
app_ports = {}

# Função para gerar um script de instalação único para cada app
def generate_install_script(app_name, app_port):
    return f"""
    docker run -d -p {app_port}:80 --name {app_name} {app_name}
    """

# Função para verificar se a porta está em uso
def is_port_in_use(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            result = s.connect_ex(('127.0.0.1', port))  # Tentando conectar à porta local
            return result == 0  # Retorna True se a porta estiver em uso
    except Exception as e:
        print(f"Erro ao verificar a porta {port}: {e}")
        return True  # Se houver erro, assumimos que a porta pode estar em uso

# Função para gerar uma porta única e garantir que não esteja em uso
def generate_unique_port(start_port=8000, end_port=9999):
    # Tentar várias portas até encontrar uma disponível
    for port in range(start_port, end_port):
        if not is_port_in_use(port):
            return port
    raise Exception("Nenhuma porta disponível na faixa especificada!")

# Função para carregar a lista de apps do arquivo JSON
def load_apps():
    json_file_path = 'dockers.json'  # Caminho para o arquivo JSON
    if os.path.exists(json_file_path):
        try:
            with open(json_file_path, 'r') as file:
                return json.load(file)
        except json.JSONDecodeError as e:
            print(f"Erro ao ler o arquivo JSON: {e}")
            return {}
        except Exception as e:
            print(f"Erro inesperado ao carregar o JSON: {e}")
            return {}
    else:
        print(f"O arquivo {json_file_path} não foi encontrado.")
        return {}

# Função para obter ou gerar a porta única para um app
def get_app_port(app_name):
    # Verifica se a porta já foi gerada para esse app
    if app_name not in app_ports:
        # Se a porta não foi gerada, gera uma nova porta
        app_ports[app_name] = generate_unique_port()
    return app_ports[app_name]

@app.route('/')
def index():
    # Carregar apps do JSON
    apps_data = load_apps()

    apps = []
    for category, apps_list in apps_data.items():
        for app in apps_list:
            app_port = get_app_port(app['name'])  # Obter ou gerar a porta única para o app
            app_info = {
                'name': app['name'],
                'description': app['description'],
                'category': category,
                'install_script': generate_install_script(app['name'], app_port)
            }
            apps.append(app_info)

    return render_template('index.html', apps=apps)

@app.route('/app/<app_name>')
def app_details(app_name):
    apps_data = load_apps()
    app_found = None

    # Buscar pelo app na lista
    for category, apps_list in apps_data.items():
        for app in apps_list:
            if app['name'].lower() == app_name.lower():
                app_found = app
                break
    
    if app_found:
        app_port = get_app_port(app_found['name'])  # Obter a mesma porta já gerada
        install_script = generate_install_script(app_found['name'], app_port)
        return render_template('details.html', app=app_found, install_script=install_script)
    else:
        return "App não encontrado!", 404

if __name__ == '__main__':
    app.run(debug=True)
