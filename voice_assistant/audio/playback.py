# -*- coding: utf-8 -*-
import sys
import time
import threading
from pathlib import Path
from typing import Optional, Dict, Any

class AudioPlayer:
    """Classe pour la lecture audio multi-plateformes"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialise le lecteur audio
        
        Args:
            config: Configuration audio
        """
        self.pygame_available = False
        self.winsound_available = False
        
        # Tente d'initialiser pygame pour la lecture MP3
        try:
            import pygame
            pygame.mixer.init()
            self.pygame_available = True
            print("Pygame mixer initialized.")
        except ImportError:
            print("Warning: 'pygame' not found. MP3 playback disabled.")
        except Exception as e:
            print(f"Warning: Failed to initialize pygame mixer: {e}. MP3 playback disabled.")
        
        # Tente d'importer winsound pour Windows
        if sys.platform == 'win32':
            try:
                import winsound
                self.winsound_available = True
            except ImportError:
                print("Warning: 'winsound' not found on Windows.")
        
        # Chemins des sons système
        self.thinking_sound_path = config.get('thinking_sound')
        self.result_sound_path = config.get('result_sound')
        
        if self.thinking_sound_path:
            self.thinking_sound_path = Path(self.thinking_sound_path)
            if not self.thinking_sound_path.exists():
                print(f"Warning: Thinking sound not found at {self.thinking_sound_path}")
                self.thinking_sound_path = None
        
        if self.result_sound_path:
            self.result_sound_path = Path(self.result_sound_path)
            if not self.result_sound_path.exists():
                print(f"Warning: Result sound not found at {self.result_sound_path}")
                self.result_sound_path = None
    
    def play_mp3(self, file_path: Path, block: bool = True) -> None:
        """
        Joue un fichier MP3
        
        Args:
            file_path: Chemin du fichier MP3
            block: Si True, bloque jusqu'à la fin de la lecture
        """
        if not self.pygame_available or not file_path or not file_path.exists():
            return
        
        try:
            import pygame
            pygame.mixer.music.load(str(file_path))
            pygame.mixer.music.play()
            if block:
                while pygame.mixer.music.get_busy():
                    time.sleep(0.05)
        except Exception as e:
            print(f"Error playing MP3 {file_path}: {e}")
    
    def play_wav(self, file_path: Path, block: bool = True) -> None:
        """
        Joue un fichier WAV
        
        Args:
            file_path: Chemin du fichier WAV
            block: Si True, bloque jusqu'à la fin de la lecture
        """
        if not file_path.exists():
            print(f"Playback error: Audio file not found at {file_path}")
            return
        
        file_path_str = str(file_path)
        
        try:
            if sys.platform == 'win32' and self.winsound_available:
                import winsound
                winsound.PlaySound(file_path_str, winsound.SND_FILENAME | winsound.SND_NODEFAULT)
            elif sys.platform == 'darwin':  # macOS
                import subprocess
                subprocess.run(['afplay', file_path_str], check=True, capture_output=True)
            elif sys.platform.startswith('linux'):
                import subprocess
                player = None
                try:
                    subprocess.run(['paplay', '--version'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    player = 'paplay'
                except (FileNotFoundError, subprocess.CalledProcessError):
                    try:
                        subprocess.run(['aplay', '--version'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        player = 'aplay'
                    except (FileNotFoundError, subprocess.CalledProcessError):
                        print("Warning: No paplay or aplay found for audio playback on Linux.")
                if player:
                    subprocess.run([player, file_path_str], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                print(f"Warning: Audio playback for platform '{sys.platform}' is not explicitly implemented.")
                # Fallback to pygame if available
                if self.pygame_available:
                    self.play_mp3(file_path, block)
        except Exception as e:
            print(f"Error during audio playback of {file_path}: {e}")
        finally:
            if sys.platform == 'win32':
                time.sleep(0.1)  # Small delay to ensure audio is played
    
    def play_audio_async(self, file_path: Path) -> None:
        """
        Joue un fichier audio de manière asynchrone
        
        Args:
            file_path: Chemin du fichier audio
        """
        if not file_path.exists():
            return
        
        threading.Thread(target=self._play_audio_worker, args=(file_path,), daemon=True).start()
    
    def _play_audio_worker(self, file_path: Path) -> None:
        """
        Worker thread pour la lecture audio asynchrone
        
        Args:
            file_path: Chemin du fichier audio
        """
        if file_path.suffix.lower() == '.mp3':
            self.play_mp3(file_path, block=True)
        elif file_path.suffix.lower() == '.wav':
            self.play_wav(file_path, block=True)
    
    def play_thinking_sound(self, block: bool = False) -> None:
        """
        Joue le son de réflexion
        
        Args:
            block: Si True, bloque jusqu'à la fin de la lecture
        """
        if self.thinking_sound_path:
            if block:
                self.play_mp3(self.thinking_sound_path, block=True)
            else:
                self.play_audio_async(self.thinking_sound_path)
    
    def play_result_sound(self, block: bool = True) -> None:
        """
        Joue le son de résultat
        
        Args:
            block: Si True, bloque jusqu'à la fin de la lecture
        """
        if self.result_sound_path:
            if block:
                self.play_mp3(self.result_sound_path, block=True)
            else:
                self.play_audio_async(self.result_sound_path) 