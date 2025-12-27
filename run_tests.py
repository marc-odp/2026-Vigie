import subprocess
import os
import sys

def main():
    print("🚀 Déclenchement de la suite de tests Vigie...")
    
    # Set PYTHONPATH
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    
    # Run pytest
    try:
        result = subprocess.run(
            ["uv", "run", "pytest", "tests", "-v"],
            env=env,
            capture_output=False,
            text=True
        )
        if result.returncode == 0:
            print("\n✅ Tous les tests sont passés !")
        else:
            print(f"\n❌ Échec des tests (code {result.returncode})")
            sys.exit(result.returncode)
    except FileNotFoundError:
        print("\n❌ Erreur: 'uv' ou 'pytest' n'est pas installé.")
        sys.exit(1)

if __name__ == "__main__":
    main()
