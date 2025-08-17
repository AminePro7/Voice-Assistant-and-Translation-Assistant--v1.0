# -*- coding: utf-8 -*-

from pathlib import Path

from typing import Dict, Any, Optional, List, Generator, Union



from langchain_community.llms import LlamaCpp

from langchain.prompts import (

    ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate,

    MessagesPlaceholder, PromptTemplate

)

from langchain.schema import AIMessage, HumanMessage



class LlamaCppLLM:

    """Classe pour le modèle de langage LlamaCpp"""

    

    def __init__(self, config: Dict[str, Any]):

        """

        Initialise le modèle LlamaCpp

        

        Args:

            config: Configuration LLM

        """

        self.model_path = Path(config.get('model_path', 'llm_models/gemma-2b-it.Q4_K_M.gguf'))

        self.n_batch = config.get('n_batch', 256)

        self.n_ctx = config.get('n_ctx', 1024)

        self.temperature = config.get('temperature', 0.1)

        self.max_tokens = config.get('max_tokens', 512)

        self.top_p = config.get('top_p', 0.9)

        self.repeat_penalty = config.get('repeat_penalty', 1.1)

        self.verbose = config.get('verbose', False)

        self.streaming = config.get('streaming', True)

        

        # Vérification du fichier modèle

        self._check_model_file()

        

        # Détermination du format de chat

        model_name_lower = self.model_path.name.lower()

        self.chat_format = "gemma" if "gemma" in model_name_lower else None

        

        # Initialisation du modèle LlamaCpp

        self._initialize_llm()

    

    def _check_model_file(self) -> None:

        """

        Vérifie que le fichier modèle existe

        

        Raises:

            FileNotFoundError: Si le fichier modèle est manquant

        """

        if not self.model_path.exists():

            raise FileNotFoundError(f"LLM model file not found: {self.model_path}")

    

    def _initialize_llm(self) -> None:

        """Initialise le modèle LlamaCpp"""

        try:

            # Détermination du nombre de couches GPU

            n_gpu_layers = -1 if self._is_cuda_available() else 0

            

            # Initialisation du modèle

            self.llm = LlamaCpp(

                model_path=str(self.model_path),

                n_gpu_layers=n_gpu_layers,

                n_batch=self.n_batch,

                n_ctx=self.n_ctx,

                temperature=self.temperature,

                max_tokens=self.max_tokens,

                top_p=self.top_p,

                repeat_penalty=self.repeat_penalty,

                verbose=self.verbose,

                streaming=self.streaming,

                chat_format=self.chat_format

            )

            

            print(f"LLM loaded (Chat Format: {self.chat_format or 'auto'}, "

                  f"n_ctx={self.llm.n_ctx}, temp={self.llm.temperature}).")

            

            # Test du modèle

            try:

                self.llm.invoke("Test")

                print("LLM test OK.")

            except Exception as llm_e:

                print(f"LLM test failed: {llm_e}")

        

        except Exception as e:

            print(f"Error loading LLM: {e}")

            raise

    

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

    

    def invoke(self, prompt: str) -> str:

        """

        Invoque le modèle avec un prompt simple

        

        Args:

            prompt: Prompt à envoyer au modèle

            

        Returns:

            Réponse du modèle

        """

        try:

            return self.llm.invoke(prompt)

        except Exception as e:

            print(f"LLM invocation error: {e}")

            return ""

    

    def stream(self, prompt: str) -> Generator[str, None, None]:

        """

        Invoque le modèle avec un prompt simple en mode streaming

        

        Args:

            prompt: Prompt à envoyer au modèle

            

        Yields:

            Tokens générés par le modèle

        """

        try:

            for token in self.llm.stream(prompt):

                yield token

        except Exception as e:

            print(f"LLM streaming error: {e}")

            yield ""

    

    def create_rag_prompt_template(self) -> ChatPromptTemplate:

        """

        Crée un template de prompt pour le RAG

        

        Returns:

            Template de prompt pour le RAG

        """

        system_rag_template = """Tu es un expert technique. 



RÈGLES STRICTES:

1. Utilise UNIQUEMENT la "Documentation Technique" fournie pour répondre. Ne jamais inventer.

2. Réponds en 2-3 phrases maximum par étape pour la clarté.

3. Si la documentation ne contient PAS l'information, dis EXACTEMENT: "Information non disponible dans ma base de connaissances."

4. Structure ta réponse avec des tirets pour les étapes (ex: "- Fais ceci.").

5. Sois DIRECT, CONCIS et SIMPLE. Évite le jargon.



STYLE:

- Commence par "Voici la solution:" si tu as trouvé une réponse.

- Utilise un ton professionnel et aidant."""



        system_message_prompt = SystemMessagePromptTemplate.from_template(system_rag_template)

        memory_placeholder = MessagesPlaceholder(variable_name="history_lc_mem_obj")

        

        human_rag_template = """HISTORIQUE DE CONVERSATION (pour contexte - UTILISE CECI):

{history_text_for_prompt}



DOCUMENTATION TECHNIQUE (source principale d'information):

```markdown

{context}

```



QUESTION DE L'UTILISATEUR: {question}



RÉPONSE TECHNIQUE de l'Assistant (basée STRICTEMENT sur la Documentation Technique):"""

        

        human_message_prompt = HumanMessagePromptTemplate.from_template(human_rag_template)

        

        return ChatPromptTemplate.from_messages([

            system_message_prompt, 

            memory_placeholder, 

            human_message_prompt

        ])

    

    def create_non_rag_prompt_template(self) -> PromptTemplate:

        """

        Crée un template de prompt pour le mode non-RAG

        

        Returns:

            Template de prompt pour le mode non-RAG

        """

        non_rag_template_str = """Tu es un assistant vocal conversationnel amical, serviable et concis.

Réponds à la "Question de l'utilisateur" en français, de manière polie et directe.

L' "Historique de Conversation" (fourni ci-dessous) EST CRUCIAL pour comprendre le contexte. TU DOIS l'utiliser pour les questions de suivi.

NE JAMAIS DIRE que tu n'as pas accès à l'historique. Il T'EST FOURNI.



Instructions Spécifiques pour cette interaction:

- Si l' "Historique de Conversation" existe et que la "Question de l'utilisateur" est très courte, vague ou confuse (par exemple "Oh c'est bien" sans contexte clair, "Quoi ?"), demande poliment à l'utilisateur de clarifier sa pensée ou sa question. Par exemple: "Pourriez-vous préciser votre pensée ?" ou "Que voulez-vous dire par là ?".

- Si la question est une simple affirmation de satisfaction (comme "parfait", "excellent") et que l'historique ne suggère pas un problème en cours, tu peux répondre par un simple accusé de réception comme "Entendu." ou "Parfait alors !".

- **Si la question porte sur un problème technique et que la base de connaissances RAG n'a rien trouvé, dis clairement: "Information non disponible dans ma base de connaissances. Pourriez-vous reformuler ou me poser une autre question ?"**

- Sinon, réponds de manière conversationnelle et pertinente par rapport à la question et à l'historique.



Historique de Conversation (UTILISE CECI POUR LE CONTEXTE):

{history_str}



Question de l'utilisateur: {question}

Est-ce une question technique sans réponse RAG : {is_technical_no_rag_found}



Réponse Conversationnelle de l'Assistant:"""

        

        return PromptTemplate(

            input_variables=["history_str", "question", "is_technical_no_rag_found"], 

            template=non_rag_template_str

        ) 