# conftest.py
import pytest
import tempfile
from pathlib import Path
import yaml

@pytest.fixture(scope="session")
def test_config():
    '''Configuration de test partagée'''
    config = {
        'general': {
            'device_type': 'cpu',
            'temp_dir': tempfile.mkdtemp(),
            'output_dir': 'test_output'
        },
        'audio': {
            'format': 'paInt16',
            'channels': 1,
            'rate': 16000,
            'chunk': 2048,
            'vad_silence_threshold_chunk': 0.002,
            'vad_min_silent_chunks_to_stop': 2.0
        },
        'stt': {
            'model_size': 'tiny',  # Plus petit modèle pour les tests
            'language': 'fr'
        },
        'tts': {
            'piper_exe': 'piper/piper.exe',
            'model': 'models/test_model.onnx'
        },
        'llm': {
            'model_path': 'llm_models/test_model.gguf',
            'n_ctx': 512,
            'temperature': 0.1
        },
        'rag': {
            'embedding_model': 'paraphrase-multilingual-MiniLM-L12-v2',
            'vectorstore_dir': 'test_vectorstore',
            'doc_path': 'test_doc.md'
        }
    }
    return config

@pytest.fixture
def mock_audio_data():
    '''Génère des données audio de test'''
    duration = 1.0  # 1 seconde
    sample_rate = 16000
    samples = int(duration * sample_rate)
    # Génère un signal sinusoïdal
    frequency = 440  # La 440 Hz
    t = np.linspace(0, duration, samples)
    audio_data = np.sin(2 * np.pi * frequency * t) * 0.5
    return (audio_data * 32767).astype(np.int16)

@pytest.fixture
def performance_monitor():
    '''Moniteur de performance pour les tests'''
    from voice_assistant.utils.performance import PerformanceMonitor
    return PerformanceMonitor()