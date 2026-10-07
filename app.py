import time
import urllib.parse
from typing import Optional
import traceback
import re
import urllib3

import streamlit as st
import boto3
import requests
from requests.auth import AuthBase
from botocore.exceptions import ClientError
from botocore.config import Config

# Cloudera RAZ imports
import raz_client.raz_util
import raz_client.raz_signer
from raz_client import configure_ranger_raz, Configuration, RAZ_URL_KEY, RAZ_CLIENT_USE_DELEGATION_TOKEN

# Disable SSL warnings for local execution
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# STREAMLIT PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="RAZ S3 Data Explorer",
    page_icon="☁️",
    layout="wide"
)

# ==========================================
# 1. REGIONAL ENDPOINT MONKEY PATCH
# ==========================================
# Intercepts regex matching in raz_signer to support regional endpoints (e.g., eu-west-1)
_original_re_match = re.match

def _patched_re_match(pattern, string, flags=0):
    if ".s3.amazonaws.com/" in pattern or r"\.s3\.amazonaws\.com\/" in pattern:
        pattern = r"(.*)\.s3[.-]?[a-z0-9-]*\.amazonaws\.com\/(.*)"
    elif "s3.amazonaws.com/" in pattern or r"s3\.amazonaws\.com\/" in pattern:
        pattern = r"s3[.-]?[a-z0-9-]*\.amazonaws\.com\/(.*)"

    match = _original_re_match(pattern, string, flags)

    if match is None and "amazonaws.com" in string:
        match = _original_re_match(r"(.*?)\.s3[.-]?[a-z0-9-]*\.amazonaws\.com\/(.*)", string, flags)
        if match is None:
            match = _original_re_match(r"s3[.-]?[a-z0-9-]*\.amazonaws\.com\/(.*)", string, flags)

    return match

raz_client.raz_signer.re.match = _patched_re_match


# ==========================================
# 2. DYNAMIC KEYCLOAK TOKEN MANAGER
# ==========================================
class TokenManager:
    """Fetches and caches JWT from Entra ID based on Streamlit inputs."""
    def __init__(self, tenant_id, client_id, client_secret, scope):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self._token = None
        self._expires_at = 0

    def get_token(self):
        if not self._token or time.time() >= (self._expires_at - 30):
            kc_host = "https://login.microsoftonline.com"
            url = f"{kc_host}/{self.tenant_id}/oauth2/v2.0/token"
            
            response = requests.post(url, data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": self.scope
            })
            response.raise_for_status()
            
            payload = response.json()
            self._token = payload["access_token"]
            self._expires_at = time.time() + payload.get("expires_in", 300)
        return self._token


# ==========================================
# 3. REQUEST INTERCEPTOR FOR KNOX/RAZ
# ==========================================
class RazJwtAuth(AuthBase):
    """Injects Bearer token and strips delegation query parameter."""
    def __init__(self, token_manager):
        self.token_manager = token_manager

    def __call__(self, r):
        r.headers["Authorization"] = f"Bearer {self.token_manager.get_token()}"
        
        # Strip delegation= from URL to avoid Java backend parsing exception
        if "delegation=" in r.url:
            parsed = urllib.parse.urlsplit(r.url)
            qs = urllib.parse.parse_qs(parsed.query)
            qs.pop('delegation', None)
            new_query = urllib.parse.urlencode(qs, doseq=True)
            r.url = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, new_query, parsed.fragment))
            
        return r


# ==========================================
# 4. RAZ CLIENT PATCHES
# ==========================================
# Use Streamlit session state to hold the dynamic AuthBase instance
if 'auth_interceptor' not in st.session_state:
    st.session_state.auth_interceptor = None

raz_client.raz_util.has_valid_kerberos_ticket = lambda: True

original_signer_init = raz_client.raz_signer.RazS3Signer.__init__
def patched_init(self, conf=None, auth_type="BASIC"):
    original_signer_init(self, conf, auth_type)
    # Inject the session-specific auth interceptor containing the user's UI inputs
    if st.session_state.auth_interceptor:
        self._auth = st.session_state.auth_interceptor

raz_client.raz_signer.RazS3Signer.__init__ = patched_init
raz_client.raz_signer.RazS3Signer._create_delegation_token = lambda self: "DUMMY"


# ==========================================
# 5. FETCH DATA FUNCTION
# ==========================================
def fetch_s3_object_data(bucket: str, key: str, raz_url: str, ssl_verify: bool = False) -> Optional[bytes]:
    """
    Fetches S3 object content if authorized by RAZ.
    Returns bytes on success, or None on failure.
    """
    # Using eu-west-1 region as established in previous iterations
    client = boto3.client("s3", config=Config(region_name="eu-west-1"))
    
    conf = Configuration()
    conf[RAZ_URL_KEY] = raz_url
    conf[RAZ_CLIENT_USE_DELEGATION_TOKEN] = True
    conf["raz.client.use.ssl.verification"] = ssl_verify

    configure_ranger_raz(client, conf)

    try:
        response = client.get_object(Bucket=bucket, Key=key)
        return response["Body"].read()

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response is not None else "Unknown"
        if status_code in (401, 403):
            st.error(f"**Authorization Failure (RAZ/Knox):** Denied with HTTP {status_code}")
        else:
            st.error(f"**Authorization Request Failed:** HTTP {status_code} - {e}")
        return None

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        st.error(f"**AWS S3 Client Failure [{error_code}]:** {e.response['Error']['Message']}")
        return None

    except Exception as e:
        st.error(f"**Unexpected Error:** {e}")
        st.code(traceback.format_exc(), language="python")
        return None


# ==========================================
# 6. STREAMLIT UI LAYOUT
# ==========================================
st.title("☁️ RAZ S3 Data Explorer")
st.markdown("Fetch and preview S3 object data via Knox and Ranger RAZ using Entra ID (Azure AD) Client Credentials.")

# --- Sidebar Inputs ---
with st.sidebar:
    st.header("Configuration")
    
    st.subheader("Azure AD Credentials")
    ui_tenant_id = st.text_input("Tenant ID", value="")
    ui_client_id = st.text_input("Client ID", value="")
    ui_client_secret = st.text_input("Client Secret", type="password", value="")
    ui_scope = st.text_input("Scope", value="api://example.jwt.auth/.default")
    
    st.subheader("Ranger RAZ Settings")
    ui_raz_url = st.text_input("RAZ Gateway URL", value="https://<gateway-host>:443/mwi-aw-dl/cdp-entraid/rangerraz/")
    
    st.subheader("S3 Target")
    ui_bucket = st.text_input("S3 Bucket", value="mwi-buk-6d569a46")
    ui_key = st.text_input("Object Key", value="data/example/file.txt")

# --- Main Action ---
if st.button("Fetch Object Data", type="primary"):
    # Validate required inputs
    if not all([ui_tenant_id, ui_client_id, ui_client_secret, ui_raz_url, ui_bucket, ui_key]):
        st.warning("Please fill out all configuration fields in the sidebar before fetching data.")
    else:
        with st.spinner(f"Requesting data for s3://{ui_bucket}/{ui_key}..."):
            
            # 1. Initialize the Token Manager with the UI inputs
            token_mgr = TokenManager(
                tenant_id=ui_tenant_id,
                client_id=ui_client_id,
                client_secret=ui_client_secret,
                scope=ui_scope
            )
            
            # 2. Bind the Auth Interceptor to the session state for the patched RazS3Signer
            st.session_state.auth_interceptor = RazJwtAuth(token_mgr)
            
            # 3. Fetch the data
            data = fetch_s3_object_data(
                bucket=ui_bucket, 
                key=ui_key, 
                raz_url=ui_raz_url, 
                ssl_verify=False
            )

        # 4. Render Results
        if data is not None:
            st.success("Authorization Successful!")
            st.metric(label="Payload Size", value=f"{len(data):,} bytes")
            
            st.subheader("File Preview")
            try:
                # Attempt to decode as UTF-8 text for display
                decoded_text = data.decode("utf-8", errors="replace")
                st.code(decoded_text, language="text")
            except Exception as e:
                st.warning("Data retrieved successfully, but could not be rendered as text. Showing raw bytes.")
                st.write(data)
