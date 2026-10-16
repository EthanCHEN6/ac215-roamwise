"""Use the same checksum-pinned ONNX encoder for indexing and queries."""

from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2


def encoder():
    model = ONNXMiniLM_L6_V2(preferred_providers=["CPUExecutionProvider"])
    return model


def model_info():
    return {
        "model": ONNXMiniLM_L6_V2.MODEL_NAME,
        "archive_sha256": ONNXMiniLM_L6_V2._MODEL_SHA256,
        "download_url": ONNXMiniLM_L6_V2.MODEL_DOWNLOAD_URL,
        "dimensions": 384,
        "provider": "CPUExecutionProvider",
        "distance": "cosine",
    }
