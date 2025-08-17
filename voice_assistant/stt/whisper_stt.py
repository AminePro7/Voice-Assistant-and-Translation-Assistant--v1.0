# -*- coding: utf-8 -*-

import time
import numpy as np 
import wave

import numpy as np

from pathlib import Path

import tempfile

from typing import Dict, Any, Optional, Tuple, List



from faster_whisper import WhisperModel



from voice_assistant.utils.text_utils import simple_spell_correction



class WhisperSTT:

    """Classe pour la transcription vocale avec Whisper"""

    

    def __init__(self, config: Dict[str, Any]):

        """

        Initialise le modèle Whisper

        

        Args:

            config: Configuration STT

        """

        self.model_size = config.get('model_size', 'small')

        

        # Déterminer le type de calcul

        compute_type = config.get('compute_type', 'auto')

        if compute_type == 'auto':

            compute_type = self._determine_compute_type()

        

        # Paramètres de transcription

        self.language = config.get('language', 'fr')

        self.beam_size = config.get('beam_size', 3)

        self.best_of = config.get('best_of', 3)

        self.temperature = config.get('temperature', 0.0)

        self.compression_ratio_threshold = config.get('compression_ratio_threshold', 2.4)

        self.log_prob_threshold = config.get('log_prob_threshold', -1.0)

        self.no_speech_threshold = config.get('no_speech_threshold', 0.3)

        self.condition_on_previous_text = config.get('condition_on_previous_text', True)

        self.vad_filter = config.get('vad_filter', False)

        

        # Initialisation du modèle Whisper

        print(f"Loading Whisper model: {self.model_size} ({self._get_device_type()}, {compute_type})")

        try:

            self.model = WhisperModel(

                self.model_size, 

                device=self._get_device_type(), 

                compute_type=compute_type

            )

            print("Whisper model loaded successfully.")

        except Exception as e:

            print(f"Error initializing WhisperModel: {e}")

            raise

    

    def _determine_compute_type(self) -> str:

        """

        Détermine le type de calcul optimal

        

        Returns:

            Type de calcul ('float16' ou 'float32')

        """

        if self._is_cuda_available():

            return "float16"

        return "float32"

    

    def _get_device_type(self) -> str:

        """

        Détermine le type d'appareil à utiliser

        

        Returns:

            Type d'appareil ('cuda' ou 'cpu')

        """

        if self._is_cuda_available():

            return "cuda"

        return "cpu"

    

    def _is_cuda_available(self) -> bool:

        """

        Vérifie si CUDA est disponible

        

        Returns:

            True si CUDA est disponible, False sinon

        """

        try:

            import torch

            return torch.cuda.is_available()

        except:

            return False

    

    def transcribe_audio_data(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:

        """

        Transcrit les données audio

        

        Args:

            audio_data: Données audio en numpy array

            sample_rate: Taux d'échantillonnage en Hz

            

        Returns:

            Texte transcrit

        """

        if audio_data is None or len(audio_data) == 0:

            return ""

        

        # Sauvegarde temporaire des données audio

        timestamp = int(time.time()*1000)

        temp_dir = Path(tempfile.gettempdir()) / "whisper_stt"

        temp_dir.mkdir(exist_ok=True)

        

        temp_wav_path = temp_dir / f'transcribe_audio_{timestamp}.wav'

        temp_wav_str = str(temp_wav_path)

        

        try:

            with wave.open(temp_wav_str, 'wb') as wf:

                wf.setnchannels(1)  # Mono

                wf.setsampwidth(2)  # 16 bits

                wf.setframerate(sample_rate)

                wf.writeframes(audio_data.tobytes())

            

            segments, info = self.model.transcribe(

                temp_wav_str, 

                language=self.language,

                beam_size=self.beam_size,

                best_of=self.best_of,

                temperature=self.temperature,

                compression_ratio_threshold=self.compression_ratio_threshold,

                log_prob_threshold=self.log_prob_threshold,

                no_speech_threshold=self.no_speech_threshold,

                condition_on_previous_text=self.condition_on_previous_text,

                vad_filter=self.vad_filter,

            )

            

            # Conversion des segments en liste

            detected_segments = list(segments)

            print(f"DEBUG: Whisper raw detected segments: {[s.text for s in detected_segments]}")

            print(f"DEBUG: Whisper detected language: {info.language}, probability: {info.language_probability:.2f}")



            # Post-traitement du texte

            transcribed_text_parts = []

            for segment in detected_segments:

                text = segment.text.strip()

                # Suppression des hésitations

                text = self._remove_hesitations(text)

                if text:

                    transcribed_text_parts.append(text)

            

            full_text = " ".join(transcribed_text_parts).strip()

            

            # Correction orthographique simple

            full_text = simple_spell_correction(full_text)

            

            if full_text:

                print(f"Transcription: \"{full_text}\" (Lang: {info.language}, Prob: {info.language_probability:.2f})")

            else:

                print("Transcription empty after processing.")

                

            return full_text



        except Exception as e:

            print(f"Transcription error: {e}")

            import traceback

            traceback.print_exc()

            return ""

        finally:

            try:

                if temp_wav_path.exists():

                    temp_wav_path.unlink()

            except:

                pass

    

    def transcribe_file(self, file_path: str) -> str:

        """

        Transcrit un fichier audio

        

        Args:

            file_path: Chemin du fichier audio

            

        Returns:

            Texte transcrit

        """

        try:

            segments, info = self.model.transcribe(

                file_path, 

                language=self.language,

                beam_size=self.beam_size,

                best_of=self.best_of,

                temperature=self.temperature,

                compression_ratio_threshold=self.compression_ratio_threshold,

                log_prob_threshold=self.log_prob_threshold,

                no_speech_threshold=self.no_speech_threshold,

                condition_on_previous_text=self.condition_on_previous_text,

                vad_filter=self.vad_filter,

            )

            

            # Conversion des segments en liste

            detected_segments = list(segments)

            

            # Post-traitement du texte

            transcribed_text_parts = []

            for segment in detected_segments:

                text = segment.text.strip()

                # Suppression des hésitations

                text = self._remove_hesitations(text)

                if text:

                    transcribed_text_parts.append(text)

            

            full_text = " ".join(transcribed_text_parts).strip()

            

            # Correction orthographique simple

            full_text = simple_spell_correction(full_text)

            

            return full_text

            

        except Exception as e:

            print(f"File transcription error: {e}")

            import traceback

            traceback.print_exc()

            return ""

    

    def _remove_hesitations(self, text: str) -> str:

        """

        Supprime les hésitations du texte

        

        Args:

            text: Texte à nettoyer

            

        Returns:

            Texte nettoyé

        """

        import re

        text = re.sub(r'\b(euh|heu|hmm|ah|oh)\b', '', text, flags=re.IGNORECASE)

        text = re.sub(r'\s+', ' ', text).strip()

        return text 