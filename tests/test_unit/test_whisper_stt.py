from unittest.mock import MagicMock, patch
import tempfile
import numpy as np  
import  unittest

class TestWhisperSTT(unittest.TestCase):
    """Tests unitaires pour WhisperSTT"""
    
    def setUp(self):
        self.config = {
            'model_size': 'tiny',
            'language': 'fr',
            'beam_size': 3,
            'temperature': 0.0
        }
    
    @patch('faster_whisper.WhisperModel')
    def test_initialization(self, mock_whisper):
        """Test l'initialisation du modèle Whisper"""
        from voice_assistant.stt.whisper_stt import WhisperSTT
        
        stt = WhisperSTT(self.config)
        
        mock_whisper.assert_called_once()
        self.assertEqual(stt.model_size, 'tiny')
        self.assertEqual(stt.language, 'fr')
    
    @patch('faster_whisper.WhisperModel')
    def test_transcribe_audio_data(self, mock_whisper):
        """Test la transcription de données audio"""
        from voice_assistant.stt.whisper_stt import WhisperSTT
        
        # Mock du modèle et des segments
        mock_model = MagicMock()
        mock_segment = MagicMock()
        mock_segment.text = "Bonjour, ceci est un test"
        mock_info = MagicMock()
        mock_info.language = "fr"
        mock_info.language_probability = 0.99
        
        mock_model.transcribe.return_value = (iter([mock_segment]), mock_info)
        mock_whisper.return_value = mock_model
        
        stt = WhisperSTT(self.config)
        
        # Créer des données audio de test
        test_audio = np.random.randn(16000).astype(np.int16)
        
        with patch('wave.open'), patch('pathlib.Path.mkdir'):
            result = stt.transcribe_audio_data(test_audio)
        
        self.assertEqual(result, "Bonjour, ceci est un test")
        mock_model.transcribe.assert_called_once()
    
    def test_remove_hesitations(self):
        """Test la suppression des hésitations"""
        from voice_assistant.stt.whisper_stt import WhisperSTT
        
        with patch('faster_whisper.WhisperModel'):
            stt = WhisperSTT(self.config)
            
            text_with_hesitations = "Euh bonjour, hmm comment allez-vous ah bien"
            cleaned = stt._remove_hesitations(text_with_hesitations)
            
            self.assertNotIn("euh", cleaned.lower())
            self.assertNotIn("hmm", cleaned.lower())
            self.assertIn("bonjour", cleaned.lower())

# test_unit/test_piper_tts.py
class TestPiperTTS(unittest.TestCase):
    """Tests unitaires pour PiperTTS"""
    
    def setUp(self):
        self.config = {
            'piper_exe': 'piper/piper.exe',
            'model': 'models/test.onnx',
            'config': 'models/test.onnx.json',
            'length_scale': 1.0
        }
    
    @patch('pathlib.Path.exists')
    def test_initialization(self, mock_exists):
        """Test l'initialisation de Piper TTS"""
        mock_exists.return_value = True
        
        from voice_assistant.tts.piper_tts import PiperTTS
        
        tts = PiperTTS(self.config)
        
        self.assertEqual(tts.length_scale, 1.0)
        self.assertIsNotNone(tts.temp_dir)
    
    @patch('subprocess.Popen')
    @patch('pathlib.Path.exists')
    def test_generate_wav(self, mock_exists, mock_popen):
        """Test la génération de fichier WAV"""
        mock_exists.return_value = True
        
        # Mock du processus Piper
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b'', b'')
        mock_popen.return_value = mock_process
        
        from voice_assistant.tts.piper_tts import PiperTTS
        
        tts = PiperTTS(self.config)
        
        with patch('pathlib.Path.stat') as mock_stat:
            mock_stat.return_value.st_size = 1000
            result = tts._generate_wav("Test de synthèse")
        
        self.assertIsNotNone(result)
        mock_popen.assert_called_once()
    
    def test_clean_text(self):
        """Test le nettoyage du texte"""
        from voice_assistant.tts.piper_tts import PiperTTS
        
        with patch('pathlib.Path.exists', return_value=True):
            tts = PiperTTS(self.config)
            
            dirty_text = "**Bonjour** #test `code`"
            cleaned = tts._clean_text(dirty_text)
            
            self.assertEqual(cleaned, "Bonjour test code")
