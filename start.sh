#!/bin/sh
# HF Spaces entrypoint. Streamlit's native Google OAuth reads its [auth] config
# ONLY from .streamlit/secrets.toml (not env vars), and that file is gitignored,
# so we materialize it here at container start from the Space's secret env vars.
# If the Google secrets aren't set, we skip it and the app runs with just
# username/password login (google_configured() hides the button).
set -e

if [ -n "$AUTH_GOOGLE_CLIENT_ID" ]; then
  mkdir -p .streamlit
  cat > .streamlit/secrets.toml <<EOF
[auth]
redirect_uri = "https://shireenaqeel-yap.hf.space/oauth2callback"
cookie_secret = "${AUTH_COOKIE_SECRET}"

[auth.google]
client_id = "${AUTH_GOOGLE_CLIENT_ID}"
client_secret = "${AUTH_GOOGLE_CLIENT_SECRET}"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
EOF
  echo "start.sh: wrote .streamlit/secrets.toml (Google OAuth enabled)"
else
  echo "start.sh: AUTH_GOOGLE_CLIENT_ID not set — Google OAuth disabled"
fi

exec streamlit run app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true
