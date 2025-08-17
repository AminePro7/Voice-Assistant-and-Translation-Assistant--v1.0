# Assistant Vocal Modulaire - Documentation Technique

## Table des matières

- [Présentation](#présentation)
- [Architecture technique](#architecture-technique)
  - [Vue d'ensemble](#vue-densemble)
  - [Flux de données](#flux-de-données)
  - [Diagramme des composants](#diagramme-des-composants)
- [Composants principaux](#composants-principaux)
  - [Système audio](#système-audio)
  - [Reconnaissance vocale (STT)](#reconnaissance-vocale-stt)
  - [Synthèse vocale (TTS)](#synthèse-vocale-tts)
  - [Modèle de langage (LLM)](#modèle-de-langage-llm)
  - [Système RAG](#système-rag)
  - [Système de traduction](#système-de-traduction)
- [Modes de fonctionnement](#modes-de-fonctionnement)
  - [Mode RAG](#mode-rag)
  - [Mode Traducteur](#mode-traducteur)
- [Structure du code](#structure-du-code)
  - [Organisation des modules](#organisation-des-modules)
  - [Points d'entrée](#points-dentrée)
  - [Gestion de la configuration](#gestion-de-la-configuration)
- [Modèles et technologies utilisés](#modèles-et-technologies-utilisés)
  - [Modèles de reconnaissance vocale](#modèles-de-reconnaissance-vocale)
  - [Modèles de synthèse vocale](#modèles-de-synthèse-vocale)
  - [Modèles de langage](#modèles-de-langage)
  - [Modèles de traduction](#modèles-de-traduction)
  - [Embeddings et vectorisation](#embeddings-et-vectorisation)
- [Optimisations techniques](#optimisations-techniques)
  - [Gestion des ressources](#gestion-des-ressources)
  - [Détection d'activité vocale (VAD)](#détection-dactivité-vocale-vad)
  - [Normalisation audio](#normalisation-audio)
  - [Mise en cache RAG](#mise-en-cache-rag)
- [Installation et déploiement](#installation-et-déploiement)
  - [Prérequis système](#prérequis-système)
  - [Installation des dépendances](#installation-des-dépendances)
  - [Configuration avancée](#configuration-avancée)
- [Développement et extension](#développement-et-extension)
  - [Ajout de nouveaux modèles](#ajout-de-nouveaux-modèles)
  - [Création de nouveaux modes](#création-de-nouveaux-modes)
  - [Personnalisation du système RAG](#personnalisation-du-système-rag)

## Présentation

L'Assistant Vocal Modulaire est une application Python qui implémente un assistant vocal entièrement local avec plusieurs modes de fonctionnement. Le projet est conçu avec une architecture modulaire permettant une grande flexibilité et extensibilité.

Caractéristiques principales :
- Fonctionnement 100% local (pas d'API cloud requise)
- Architecture modulaire avec séparation claire des responsabilités
- Multiple modes de fonctionnement (RAG, traduction)
- Optimisations pour fonctionner sur des ressources limitées

## Architecture technique

### Vue d'ensemble

L'architecture du projet suit un modèle modulaire avec des composants interchangeables et une séparation claire des responsabilités. Chaque composant est implémenté comme un module Python indépendant avec des interfaces bien définies.

```
┌─────────────────────────────────────────────────────────────────┐
│                     Assistant Launcher                          │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Voice Assistant Core                         │
├─────────────┬─────────────┬──────────────┬─────────────┬────────┤
│  Assistant  │ Translator  │ Audio System │ Config Mgmt │ Utils  │
└─────┬───────┴──────┬──────┴──────┬───────┴─────┬───────┴────────┘
      │              │             │             │
┌─────▼──────┐ ┌─────▼──────┐ ┌────▼────┐ ┌─────▼─────┐
│ STT Module │ │ TTS Module │ │ Recorder│ │ Playback  │
└─────┬──────┘ └─────┬──────┘ └────┬────┘ └─────┬─────┘
      │              │             │             │
┌─────▼──────┐ ┌─────▼──────┐ ┌────▼────┐ ┌─────▼─────┐
│ Whisper    │ │ Piper      │ │   VAD   │ │ PyAudio   │
└────────────┘ └────────────┘ └─────────┘ └───────────┘
      │              │
┌─────▼──────┐ ┌─────▼──────┐
│ LLM Module │ │ RAG Module │
└─────┬──────┘ └─────┬──────┘
      │              │
┌─────▼──────┐ ┌─────▼──────┐
│ Gemma LLM  │ │ FAISS      │
└────────────┘ └────────────┘
```

### Flux de données

Le flux de données dans l'application suit un pipeline de traitement bien défini :

1. **Entrée audio** : Capture du son via le microphone avec détection d'activité vocale (VAD)
2. **Prétraitement audio** : Normalisation et optimisation du signal audio
3. **Reconnaissance vocale** : Conversion de l'audio en texte via Whisper
4. **Traitement du texte** :
   - Mode RAG : Recherche d'informations pertinentes et génération de réponse via LLM
   - Mode Traduction : Traduction du texte via Argos Translate
5. **Synthèse vocale** : Conversion du texte en parole via Piper TTS
6. **Sortie audio** : Lecture de la réponse vocale

### Diagramme des composants

```
┌──────────────────────────────────────────────────────────────────────────┐
│                             Assistant Vocal                              │
│                                                                          │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐    │
│  │            │    │            │    │            │    │            │    │
│  │  Recorder  │───▶│  Whisper   │───▶│  LLM/RAG   │───▶│   Piper    │    │
│  │  (Audio)   │    │   (STT)    │    │            │    │   (TTS)    │    │
│  │            │    │            │    │            │    │            │    │
│  └────────────┘    └────────────┘    └────────────┘    └────────────┘    │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                      Configuration System                          │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

## Composants principaux

### Système audio

Le système audio est responsable de la capture et de la lecture du son. Il est composé de deux modules principaux :

1. **AudioRecorder** (`voice_assistant/audio/record.py`) :
   - Capture du son via PyAudio
   - Implémentation d'un système de détection d'activité vocale (VAD) personnalisé
   - Paramètres configurables pour le seuil de silence, la durée maximale d'enregistrement, etc.

2. **AudioPlayer** (`voice_assistant/audio/playback.py`) :
   - Lecture des fichiers audio via PyAudio
   - Gestion des sons système (sons de réflexion, de résultat, etc.)
   - Support du mode bloquant/non-bloquant pour la lecture

### Reconnaissance vocale (STT)

Le module de reconnaissance vocale est responsable de la conversion de l'audio en texte :

**WhisperSTT** (`voice_assistant/stt/whisper_stt.py`) :
- Utilise le modèle Whisper d'OpenAI en local
- Support multilingue (français et anglais)
- Options configurables pour la taille du modèle, le beam search, etc.
- Optimisations pour les performances sur CPU/GPU

### Synthèse vocale (TTS)

Le module de synthèse vocale est responsable de la conversion du texte en parole :

**PiperTTS** (`voice_assistant/tts/piper_tts.py`) :
- Utilise le synthétiseur vocal Piper en local
- Support multilingue avec différents modèles de voix
- Options configurables pour la vitesse, le pitch, etc.
- Gestion des erreurs et fallbacks

### Modèle de langage (LLM)

Le module LLM est responsable du traitement du langage naturel :

**LlamaCppLLM** (`voice_assistant/llm/llama_cpp_llm.py`) :
- Interface avec le modèle Gemma via llama.cpp
- Support du streaming de tokens pour une réponse plus rapide
- Paramètres configurables pour la température, le top-p, etc.
- Optimisations pour les performances sur CPU/GPU

### Système RAG

Le module RAG (Retrieval-Augmented Generation) est responsable de l'enrichissement des réponses du LLM avec des informations issues d'une base de connaissances :

**FaissRAG** (`voice_assistant/rag/faiss_rag.py`) :
- Utilise FAISS pour l'indexation et la recherche vectorielle
- Génération d'embeddings via Sentence Transformers
- Chunking et overlap configurables pour le découpage des documents
- Système de mise en cache des réponses pour les questions fréquentes
- Détection de signatures de problèmes pour une meilleure pertinence

### Système de traduction

Le module de traduction est responsable de la conversion du texte d'une langue à une autre :

**TranslatorAssistant** (`voice_assistant/translator.py`) :
- Utilise Argos Translate pour la traduction locale
- Support bidirectionnel (anglais ↔ français)
- Gestion des erreurs et fallbacks

## Modes de fonctionnement

### Mode RAG

Le mode RAG (Retrieval-Augmented Generation) permet à l'assistant de répondre à des questions en s'appuyant sur une base de connaissances :

1. L'utilisateur pose une question oralement
2. L'assistant enregistre la voix avec détection d'activité vocale
3. L'audio est transcrit en texte via Whisper
4. Le système RAG :
   - Analyse la question pour détecter des signatures de problèmes
   - Recherche des informations pertinentes dans la base de connaissances
   - Génère une réponse via le LLM en s'appuyant sur les informations trouvées
5. La réponse est synthétisée vocalement via Piper TTS

**Optimisations spécifiques au mode RAG** :
- Détection de signatures de problèmes pour une meilleure pertinence
- Mise en cache des réponses pour les questions fréquentes
- Streaming de la réponse pour une expérience utilisateur plus fluide

### Mode Traducteur

Le mode Traducteur permet à l'assistant de traduire des phrases d'une langue à une autre :

1. L'utilisateur parle dans la langue source (anglais ou français)
2. L'assistant enregistre la voix avec détection d'activité vocale
3. L'audio est transcrit en texte via Whisper (configuré pour la langue source)
4. Le texte est traduit via Argos Translate
5. La traduction est synthétisée vocalement via Piper TTS (configuré pour la langue cible)

**Directions de traduction supportées** :
- Anglais → Français
- Français → Anglais

## Structure du code

### Organisation des modules

Le projet est organisé en modules Python avec une séparation claire des responsabilités :

```
voice_assistant/
├── __init__.py          # Initialisation du package
├── __main__.py          # Point d'entrée principal
├── assistant.py         # Implémentation de l'assistant RAG
├── translator.py        # Implémentation de l'assistant traducteur
├── audio/               # Modules audio
│   ├── __init__.py
│   ├── record.py        # Enregistrement audio avec VAD
│   └── playback.py      # Lecture audio
├── stt/                 # Reconnaissance vocale
│   ├── __init__.py
│   └── whisper_stt.py   # Interface avec Whisper
├── tts/                 # Synthèse vocale
│   ├── __init__.py
│   └── piper_tts.py     # Interface avec Piper
├── llm/                 # Modèle de langage
│   ├── __init__.py
│   └── llama_cpp_llm.py # Interface avec llama.cpp
├── rag/                 # Système RAG
│   ├── __init__.py
│   └── faiss_rag.py     # Implémentation RAG avec FAISS
├── utils/               # Utilitaires
│   ├── __init__.py
│   ├── config.py        # Gestion de la configuration
│   ├── normalization.py # Normalisation audio
│   └── text_utils.py    # Traitement de texte
└── config/              # Configuration
    └── default_config.yaml # Configuration par défaut
```

### Points d'entrée

Le projet dispose de deux points d'entrée principaux :

1. **assistant_launcher.py** :
   - Interface utilisateur pour lancer l'assistant
   - Vérification des dépendances et des fichiers nécessaires
   - Sélection du mode de fonctionnement

2. **voice_assistant/__main__.py** :
   - Point d'entrée programmatique
   - Analyse des arguments de ligne de commande
   - Initialisation et exécution du mode sélectionné

### Gestion de la configuration

La configuration du projet est centralisée dans un fichier YAML et gérée par un module dédié :

**ConfigManager** (`voice_assistant/utils/config.py`) :
- Chargement de la configuration depuis un fichier YAML
- Valeurs par défaut pour les paramètres manquants
- Accès hiérarchique aux paramètres
- Support de la surcharge de configuration

**Configuration par défaut** (`voice_assistant/config/default_config.yaml`) :
- Paramètres généraux (device_type, temp_dir, etc.)
- Paramètres audio (format, rate, VAD, etc.)
- Paramètres STT (model_size, language, etc.)
- Paramètres TTS (model, length_scale, etc.)
- Paramètres LLM (model_path, temperature, etc.)
- Paramètres RAG (embedding_model, chunk_size, etc.)
- Sons système et réponses prédéfinies

## Modèles et technologies utilisés

### Modèles de reconnaissance vocale

**Whisper** :
- Modèle : `small` (par défaut, configurable)
- Caractéristiques :
  - Support multilingue (français et anglais)
  - Reconnaissance robuste dans des environnements bruités
  - Beam search configurable pour une meilleure précision
- Performances :
  - CPU : ~10x temps réel sur un CPU moderne
  - GPU : ~30x temps réel sur un GPU moderne

### Modèles de synthèse vocale

**Piper** :
- Modèles :
  - `fr_FR-upmc-medium.onnx` : Voix française
  - `en_US-amy-medium.onnx` : Voix anglaise
- Caractéristiques :
  - Synthèse vocale de haute qualité
  - Faible latence
  - Support ONNX pour des performances optimisées
- Performances :
  - ~50x temps réel sur un CPU moderne

### Modèles de langage

**Gemma** :
- Modèle : `gemma-2b-it.Q4_K_M.gguf` (quantisé)
- Caractéristiques :
  - Modèle instruction-tuned
  - Taille de contexte : 1024 tokens
  - Quantisation pour réduire l'empreinte mémoire
- Performances :
  - ~10-15 tokens/s sur un CPU moderne
  - ~50-100 tokens/s sur un GPU moderne

### Modèles de traduction

**Argos Translate** :
- Modèles : Paires de langues anglais ↔ français
- Caractéristiques :
  - Traduction locale sans API
  - Basé sur des modèles de traduction neuronaux
  - Léger et rapide
- Performances :
  - ~0.5-1s par phrase sur un CPU moderne

### Embeddings et vectorisation

**Sentence Transformers** :
- Modèle : `paraphrase-multilingual-MiniLM-L12-v2`
- Caractéristiques :
  - Support multilingue
  - Embeddings de haute qualité pour la recherche sémantique
  - Taille d'embedding : 384 dimensions
- Performances :
  - ~100-200 phrases/s sur un CPU moderne
  - ~1000+ phrases/s sur un GPU moderne

**FAISS** :
- Type d'index : FlatL2 (par défaut)
- Caractéristiques :
  - Recherche de similarité vectorielle rapide
  - Optimisé pour les grands ensembles de données
  - Support CPU et GPU
- Performances :
  - ~1000+ recherches/s sur un CPU moderne

## Optimisations techniques

### Gestion des ressources

Le projet intègre plusieurs optimisations pour fonctionner efficacement sur des ressources limitées :

1. **Optimisations CPU** :
   - Limitation du nombre de threads pour éviter la surcharge
   - Configuration de variables d'environnement OMP_NUM_THREADS et MKL_NUM_THREADS
   - Optimisation des paramètres torch.set_num_threads

2. **Gestion de la mémoire** :
   - Garbage collection plus agressif
   - Nettoyage des ressources temporaires
   - Chargement différé des modèles

3. **Optimisations GPU** (si disponible) :
   - Détection automatique de la disponibilité du GPU
   - Utilisation de modèles quantisés pour réduire l'empreinte mémoire
   - Optimisations CUDA pour les modèles supportés

### Détection d'activité vocale (VAD)

Le système implémente un mécanisme de détection d'activité vocale personnalisé :

1. **Paramètres configurables** :
   - Seuil de silence pour la détection d'activité
   - Durée minimale de silence pour arrêter l'enregistrement
   - Durée minimale de parole pour considérer une entrée valide

2. **Algorithme** :
   - Analyse du niveau RMS (Root Mean Square) du signal audio
   - Détection des transitions parole/silence
   - Arrêt automatique après une période de silence

3. **Avantages** :
   - Meilleure expérience utilisateur (pas besoin d'appuyer sur un bouton)
   - Économie de ressources (évite de traiter des périodes de silence)
   - Adaptabilité à différents environnements sonores

### Normalisation audio

Le projet intègre un système de normalisation audio avancé :

1. **Techniques utilisées** :
   - Normalisation du volume
   - Filtrage du bruit
   - Égalisation

2. **Avantages** :
   - Amélioration de la qualité de la reconnaissance vocale
   - Robustesse face aux variations de niveau d'entrée
   - Meilleure qualité sonore pour l'utilisateur

### Mise en cache RAG

Le système RAG implémente un mécanisme de mise en cache des réponses :

1. **Détection de signatures de problèmes** :
   - Analyse des requêtes pour identifier des patterns de problèmes
   - Association de mots-clés à des catégories de problèmes
   - Fuzzy matching pour la tolérance aux variations

2. **Cache de réponses** :
   - Stockage des réponses associées à des signatures de problèmes
   - Réutilisation des réponses pour les questions similaires
   - Amélioration de la latence pour les questions fréquentes

## Installation et déploiement

### Prérequis système

- **Système d'exploitation** : Windows 10/11, Linux (Ubuntu 20.04+), macOS 12+
- **Python** : 3.10+ (3.11 recommandé)
- **RAM** : 8 Go minimum, 16 Go recommandé
- **Espace disque** : 5 Go minimum pour les modèles et dépendances
- **CPU** : 4 cœurs minimum, 8 cœurs recommandés
- **GPU** : Optionnel, CUDA compatible pour de meilleures performances
- **Audio** : Microphone et haut-parleurs/écouteurs

### Installation des dépendances

1. **Installation de Python et des outils de base** :
   ```bash
   # Sur Windows, télécharger et installer Python depuis python.org
   # Sur Linux
   sudo apt update
   sudo apt install python3.11 python3.11-dev python3.11-venv python3-pip
   sudo apt install portaudio19-dev  # Pour PyAudio
   ```

2. **Création d'un environnement virtuel** :
   ```bash
   python -m venv venv
   # Sur Windows
   venv\Scripts\activate
   # Sur Linux/macOS
   source venv/bin/activate
   ```

3. **Installation des dépendances Python** :
   ```bash
   pip install -r requirements.txt
   ```

4. **Installation des modèles** :
   - Placer les modèles Whisper dans le dossier approprié
   - Placer les modèles Piper dans le dossier `models/`
   - Placer le modèle Gemma dans le dossier `llm_models/`

### Configuration avancée

La configuration du projet peut être personnalisée en modifiant le fichier `voice_assistant/config/default_config.yaml` ou en créant un fichier de configuration personnalisé :

1. **Personnalisation des modèles** :
   - Changer la taille du modèle Whisper
   - Utiliser des modèles Piper différents
   - Configurer un modèle LLM alternatif

2. **Optimisation des performances** :
   - Ajuster les paramètres de batch size, context size, etc.
   - Configurer les paramètres de VAD pour votre environnement
   - Optimiser les paramètres RAG pour votre cas d'usage

3. **Personnalisation de l'interface** :
   - Modifier les messages d'accueil et les réponses prédéfinies
   - Ajouter des réponses communes personnalisées
   - Configurer les sons système

## Développement et extension

### Ajout de nouveaux modèles

Le projet est conçu pour être facilement extensible avec de nouveaux modèles :

1. **Ajout d'un nouveau modèle STT** :
   - Créer une nouvelle classe dans `voice_assistant/stt/`
   - Implémenter l'interface commune (méthode `transcribe_audio_data`)
   - Mettre à jour la configuration pour utiliser le nouveau modèle

2. **Ajout d'un nouveau modèle TTS** :
   - Créer une nouvelle classe dans `voice_assistant/tts/`
   - Implémenter l'interface commune (méthode `speak`)
   - Mettre à jour la configuration pour utiliser le nouveau modèle

3. **Ajout d'un nouveau modèle LLM** :
   - Créer une nouvelle classe dans `voice_assistant/llm/`
   - Implémenter l'interface commune (méthodes `generate` et `generate_stream`)
   - Mettre à jour la configuration pour utiliser le nouveau modèle

### Création de nouveaux modes

Le projet permet d'ajouter facilement de nouveaux modes de fonctionnement :

1. **Création d'une nouvelle classe d'assistant** :
   - S'inspirer de `VoiceAssistant` ou `TranslatorAssistant`
   - Implémenter la méthode `run()` pour le flux principal
   - Réutiliser les composants existants (STT, TTS, etc.)

2. **Mise à jour du point d'entrée** :
   - Ajouter le nouveau mode dans `__main__.py`
   - Configurer les paramètres spécifiques au mode

### Personnalisation du système RAG

Le système RAG peut être personnalisé pour différents cas d'usage :

1. **Utilisation d'une base de connaissances différente** :
   - Préparer un nouveau document markdown
   - Mettre à jour la configuration RAG pour pointer vers ce document
   - Reconstruire l'index vectoriel

2. **Optimisation des paramètres RAG** :
   - Ajuster la taille des chunks et l'overlap
   - Modifier le nombre de documents à récupérer (k)
   - Personnaliser le prompt pour le LLM

3. **Utilisation d'un modèle d'embedding différent** :
   - Choisir un modèle d'embedding alternatif
   - Mettre à jour la configuration RAG
   - Reconstruire l'index vectoriel 