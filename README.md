# *Evolving-LLM-Experiments*

This repository serves as an experimentation platform for LLMs—ideal for developers and researchers looking to evaluate, compare, 
and interact with various language models in a local environment.

Many new features, tools, and experiments will be added in the future, making this repository a continuously evolving resource for LLM testing and development.

## Technical Introduction to Large Language Models (LLMs)

*Large language models* (LLMs) are sophisticated deep learning architectures, typically based on Transformer networks, trained on massive natural language datasets. 
With billions of parameters and extensive pre-training on diverse text sources, LLMs can model complex linguistic structures, semantic relationships, and contextual dependencies within language.
These models support a wide range of advanced tasks, such as contextualized text generation, question answering, code synthesis, and multimodal data processing when extended beyond text. 
LLMs are fundamental tools in modern AI research, enabling innovative applications in language understanding, information extraction, natural language-driven automation, and knowledge discovery.

Constant progress in scaling, fine-tuning, and domain adaptation methods further improves the performance, versatility, and security of LLMs, placing them 
at the heart of cutting-edge artificial intelligence systems.


## Detailed Python Program Descriptions

### OllamaConversation.py:
The main interface for conversing with an LLM model via the local Ollama server. Automates Ollama startup, allows model selection, logs conversations, and supports dynamic temperature adjustment. Also features text-to-speech support for model responses.

### OllamaConversationPicture.py:
A variant of the conversation tool that supports image input and processing. This script enables not only text dialogue but also image analysis using a multimodal Ollama-compatible model.

### OllamaModelEnrichment.py:
A script dedicated to model enrichment and management: adding information, manipulating LLM meta-data, exploring capabilities, and configuring locally available models.

### OllamaModelEnrichmentDocs.py:
Similar to the above, but focused on integrating and leveraging textual documents. It enables adding document sources to provide context or train the models to answer based on references.

### OllamaModelEnrichmentDocsAndPics.py:
Combines enrichment through both documents and images, to test multi-source and multimedia scenarios, making the most of the multimodal capabilities of advanced LLMs.

### OllamaModelEnrichmentDocsGamma.py:
An experimental or alternative version of multi-document enrichment, testing different strategies or pipelines with unique configurations.

### OllamaModelEnrichmentDocsSqlite.py:
Adds persistence for enriched documents via a local SQLite database, making it easier to manage, update, and archive items used in LLM tests.

### OllamaModelEnrichmentDocsSqliteWiki.py:
A variant using a dedicated SQLite wiki database, supporting Q&A logic over a locally stored encyclopedic corpus.

### OllamaModelsUpdate.py:
Automates updating and managing installed Ollama models: adding, removing, version checking, and local synchronization of different variants.

### OllamaReadPDF.py:
A utility for analyzing and automatically reading PDF files, extracting content to process or feed into an LLM model—ideal for synthesizing and analyzing large documents.

### OllamaSynthesis.py:
A script dedicated to auto-generating summaries (abstracts, excerpts) from responses or documents processed by the LLM.


