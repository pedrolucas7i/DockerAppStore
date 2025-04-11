from flask import Flask, render_template, request
import socket
import json
import os

app = Flask(__name__)

# Dicionário para armazenar as portas já geradas
app_ports = {}

# Gera um script Docker para instalação do app
def generate_install_script(app_name, app_port):
    return f"docker run -d -p {app_port}:80 --name {app_name} {app_name}"

# Verifica se uma porta está em uso
def is_port_in_use(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('127.0.0.1', port)) == 0
    except Exception as e:
        print(f"Erro ao verificar a porta {port}: {e}")
        return True

# Gera uma porta única e disponível
def generate_unique_port(start_port=8000, end_port=9999):
    used_ports = set(app_ports.values())  # Pegar as portas já usadas
    for port in range(start_port, end_port):
        if port not in used_ports and not is_port_in_use(port):
            return port
    raise Exception("Nenhuma porta disponível na faixa especificada!")


# Carrega os dados do arquivo JSON
def load_apps():
    json_file_path = 'dockers.json'
    if os.path.exists(json_file_path):
        try:
            with open(json_file_path, 'r') as file:
                return json.load(file)
        except Exception as e:
            print(f"Erro ao carregar o JSON: {e}")
            return {}
    return {}

# Garante uma porta única por app
def get_app_port(app_name):
    if app_name not in app_ports:
        app_ports[app_name] = generate_unique_port()
    return app_ports[app_name]

@app.route('/')
def index():
    apps_data = load_apps()
    apps = []

    for category, apps_list in apps_data.items():
        for app in apps_list:
            port = get_app_port(app['name'])
            apps.append({
                'name': app['name'],
                'description': app['description'],
                'category': category,
                'install_script': generate_install_script(app['name'], port)
            })

    return render_template('index.html', apps=apps)

@app.route('/app/<app_name>')
def app_details(app_name):
    apps_data = load_apps()
    for category, apps_list in apps_data.items():
        for app in apps_list:
            if app['name'].lower() == app_name.lower():
                port = get_app_port(app['name'])
                script = generate_install_script(app['name'], port)
                return render_template('details.html', app=app, install_script=script)
    return "App não encontrado!", 404

if __name__ == '__main__':
    app.run(debug=True)
