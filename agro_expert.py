import subprocess
import json
import os
import sqlite3
import datetime
from google import genai

# --- CONFIGURĂRI ---
DB_PATH = "/var/lib/weewx/weewx.sdb"
API_KEY = "AIzaSyA05SDDWnsDYMSDgBjn5Vh8r4n0G55z4dQ"
REPO_PATH = "/home/tiberiu/ferma_ai"

def extract_last_24h_data():
    if not os.path.exists(DB_PATH):
        print("Eroare: Nu s-a găsit baza de date WeeWX.")
        return None
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    yesterday = int((datetime.datetime.now() - datetime.timedelta(hours=24)).timestamp())
    query = "SELECT dateTime, outTemp, outHumidity, rain FROM archive WHERE dateTime > ? ORDER BY dateTime ASC"
    cursor.execute(query, (yesterday,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def analyze_with_ai(data_rows):
    client = genai.Client(api_key=API_KEY)
    
    formatted_data = []
    for row in data_rows:
        dt = datetime.datetime.fromtimestamp(row[0]).strftime('%Y-%m-%d %H:%M')
        formatted_data.append(f"Ora: {dt} | Temp: {row[1]}F | Umiditate: {row[2]}% | Ploaie: {row[3]} in")
    
    data_text = "\n".join(formatted_data)

    prompt = f"""Ești un asistent fitopatolog expert pentru o fermă didactică de meri din Rusciori, județul Sibiu.
Sarcina ta: Analizează datele meteo de mai jos (ultimele 24h) și emite un buletin de avertizare scurt, obiectiv și pragmatic.

REGULI STRICTE DE ANALIZĂ:
1. Datele primite sunt în Fahrenheit și inchi. Convertește-le obligatoriu în Celsius și mm înainte de a face analiza.
2. Evaluează riscul de Rapăn (Venturia inaequalis) conform Tabelului Mills:
   - Condiție de bază: frunza este considerată udă dacă Umiditatea > 90%.
   - Praguri de infecție: 9h umectare continuă la 15°C, 14h la 10°C, 21h la 7°C.
3. Evaluează riscul de Foc Bacterian (Erwinia amylovora) conform Maryblyt:
   - Risc crescut dacă temperatura maximă > 18.3°C asociată cu precipitații sau umiditate > 85%.
4. Răspunde direct, fără introduceri politicoase. Folosește formatare Markdown pentru evidențiere.

STRUCTURA OBLIGATORIE A RĂSPUNSULUI:
### STATUS ACTUAL: 
(ex: SĂNĂTOS / RISC MODERAT / INFECȚIE CONFIRMATĂ)
### ANALIZA DATELOR: 
(explică scurt ce ai calculat în C și mm)
### RECOMANDARE: 
(acțiunea de întreprins în livadă)

DATELE EXTRASE DIN STAȚIE:
{data_text}"""
    
    print("Se trimit datele către Gemini (gemini-2.5-flash)...")
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"Eroare de comunicare cu API-ul: {e}")
        return None

def trimite_pe_github(text_raport):
    os.chdir(REPO_PATH)
    
    try:
        with open("raport.json", "w", encoding="utf-8") as f:
            json.dump({"continut": text_raport}, f, ensure_ascii=False, indent=4)
        print("Fișier raport.json salvat local.")
        
        subprocess.run(["git", "add", "raport.json"], check=True)
        subprocess.run(["git", "commit", "-m", f"Actualizare raport meteo {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("✅ SUCCES: Raportul este LIVE pe GitHub Pages!")
    except subprocess.CalledProcessError as e:
        print(f"❌ EROARE GIT: Nu s-a putut face upload-ul. Detalii: {e}")

# --- EXECUȚIA PRINCIPALĂ ---
if __name__ == "__main__":
    print("Se extrag datele meteo...")
    records = extract_last_24h_data()
    
    if records:
        print(f"S-au extras {len(records)} înregistrări din ultimele 24h.")
        raport = analyze_with_ai(records)
        
        if raport:
            trimite_pe_github(raport)
        else:
            print("Eroare: Nu s-a putut genera raportul AI.")
    else:
        print("Nu există date meteo în ultimele 24h pentru a fi analizate.")
