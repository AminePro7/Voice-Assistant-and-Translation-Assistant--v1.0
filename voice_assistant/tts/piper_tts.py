# -*- coding: utf-8 -*-

import time

import subprocess

import re

from pathlib import Path

import tempfile

import threading

from typing import Dict, Any, Optional, List



class PiperTTS:

    """Classe pour la synthèse vocale avec Piper TTS"""

    

    def __init__(self, config: Dict[str, Any]):

        """

        Initialise le système TTS Piper

        

        Args:

            config: Configuration TTS

        """

        # Chemins des fichiers Piper

        self.piper_exe = Path(config.get('piper_exe', 'piper/piper.exe'))

        self.tts_model = Path(config.get('model', 'models/fr_FR-upmc-medium.onnx'))

        self.tts_config = Path(config.get('config', 'models/fr_FR-upmc-medium.onnx.json'))

        self.length_scale = config.get('length_scale', 1.0)
        
        # Modèles de voix par langue
        self.language_models = {
            "fr": {
                "model": Path(config.get('model', 'models/fr_FR-upmc-medium.onnx')),
                "config": Path(config.get('config', 'models/fr_FR-upmc-medium.onnx.json'))
            },
            "en": {
                "model": Path('models/en_US-amy-medium.onnx'),
                "config": Path('models/en_US-amy-medium.onnx.json')
            }
        }
        
        # Vérification des fichiers
        self._check_files()
        
        # Création du répertoire temporaire
        self.temp_dir = Path(tempfile.mkdtemp(prefix='piper_tts_'))
        print(f"Piper TTS temp directory: {self.temp_dir}")
        
        # Conversion des chemins en chaînes
        self.piper_exe_str = str(self.piper_exe)
        self.tts_model_str = str(self.tts_model)
        self.tts_config_str = str(self.tts_config)
    
    def _check_files(self) -> None:
        """
        Vérifie que les fichiers nécessaires existent
        
        Raises:
            FileNotFoundError: Si un fichier est manquant
        """
        essential_files = {
            self.piper_exe: "Piper executable",
            self.tts_model: "TTS model",
            self.tts_config: "TTS config",
        }
        
        # Vérification des modèles supplémentaires
        for lang, model_info in self.language_models.items():
            essential_files[model_info["model"]] = f"TTS model for {lang}"
            essential_files[model_info["config"]] = f"TTS config for {lang}"
        
        for file_path, description in essential_files.items():
            if not file_path.exists():
                raise FileNotFoundError(f"{description} not found: {file_path}")
    
    def speak(self, text: str, language: str = None, wait: bool = True) -> bool:
        """
        Synthétise et joue le texte
        
        Args:
            text: Texte à synthétiser
            language: Langue à utiliser (fr ou en)
            wait: Si True, attend la fin de la lecture
            
        Returns:
            True si la synthèse a réussi, False sinon
        """
        if not text or not text.strip():
            return False
        
        # Nettoyage du texte
        cleaned_text = self._clean_text(text)
        if not cleaned_text:
            return False

        # Sélection du modèle en fonction de la langue
        model_str = self.tts_model_str
        config_str = self.tts_config_str
        
        if language and language in self.language_models:
            model_str = str(self.language_models[language]["model"])
            config_str = str(self.language_models[language]["config"])
            print(f"Using {language} voice model: {model_str}")

        # Génération du fichier WAV
        output_wav_path = self._generate_wav(cleaned_text, model_str, config_str)
        if not output_wav_path or not output_wav_path.exists():
            return False
        
        # Lecture du fichier WAV
        if wait:
            return self._play_audio_sync(output_wav_path)
        else:
            threading.Thread(target=self._play_audio_async, 
                            args=(output_wav_path,), daemon=True).start()
            return True
    
    def _clean_text(self, text: str) -> str:
        """
        Nettoie le texte pour la synthèse
        
        Args:
            text: Texte à nettoyer
            
        Returns:
            Texte nettoyé
        """
        # Suppression des caractères spéciaux
        cleaned_text = re.sub(r'[*#`]', '', text).strip()
        return cleaned_text
    
    def _generate_wav(self, text: str, model_str: str = None, config_str: str = None) -> Optional[Path]:
        """
        Génère un fichier WAV à partir du texte
        
        Args:
            text: Texte à synthétiser
            model_str: Chemin du modèle à utiliser
            config_str: Chemin du fichier de configuration à utiliser
            
        Returns:
            Chemin du fichier WAV ou None en cas d'erreur
        """
        timestamp = int(time.time() * 1000)
        output_wav_path = self.temp_dir / f"response_part_{timestamp}.wav"
        output_wav_str = str(output_wav_path)

        # Utiliser les valeurs par défaut si non spécifiées
        if model_str is None:
            model_str = self.tts_model_str
        if config_str is None:
            config_str = self.tts_config_str

        piper_command = [
            self.piper_exe_str, 
            "--model", model_str,
            "--config", config_str, 
            "--output_file", output_wav_str,
            "--length-scale", str(self.length_scale)
        ]
        
        try:
            process = subprocess.Popen(
                piper_command, 
                stdin=subprocess.PIPE, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            _, stderr_output = process.communicate(input=text.encode('utf-8'))

            if process.returncode != 0:
                print(f"Piper TTS Error (Code {process.returncode}):\n"
                      f"{stderr_output.decode('utf-8', errors='ignore')}")
                return None

            if output_wav_path.exists() and output_wav_path.stat().st_size > 100:
                return output_wav_path
            else:
                print(f"Piper TTS Error: Output WAV missing or too small.\n"
                      f"Stderr: {stderr_output.decode('utf-8', errors='ignore')}")
                return None
        except Exception as e:
            print(f"TTS generation error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _play_audio_sync(self, wav_file_path: Path) -> bool:
        """
        Joue un fichier audio de manière synchrone
        
        Args:
            wav_file_path: Chemin du fichier WAV
            
        Returns:
            True si la lecture a réussi, False sinon
        """
        if not wav_file_path.exists():
            print(f"Playback error: Audio file not found at {wav_file_path}")
            return False
        
        try:
            import sys
            
            if sys.platform == 'win32':
                try:
                    import winsound
                    winsound.PlaySound(str(wav_file_path), winsound.SND_FILENAME | winsound.SND_NODEFAULT)
                except ImportError:
                    print("Warning: winsound not available on Windows.")
                    return False
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['afplay', str(wav_file_path)], check=True, capture_output=True)
            elif sys.platform.startswith('linux'):
                player = None
                try:
                    subprocess.run(['paplay', '--version'], check=True, 
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    player = 'paplay'
                except (FileNotFoundError, subprocess.CalledProcessError):
                    try:
                        subprocess.run(['aplay', '--version'], check=True, 
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        player = 'aplay'
                    except (FileNotFoundError, subprocess.CalledProcessError):
                        print("Warning: No paplay or aplay found for audio playback on Linux.")
                        return False
                if player:
                    subprocess.run([player, str(wav_file_path)], check=True, 
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                print(f"Warning: Audio playback for platform '{sys.platform}' is not implemented.")
                return False
            
            return True
        except Exception as e:
            print(f"Error during audio playback of {wav_file_path}: {e}")
            return False
        finally:
            if sys.platform == 'win32':
                time.sleep(0.1)  # Small delay to ensure audio is played
            try:
                if wav_file_path.exists():
                    wav_file_path.unlink()
            except Exception as e:
                print(f"Warning: Could not remove temporary WAV file {wav_file_path}: {e}")
    
    def _play_audio_async(self, wav_file_path: Path) -> None:
        """
        Joue un fichier audio de manière asynchrone
        
        Args:
            wav_file_path: Chemin du fichier WAV
        """
        self._play_audio_sync(wav_file_path)
    
    def speak_sentences(self, text: str, language: str = None, wait: bool = True) -> bool:
        """
        Synthétise et joue un texte en le découpant en phrases
        
        Args:
            text: Texte à synthétiser
            language: Langue à utiliser (fr ou en)
            wait: Si True, attend la fin de la lecture
            
        Returns:
            True si la synthèse a réussi, False sinon
        """
        if not text or not text.strip():
            return False
        
        # Découpage en phrases
        sentences = self._split_into_sentences(text)
        
        success = True
        for sentence in sentences:
            if sentence.strip():
                result = self.speak(sentence, language=language, wait=wait)
                success = success and result
        
        return success
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Découpe un texte en phrases
        
        Args:
            text: Texte à découper
            
        Returns:
            Liste des phrases
        """
        # Motif pour séparer les phrases
        sentence_pattern = re.compile(r'(?<=[.!?\n])\s+')
        
        # Découpage en phrases
        sentences = sentence_pattern.split(text)
        
        return sentences
    
    def cleanup(self) -> None:
        """Nettoie les fichiers temporaires"""
        try:
            import shutil
            if self.temp_dir and self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                print(f"Removed temporary directory: {self.temp_dir}")
        except Exception as e:
            print(f"Error during cleanup: {e}") 