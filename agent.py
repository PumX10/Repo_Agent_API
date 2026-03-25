"""
Agent de cerca diari de Fotocasa via Apify
Executa la cerca, detecta novetats i envia email d'alerta
"""

import os
import json
import time
import hashlib
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests


# ── Configuració (llegida des de variables d'entorn / GitHub Secrets) ──────────
APIFY_TOKEN      = os.environ["APIFY_TOKEN"]
ACTOR_ID         = "ralvaromariano~fotocasa"   # Actor Fotocasa a Apify

EMAIL_FROM       = os.environ["EMAIL_FROM"]       # ex: agent@gmail.com
EMAIL_PASSWORD   = os.environ["EMAIL_PASSWORD"]   # App Password de Gmail
EMAIL_TO         = os.environ["EMAIL_TO"]         # el teu email

# Paràmetres de la cerca (pots modificar-los)
SEARCH_CONFIG = {
    "location":      os.environ.get("SEARCH_LOCATION", "Barcelona"),
    "operation":     os.environ.get("SEARCH_OPERATION", "rent"),   # "rent" o "sale"
    "propertyType":  os.environ.get("SEARCH_TYPE",      "homes"),
    "maxItems":      int(os.environ.get("SEARCH_MAX_ITEMS", "50")),
    "minPrice":      int(os.environ.get("SEARCH_MIN_PRICE", "0")),
    "maxPrice":      int(os.environ.get("SEARCH_MAX_PRICE", "999999")),
    "minSize":       int(os.environ.get("SEARCH_MIN_SIZE", "0")),
}

SEEN_IDS_FILE = "seen_ids.json"


# ── Apify: llançar scraper ─────────────────────────────────────────────────────
def run_fotocasa_scraper() -> list[dict]:
    print(f"🔍 Llançant Fotocasa scraper per '{SEARCH_CONFIG['location']}'...")

    url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs"
    resp = requests.post(
        url,
        params={"token": APIFY_TOKEN},
        json=SEARCH_CONFIG,
        timeout=30,
    )
    resp.raise_for_status()
    run_id = resp.json()["data"]["id"]
    print(f"   Run ID: {run_id}")

    # Esperar que acabi (màx 10 min)
    for _ in range(120):
        time.sleep(5)
        status_resp = requests.get(
            f"https://api.apify.com/v2/actor-runs/{run_id}",
            params={"token": APIFY_TOKEN},
            timeout=15,
        )
        status = status_resp.json()["data"]["status"]
        print(f"   Estat: {status}")
        if status == "SUCCEEDED":
            dataset_id = status_resp.json()["data"]["defaultDatasetId"]
            break
        if status in ("FAILED", "ABORTED", "TIMED-OUT"):
            raise RuntimeError(f"Scraper fallat amb estat: {status}")
    else:
        raise TimeoutError("El scraper ha trigat massa (>10 min)")

    # Obtenir resultats
    items_resp = requests.get(
        f"https://api.apify.com/v2/datasets/{dataset_id}/items",
        params={"token": APIFY_TOKEN, "format": "json"},
        timeout=30,
    )
    items_resp.raise_for_status()
    properties = items_resp.json()
    print(f"   ✅ {len(properties)} propietats obtingudes")
    return properties


# ── Filtre de novetats ─────────────────────────────────────────────────────────
def load_seen_ids() -> set:
    if os.path.exists(SEEN_IDS_FILE):
        with open(SEEN_IDS_FILE) as f:
            return set(json.load(f))
    return set()


def save_seen_ids(ids: set):
    with open(SEEN_IDS_FILE, "w") as f:
        json.dump(list(ids), f)


def filter_new_properties(properties: list[dict]) -> list[dict]:
    seen = load_seen_ids()
    new_props = []
    new_ids = set()

    for p in properties:
        pid = str(p.get("id") or p.get("url") or hashlib.md5(json.dumps(p, sort_keys=True).encode()).hexdigest())
        if pid not in seen:
            new_props.append(p)
            new_ids.add(pid)

    # Desar tots els IDs (antics + nous)
    save_seen_ids(seen | new_ids)
    print(f"   🆕 {len(new_props)} propietats noves (de {len(properties)} totals)")
    return new_props


# ── Generació de l'email HTML ──────────────────────────────────────────────────
def build_email_html(properties: list[dict]) -> str:
    date_str = datetime.now().strftime("%d/%m/%Y")
    location = SEARCH_CONFIG["location"]
    operation_label = "Lloguer" if SEARCH_CONFIG["operation"] == "rent" else "Venda"

    cards_html = ""
    for p in properties:
        price     = p.get("price", "N/D")
        size      = p.get("size", "N/D")
        rooms     = p.get("rooms", "N/D")
        address   = p.get("address") or p.get("location", "Adreça no disponible")
        url       = p.get("url", "#")
        img       = (p.get("images") or ["https://via.placeholder.com/300x180?text=Sense+foto"])[0]
        desc      = (p.get("description") or "")[:120] + "..."

        cards_html += f"""
        <div style="border:1px solid #e0e0e0; border-radius:10px; margin:16px 0;
                    padding:0; overflow:hidden; font-family:sans-serif; box-shadow:0 2px 6px rgba(0,0,0,.07);">
          <img src="{img}" alt="foto" style="width:100%; height:180px; object-fit:cover;">
          <div style="padding:16px;">
            <div style="font-size:22px; font-weight:700; color:#e3000b;">{price} €</div>
            <div style="color:#555; margin:4px 0;">{size} m² &nbsp;·&nbsp; {rooms} hab.</div>
            <div style="font-size:13px; color:#888; margin-bottom:8px;">📍 {address}</div>
            <p style="font-size:13px; color:#444; margin:0 0 12px;">{desc}</p>
            <a href="{url}" style="background:#e3000b; color:white; padding:8px 16px;
               border-radius:6px; text-decoration:none; font-size:14px;">Veure anunci →</a>
          </div>
        </div>"""

    return f"""
    <html><body style="background:#f5f5f5; padding:20px; font-family:sans-serif;">
      <div style="max-width:600px; margin:auto; background:white; border-radius:12px;
                  padding:24px; box-shadow:0 4px 12px rgba(0,0,0,.1);">
        <h1 style="color:#e3000b; margin:0 0 4px;">🏠 Noves propietats a Fotocasa</h1>
        <p style="color:#888; margin:0 0 20px; font-size:14px;">
          {date_str} &nbsp;·&nbsp; {location} &nbsp;·&nbsp; {operation_label}
          &nbsp;·&nbsp; <strong>{len(properties)} noves</strong>
        </p>
        {cards_html}
        <hr style="border:none; border-top:1px solid #eee; margin:24px 0;">
        <p style="font-size:12px; color:#aaa; text-align:center;">
          Agent automàtic · GitHub Actions · Fotocasa via Apify
        </p>
      </div>
    </body></html>"""


# ── Enviament d'email ──────────────────────────────────────────────────────────
def send_email(properties: list[dict]):
    date_str = datetime.now().strftime("%d/%m/%Y")
    location = SEARCH_CONFIG["location"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🏠 {len(properties)} noves propietats a {location} — {date_str}"
    msg["From"]    = EMAIL_FROM
    msg["To"]      = EMAIL_TO

    html_content = build_email_html(properties)
    msg.attach(MIMEText(html_content, "html"))

    print(f"📧 Enviant email a {EMAIL_TO}...")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
    print("   ✅ Email enviat!")


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print(f"\n{'='*50}")
    print(f"  Agent Fotocasa — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}\n")

    properties   = run_fotocasa_scraper()
    new_props    = filter_new_properties(properties)

    if not new_props:
        print("ℹ️  Cap propietat nova avui. No s'envia email.")
        return

    send_email(new_props)
    print(f"\n✅ Agent completat. {len(new_props)} propietats noves notificades.")


if __name__ == "__main__":
    main()
