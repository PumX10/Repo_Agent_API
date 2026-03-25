# 🏠 Agent Fotocasa Diari

Agent automàtic que cerca propietats noves a Fotocasa cada dia i t'envia un email amb les novetats.

**Stack:** Python · Apify · GitHub Actions · Gmail SMTP

---

## ⚙️ Configuració pas a pas

### 1. Crear el repositori a GitHub

```bash
git init fotocasa-agent
cd fotocasa-agent
# Copia els fitxers agent.py i .github/workflows/agent.yml aquí
git add .
git commit -m "Agent Fotocasa inicial"
git push -u origin main
```

### 2. Obtenir el token d'Apify

1. Registra't a [apify.com](https://apify.com)
2. Ves a **Settings → Integrations → API tokens**
3. Copia el teu **Personal API Token**

### 3. Configurar App Password de Gmail

Per enviar emails des d'un script, cal una "App Password" (no la contrasenya normal):

1. Ves a [myaccount.google.com/security](https://myaccount.google.com/security)
2. Activa la **Verificació en dos passos** (si no la tens)
3. Busca **"App passwords"** → crea una nova → selecciona "Mail"
4. Copia la contrasenya de 16 caràcters que et genera

### 4. Afegir Secrets a GitHub

Ves al teu repositori → **Settings → Secrets and variables → Actions** → **New repository secret**

| Secret | Valor |
|---|---|
| `APIFY_TOKEN` | El token d'Apify |
| `EMAIL_FROM` | El teu Gmail (ex: `tunom@gmail.com`) |
| `EMAIL_PASSWORD` | L'App Password de 16 caràcters |
| `EMAIL_TO` | On vols rebre les alertes |

### 5. Configurar variables de cerca (opcional)

A **Settings → Secrets and variables → Actions → Variables** pots personalitzar:

| Variable | Valor per defecte | Descripció |
|---|---|---|
| `SEARCH_LOCATION` | `Barcelona` | Ciutat o barri |
| `SEARCH_OPERATION` | `rent` | `rent` (lloguer) o `sale` (venda) |
| `SEARCH_TYPE` | `homes` | `homes`, `offices`, `garages`... |
| `SEARCH_MAX_ITEMS` | `50` | Màxim de resultats per cerca |
| `SEARCH_MIN_PRICE` | `0` | Preu mínim en € |
| `SEARCH_MAX_PRICE` | `999999` | Preu màxim en € |
| `SEARCH_MIN_SIZE` | `0` | Superfície mínima en m² |

---

## 🚀 Provar manualment

Ves a **Actions → Agent Fotocasa Diari → Run workflow** i pots passar la localització que vulguis.

---

## 📅 Horari d'execució

L'agent s'executa cada dia a les **8:00 AM UTC** (9:00 AM hora Espanya a l'estiu).
Per canviar l'hora, edita la línia `cron` del fitxer `.github/workflows/agent.yml`.

Exemples de cron:
- `0 7 * * *` → 7:00 AM UTC (8:00 AM Espanya hivern)
- `0 6 * * 1-5` → 6:00 AM UTC, només dies laborables

---

## 💰 Cost estimat

| Servei | Cost |
|---|---|
| GitHub Actions | ✅ Gratuït (2.000 min/mes) |
| Apify Fotocasa | ~$3 per 1.000 propietats |
| Gmail SMTP | ✅ Gratuït |

Una execució diària de 50 resultats = **~$0,15/mes**

---

## 📁 Estructura del projecte

```
fotocasa-agent/
├── agent.py                        # Script principal
├── seen_ids.json                   # IDs vistos (generat automàticament)
├── README.md
└── .github/
    └── workflows/
        └── agent.yml               # Configuració GitHub Actions
```
