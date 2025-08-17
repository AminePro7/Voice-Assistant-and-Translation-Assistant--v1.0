# -*- coding: utf-8 -*-

import time

import tempfile

import shutil

import gc

import re

from pathlib import Path

from typing import Dict, Any, Optional, Tuple, List, Generator



from voice_assistant.utils.config import get_config

from voice_assistant.utils.text_utils import preprocess_user_query, identify_problem_signature

from voice_assistant.utils.normalization import normalize_audio_advanced

from voice_assistant.stt.whisper_stt import WhisperSTT

from voice_assistant.tts.piper_tts import PiperTTS

from voice_assistant.llm.llama_cpp_llm import LlamaCppLLM

from voice_assistant.rag.faiss_rag import FaissRAG

from voice_assistant.audio.record import AudioRecorder

from voice_assistant.audio.playback import AudioPlayer



class VoiceAssistant:

    """Classe principale pour l'assistant vocal RAG"""

    

    def __init__(self, config_path: Optional[str] = None):

        """

        Initialise l'assistant vocal

        

        Args:

            config_path: Chemin vers le fichier de configuration

        """

        print("Initializing RAG voice assistant...")

        

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

        self.llm = self._init_llm()

        self.rag = self._init_rag()

        

        # Messages système

        self.welcome_message = self.config.get('general', 'welcome_message', 

            "Bonjour, je suis votre assistant vocal RAG, prêt à vous aider. Comment puis-je vous assister ?")

        self.no_speech_msg = self.config.get('messages', 'no_speech', 

            "Je n'ai pas bien entendu. Pourriez-vous répéter plus clairement s'il vous plaît ?")

        self.empty_transcription_msg = self.config.get('messages', 'empty_transcription', 

            "Je n'ai pas réussi à comprendre votre demande. Pouvez-vous reformuler ?")

        self.llm_error_msg = self.config.get('messages', 'llm_error', 

            "Désolé, une erreur interne est survenue lors de la génération de la réponse.")

        

        # Réponses communes

        self.common_responses = self.config.get_section('common_responses', {})

        

        # Réponses génériques

        self.responses = self.config.get_section('responses', {})

        

        # Détection de problèmes

        self.problem_detection_config = self.config.get_section('problem_detection', {})

        

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

        temp_dir_config = self.config.get('general', 'temp_dir')

        if temp_dir_config:

            self.temp_dir = Path(temp_dir_config)

            self.temp_dir.mkdir(exist_ok=True)

        else:

            self.temp_dir = Path(tempfile.mkdtemp(prefix='voice_assistant_rag_'))

        

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

        return WhisperSTT(stt_config)

    

    def _init_tts(self) -> PiperTTS:

        """Initialise le système TTS"""

        tts_config = self.config.get_section('tts')

        return PiperTTS(tts_config)

    

    def _init_llm(self) -> LlamaCppLLM:

        """Initialise le modèle LLM"""

        llm_config = self.config.get_section('llm')

        return LlamaCppLLM(llm_config)

    

    def _init_rag(self) -> FaissRAG:

        """Initialise le système RAG"""

        rag_config = self.config.get_section('rag')

        return FaissRAG(rag_config, self.llm)

    

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

    

    def get_random_response(self, category: str) -> str:

        """

        Récupère une réponse aléatoire d'une catégorie

        

        Args:

            category: Catégorie de réponse

            

        Returns:

            Réponse aléatoire

        """

        import random

        responses = self.responses.get(category, [])

        if responses:

            return random.choice(responses)

        return ""

    

    def speak_llm_stream(self, token_generator: Generator[str, None, None]) -> str:

        """

        Synthétise et joue un stream de tokens LLM

        

        Args:

            token_generator: Générateur de tokens LLM

            

        Returns:

            Réponse complète

        """

        full_response_for_memory = []

        sentence_buffer = ""

        sentence_terminator_pattern = re.compile(r'(?<=[.!?\n])\s*')

        stream_had_output = False



        for token_str in token_generator:

            if not isinstance(token_str, str):

                continue 

            

            full_response_for_memory.append(token_str)

            sentence_buffer += token_str

            stream_had_output = True

            

            parts = sentence_terminator_pattern.split(sentence_buffer)

            

            if len(parts) > 1:

                for i in range(len(parts) - 1):

                    sentence_to_speak = parts[i].strip()

                    if sentence_to_speak:

                        self.tts.speak(sentence_to_speak, wait=True)

                sentence_buffer = parts[-1]

        

        if sentence_buffer.strip():

            final_text_to_speak = sentence_buffer.strip()

            if final_text_to_speak:

                self.tts.speak(final_text_to_speak, wait=True)

        

        if not stream_had_output:

            print("LLM stream was empty.")

            return self.empty_transcription_msg



        return "".join(full_response_for_memory).strip()

    

    def run(self) -> None:

        """Exécute l'assistant vocal"""

        try:

            print("\n" + "="*40 + "\n RAG Voice Assistant Ready \n Ctrl+C to stop \n" + "="*40 + "\n")

            self.tts.speak(self.welcome_message, wait=True)



            while True:

                response_text = ""

                is_common = False

                is_cached_rag = False

                identified_sig = None

                

                try:

                    # Enregistrement audio

                    audio_data, audio_level_rms = self.audio_recorder.record()

                    if audio_data is None:

                        self.tts.speak("Problème lors de l'enregistrement audio. Réessayez.", wait=True)

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

                    transcribed_text = self.stt.transcribe_audio_data(normalized_audio)

                    if not transcribed_text:

                        self.tts.speak(self.empty_transcription_msg, wait=True)

                        continue

                    

                    print(f"User said: \"{transcribed_text}\"")

                    text_lower = transcribed_text.lower()



                    # Vérification des réponses communes

                    for k_common, v_common in self.common_responses.items():

                        if (k_common == text_lower) or re.search(r'' + re.escape(k_common) + r'', text_lower) or (len(k_common.split()) > 1 and k_common in text_lower):

                            response_text = v_common

                            is_common = True

                            print(f"Common response for: '{k_common}'")

                            self.tts.speak(response_text, wait=True)

                            break

                    

                    if is_common:

                        self.rag.save_to_memory(transcribed_text, response_text)

                        print("\nReady for next command...")

                        continue



                    # Identification de la signature du problème

                    problem_patterns = self.problem_detection_config.get('generic_problem_patterns', [])

                    device_keywords = self._format_device_keywords()

                    fuzzy_match_threshold = self.problem_detection_config.get('fuzzy_match_threshold', 80)

                    

                    identified_sig = identify_problem_signature(

                        transcribed_text, problem_patterns, device_keywords, fuzzy_match_threshold

                    )

                    

                    # Vérification du cache RAG

                    if identified_sig:

                        cached_response = self.rag.get_cached_rag_solution(identified_sig)

                        if cached_response:

                            response_text = cached_response

                            is_cached_rag = True

                            print(f"Using CACHED RAG for: '{identified_sig}'")

                            self.tts.speak(response_text, wait=True)

                            self.rag.save_to_memory(transcribed_text, response_text)

                            print("\nReady for next command...")

                            continue



                    # Détermination du mode RAG

                    use_rag_for_llm_flag = False

                    if identified_sig and "unknown_device" not in identified_sig:

                        use_rag_for_llm_flag = True

                        print(f"Clear problem signature '{identified_sig}' found. Considering RAG.")

                    else:

                        print(f"No clear problem signature identified or device unclear. Defaulting to Non-RAG.")

                    

                    # Son de réflexion

                    self.audio_player.play_thinking_sound(block=False)

                    

                    # Message de réflexion

                    filler = self.get_random_response('thinking')

                    print(f"Speaking filler: \"{filler}\"")

                    self.tts.speak(filler, wait=True)



                    # Prétraitement de la question

                    processed_text = preprocess_user_query(transcribed_text)

                    

                    # Génération de la réponse

                    print(f"Querying LLM (initial suggestion: {'RAG' if use_rag_for_llm_flag else 'Non-RAG'}) "

                          f"for: \"{processed_text}\" (Streaming...)")

                    

                    llm_token_generator = self.rag.get_llm_stream_generator(

                        processed_text, use_rag_initial=use_rag_for_llm_flag

                    )

                    

                    # Son de résultat

                    if not is_common and not is_cached_rag:

                        self.audio_player.play_result_sound(block=True)



                    # Synthèse de la réponse

                    response_text = self.speak_llm_stream(llm_token_generator)



                    # Traitement de la réponse

                    if response_text:

                        if response_text == self.llm_error_msg:

                            print("LLM processing resulted in an error message.")

                        else:

                            print(f"Assistant full streamed response: \"{response_text[:200].replace(chr(10),' ')}...\"")

                            self.rag.save_to_memory(transcribed_text, response_text)



                            # Mise en cache de la solution RAG

                            rag_info_not_found_msg = self.config.get('messages', 'rag_info_not_found', 

                                "Je n'ai pas trouvé d'information spécifique à ce sujet dans ma base de connaissances.")

                            

                            if (identified_sig and "unknown_device" not in identified_sig and 

                                use_rag_for_llm_flag and response_text != self.llm_error_msg and 

                                rag_info_not_found_msg not in response_text):

                                self.rag.cache_rag_solution(identified_sig, response_text)

                            elif identified_sig:

                                print(f"Not caching for '{identified_sig}' (RAG not used, unknown device, "

                                      f"LLM error, or info not found by LLM).")

                    else:

                        print("LLM stream resulted in empty or no valid response text.")

                        self.tts.speak("Je n'ai pas pu générer de réponse.", wait=True)

                    

                    print("\nReady for next command...")



                except Exception as e_loop:

                    print(f"\n--- Error in main loop iteration: {e_loop} ---")

                    import traceback

                    traceback.print_exc()

                    self.tts.speak("Oups, une erreur inattendue est survenue. Réessayons.", wait=True)

                    time.sleep(1)

                    continue

        

        except KeyboardInterrupt:

            print("\nCtrl+C detected. Stopping assistant...")

            try:

                self.tts.speak("Au revoir et à bientôt !", wait=True)

            except:

                pass

        finally:

            self.cleanup()

    

    def _format_device_keywords(self) -> Dict[str, List[str]]:

        """

        Formate les mots-clés de périphériques

        

        Returns:

            Dictionnaire des mots-clés de périphériques

        """

        device_keywords = {}

        raw_device_keywords = self.problem_detection_config.get('device_keywords', {})

        

        for device, keywords in raw_device_keywords.items():

            device_keywords[device] = keywords

        

        return device_keywords

    

    def cleanup(self) -> None:

        """Nettoie les ressources"""

        print("Cleaning up resources...")

        try:

            # Nettoyage TTS

            if hasattr(self, 'tts') and hasattr(self.tts, 'cleanup'):

                self.tts.cleanup()

            

            # Suppression du répertoire temporaire

            if hasattr(self, 'temp_dir') and self.temp_dir and self.temp_dir.exists():

                shutil.rmtree(self.temp_dir)

                print(f"Removed temporary directory: {self.temp_dir}")

        except Exception as e:

            print(f"Error during cleanup: {e}") 