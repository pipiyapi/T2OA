from typing import List, Optional
from langchain_core.embeddings import Embeddings
from langchain_core.utils import get_from_dict_or_env
from pydantic import BaseModel, Field, model_validator
import requests
class SiliconFlowEmbeddings(BaseModel, Embeddings):
    """SiliconFlow embedding models.

    Setup:
        To use, you should have the environment variable ``SILICONFLOW_API_KEY``
        set with your API key, or pass it as a named parameter.

        Example:
            .. code-block:: python

                from my_embedding import SiliconFlowEmbeddings

                embed = SiliconFlowEmbeddings(
                    model="BAAI/bge-large-zh-v1.5",
                    # api_key="your_api_key_here",
                )
    """

    model: str = Field(default="BAAI/bge-large-zh-v1.5")
    api_key: str = Field(exclude=True)
    base_url: str = Field(default="https://api.siliconflow.cn/v1/embeddings")
    encoding_format: str = Field(default="float")

    @model_validator(mode="before")
    @classmethod
    def validate_environment(cls, values: dict) -> dict:
        """Validate API key exists in environment."""
        values["api_key"] = get_from_dict_or_env(
            values, "api_key", "SILICONFLOW_API_KEY"
        )
        return values

    def embed_query(self, text: str) -> List[float]:
        """Embed single text query."""
        return self.embed_documents([text])[0]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "input": texts,
            "encoding_format": self.encoding_format
        }

        response = requests.post(self.base_url, json=payload, headers=headers)
        response.raise_for_status()  # 添加基础的错误检查

        data = response.json()
        return [item["embedding"] for item in data["data"]]