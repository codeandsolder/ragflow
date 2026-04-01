# RAGFlow Python SDK

The official Python SDK for RAGFlow, an open-source RAG (Retrieval-Augmented Generation) engine based on deep document understanding.

## Installation

```bash
pip install ragflow-sdk
```

## Quick Start

```python
import ragflow_sdk

API_KEY = "your-api-key"
BASE_URL = "http://127.0.0.1:9380"

ragflow = ragflow_sdk.RAGFlow(api_key=API_KEY, base_url=BASE_URL)

datasets = ragflow.list_datasets(id="your_dataset_id")
for dataset in datasets:
    print(f"Dataset: {dataset.name}")

ragflow.close()
```

## Features

- **Dataset Management**: Create, list, update, and delete datasets
- **Document Handling**: Upload, parse, and manage documents
- **Chat Interface**: Create and manage chat sessions
- **Chunk Operations**: Access and search document chunks
- **Agent Support**: Build and deploy AI agents

## API Reference

### Initialization

```python
ragflow = ragflow_sdk.RAGFlow(api_key, base_url)
```

### Dataset Operations

```python
datasets = ragflow.list_datasets()           # List all datasets
dataset = ragflow.create_dataset(name="my_kb")  # Create a dataset
ragflow.update_dataset(dataset.id, {...})    # Update a dataset
ragflow.delete_dataset(dataset.id)           # Delete a dataset
```

### Document Operations

```python
documents = dataset.list_documents()         # List documents in dataset
dataset.upload_documents(["file.pdf"])      # Upload documents
document = dataset.get_document(doc_id)     # Get a specific document
dataset.delete_documents([doc_id])          # Delete documents
```

### Chat Operations

```python
chats = ragflow.list_chats(dataset_id=id)  # List chats
chat = ragflow.create_chat(name="My Chat") # Create a chat
session = chat.create_session()            # Create a session
```

## License

Apache License 2.0
