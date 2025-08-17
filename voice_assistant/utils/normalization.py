# -*- coding: utf-8 -*-
import numpy as np

from typing import Optional



def normalize_audio_simple(data: np.ndarray) -> np.ndarray:

    """

    Normalisation audio simple

    

    Args:

        data: Données audio en numpy array

        

    Returns:

        Données audio normalisées

    """

    if data is None or len(data) == 0:

        return data

        

    # Conversion en float

    audio_float = data.astype(np.float32) / 32768.0

    

    # Normalisation par pic

    if np.max(np.abs(audio_float)) > 0:

        audio_float = audio_float / np.max(np.abs(audio_float)) * 0.9

    

    # Retour en int16

    return (audio_float * 32768.0).astype(np.int16)



def normalize_audio_advanced(data: np.ndarray) -> np.ndarray:

    """

    Normalisation audio avancée avec suppression DC offset et limitation douce

    

    Args:

        data: Données audio en numpy array

        

    Returns:

        Données audio normalisées

    """

    if data is None or len(data) == 0:

        return data

        

    try:

        # Conversion en float

        audio_float = data.astype(np.float32) / 32768.0

        

        # Suppression du DC offset

        audio_float = audio_float - np.mean(audio_float)

        

        # Normalisation par RMS plutôt que par pic

        rms = np.sqrt(np.mean(audio_float**2))

        if rms > 1e-6:  # Éviter la division par zéro

            target_rms = 0.15  # RMS cible (peut être ajusté)

            audio_float = audio_float * (target_rms / rms)

        

        # Limitation douce (soft clipping) pour éviter les distortions extrêmes

        audio_float = np.tanh(audio_float * 0.9) * 0.9

        

        # Retour en int16

        return (audio_float * 32768.0).astype(np.int16)

        

    except Exception as e:

        print(f"Erreur normalisation audio avancée: {e}")

        return data



def apply_bandpass_filter(data: np.ndarray, sample_rate: int, 

                         low_freq: float = 80.0, high_freq: float = 7500.0) -> Optional[np.ndarray]:

    """

    Applique un filtre passe-bande aux données audio

    

    Args:

        data: Données audio en numpy array

        sample_rate: Taux d'échantillonnage en Hz

        low_freq: Fréquence de coupure basse en Hz

        high_freq: Fréquence de coupure haute en Hz

        

    Returns:

        Données audio filtrées ou None si scipy n'est pas disponible

    """

    try:

        from scipy import signal

        

        # Conversion en float

        audio_float = data.astype(np.float32) / 32768.0

        

        # Conception du filtre

        nyquist = 0.5 * sample_rate

        low = low_freq / nyquist

        high = high_freq / nyquist

        

        # Filtre Butterworth ordre 4

        b, a = signal.butter(4, [low, high], btype='band')

        

        # Application du filtre

        filtered_audio = signal.lfilter(b, a, audio_float)

        

        # Retour en int16

        return (filtered_audio * 32768.0).astype(np.int16)

        

    except ImportError:

        print("Warning: scipy not installed. Bandpass filtering unavailable.")

        return None

    except Exception as e:

        print(f"Error applying bandpass filter: {e}")

        return None 