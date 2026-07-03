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

class EnvAndFileHandler(BaseHTTPRequestHandler):
    def get_directory_contents(self, path):
        """Helper to list all files (including hidden ones) safely."""
        try:
            if os.path.exists(path):
                # os.listdir automatically includes hidden files (e.g., .bashrc)
                return os.listdir(path)
            else:
                return f"Error: Path '{path}' does not exist."
        except PermissionError:
            return f"Error: Permission denied for path '{path}'."
        except Exception as e:
            return f"Error: {str(e)}"

    def do_GET(self):
        # Send 200 OK status code
        self.send_response(200)
        
        # Set content type to JSON
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # Gather the requested payloads
        payload = {
            "environment_variables": dict(os.environ),
            "tmp_contents": self.get_directory_contents('/tmp'),
            "home_cdsw_contents": self.get_directory_contents('/home/cdsw')
        }
        
        # Format the response as nicely indented JSON
        response_json = json.dumps(payload, indent=4, sort_keys=True)
        
        # Write response back to the client
        self.wfile.write(response_json.encode('utf-8'))

def run():
    # Read the designated application port assigned by CML/CAII
    port = int(os.environ.get('CDSW_APP_PORT', os.environ.get('PORT', 8080)))
    
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, EnvAndFileHandler)
    print(f"HTTP Server successfully running on port {port}...")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        print("Server safely shut down.")

if __name__ == '__main__':
    run()
