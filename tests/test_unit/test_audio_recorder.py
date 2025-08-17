from unittest.mock import MagicMock, patch
import tempfile
import numpy as np  
import unittest
import wave
from pathlib import Path

class TestAudioRecorder(unittest.TestCase):
    """Tests unitaires pour AudioRecorder"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        self.config = {
            'format': 'paInt16',
            'channels': 1,
            'rate': 16000,
            'chunk': 2048,
            'vad_silence_threshold_chunk': 0.002,
            'vad_min_silent_chunks_to_stop': 2.0,
            'vad_min_speech_chunks_before_stop_active': 0.5,
            'vad_max_record_seconds': 15,
            'overall_silence_threshold_rms': 0.005
        }
    
    @patch('pyaudio.PyAudio')
    def test_initialization(self, mock_pyaudio):
        """Test l'initialisation de l'enregistreur"""
        from voice_assistant.audio.record import AudioRecorder
        
        recorder = AudioRecorder(self.config)
        
        self.assertEqual(recorder.rate, 16000)
        self.assertEqual(recorder.chunk, 2048)
        self.assertIsNotNone(recorder.vad_min_silent_chunks_to_stop)
    
    @patch('pyaudio.PyAudio')
    def test_vad_detection(self, mock_pyaudio):
        """Test la détection d'activité vocale (VAD)"""
        from voice_assistant.audio.record import AudioRecorder
        
        # Créer un mock stream
        mock_stream = MagicMock()
        mock_instance = MagicMock()
        mock_instance.open.return_value = mock_stream
        mock_pyaudio.return_value = mock_instance
        
        # Simuler des données audio avec parole puis silence
        speech_data = np.random.randn(2048).astype(np.int16) * 5000  # Fort volume
        silence_data = np.random.randn(2048).astype(np.int16) * 100   # Faible volume
        
        # Créer un cycle infini pour éviter StopIteration
        def mock_read_generator():
            # Cycle: 3 chunks de parole, puis répéter le silence indéfiniment
            speech_cycle = [speech_data.tobytes()] * 3
            for data in speech_cycle:
                yield data
            while True:  # Silence infini après la parole
                yield silence_data.tobytes()
        
        mock_generator = mock_read_generator()
        mock_stream.read.side_effect = lambda *args, **kwargs: next(mock_generator)
        
        recorder = AudioRecorder(self.config)
        audio_data, rms = recorder.record()
        
        self.assertIsNotNone(audio_data)
        self.assertGreater(rms, 0)
        mock_stream.stop_stream.assert_called_once()
        mock_stream.close.assert_called_once()
    
    def test_save_audio_to_file(self):
        """Test la sauvegarde audio dans un fichier"""
        from voice_assistant.audio.record import AudioRecorder
        
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = AudioRecorder(self.config)
            
            # Créer des données audio de test
            test_audio = np.random.randn(16000).astype(np.int16)
            file_path = Path(tmpdir) / "test.wav"
            
            # Sauvegarder
            success = recorder.save_audio_to_file(test_audio, file_path)
            
            self.assertTrue(success)
            self.assertTrue(file_path.exists())
            
            # Vérifier le contenu
            with wave.open(str(file_path), 'rb') as wf:
                self.assertEqual(wf.getnchannels(), 1)
                self.assertEqual(wf.getframerate(), 16000)
