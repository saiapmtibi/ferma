import subprocess
import json
import os
import datetime

# CONFIGURARE
REPO_PATH = "/home/tiberiu/ferma_ai"

def test_upload_github():
    # Ne asigurăm că suntem în folderul corect
    os.chdir(REPO_PATH)
    
    # 1. Creăm un raport fictiv (fără Gemini)
    ora_actuala = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    test_data = {
        "continut": f"TEST AUTOMATIZARE - Raport generat la ora {ora_actuala}. Legătura cu GitHub este activă."
    }
    
    try:
        # Salvare raport.json
        with open("raport.json", "w", encoding="utf-8") as f:
            json.dump(test_data, f, ensure_ascii=False, indent=4)
        print("--- Pasul 1: raport.json a fost creat local. ---")

        # 2. Executare comenzi Git
        print("--- Pasul 2: Se încearcă trimiterea către GitHub... ---")
        
        subprocess.run(["git", "add", "raport.json"], check=True)
        
        # Folosim un mesaj de commit care include ora pentru a vedea clar schimbarea
        commit_msg = f"Test upload fara Gemini {ora_actuala}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        
        subprocess.run(["git", "push", "origin", "main"], check=True)
        
        print("\n✅ SUCCES: Fișierul a fost urcat pe GitHub!")
        print(f"Verifică aici: https://draghicitiberiu97-ai.github.io/ferma/")

    except subprocess.CalledProcessError as e:
        print(f"\n❌ EROARE GIT: {e}")
        print("Asigură-te că ai rulat comenzile 'git config' pentru email și nume.")
    except Exception as e:
        print(f"\n❌ EROARE GENERALĂ: {e}")

if __name__ == "__main__":
    test_upload_github()
