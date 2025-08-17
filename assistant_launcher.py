# -*- coding: utf-8 -*-
"""
Lanceur interactif pour l'assistant vocal
"""
import sys
import os
import subprocess
from pathlib import Path

def check_files():
    """Vérifie que tous les fichiers nécessaires sont présents"""
    required_paths = [
        "models/fr_FR-upmc-medium.onnx",
        "models/fr_FR-upmc-medium.onnx.json",
        "models/en_US-amy-medium.onnx",
        "models/en_US-amy-medium.onnx.json",
        "sounds/model_is_thinking.mp3",
        "sounds/result.mp3",
        "piper/piper.exe",
        "llm_models/gemma-2b-it.Q4_K_M.gguf",
        "doc_resolutions.md",
        "voice_assistant/__main__.py",
        "voice_assistant/assistant.py",
        "voice_assistant/translator.py"
    ]
    
    all_ok = True
    for path_str in required_paths:
        path = Path(path_str)
        if path.exists():
            print(f"[OK] {path_str}")
        else:
            print(f"[MISSING] {path_str}")
            all_ok = False
    
    return all_ok

def launch_assistant(mode):
    """Lance l'assistant dans le mode spécifié"""
    print(f"\nLancement de l'assistant en mode: {mode}")
    
    # Construire la commande
    python_exe = sys.executable
    command = [python_exe, "-m", "voice_assistant", "--mode", mode]
    
    # Exécuter la commande dans un nouveau processus
    try:
        result = subprocess.run(command)
        return result.returncode
    except KeyboardInterrupt:
        print("\nAssistant arrêté par l'utilisateur.")
        return 0
    except Exception as e:
        print(f"\nErreur lors de l'exécution de l'assistant: {e}")
        return 1

def display_menu():
    """Affiche le menu principal"""
    print("\n" + "="*50)
    print("ASSISTANT VOCAL - MENU PRINCIPAL")
    print("="*50)
    print("1. Assistant RAG (questions-réponses)")
    print("2. Traducteur Anglais -> Français")
    print("3. Traducteur Français -> Anglais")
    print("4. Vérifier les fichiers")
    print("0. Quitter")
    print("="*50)

def main():
    """Fonction principale"""
    print("ASSISTANT VOCAL - LANCEUR INTERACTIF")
    print("\nVérification des fichiers nécessaires...")
    
    files_ok = check_files()
    if not files_ok:
        print("\nCertains fichiers sont manquants. L'assistant pourrait ne pas fonctionner correctement.")
        input("Appuyez sur Entrée pour continuer...")
    
    while True:
        display_menu()
        choice = input("\nVotre choix (0-4): ")
        
        if choice == "1":
            launch_assistant("rag")
        elif choice == "2":
            launch_assistant("en_to_fr")
        elif choice == "3":
            launch_assistant("fr_to_en")
        elif choice == "4":
            print("\nVérification des fichiers...")
            check_files()
            input("\nAppuyez sur Entrée pour continuer...")
        elif choice == "0":
            print("\nFermeture du lanceur. Au revoir!")
            return 0
        else:
            print("\nChoix invalide. Veuillez réessayer.")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nLanceur arrêté par l'utilisateur.")
        sys.exit(0) 