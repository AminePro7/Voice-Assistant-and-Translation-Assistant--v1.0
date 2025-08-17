# -*- coding: utf-8 -*-
import re
from typing import Dict, List, Optional, Tuple

def simple_spell_correction(text: str) -> str:
    """
    Corrections orthographiques simples pour les erreurs courantes de transcription
    
    Args:
        text: Texte à corriger
        
    Returns:
        Texte corrigé
    """
    corrections = {
        "imprimente": "imprimante",
        "imprimonte": "imprimante",
        "modeme": "modem",
        "routeure": "routeur",
        "télévisons": "télévision",
        "conexion": "connexion",
        "marche pas": "ne marche pas",
        "fonctionne pas": "ne fonctionne pas",
        "y'a pas": "il n'y a pas",
    }
    
    text_lower = text.lower()
    for error, correction in corrections.items():
        text_lower = re.sub(r'\b' + re.escape(error) + r'\b', correction, text_lower)
    
    if text_lower and text:
        if text[0].isupper():
            return text_lower.capitalize()
    return text_lower


def preprocess_user_query(text: str) -> str:
    """
    Pré-traitement de la question utilisateur avant de l'envoyer à l'LLM
    
    Args:
        text: Texte de la question utilisateur
        
    Returns:
        Texte prétraité
    """
    # Expansion des abréviations courantes
    expansions = {
        "pb": "problème",
        "pc": "ordinateur",
        "tel": "téléphone",
        "tv": "télévision",
        "net": "internet",
        "wifi": "wi-fi"
    }
    
    text_processed = text.lower()
    for abbrev, full in expansions.items():
        text_processed = re.sub(r'\b' + abbrev + r'\b', full, text_processed)
    
    # Ajout de contexte si question très courte
    if len(text_processed.split()) < 3:
        text_processed = f"J'ai une question à propos de: {text_processed}"
    
    return text_processed


def identify_problem_signature(text: str, 
                              problem_patterns: List[str], 
                              device_keywords: Dict[str, List[str]], 
                              fuzzy_match_threshold: int = 80) -> Optional[str]:
    """
    Identifie la signature d'un problème dans le texte
    
    Args:
        text: Texte à analyser
        problem_patterns: Liste des patterns regex pour détecter un problème
        device_keywords: Dictionnaire des mots-clés de périphériques
        fuzzy_match_threshold: Seuil de correspondance floue
        
    Returns:
        Signature du problème ou None si aucun problème détecté
    """
    try:
        from thefuzz import fuzz
    except ImportError:
        print("Warning: thefuzz not installed. Fuzzy matching disabled.")
        return None
        
    text_lower = text.lower()
    found_problem_indicator = False
    canonical_device_name = None
    best_match_ratio = 0
    matched_keyword_for_log = ""

    # Recherche d'indicateurs de problèmes
    for pattern in problem_patterns:
        if re.search(pattern, text_lower):
            found_problem_indicator = True
            break
    
    if not found_problem_indicator:
        return None

    words_in_text = re.findall(r'\b\w+\b', text_lower)
    
    # Recherche de périphériques mentionnés
    for canonical_name, keywords in device_keywords.items():
        for keyword in keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                canonical_device_name = canonical_name
                matched_keyword_for_log = keyword
                best_match_ratio = 100
                break
        
        if canonical_device_name:
            break

    # Si pas de correspondance exacte, essayer la correspondance floue
    if not canonical_device_name:
        for canonical_name, keywords in device_keywords.items():
            for keyword in keywords:
                for word_user in words_in_text:
                    ratio = fuzz.ratio(word_user, keyword)
                    if ratio > fuzzy_match_threshold and ratio > best_match_ratio:
                        best_match_ratio = ratio
                        canonical_device_name = canonical_name
                        matched_keyword_for_log = f"{word_user} (fuzzy for {keyword})"
    
    if found_problem_indicator and canonical_device_name:
        signature = f"{canonical_device_name}_generic_problem"
        print(f"Identified problem signature: '{signature}' (Indicator + Device: '{canonical_device_name}' from '{matched_keyword_for_log}', Match Ratio: {best_match_ratio if best_match_ratio < 100 else 'Exact'})")
        return signature
    elif found_problem_indicator:
        print(f"Found problem indicator, but no clear device identified.")
        return "unknown_device_generic_problem"
    
    return None


def format_history_as_string_for_prompt(message_list: List) -> str:
    """
    Formate l'historique de conversation pour le prompt
    
    Args:
        message_list: Liste des messages (HumanMessage, AIMessage)
        
    Returns:
        Historique formaté sous forme de chaîne
    """
    if not message_list:
        return "Pas d'historique de conversation."
    
    formatted_history = []
    for msg in message_list:
        try:
            from langchain.schema import AIMessage, HumanMessage
            role = "Utilisateur" if isinstance(msg, HumanMessage) else "Assistant"
            formatted_history.append(f"{role}: {msg.content}")
        except:
            # Fallback si langchain n'est pas disponible ou si le format a changé
            if hasattr(msg, 'role') and hasattr(msg, 'content'):
                role = "Utilisateur" if msg.role == "human" else "Assistant"
                formatted_history.append(f"{role}: {msg.content}")
            else:
                formatted_history.append(str(msg))
                
    return "\n".join(formatted_history) 