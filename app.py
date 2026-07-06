# ###########################################################################
#
#  CLOUDERA APPLIED MACHINE LEARNING PROTOTYPE (AMP)
#  (C) Cloudera, Inc. 2026
#  All rights reserved.
#
# ###########################################################################

from flask import Flask, request, Response

app = Flask(__name__)

# ==========================================
# Routes
# ==========================================
@app.route('/', methods=['GET'])
def handle_get():
    """Reject GET requests with a specific message."""
    return Response("Only a POST request is supported\n", status=405, mimetype='text/plain')

@app.route('/', methods=['POST'])
def debug_post():
    """Handle incoming POST requests with JSON payloads and key validation."""
    if not request.is_json:
        return Response("Bad Request: Payload must be JSON\n", status=400, mimetype='text/plain')
    
    payload = request.get_json()
    
    if not isinstance(payload, dict):
        return Response("Bad Request: JSON payload must be an object\n", status=400, mimetype='text/plain')

    # Define the exact required keys
    required_keys = {"jwt_token", "raz_endpoint", "s3_bucket", "s3_key", "s3_op"}
    provided_keys = set(payload.keys())
    
    # Check for missing keys
    missing_keys = required_keys - provided_keys
    
    if missing_keys:
        error_message = (
            "Error: Missing or misspelled keys in JSON payload.\n\n"
            "The strictly required keys are:\n"
            "- jwt_token\n"
            "- raz_endpoint\n"
            "- s3_bucket\n"
            "- s3_key\n"
            "- s3_op\n\n"
            f"You are missing: {', '.join(sorted(missing_keys))}\n"
        )
        return Response(error_message, status=400, mimetype='text/plain')

    # Format the text response (dumps every key/value provided)
    response_lines = [
        f"DEBUG_KEY: {key} and DEBUG_VALUE : {value}"
        for key, value in payload.items()
    ]
    response_text = "\n".join(response_lines) + "\n"
    
    return Response(response_text, status=200, mimetype='text/plain')

# ==========================================
# Execution
# ==========================================
if __name__ == '__main__':
    # Hardcoded port 8080 as mandated
    app.run(host='0.0.0.0', port=8080)
