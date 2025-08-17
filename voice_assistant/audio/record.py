# -*- coding: utf-8 -*-

import time
import numpy as np 
import wave

import numpy as np

import pyaudio

from pathlib import Path

from typing import Tuple, Optional, Dict, Any



class AudioRecorder:

    """Classe pour l'enregistrement audio avec détection d'activité vocale (VAD)"""

    

    def __init__(self, config: Dict[str, Any]):

        """

        Initialise l'enregistreur audio

        

        Args:

            config: Configuration audio

        """

        self.audio_format = getattr(pyaudio, config.get('format', 'paInt16'))

        self.channels = config.get('channels', 1)

        self.rate = config.get('rate', 16000)

        self.chunk = config.get('chunk', 2048)

        self.volume_norm = config.get('volume_norm', 0.7)

        

        # Paramètres VAD

        self.vad_max_record_seconds = config.get('vad_max_record_seconds', 15)

        self.vad_silence_threshold_chunk = config.get('vad_silence_threshold_chunk', 0.002)

        

        # Conversion des secondes en nombre de chunks

        seconds_to_chunks = lambda s: int(s * (self.rate / self.chunk))

        self.vad_min_silent_chunks_to_stop = seconds_to_chunks(

            config.get('vad_min_silent_chunks_to_stop', 2.0)

        )

        self.vad_min_speech_chunks_before_stop_active = seconds_to_chunks(

            config.get('vad_min_speech_chunks_before_stop_active', 0.5)

        )

        self.overall_silence_threshold_rms = config.get('overall_silence_threshold_rms', 0.005)

        

        # Initialisation de PyAudio pour obtenir la taille d'échantillon

        _pa = pyaudio.PyAudio()

        self.sample_width = _pa.get_sample_size(self.audio_format)

        _pa.terminate()

        

        print(f"Audio recorder initialized: rate={self.rate}, chunk={self.chunk}, "

              f"VAD threshold={self.vad_silence_threshold_chunk}")

    

    def record(self) -> Tuple[Optional[np.ndarray], float]:

        """

        Enregistre l'audio avec détection d'activité vocale

        

        Returns:

            Tuple contenant:

                - Les données audio normalisées (ou None en cas d'erreur)

                - Le niveau RMS global

        """

        pa = pyaudio.PyAudio()

        stream = None

        frames = []

        speech_started = False

        silent_chunks_count = 0

        speech_chunks_count = 0

        total_chunks_recorded = 0

        max_chunks_to_record = int(self.vad_max_record_seconds * self.rate / self.chunk)



        try:

            stream = pa.open(format=self.audio_format, channels=self.channels, rate=self.rate,

                            input=True, frames_per_buffer=self.chunk)

            print("Recording (VAD enabled)...")



            for i in range(max_chunks_to_record):

                try:

                    data_chunk = stream.read(self.chunk, exception_on_overflow=False)

                    frames.append(data_chunk)

                    total_chunks_recorded += 1



                    audio_chunk_np = np.frombuffer(data_chunk, dtype=np.int16)

                    rms_chunk = np.sqrt(np.mean((audio_chunk_np.astype(np.float32) / 32768.0)**2))



                    # Affiche le RMS toutes les 0.5 secondes

                    if i % (self.rate // self.chunk // 2) == 0:

                        print(f"DEBUG: Chunk {i+1} ({(i+1)*self.chunk/self.rate:.2f}s) "

                              f"RMS: {rms_chunk:.4f} (Threshold: {self.vad_silence_threshold_chunk:.4f}), "

                              f"Speech started: {speech_started}")



                    if rms_chunk > self.vad_silence_threshold_chunk:

                        if not speech_started:

                            print(f"VAD: Speech started (RMS chunk: {rms_chunk:.4f} > "

                                  f"{self.vad_silence_threshold_chunk:.4f}).")

                        speech_started = True

                        speech_chunks_count += 1

                        silent_chunks_count = 0

                    elif speech_started:

                        silent_chunks_count += 1

                    

                    if (speech_started and 

                        speech_chunks_count >= self.vad_min_speech_chunks_before_stop_active and 

                        silent_chunks_count >= self.vad_min_silent_chunks_to_stop):

                        print(f"VAD: Detected end of speech after "

                              f"{total_chunks_recorded * self.chunk / self.rate:.2f}s.")

                        break

                

                except IOError as e:

                    if e.errno == pyaudio.paInputOverflowed:

                        print("Warning: Audio input overflowed.")

                    else:

                        print(f"Warning: PyAudio IOError during recording: {e}")

                    time.sleep(0.01)



            print(f"Recording finished after {total_chunks_recorded * self.chunk / self.rate:.2f}s.")

            

            if not speech_started:

                print("DEBUG: PyAudio VAD did NOT detect speech. Recording went for max duration.")



            if not frames:

                return None, 0.0



            audio_data_np = np.frombuffer(b''.join(frames), dtype=np.int16)

            

            # La normalisation sera appliquée par l'appelant

            overall_rms = np.sqrt(np.mean((audio_data_np.astype(np.float32) / 32768.0)**2))

            print(f"Overall RMS: {overall_rms:.4f}")

            

            return audio_data_np, overall_rms



        except Exception as e:

            print(f"Recording error: {e}")

            import traceback

            traceback.print_exc()

            return None, 0.0

        finally:

            if stream:

                try:

                    if stream.is_active():

                        stream.stop_stream()

                    stream.close()

                except:

                    pass

            if pa:

                try:

                    pa.terminate()

                except:

                    pass

    

    def save_audio_to_file(self, audio_data: np.ndarray, file_path: Path) -> bool:

        """

        Sauvegarde les données audio dans un fichier WAV

        

        Args:

            audio_data: Données audio à sauvegarder

            file_path: Chemin du fichier WAV

            

        Returns:

            True si la sauvegarde a réussi, False sinon

        """

        try:

            with wave.open(str(file_path), 'wb') as wf:

                wf.setnchannels(self.channels)

                wf.setsampwidth(self.sample_width)

                wf.setframerate(self.rate)

                wf.writeframes(audio_data.tobytes())

            return True

        except Exception as e:

            print(f"Error saving audio to {file_path}: {e}")

            return False 