# -*- coding: utf-8 -*-

from pathlib import Path

import gc

from typing import Dict, Any, List, Optional, Tuple, Union



from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain_huggingface import HuggingFaceEmbeddings

from langchain_community.vectorstores import FAISS

from langchain_core.documents import Document

from langchain.schema.runnable import RunnablePassthrough, RunnableLambda

from langchain.schema.output_parser import StrOutputParser

from langchain.memory import ConversationBufferMemory

from operator import itemgetter



from voice_assistant.utils.text_utils import format_history_as_string_for_prompt



class FaissRAG:

    """Classe pour le système RAG avec FAISS"""

    

    def __init__(self, config: Dict[str, Any], llm):

        """

        Initialise le système RAG

        

        Args:

            config: Configuration RAG

            llm: Instance du modèle de langage

        """

        self.embedding_model = config.get('embedding_model', 'paraphrase-multilingual-MiniLM-L12-v2')

        self.vectorstore_dir = Path(config.get('vectorstore_dir', 'vectorstore_faiss_md'))

        self.chunk_size = config.get('chunk_size', 700)

        self.chunk_overlap = config.get('chunk_overlap', 70)

        self.retriever_k = config.get('retriever_k', 2)

        self.doc_path = Path(config.get('doc_path', 'doc_resolutions.md'))

        

        # Vérification du fichier de documentation

        self._check_doc_file()

        

        # Initialisation des embeddings et du vectorstore

        self._initialize_embeddings()

        self._initialize_vectorstore()

        

        # Initialisation de la mémoire de conversation

        self.memory = ConversationBufferMemory(

            memory_key="history", input_key="question", output_key="output", return_messages=True

        )

        

        # Initialisation des chaînes RAG et non-RAG

        self.llm = llm

        self._initialize_rag_chain()

        self._initialize_non_rag_chain()

        

        # Cache pour les problèmes RAG

        self.rag_problem_cache = self._create_limited_size_dict(max_size=10)

    

    def _check_doc_file(self) -> None:

        """

        Vérifie que le fichier de documentation existe

        

        Raises:

            FileNotFoundError: Si le fichier de documentation est manquant

        """

        if not self.doc_path.exists():

            raise FileNotFoundError(f"Documentation file not found: {self.doc_path}")

    

    def _initialize_embeddings(self) -> None:

        """Initialise le modèle d'embeddings"""

        try:

            device_type = "cuda" if self._is_cuda_available() else "cpu"

            self.embeddings = HuggingFaceEmbeddings(

                model_name=self.embedding_model,

                model_kwargs={'device': device_type}

            )

            print(f"Embedding model loaded: {self.embedding_model} on {device_type}")

        except Exception as e:

            print(f"Error loading embedding model: {e}")

            raise

    

    def _initialize_vectorstore(self) -> None:

        """Initialise le vectorstore FAISS"""

        vs_path_str = str(self.vectorstore_dir)

        

        # Tente de charger le vectorstore existant

        if self.vectorstore_dir.exists():

            try:

                self.vectorstore = FAISS.load_local(

                    vs_path_str, self.embeddings, allow_dangerous_deserialization=True

                )

                print("FAISS index loaded.")

                self._setup_retriever()

                return

            except Exception as e:

                print(f"Error loading FAISS: {e}. Rebuilding.")

        

        # Crée un nouveau vectorstore

        try:

            docs = self._load_markdown_document(str(self.doc_path))

            if not docs:

                raise ValueError("Markdown document load failed.")

                

            text_splitter = RecursiveCharacterTextSplitter(

                chunk_size=self.chunk_size,

                chunk_overlap=self.chunk_overlap,

                length_function=len,

                is_separator_regex=False,

            )

            

            split_docs = text_splitter.split_documents(docs)

            if not split_docs:

                raise ValueError("Doc splitting yielded zero chunks.")

                

            self.vectorstore = FAISS.from_documents(split_docs, self.embeddings)

            self.vectorstore_dir.mkdir(exist_ok=True)

            self.vectorstore.save_local(vs_path_str)

            print(f"FAISS index created/saved: {vs_path_str}.")

            

            self._setup_retriever()

            

        except Exception as e:

            print(f"FATAL: FAISS index creation failed: {e}")

            import traceback

            traceback.print_exc()

            raise

    

    def _setup_retriever(self) -> None:

        """Configure le retriever FAISS"""

        self.retriever = self.vectorstore.as_retriever(

            search_type="similarity",

            search_kwargs={"k": self.retriever_k}

        )

        print(f"Retriever configured with k={self.retriever.search_kwargs['k']}.")

    

    def _initialize_rag_chain(self) -> None:

        """Initialise la chaîne RAG"""

        rag_prompt_chat = self.llm.create_rag_prompt_template()

        

        self.rag_chain = (

            RunnablePassthrough.assign(

                history_lc_mem_obj=RunnableLambda(self.memory.load_memory_variables) | itemgetter("history"),

                history_text_for_prompt=RunnableLambda(self.memory.load_memory_variables) | itemgetter("history") | RunnableLambda(format_history_as_string_for_prompt),

                context=itemgetter("question") | self.retriever | self._format_docs

            ) | rag_prompt_chat | self.llm.llm | StrOutputParser()

        )

    

    def _initialize_non_rag_chain(self) -> None:

        """Initialise la chaîne non-RAG"""

        non_rag_prompt = self.llm.create_non_rag_prompt_template()

        

        self.non_rag_chain = (

            RunnablePassthrough.assign(

                history_str=RunnableLambda(self.memory.load_memory_variables) | itemgetter("history") | RunnableLambda(format_history_as_string_for_prompt),

                question=itemgetter("question"),

                is_technical_no_rag_found=itemgetter("is_technical_no_rag_found")

            ) | non_rag_prompt | self.llm.llm | StrOutputParser()

        )

    

    def _load_markdown_document(self, markdown_path: str) -> List[Document]:

        """

        Charge un document Markdown

        

        Args:

            markdown_path: Chemin du fichier Markdown

            

        Returns:

            Liste de documents

        """

        try:

            with open(markdown_path, 'r', encoding='utf-8') as f:

                content = f.read()

            return [Document(page_content=content, metadata={"source": markdown_path})]

        except Exception as e:

            print(f"Error loading Markdown '{markdown_path}': {e}")

            return []

    

    def _format_docs(self, docs: List[Document]) -> str:

        """

        Formate les documents pour le prompt

        

        Args:

            docs: Liste de documents

            

        Returns:

            Documents formatés en chaîne de caractères

        """

        return "\n\n---\n\n".join(doc.page_content for doc in docs)

    

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

    

    def _create_limited_size_dict(self, max_size: int = 10) -> Dict:

        """

        Crée un dictionnaire à taille limitée

        

        Args:

            max_size: Taille maximale du dictionnaire

            

        Returns:

            Dictionnaire à taille limitée

        """

        class LimitedSizeDict(dict):

            def __init__(self, *args, **kwargs):

                self.max_size = kwargs.pop("max_size", max_size)

                super().__init__(*args, **kwargs)

                self._keys = []



            def __setitem__(self, key, value):

                if key in self:

                    self._keys.remove(key)

                elif len(self._keys) >= self.max_size:

                    oldest_key = self._keys.pop(0)

                    del self[oldest_key]

                super().__setitem__(key, value)

                self._keys.append(key)



            def __delitem__(self, key):

                super().__delitem__(key)

                if key in self._keys:

                    self._keys.remove(key)



            def __contains__(self, key):

                return super().__contains__(key)

        

        return LimitedSizeDict(max_size=max_size)

    

    def get_llm_stream_generator(self, text: str, use_rag_initial: bool = True):

        """

        Obtient un générateur de stream LLM

        

        Args:

            text: Texte de la question

            use_rag_initial: Si True, tente d'utiliser le RAG

            

        Returns:

            Générateur de stream LLM

        """

        if not text:

            def empty_gen():

                if False: yield

            return empty_gen()

        

        gc.collect()

        

        # Cette variable sera passée à la chaîne non-RAG si le RAG échoue

        is_technical_no_rag_found = False



        if use_rag_initial:

            relevant_docs_with_scores = self.vectorstore.similarity_search_with_relevance_scores(

                text, k=self.retriever.search_kwargs['k']

            )

            

            # DEBUG: Affiche les documents récupérés et leurs scores/distances

            print(f"DEBUG: Retrieved documents with scores: {relevant_docs_with_scores}")



            # Filtrage des documents

            filtered_docs = [doc for doc, score in relevant_docs_with_scores]



            if not filtered_docs:

                print(f"DEBUG: No documents were considered relevant after initial retrieval. "

                      f"Passing to non-RAG mode.")

                use_rag_mode = False

                

                # Détermine si la question était technique mais n'a pas trouvé de RAG

                import re

                from voice_assistant.utils.config import get_config

                config = get_config()

                problem_patterns = config.get_section('problem_detection').get('generic_problem_patterns', [])

                

                if any(re.search(p, text.lower()) for p in problem_patterns):

                    is_technical_no_rag_found = True

            else:

                print(f"DEBUG: {len(filtered_docs)} relevant documents found. Using RAG mode.")

                use_rag_mode = True

        else:

            use_rag_mode = False



        try:

            input_data = {"question": text}

            if use_rag_mode:

                return self.rag_chain.stream(input_data)

            else:

                # Passe 'is_technical_no_rag_found' à la chaîne non-RAG

                input_data["is_technical_no_rag_found"] = is_technical_no_rag_found

                return self.non_rag_chain.stream(input_data)

        except Exception as e:

            print(f"LLM stream generation error: {e}")

            import traceback

            traceback.print_exc()

            

            def error_generator():

                yield "Désolé, une erreur interne est survenue lors de la génération de la réponse."

            

            return error_generator()

    

    def save_to_memory(self, question: str, response: str) -> None:

        """

        Sauvegarde la question et la réponse dans la mémoire

        

        Args:

            question: Question de l'utilisateur

            response: Réponse de l'assistant

        """

        try:

            self.memory.save_context({"question": question}, {"output": response})

        except Exception as e:

            print(f"Warning: Memory save failed: {e}")

    

    def cache_rag_solution(self, problem_signature: str, response: str) -> None:

        """

        Met en cache une solution RAG

        

        Args:

            problem_signature: Signature du problème

            response: Réponse de l'assistant

        """

        if problem_signature and "unknown_device" not in problem_signature:

            self.rag_problem_cache[problem_signature] = response

            print(f"CACHED new RAG solution for: '{problem_signature}'")

    

    def get_cached_rag_solution(self, problem_signature: str) -> Optional[str]:

        """

        Récupère une solution RAG en cache

        

        Args:

            problem_signature: Signature du problème

            

        Returns:

            Solution en cache ou None si non trouvée

        """

        if problem_signature in self.rag_problem_cache:

            return self.rag_problem_cache[problem_signature]

        return None 