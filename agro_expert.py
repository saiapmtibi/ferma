import subprocess
import json
import os
import sqlite3
import datetime
import platform 

# --- CONFIGURĂRI DINAMICE ---
if platform.system() == "Windows":
    DB_PATH = "weewx.sdb"  
    REPO_PATH = "."        
    MOD_TEST = False        
else:
    DB_PATH = "/var/lib/weewx/weewx.sdb"
    REPO_PATH = "/home/tiberiu/ferma_ai"
    MOD_TEST = True       

API_KEY = ""

def extract_last_24h_data():
    if not os.path.exists(DB_PATH):
        print(f"❌ EROARE: Nu am găsit fișierul {DB_PATH} în folder!")
        return None
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # TEST: Vedem dacă există date în ultimele 24h reale
        yesterday = int((datetime.datetime.now() - datetime.timedelta(hours=24)).timestamp())
        query_real = "SELECT dateTime, outTemp, outHumidity, rain FROM archive WHERE dateTime > ? ORDER BY dateTime ASC"
        cursor.execute(query_real, (yesterday,))
        rows = cursor.fetchall()

        # DACĂ NU SUNT DATE NOI (cazul tău pe PC), luăm ultimele 288 de rânduri (aprox 24h)
        if not rows:
            print("⚠️ Info: Nu sunt date din ultimele 24h. Extrag ultimele înregistrări disponibile...")
            query_fallback = "SELECT dateTime, outTemp, outHumidity, rain FROM archive ORDER BY dateTime DESC LIMIT 288"
            cursor.execute(query_fallback)
            rows = cursor.fetchall()
            rows.reverse() # Le punem în ordine cronologică

        conn.close()
        return rows
    except Exception as e:
        print(f"❌ EROARE SQLITE: {e}")
        return None

def analyze_with_ai(data_rows):
    if MOD_TEST:
        print("--- MOD TEST ACTIVAT (Simulare locală) ---")
        return """### STATUS ACTUAL: RISC MODERAT
### ANALIZA DATELOR:
S-au analizat datele extrase din baza de date locală. S-au identificat perioade de umiditate ridicată care pot favoriza apariția Rapănului (Venturia inaequalis).
### RECOMANDARE:
Monitorizați livada. Acest raport este generat în MOD TEST pe PC-ul local.
### BIBLIOGRAFIE:
* MacHardy, W. E., & Gadoury, D. M. (1989). A Revision of Mill's Criteria for Predicting Apple Scab Infection Periods. *Phytopathology*, 79(3), 304-310. https://doi.org/10.1094/Phyto-79-304"""

    # --- LOGICA REALĂ GEMINI ---
    try:
        from google import genai
        client = genai.Client(api_key=API_KEY)
        
        formatted_data = []
        for row in data_rows:
            dt = datetime.datetime.fromtimestamp(row[0]).strftime('%Y-%m-%d %H:%M')
            formatted_data.append(f"Ora: {dt} | Temp: {row[1]}F | Umiditate: {row[2]}% | Ploaie: {row[3]} in")
        
        data_text = "\n".join(formatted_data)
        
# PROMPT DE INTERPRETARE EXPERTĂ
        prompt = f"""Ești expert fitopatolog. Analizează datele meteo pentru măr (Rusciori, Sibiu):
{data_text}

LOGICA DE CALCUL (Referință MacHardy & Gadoury, 1989):
1. Identifică perioada de umectare: intervalul continuu cu Umiditate > 90%.
2. Calculează temperatura medie pe acea perioadă.
3. Determină riscul conform pragurilor:
   - La 7°C: Ușoară (13h), Medie (17h), Severă (23h).
   - La 8°C: Ușoară (11h), Medie (15h), Severă (20h).
   - [Folosește interpolarea pentru temperaturi intermediare].

SARCINĂ:
- Execută calculele matematice pe datele furnizate.
- Decide nivelul de risc: SĂNĂTOS, RISC MODERAT sau RISC RIDICAT.

STRUCTURA OBLIGATORIE (FĂRĂ REDUNDANȚĂ):
### STATUS: [Rezultatul tău: SĂNĂTOS / RISC MODERAT / RISC RIDICAT]

### ANALIZA TEHNICĂ:
- Umectare: [Ora start - Ora final] ([X] ore).
- Temp. medie: [Y]°C.
- Justificare: [Explicație scurtă a încadrării în tabelul Mills].

### RECOMANDARE:
- [Acțiune practică scurtă].

### BIBLIOGRAFIE:
Pe langa aceasta referinta mia adauga 4 referinte reale ongligatorii neinventate, care pot fi accesate prin doi
* MacHardy, W. E., & Gadoury, D. M. (1989). https://doi.org/10.1094/Phyto-79-304"""

    

        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        return response.text
    except Exception as e:
        print(f"❌ EROARE AI: {e}")
        return None

def trimite_pe_github(text_raport):
    # Determinăm folderul unde se află scriptul
    folder_actual = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(folder_actual, "raport.json")
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({"continut": text_raport}, f, ensure_ascii=False, indent=4)
        print(f"✅ SUCCES: Fișierul {file_path} a fost actualizat!")
        
        # Push pe GitHub doar dacă suntem pe Linux (Raspberry Pi)
        if platform.system() != "Windows":
            os.chdir(REPO_PATH)
            subprocess.run(["git", "add", "raport.json"], check=True)
            subprocess.run(["git", "commit", "-m", "Actualizare automata"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
    except Exception as e:
        print(f"❌ EROARE SALVARE: {e}")

if __name__ == "__main__":
    print("🚀 Pornire script...")
    records = extract_last_24h_data()
    if records:
        print(f"📊 Date procesate: {len(records)} linii.")
        raport = analyze_with_ai(records)
        if raport:
            trimite_pe_github(raport)
    else:
        print("🛑 Scriptul s-a oprit deoarece nu a găsit date.")