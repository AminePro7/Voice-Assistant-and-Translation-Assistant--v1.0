# -*- coding: utf-8 -*-
import sys
import argparse
from pathlib import Path

def main():
    """Point d'entrée principal de l'assistant vocal"""
    
    # Analyse des arguments de ligne de commande
    parser = argparse.ArgumentParser(description="Assistant Vocal")
    parser.add_argument("--config", type=str, help="Chemin vers le fichier de configuration")
    parser.add_argument("--mode", type=str, choices=["rag", "en_to_fr", "fr_to_en"], default="rag",
                       help="Mode de l'assistant: 'rag' (assistant RAG), 'en_to_fr' (traduction anglais->français), "
                            "'fr_to_en' (traduction français->anglais)")
    args = parser.parse_args()
    
    # Vérification de PyAudio
    try:
        import pyaudio
        pa_test = pyaudio.PyAudio()
        pa_test.terminate()
        print("PyAudio OK.")
    except Exception as pa_err:
        print(f"Fatal: PyAudio initialization failed: {pa_err}. "
              f"Ensure microphone is connected and PyAudio is installed correctly.")
        sys.exit(1)
    
    # Initialisation et exécution de l'assistant selon le mode choisi
    assistant = None
    try:
        if args.mode == "rag":
            # Import différé pour éviter les imports circulaires
            from voice_assistant.assistant import VoiceAssistant
            print("Starting RAG Voice Assistant...")
            assistant = VoiceAssistant(args.config)
        elif args.mode in ["en_to_fr", "fr_to_en"]:
            # Vérification de la disponibilité d'Argos Translate
            try:
                import argostranslate.package
                import argostranslate.translate
            except ImportError:
                print("Fatal: Argos Translate library is required for translation mode.")
                print("Install it with: pip install argostranslate")
                sys.exit(1)
                
            # Import différé pour éviter les imports circulaires
            from voice_assistant.translator import create_translator
            direction = args.mode
            print(f"Starting Voice Translator Assistant ({direction})...")
            assistant = create_translator(direction=direction, config_path=args.config)
        else:
            print(f"Invalid mode: {args.mode}")
            sys.exit(1)
            
        # Exécution de l'assistant
        assistant.run()
        
    except FileNotFoundError as e:
        print(f"Fatal Error: A required file was not found: {e}")
        if hasattr(e, 'filename'):
            print(f"Missing file: {e.filename}")
        sys.exit(1)
    except Exception as e:
        print(f"Fatal Error in main execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if assistant and hasattr(assistant, 'cleanup') and callable(assistant.cleanup):
            try:
                assistant.cleanup()
            except:
                pass
        print("Program finished.")

if __name__ == "__main__":
    main()