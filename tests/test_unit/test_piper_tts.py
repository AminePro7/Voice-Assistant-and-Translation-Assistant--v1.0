from unittest.mock import MagicMock, patch
import tempfile
import numpy as np  
import  unittest

# -*- coding: utf-8 -*-
"""
Tests unitaires pour PiperTTS
"""

import unittest
import subprocess
import tempfile
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
import time


class TestPiperTTS(unittest.TestCase):
    """Tests unitaires pour la classe PiperTTS"""
    
    def setUp(self):
        """Configuration des tests"""
        self.config = {
            'piper_exe': 'piper/piper.exe',
            'model': 'models/fr_FR-upmc-medium.onnx',
            'config': 'models/fr_FR-upmc-medium.onnx.json',
            'length_scale': 1.0
        }
        self.temp_dir = tempfile.mkdtemp()
    
    @patch('pathlib.Path.exists')
    def test_initialization(self, mock_exists):
        """Test l'initialisation de PiperTTS"""
        mock_exists.return_value = True
        
        from voice_assistant.tts.piper_tts import PiperTTS
        
        tts = PiperTTS(self.config)
        
        self.assertEqual(tts.length_scale, 1.0)
        self.assertIsNotNone(tts.temp_dir)
        self.assertIn('fr', tts.language_models)
        self.assertIn('en', tts.language_models)
    
    @patch('pathlib.Path.exists')
    def test_check_files_missing(self, mock_exists):
        """Test la vérification des fichiers manquants"""
        mock_exists.return_value = False
        
        from voice_assistant.tts.piper_tts import PiperTTS
        
        with self.assertRaises(FileNotFoundError):
            PiperTTS(self.config)
    
    def test_clean_text(self):
        """Test le nettoyage du texte"""
        from voice_assistant.tts.piper_tts import PiperTTS
        
        with patch('pathlib.Path.exists', return_value=True):
            tts = PiperTTS(self.config)
            
            # Test avec caractères spéciaux
            dirty_text = "**Bonjour** #monde `code` ***test***"
            cleaned = tts._clean_text(dirty_text)
            self.assertEqual(cleaned, "Bonjour monde code test")
            
            # Test avec texte vide
            self.assertEqual(tts._clean_text(""), "")
            self.assertEqual(tts._clean_text("   "), "")
    
    @patch('subprocess.Popen')
    @patch('pathlib.Path.exists')
    def test_generate_wav_success(self, mock_exists, mock_popen):
        """Test la génération réussie d'un fichier WAV"""
        mock_exists.return_value = True
        
        # Mock du processus Piper
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b'', b'')
        mock_popen.return_value = mock_process
        
        from voice_assistant.tts.piper_tts import PiperTTS
        
        tts = PiperTTS(self.config)
        
        # Mock pour vérifier que le fichier existe après génération
        with patch('pathlib.Path.stat') as mock_stat:
            mock_stat.return_value.st_size = 10000  # Fichier de 10KB
            result = tts._generate_wav("Bonjour le monde")
        
        self.assertIsNotNone(result)
        mock_popen.assert_called_once()
        
        # Vérifier les arguments passés à Piper
        call_args = mock_popen.call_args[0][0]
        self.assertIn('--model', call_args)
        self.assertIn('--length-scale', call_args)
    
    @patch('subprocess.Popen')
    @patch('pathlib.Path.exists')
    def test_generate_wav_failure(self, mock_exists, mock_popen):
        """Test l'échec de génération WAV"""
        mock_exists.return_value = True
        
        # Mock d'un processus qui échoue
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = (b'', b'Error: Model not found')
        mock_popen.return_value = mock_process
        
        from voice_assistant.tts.piper_tts import PiperTTS
        
        tts = PiperTTS(self.config)
        result = tts._generate_wav("Test")
        
        self.assertIsNone(result)
    
    @patch('pathlib.Path.exists')
    def test_speak_with_language_selection(self, mock_exists):
        """Test la synthèse avec sélection de langue"""
        mock_exists.return_value = True
        
        from voice_assistant.tts.piper_tts import PiperTTS
        
        tts = PiperTTS(self.config)
        
        with patch.object(tts, '_generate_wav') as mock_generate:
            with patch.object(tts, '_play_audio_sync') as mock_play:
                mock_generate.return_value = Path('test.wav')
                mock_play.return_value = True
                
                # Test avec français
                tts.speak("Bonjour", language="fr", wait=True)
                call_args = mock_generate.call_args[0]
                self.assertIn("fr_FR", str(mock_generate.call_args))
                
                # Test avec anglais
                tts.speak("Hello", language="en", wait=True)
                self.assertIn("en_US", str(mock_generate.call_args))
    
    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    def test_play_audio_sync_windows(self, mock_exists, mock_run):
        """Test la lecture synchrone sur Windows"""
        mock_exists.return_value = True
        
        from voice_assistant.tts.piper_tts import PiperTTS
        
        with patch('sys.platform', 'win32'):
            tts = PiperTTS(self.config)
            
            test_file = Path('test.wav')
            with patch('pathlib.Path.exists', return_value=True):
                with patch('winsound.PlaySound') as mock_playsound:
                    result = tts._play_audio_sync(test_file)
                    
                    self.assertTrue(result)
                    mock_playsound.assert_called_once()
    
    def test_split_into_sentences(self):
        """Test le découpage en phrases"""
        from voice_assistant.tts.piper_tts import PiperTTS
        
        with patch('pathlib.Path.exists', return_value=True):
            tts = PiperTTS(self.config)
            
            text = "Première phrase. Deuxième phrase! Troisième phrase? Quatrième."
            sentences = tts._split_into_sentences(text)
            
            self.assertEqual(len(sentences), 4)
            self.assertIn("Première phrase", sentences[0])
            self.assertIn("Deuxième phrase", sentences[1])
    
    @patch('shutil.rmtree')
    @patch('pathlib.Path.exists')
    def test_cleanup(self, mock_exists, mock_rmtree):
        """Test le nettoyage des fichiers temporaires"""
        mock_exists.return_value = True
        
        from voice_assistant.tts.piper_tts import PiperTTS
        
        tts = PiperTTS(self.config)
        tts.cleanup()
        
        mock_rmtree.assert_called_once()