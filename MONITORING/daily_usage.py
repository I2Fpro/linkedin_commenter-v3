#!/usr/bin/env python3
# Script: daily_usage.py
# Description: Récupère la consommation de tokens d'OpenAI pour J-1 et envoie un rapport sur Discord.

import os, datetime, time, json
import urllib.request

# Chargement des variables d'environnement depuis .env (s'il existe)
script_dir = os.path.dirname(os.path.realpath(__file__))
env_path = os.path.join(script_dir, '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                # Parsing simple des lignes KEY=VALUE
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip().strip('\"')

# Récupère les valeurs nécessaires des variables d'environnement
openai_api_key = os.environ.get("OPENAI_ADMINAPI_KEY")
webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")

if not openai_api_key or not webhook_url:
    raise RuntimeError("Clé OpenAI ou URL du webhook Discord manquante dans les variables d'environnement.")

# Calcul de la plage de dates (hier)
now_utc = datetime.datetime.now(datetime.timezone.utc)
today_utc_midnight = datetime.datetime(year=now_utc.year, month=now_utc.month, day=now_utc.day, tzinfo=datetime.timezone.utc)
yesterday_utc_midnight = today_utc_midnight - datetime.timedelta(days=1)
# Timestamp Unix (secondes)
start_time = int(yesterday_utc_midnight.timestamp())
end_time = int(today_utc_midnight.timestamp())

# Appel à l'endpoint OpenAI Usage (completions) pour la journée d'hier
url = f"https://api.openai.com/v1/organization/usage/completions?start_time={start_time}&end_time={end_time}&bucket_width=1d"
req = urllib.request.Request(url, headers={
    "Authorization": f"Bearer {openai_api_key}",
    "Content-Type": "application/json"
})
try:
    with urllib.request.urlopen(req) as res:
        data = json.load(res)
except Exception as e:
    print(f"Erreur lors de l'appel à l'API OpenAI: {e}")
    exit(1)

# Extraction du nombre total de tokens utilisés hier
total_tokens = 0
if "data" in data:
    # Parcourt les résultats éventuels (normalement 1 bucket pour hier)
    for bucket in data.get("data", []):
        for result in bucket.get("results", []):
            tokens_in = result.get("input_tokens", 0)
            tokens_out = result.get("output_tokens", 0)
            total_tokens += tokens_in + tokens_out

# Préparation du message Discord
yesterday_str = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%d/%m/%Y")
message = f"**Consommation de tokens OpenAI le {yesterday_str}** : {total_tokens} tokens au total."

# Envoi du message au webhook Discord
discord_req = urllib.request.Request(webhook_url, data=json.dumps({"content": message}).encode(),
                                     headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(discord_req) as resp:
        pass  # Succès (HTTP 204 attendu)
except Exception as e:
    print(f"Erreur lors de l'envoi sur Discord: {e}")
    exit(1)
