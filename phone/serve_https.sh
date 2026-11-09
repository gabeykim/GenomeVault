#!/usr/bin/env bash
# Serve GenomeVault on the local network over HTTPS so a phone on the same Wi-Fi can open /phone (S2, S6).
#
#   bash phone/serve_https.sh            # demo mode by default (DEMO=1), port 8443
#   PORT=9443 DEMO=0 bash phone/serve_https.sh
#   GV_OCR=vlm bash phone/serve_https.sh   # stage: labels read by the on-device vision model (D-029)
#
# - Makes a self-signed certificate for this laptop's LAN IP with the system `openssl` (no Python
#   dependency), valid 7 days, kept outside the repo in ~/.genomevault/cert (never committed).
# - Every request that isn't from this laptop needs the pairing code shown in Actions -> Use your phone.
# - Nothing here talks to the internet; only the phone on your network connects in.
set -euo pipefail
cd "$(dirname "$0")/.."

PORT="${PORT:-8443}"
CERT_DIR="${GV_CERT_DIR:-$HOME/.genomevault/cert}"
IP="${GV_LAN_IP:-}"
if [ -z "$IP" ]; then
  for ifc in en0 en1; do IP="$(ipconfig getifaddr "$ifc" 2>/dev/null || true)"; [ -n "$IP" ] && break; done
fi
[ -z "$IP" ] && IP="$(hostname -I 2>/dev/null | awk '{print $1}' || true)"
[ -z "$IP" ] && { echo "Couldn't find this laptop's LAN IP; set GV_LAN_IP=..."; exit 1; }

mkdir -p "$CERT_DIR"
if [ ! -f "$CERT_DIR/cert.pem" ] || [ "$(cat "$CERT_DIR/ip" 2>/dev/null)" != "$IP" ]; then
  openssl req -x509 -newkey rsa:2048 -nodes -days 7 -subj "/CN=GenomeVault demo" \
    -addext "subjectAltName=IP:${IP},IP:127.0.0.1,DNS:localhost" \
    -keyout "$CERT_DIR/key.pem" -out "$CERT_DIR/cert.pem" 2>/dev/null
  echo "$IP" > "$CERT_DIR/ip"
  chmod 600 "$CERT_DIR/key.pem"
fi

export DEMO="${DEMO:-1}"
export GV_PHONE_URL="https://${IP}:${PORT}/phone"
UVICORN="${UVICORN:-$( [ -x .venv/bin/uvicorn ] && echo .venv/bin/uvicorn || echo uvicorn )}"

echo
echo "  Laptop:  https://localhost:${PORT}/"
echo "  Phone:   ${GV_PHONE_URL}   (same Wi-Fi; accept the certificate warning once)"
echo "  Pairing code: shown on the laptop in Actions -> Use your phone"
case "${GV_OCR:-auto}" in
  vlm) echo "  Labels:  read by the on-device vision model (GV_OCR=vlm); warming it up now, ~10 s" ;;
  *)   echo "  Labels:  GV_OCR=${GV_OCR:-auto} (sample labels use their embedded text; for the stage run use GV_OCR=vlm)" ;;
esac
echo
exec "$UVICORN" app:app --host 0.0.0.0 --port "$PORT" \
  --ssl-keyfile "$CERT_DIR/key.pem" --ssl-certfile "$CERT_DIR/cert.pem"
