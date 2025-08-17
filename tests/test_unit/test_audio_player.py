from unittest.mock import MagicMock, patch
import tempfile
import numpy as np  
import  unittest

# -*- coding: utf-8 -*-
"""
Tests unitaires pour AudioPlayer
"""

import unittest
import sys
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
import tempfile


class TestAudioPlayer(unittest.TestCase):
    """Tests unitaires pour la classe AudioPlayer"""
    
    def setUp(self):
        """Configuration des tests"""
        self.config = {
            'thinking_sound': 'sounds/thinking.mp3',
            'result_sound': 'sounds/result.mp3'
        }
    
    @patch('pygame.mixer.init')
    def test_initialization_with_pygame(self, mock_pygame_init):
        """Test l'initialisation avec pygame disponible"""
        from voice_assistant.audio.playback import AudioPlayer
        
        with patch('pathlib.Path.exists', return_value=True):
            player = AudioPlayer(self.config)
            
            self.assertTrue(player.pygame_available)
            mock_pygame_init.assert_called_once()
    
    @patch('pygame.mixer.init', side_effect=ImportError)
    def test_initialization_without_pygame(self, mock_pygame_init):
        """Test l'initialisation sans pygame"""
        from voice_assistant.audio.playback import AudioPlayer
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.print'):  # Supprime les prints de warning
                player = AudioPlayer(self.config)
            
            self.assertFalse(player.pygame_available)
    
    @patch('pygame.mixer.music')
    @patch('pygame.mixer.init')
    def test_play_mp3_blocking(self, mock_init, mock_music):
        """Test la lecture MP3 bloquante"""
        from voice_assistant.audio.playback import AudioPlayer
        
        mock_music.get_busy.side_effect = [True, True, False]  # Simule la lecture
        
        with patch('pathlib.Path.exists', return_value=True):
            player = AudioPlayer(self.config)
            player.pygame_available = True
            
            test_file = Path('test.mp3')
            with patch('pathlib.Path.exists', return_value=True):
                player.play_mp3(test_file, block=True)
            
            mock_music.load.assert_called_once_with('test.mp3')
            mock_music.play.assert_called_once()
            self.assertEqual(mock_music.get_busy.call_count, 3)
    
    @patch('subprocess.run')
    def test_play_wav_on_linux(self, mock_run):
        """Test la lecture WAV sur Linux"""
        from voice_assistant.audio.playback import AudioPlayer
        
        with patch('sys.platform', 'linux'):
            with patch('pathlib.Path.exists', return_value=True):
                player = AudioPlayer(self.config)
                
                test_file = Path('test.wav')
                with patch('pathlib.Path.exists', return_value=True):
                    # Simuler paplay disponible
                    mock_run.side_effect = [
                        MagicMock(returncode=0),  # paplay --version
                        MagicMock(returncode=0)   # paplay test.wav
                    ]
                    player.play_wav(test_file)
                
                # Vérifier l'appel à paplay
                calls = mock_run.call_args_list
                self.assertEqual(len(calls), 2)
                self.assertIn('paplay', calls[0][0][0])
                self.assertIn('test.wav', calls[1][0][0])
    
    @patch('subprocess.run')
    def test_play_wav_on_macos(self, mock_run):
        """Test la lecture WAV sur macOS"""
        from voice_assistant.audio.playback import AudioPlayer
        
        with patch('sys.platform', 'darwin'):
            with patch('pathlib.Path.exists', return_value=True):
                player = AudioPlayer(self.config)
                
                test_file = Path('test.wav')
                with patch('pathlib.Path.exists', return_value=True):
                    player.play_wav(test_file)
                
                mock_run.assert_called_once_with(
                    ['afplay', 'test.wav'],
                    check=True,
                    capture_output=True
                )
    
    @patch('winsound.PlaySound')
    def test_play_wav_on_windows(self, mock_playsound):
        """Test la lecture WAV sur Windows"""
        from voice_assistant.audio.playback import AudioPlayer
        
        with patch('sys.platform', 'win32'):
            with patch('pathlib.Path.exists', return_value=True):
                player = AudioPlayer(self.config)
                player.winsound_available = True
                
                test_file = Path('test.wav')
                with patch('pathlib.Path.exists', return_value=True):
                    player.play_wav(test_file)
                
                mock_playsound.assert_called_once()
    
    @patch('threading.Thread')
    def test_play_audio_async(self, mock_thread):
        """Test la lecture audio asynchrone"""
        from voice_assistant.audio.playback import AudioPlayer
        
        with patch('pathlib.Path.exists', return_value=True):
            player = AudioPlayer(self.config)
            
            test_file = Path('test.mp3')
            with patch('pathlib.Path.exists', return_value=True):
                player.play_audio_async(test_file)
            
            mock_thread.assert_called_once()
            args, kwargs = mock_thread.call_args
            self.assertTrue(kwargs.get('daemon', False))
    
    def test_play_thinking_sound(self):
        """Test la lecture du son de réflexion"""
        from voice_assistant.audio.playback import AudioPlayer
        
        with patch('pathlib.Path.exists', return_value=True):
            player = AudioPlayer(self.config)
            
            with patch.object(player, 'play_mp3') as mock_play:
                player.play_thinking_sound(block=True)
                mock_play.assert_called_once_with(player.thinking_sound_path, block=True)
    
    def test_play_result_sound(self):
        """Test la lecture du son de résultat"""
        from voice_assistant.audio.playback import AudioPlayer
        
        with patch('pathlib.Path.exists', return_value=True):
            player = AudioPlayer(self.config)
            
            with patch.object(player, 'play_mp3') as mock_play:
                player.play_result_sound(block=True)
                mock_play.assert_called_once_with(player.result_sound_path, block=True)

