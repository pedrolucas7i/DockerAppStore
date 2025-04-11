from flask import Flask, render_template, jsonify
import requests
import threading
import time
import socket

app = Flask(__name__)

# Global Variables
is_updating = False
app_ports = {}
apps_data = []  # Global list to cache API results

# New API URL for Docker Hub search (using official badge, 15 results per page)
DOCKER_HUB_SEARCH_URL = "https://hub.docker.com/api/search/v4?badges=official&size=200&query=&type=image"

# Category constant (not used for caching anymore)
DEFAULT_CATEGORY = "official_docker_apps"

# Function to get icons using Simple Icons
def get_icon_url(name):
    formatted = name.lower().replace(" ", "")
    return f"https://cdn.simpleicons.org/{formatted}"

# Function to fetch all official Docker apps using the new API endpoint
def fetch_all_official_apps():
    url = DOCKER_HUB_SEARCH_URL  # We're only using one page for simplicity
    print(f"Fetching from API URL: {url}")
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Ensure that results is a list; if missing, use an empty list.
            results = data.get('results') or []
            print(f"Fetched {len(results)} apps from the new API.")
            apps = []
            for item in results:
                # Use keys available in the API response; adjust if necessary.
                app_name = item.get("name", "unknown")
                # Some API responses might not include a description.
                app_description = item.get("description", "No description provided.")
                app_data = {
                    "name": app_name,
                    "description": app_description,
                    "icon_url": get_icon_url(app_name)
                }
                apps.append(app_data)
            return apps
        else:
            print(f"Failed to fetch data. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error fetching apps from API: {e}")
    return []  # Return empty list on any error

# Function to update apps in the background
def update_apps_in_background():
    global is_updating, apps_data
    is_updating = True
    # Fetch apps from the API (we are not iterating through pages now)
    new_apps = fetch_all_official_apps()
    apps_data = new_apps  # Replace the cached list entirely
    print(f"Update complete. Total apps fetched: {len(apps_data)}.")
    is_updating = False

# Function to generate an install script for the given app
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

# Function to generate a unique port
def generate_unique_port(start_port=8000, end_port=9999):
    used_ports = set(app_ports.values())
    for port in range(start_port, end_port):
        if port not in used_ports and not is_port_in_use(port):
            return port
    raise Exception("No available port in the specified range!")

# Function to get apps (if not already cached, start a background update)
def load_apps():
    global apps_data
    # If cache is empty, trigger a background update and return an empty list.
    if not apps_data:
        threading.Thread(target=update_apps_in_background, daemon=True).start()
    return apps_data

# Function to assign a unique port for an app
def get_app_port(app_name):
    if app_name not in app_ports:
        app_ports[app_name] = generate_unique_port()
    return app_ports[app_name]

@app.route('/')
def index():
    apps = []
    for app in load_apps():
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
    for app in load_apps():
        if app['name'].lower() == app_name.lower():
            port = get_app_port(app['name'])
            script = generate_install_script(app['name'], port)
            return render_template('details.html', app=app, install_script=script)
    return "App not found!", 404

@app.route('/update_apps')
def update_apps_route():
    global is_updating
    if is_updating:
        return jsonify({"message": "Update already in progress. Please wait."}), 400
    threading.Thread(target=update_apps_in_background, daemon=True).start()
    return jsonify({"message": "Update started!"}), 202

# Endpoint to fetch apps for dynamic update in the UI
@app.route('/fetch_new_apps')
def fetch_new_apps():
    return jsonify(load_apps())

if __name__ == '__main__':
    app.run(debug=True)
