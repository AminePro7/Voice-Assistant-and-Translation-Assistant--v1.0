# -*- coding: utf-8 -*-
import time
import re
import gc
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Literal

from voice_assistant.utils.config import get_config
from voice_assistant.utils.normalization import normalize_audio_advanced
from voice_assistant.stt.whisper_stt import WhisperSTT
from voice_assistant.tts.piper_tts import PiperTTS
from voice_assistant.audio.record import AudioRecorder
from voice_assistant.audio.playback import AudioPlayer

# Import pour Argos Translate
try:
    import argostranslate.package
    import argostranslate.translate
    ARGOSTRANSLATE_AVAILABLE = True
    print("Argos Translate found.")
except ImportError:
    print("ERROR: 'argostranslate' library is missing.")
    print("Install it with: pip install argostranslate")
    ARGOSTRANSLATE_AVAILABLE = False

class TranslatorAssistant:
    """Classe pour l'assistant vocal de traduction EN/FR"""
    
    def __init__(self, 
                 direction: Literal["en_to_fr", "fr_to_en"] = "en_to_fr", 
                 config_path: Optional[str] = None):
        """
        Initialise l'assistant de traduction
        
        Args:
            direction: Direction de traduction ("en_to_fr" ou "fr_to_en")
            config_path: Chemin vers le fichier de configuration
        """
        print(f"Initializing voice translator assistant ({direction})...")
        
        if not ARGOSTRANSLATE_AVAILABLE:
            raise RuntimeError("Argos Translate is not available. The assistant cannot start.")
        
        # Direction de traduction
        self.direction = direction
        self.source_lang_code = "en" if direction == "en_to_fr" else "fr"
        self.target_lang_code = "fr" if direction == "en_to_fr" else "en"
        
        # Chargement de la configuration
        self.config = get_config(config_path)
        
        # Optimisations pour les ressources limitées
        self._optimize_for_limited_resources()
        
        # Création du répertoire temporaire
        self._setup_temp_dir()
        
        # Initialisation des composants
        self.audio_recorder = self._init_audio_recorder()
        self.audio_player = self._init_audio_player()
        self.stt = self._init_stt()
        self.tts = self._init_tts()
        
        # Initialisation du moteur de traduction
        self._init_translation_engine()
        
        # Messages système selon la direction de traduction
        if direction == "en_to_fr":
            self.welcome_message = "Hello, I am your voice translation assistant. Tell me what you want to translate from English to French."
            self.no_speech_msg = "I didn't quite catch that. Could you please repeat more clearly in English?"
            self.empty_transcription_msg = "I couldn't understand what you said in English. Can you please rephrase?"
            self.translation_error_msg = "Sorry, an error occurred during translation. Please try again."
            self.recording_prompt_msg = "Recording... (Speak English now for translation)"
            self.transcription_lang_msg = "English"
            self.assistant_voice_lang = "en"
        else:  # fr_to_en
            self.welcome_message = "Bonjour, je suis votre assistant vocal de traduction. Dites-moi ce que vous voulez traduire du français vers l'anglais."
            self.no_speech_msg = "Je n'ai pas bien entendu. Pourriez-vous répéter plus clairement s'il vous plaît ?"
            self.empty_transcription_msg = "Je n'ai pas réussi à comprendre ce que vous avez dit. Pouvez-vous reformuler ?"
            self.translation_error_msg = "Désolé, une erreur est survenue pendant la traduction. Veuillez réessayer."
            self.recording_prompt_msg = "Enregistrement... (Parlez maintenant en français pour la traduction)"
            self.transcription_lang_msg = "French"
            self.assistant_voice_lang = "fr"
        
        print("Initialization complete!")
    
    def _optimize_for_limited_resources(self) -> None:
        """Optimisations pour ressources limitées"""
        device_type = self._get_device_type()
        
        # Threading optimisé pour CPU
        if device_type == "cpu":
            import os
            # Limite les threads pour éviter la surcharge
            os.environ["OMP_NUM_THREADS"] = "2"
            os.environ["MKL_NUM_THREADS"] = "2"
            
            # Setting this often helps with stability on CPU with PyTorch
            try:
                import torch
                torch.set_num_threads(2)
                print("CPU optimizations: OMP_NUM_THREADS, MKL_NUM_THREADS, torch.set_num_threads set to 2.")
            except ImportError:
                pass
        
        # Garbage collection plus fréquent
        gc.set_threshold(100, 10, 10)  # Plus agressif
        print("Garbage collection threshold set to more aggressive values.")
    
    def _setup_temp_dir(self) -> None:
        """Crée le répertoire temporaire"""
        import tempfile
        import shutil
        
        temp_dir_config = self.config.get('general', 'temp_dir')
        if temp_dir_config:
            self.temp_dir = Path(temp_dir_config)
            self.temp_dir.mkdir(exist_ok=True)
        else:
            self.temp_dir = Path(tempfile.mkdtemp(prefix='voice_translator_'))
        
        print(f"Temp directory: {self.temp_dir}")
        
        # Création du répertoire de sortie
        output_dir = self.config.get('general', 'output_dir', 'output')
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def _init_audio_recorder(self) -> AudioRecorder:
        """Initialise l'enregistreur audio"""
        audio_config = self.config.get_section('audio')
        return AudioRecorder(audio_config)
    
    def _init_audio_player(self) -> AudioPlayer:
        """Initialise le lecteur audio"""
        sounds_config = self.config.get_section('sounds')
        return AudioPlayer(sounds_config)
    
    def _init_stt(self) -> WhisperSTT:
        """Initialise le système STT"""
        stt_config = self.config.get_section('stt')
        
        # Modifier la configuration pour spécifier la langue source
        stt_config_copy = dict(stt_config)
        stt_config_copy['language'] = self.source_lang_code
        
        return WhisperSTT(stt_config_copy)
    
    def _init_tts(self) -> PiperTTS:
        """Initialise le système TTS"""
        tts_config = self.config.get_section('tts')
        return PiperTTS(tts_config)
    
    def _init_translation_engine(self) -> None:
        """Initialise le moteur de traduction Argos Translate"""
        print(f"Initializing Argos Translate engine ({self.source_lang_code} -> {self.target_lang_code})...")
        
        try:
            print("Updating Argos Translate package index...")
            argostranslate.package.update_package_index()
            available_packages = argostranslate.package.get_available_packages()
            installed_packages = argostranslate.package.get_installed_packages()
            needed_translation_found = False
            
            # Vérifier si le package de traduction est installé
            for pkg in installed_packages:
                if pkg.from_code == self.source_lang_code and pkg.to_code == self.target_lang_code:
                    needed_translation_found = True
                    print(f"Found installed package: {pkg.from_code} -> {pkg.to_code}")
                    break
            
            # Si le package n'est pas installé, essayer de l'installer
            if not needed_translation_found:
                print(f"Direct package {self.source_lang_code} -> {self.target_lang_code} not explicitly installed. Checking availability...")
                package_to_install = next(
                    filter(
                        lambda x: x.from_code == self.source_lang_code and x.to_code == self.target_lang_code,
                        available_packages
                    ),
                    None
                )
                
                if package_to_install:
                    print(f"Found direct package {self.source_lang_code} -> {self.target_lang_code}. Attempting download and installation...")
                    try:
                        argostranslate.package.install_from_path(package_to_install.download())
                        print("Package installed successfully.")
                        installed_packages = argostranslate.package.get_installed_packages()  # Recharger après installation
                    except Exception as install_e:
                        print(f"Error installing package: {install_e}")
                else:
                    print(f"Could not find a direct package for {self.source_lang_code} to {self.target_lang_code}.")
                    # Vérifier si les modèles sont installés séparément
                    source_installed = any(p.from_code == self.source_lang_code or p.to_code == self.source_lang_code for p in installed_packages)
                    target_installed = any(p.from_code == self.target_lang_code or p.to_code == self.target_lang_code for p in installed_packages)
                    
                    if not source_installed or not target_installed:
                        raise RuntimeError(
                            f"Required language models ('{self.source_lang_code}' or '{self.target_lang_code}') "
                            f"not found and direct package unavailable/failed to install. "
                            f"Please install manually (e.g., 'argospm install translate-{self.source_lang_code}_{self.target_lang_code}')."
                        )
                    else:
                        print(f"Warning: Direct {self.source_lang_code}->{self.target_lang_code} package not found/installed, "
                              f"but '{self.source_lang_code}' and '{self.target_lang_code}' seem available. "
                              f"Translation might rely on intermediate languages if possible.")
            
            # Charger le moteur de traduction
            print(f"Loading translation engine ({self.source_lang_code} -> {self.target_lang_code})...")
            installed_languages = argostranslate.translate.get_installed_languages()
            source_lang = next((lang for lang in installed_languages if lang.code == self.source_lang_code), None)
            target_lang = next((lang for lang in installed_languages if lang.code == self.target_lang_code), None)
            
            if not source_lang:
                raise RuntimeError(f"Source language '{self.source_lang_code}' model not found among installed languages after check/install attempt.")
            if not target_lang:
                raise RuntimeError(f"Target language '{self.target_lang_code}' model not found among installed languages after check/install attempt.")
            
            self.translation_engine = source_lang.get_translation(target_lang)
            
            if not self.translation_engine:
                raise RuntimeError(f"Could not get translation engine from '{self.source_lang_code}' to '{self.target_lang_code}'. "
                                  f"Check installed package capabilities (e.g., need {self.source_lang_code}_{self.target_lang_code} package).")
            
            print(f"Argos Translate engine loaded successfully ({self.source_lang_code} -> {self.target_lang_code}).")
            
        except Exception as e:
            print(f"Error initializing Argos Translate: {e}")
            print("Please ensure the required language models are available and network connection is active for downloads.")
            import traceback
            traceback.print_exc()
            raise
    
    def _get_device_type(self) -> str:
        """
        Détermine le type d'appareil à utiliser
        
        Returns:
            Type d'appareil ('cuda' ou 'cpu')
        """
        device_type = self.config.get('general', 'device_type', 'auto')
        
        if device_type == 'auto':
            try:
                import torch
                if torch.cuda.is_available():
                    return 'cuda'
            except ImportError:
                pass
            return 'cpu'
        
        return device_type
    
    def translate_text(self, text: str) -> str:
        """
        Traduit un texte
        
        Args:
            text: Texte à traduire
            
        Returns:
            Texte traduit
        """
        if not text:
            print("Translation skipped: No input text.")
            return ""
        
        print(f"Translating text from {self.source_lang_code} to {self.target_lang_code}...")
        try:
            translated_text = self.translation_engine.translate(text)
            if translated_text:
                print("Translation successful.")
                return translated_text
            else:
                print("Translation returned an empty result.")
                return self.translation_error_msg
        except Exception as e:
            print(f"Error during translation: {e}")
            import traceback
            traceback.print_exc()
            return self.translation_error_msg
    
    def run(self) -> None:
        """Exécute l'assistant de traduction"""
        try:
            print("\n" + "="*40 + f"\n Voice Translator Assistant ({self.source_lang_code} -> {self.target_lang_code}) ready.\n Press Ctrl+C to stop.\n" + "="*40 + "\n")
            self.tts.speak(self.welcome_message, language=self.assistant_voice_lang, wait=True)

            while True:
                try:
                    # Enregistrement audio
                    print(self.recording_prompt_msg)
                    audio_data, audio_level_rms = self.audio_recorder.record()
                    if audio_data is None:
                        self.tts.speak("Problème lors de l'enregistrement audio. Réessayez.", language=self.assistant_voice_lang, wait=True)
                        time.sleep(1)
                        continue
                    
                    # Vérification du niveau audio
                    overall_silence_threshold_rms = self.config.get('audio', 'overall_silence_threshold_rms', 0.005)
                    if audio_level_rms < overall_silence_threshold_rms:
                        print(f"Silence detected (Overall RMS: {audio_level_rms:.4f} < {overall_silence_threshold_rms:.4f}).")
                        time.sleep(0.5) 
                        continue
                    
                    # Normalisation audio
                    normalized_audio = normalize_audio_advanced(audio_data)
                    
                    # Transcription
                    print(f"Transcribing audio (expecting {self.transcription_lang_msg})...")
                    transcribed_text = self.stt.transcribe_audio_data(normalized_audio)
                    if not transcribed_text:
                        self.tts.speak(self.empty_transcription_msg, language=self.assistant_voice_lang, wait=True)
                        continue
                    
                    # Nettoyage du texte transcrit
                    transcribed_text = re.sub(r'\[.*?\]|\(.*?\)', '', transcribed_text).strip()
                    transcribed_text = re.sub(r'\s+', ' ', transcribed_text).strip()
                    
                    print(f"User said ({self.source_lang_code}): \"{transcribed_text}\"")
                    
                    # Traduction
                    translated_text = self.translate_text(transcribed_text)
                    
                    if translated_text and translated_text != self.translation_error_msg:
                        print(f"-> Translated text ({self.target_lang_code}): \"{translated_text}\"")
                        
                        # Synthèse vocale du texte traduit dans la langue cible
                        print(f"Speaking the translated text ({self.target_lang_code})...")
                        self.tts.speak(translated_text, language=self.target_lang_code, wait=True)
                    elif translated_text == self.translation_error_msg:
                        print("Translation failed.")
                        self.tts.speak(self.translation_error_msg, language=self.assistant_voice_lang, wait=True)
                    else:
                        print("Translation returned empty string unexpectedly.")
                        self.tts.speak("I was unable to translate that.", language=self.assistant_voice_lang, wait=True)
                    
                    print(f"\nReady for the next command (speak {self.transcription_lang_msg})...")

                except Exception as e_loop:
                    print(f"\n--- Error in main loop iteration: {e_loop} ---")
                    import traceback
                    traceback.print_exc()
                    error_message = "Oops, an unexpected error occurred. We will try again."
                    if self.assistant_voice_lang == "fr":
                        error_message = "Oups, une erreur inattendue s'est produite. Nous allons réessayer."
                    self.tts.speak(error_message, language=self.assistant_voice_lang, wait=True)
                    time.sleep(1)
                    continue
        
        except KeyboardInterrupt:
            print("\nCtrl+C detected. Stopping translator...")
            try:
                farewell_message = "Translation finished. Goodbye!"
                if self.assistant_voice_lang == "fr":
                    farewell_message = "Traduction terminée. Au revoir !"
                self.tts.speak(farewell_message, language=self.assistant_voice_lang, wait=True)
            except:
                pass
        finally:
            self.cleanup()
    
    def cleanup(self) -> None:
        """Nettoie les ressources"""
        print("Cleaning up resources...")
        try:
            # Nettoyage TTS
            if hasattr(self, 'tts') and hasattr(self.tts, 'cleanup'):
                self.tts.cleanup()
            
            # Suppression du répertoire temporaire
            if hasattr(self, 'temp_dir') and self.temp_dir and self.temp_dir.exists():
                import shutil
                shutil.rmtree(self.temp_dir)
                print(f"Removed temporary directory: {self.temp_dir}")
        except Exception as e:
            print(f"Error during cleanup: {e}")


def create_translator(direction: Literal["en_to_fr", "fr_to_en"] = "en_to_fr", config_path: Optional[str] = None) -> TranslatorAssistant:
    """
    Crée un assistant de traduction
    
    Args:
        direction: Direction de traduction ("en_to_fr" ou "fr_to_en")
        config_path: Chemin vers le fichier de configuration
        
    Returns:
        Instance de TranslatorAssistant
    """
    return TranslatorAssistant(direction=direction, config_path=config_path) 