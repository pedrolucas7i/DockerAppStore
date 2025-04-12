from flask import Flask, render_template, jsonify, request
import json
import os
import socket
import threading
import subprocess

app = Flask(__name__)

# Global Variables
app_ports = {}
apps_data = []

# Path to local JSON file
OFFLINE_JSON_PATH = "dockers.json"

# Function to get icons using Simple Icons
def get_icon_url(name):
    formatted = name.lower().replace(" ", "")
    return f"https://cdn.simpleicons.org/{formatted}"

# Load apps from local JSON file
def load_offline_apps():
    global apps_data
    if not apps_data:
        try:
            with open(OFFLINE_JSON_PATH, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                for app in raw_data:
                    app["icon_url"] = get_icon_url(app["name"])
                apps_data = raw_data
                print(f"Loaded {len(apps_data)} apps from local file.")
        except Exception as e:
            print(f"Error reading JSON file: {e}")
            apps_data = []
    return apps_data

# Function to generate an install script
def generate_install_script(app_name, app_port):
    return f"docker run -d -p {app_port}:80 --name {app_name} {app_name}"

# Function to check if a port is in use
def is_port_in_use(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('127.0.0.1', port)) == 0
    except Exception as e:
        print(f"Error checking port {port}: {e}")
        return True

# Generate a unique port
def generate_unique_port(start_port=8000, end_port=9999):
    used_ports = set(app_ports.values())
    for port in range(start_port, end_port):
        if port not in used_ports and not is_port_in_use(port):
            return port
    raise Exception("No available ports in the range!")

# Get or assign port for app
def get_app_port(app_name):
    if app_name not in app_ports:
        app_ports[app_name] = generate_unique_port()
    return app_ports[app_name]

@app.route('/')
def index():
    apps = []
    for app in load_offline_apps():
        port = get_app_port(app['name'])
        apps.append({
            'name': app['name'],
            'description': app['description'],
            'install_script': generate_install_script(app['name'], port),
            'icon_url': app.get("icon_url")
        })
    return render_template('index.html', apps=apps)

@app.route('/app/<app_name>')
def app_details(app_name):
    for app in load_offline_apps():
        if app['name'].lower() == app_name.lower():
            port = get_app_port(app['name'])
            script = generate_install_script(app['name'], port)
            return render_template('details.html', app=app, install_script=script)
    return "App not found!", 404

@app.route('/fetch_new_apps')
def fetch_new_apps():
    return jsonify(load_offline_apps())

@app.route('/search', methods=['GET'])
def search():
    search_value = request.args.get('search-value', '').strip().lower()
    apps = []

    for app in load_offline_apps():
        if app['name'].lower().startswith(search_value):
            port = get_app_port(app['name'])
            apps.append({
                'name': app['name'],
                'description': app['description'],
                'install_script': generate_install_script(app['name'], port),
                'icon_url': app.get("icon_url")
            })

    return render_template('index.html', apps=apps)

# Route to install a selected Docker app via subprocess
@app.route('/install/<app_name>', methods=['POST'])
def install_app_route(app_name):
    try:
        # Iterate through the cached apps and check if the app exists
        for app in load_offline_apps():
            if app['name'].lower() == app_name.lower():
                # Get the unique port for the app
                port = get_app_port(app['name'])

                # Generate the Docker installation command
                command = ["docker", "run", "-d", "-p", f"{port}:80", "--name", app_name, app_name]

                # Run the command using subprocess to install the app
                result = subprocess.run(command, capture_output=True, text=True, check=True)

                # If the installation is successful, return the output
                return jsonify({"success": True, "output": result.stdout.strip()})

        # If the app is not found in the list of apps
        return jsonify({"success": False, "error": "App not found!"}), 404

    except subprocess.CalledProcessError as e:
        # Handle errors from the subprocess (Docker command failure)
        return jsonify({"success": False, "error": e.stderr.strip()})

    except Exception as e:
        # General exception handling for any other issues
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
