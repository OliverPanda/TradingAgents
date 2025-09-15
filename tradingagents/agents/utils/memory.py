import chromadb
from chromadb.config import Settings
from openai import OpenAI
import os
import time

# Import DashScope if available
try:
    import dashscope
    from dashscope import TextEmbedding
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False
    dashscope = None
    TextEmbedding = None


class FinancialSituationMemory:
    def __init__(self, name, config):
        self.config = config
        self.llm_provider = config.get("llm_provider", "openai").lower()

        # Configure embedding model and client based on LLM provider
        if (self.llm_provider == "dashscope" or
            "dashscope" in self.llm_provider or
            "alibaba" in self.llm_provider):

            # Check if DashScope is available and configured
            dashscope_key = os.getenv('DASHSCOPE_API_KEY')
            openai_key = os.getenv('OPENAI_API_KEY')

            if DASHSCOPE_AVAILABLE and dashscope_key:
                # Use DashScope embeddings
                self.embedding = "text-embedding-v3"
                self.client = None  # DashScope doesn't need OpenAI client
                dashscope.api_key = dashscope_key
                print("✅ Using DashScope embeddings")
            elif openai_key:
                # Fallback to OpenAI embeddings
                print("⚠️ DashScope not available or not configured, falling back to OpenAI embeddings")
                self.embedding = "text-embedding-3-small"
                self.client = OpenAI(base_url=config.get("backend_url", "https://api.openai.com/v1"))
            else:
                # No valid API keys available
                raise ValueError(
                    "No valid API keys found. For DashScope provider, please set either:\n"
                    "1. DASHSCOPE_API_KEY (preferred for DashScope embeddings)\n"
                    "2. OPENAI_API_KEY (fallback for OpenAI embeddings)\n"
                    "Install dashscope package: pip install dashscope"
                )
        elif self.llm_provider == "google":
            # Google AI uses DashScope embedding if available, otherwise OpenAI
            dashscope_key = os.getenv('DASHSCOPE_API_KEY')
            openai_key = os.getenv('OPENAI_API_KEY')

            if dashscope_key and DASHSCOPE_AVAILABLE:
                self.embedding = "text-embedding-v3"
                self.client = None
                dashscope.api_key = dashscope_key
                print("💡 Google AI using DashScope embedding service")
            elif openai_key:
                self.embedding = "text-embedding-3-small"
                self.client = OpenAI(base_url=config.get("backend_url", "https://api.openai.com/v1"))
                print("⚠️ Google AI falling back to OpenAI embedding service")
            else:
                raise ValueError(
                    "No valid API keys found for Google AI embeddings. Please set either:\n"
                    "1. DASHSCOPE_API_KEY (preferred)\n"
                    "2. OPENAI_API_KEY (fallback)"
                )
        elif config["backend_url"] == "http://localhost:11434/v1":
            self.embedding = "nomic-embed-text"
            self.client = OpenAI(base_url=config["backend_url"])
        else:
            self.embedding = "text-embedding-3-small"
            self.client = OpenAI(base_url=config["backend_url"])

        self.chroma_client = chromadb.Client(Settings(allow_reset=True))

        # Try to get existing collection, create new one if it doesn't exist
        try:
            self.situation_collection = self.chroma_client.get_collection(name=name)
        except Exception:
            # Collection doesn't exist, create new one
            self.situation_collection = self.chroma_client.create_collection(name=name)

    def get_embedding(self, text):
        """Get embedding for a text using the configured provider"""

        if ((self.llm_provider == "dashscope" or
             "dashscope" in self.llm_provider or
             "alibaba" in self.llm_provider or
             (self.llm_provider == "google" and self.client is None)) and
            DASHSCOPE_AVAILABLE and self.client is None):
            # Use DashScope embedding model with retry and timeout handling
            import time
            import requests
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
            
            max_retries = 3
            timeout = 30  # 30秒超时
            
            for attempt in range(max_retries):
                try:
                    # 设置重试策略
                    session = requests.Session()
                    retry_strategy = Retry(
                        total=2,
                        backoff_factor=1,
                        status_forcelist=[429, 500, 502, 503, 504],
                    )
                    adapter = HTTPAdapter(max_retries=retry_strategy)
                    session.mount("http://", adapter)
                    session.mount("https://", adapter)
                    
                    # 调用DashScope API
                    response = TextEmbedding.call(
                        model=self.embedding,
                        input=text,
                        timeout=timeout
                    )
                    
                    if response.status_code == 200:
                        return response.output['embeddings'][0]['embedding']
                    else:
                        error_msg = f"DashScope embedding error: {response.code} - {response.message}"
                        if attempt < max_retries - 1:
                            print(f"⚠️ DashScope embedding失败，第{attempt + 1}次重试: {error_msg}")
                            time.sleep(2 ** attempt)  # 指数退避
                            continue
                        else:
                            raise Exception(error_msg)
                            
                except (requests.exceptions.ConnectTimeout, 
                        requests.exceptions.ReadTimeout,
                        requests.exceptions.ConnectionError) as e:
                    if attempt < max_retries - 1:
                        print(f"⚠️ DashScope连接超时，第{attempt + 1}次重试: {str(e)}")
                        time.sleep(2 ** attempt)  # 指数退避
                        continue
                    else:
                        # 最后一次尝试失败，降级到OpenAI
                        print(f"❌ DashScope连接最终失败，尝试降级到OpenAI: {str(e)}")
                        return self._get_openai_embedding_fallback(text)
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"⚠️ DashScope API错误，第{attempt + 1}次重试: {str(e)}")
                        time.sleep(2 ** attempt)
                        continue
                    else:
                        # 最后一次尝试失败，降级到OpenAI
                        print(f"❌ DashScope API最终失败，尝试降级到OpenAI: {str(e)}")
                        return self._get_openai_embedding_fallback(text)
        else:
            # Use OpenAI-compatible embedding model
            response = self.client.embeddings.create(
                model=self.embedding, input=text
            )
            return response.data[0].embedding
    
    def _get_openai_embedding_fallback(self, text):
        """降级到OpenAI embedding的备用方案"""
        try:
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key:
                from openai import OpenAI
                client = OpenAI(api_key=openai_key)
                response = client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text
                )
                print("✅ 成功降级到OpenAI embedding")
                return response.data[0].embedding
            else:
                # 如果连OpenAI都没有，返回随机向量
                print("⚠️ 无可用embedding服务，使用随机向量")
                import numpy as np
                return np.random.random(1536).tolist()  # 1536维随机向量
        except Exception as e:
            print(f"❌ OpenAI embedding降级也失败: {str(e)}")
            # 最后的备用方案：返回随机向量
            import numpy as np
            return np.random.random(1536).tolist()

    def add_situations(self, situations_and_advice):
        """Add financial situations and their corresponding advice. Parameter is a list of tuples (situation, rec)"""

        situations = []
        advice = []
        ids = []
        embeddings = []

        offset = self.situation_collection.count()

        for i, (situation, recommendation) in enumerate(situations_and_advice):
            situations.append(situation)
            advice.append(recommendation)
            ids.append(str(offset + i))
            embeddings.append(self.get_embedding(situation))

        self.situation_collection.add(
            documents=situations,
            metadatas=[{"recommendation": rec} for rec in advice],
            embeddings=embeddings,
            ids=ids,
        )

    def get_memories(self, current_situation, n_matches=1):
        """Find matching recommendations using embeddings"""
        query_embedding = self.get_embedding(current_situation)

        results = self.situation_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_matches,
            include=["metadatas", "documents", "distances"],
        )

        matched_results = []
        for i in range(len(results["documents"][0])):
            matched_results.append(
                {
                    "matched_situation": results["documents"][0][i],
                    "recommendation": results["metadatas"][0][i]["recommendation"],
                    "similarity_score": 1 - results["distances"][0][i],
                }
            )

        return matched_results


if __name__ == "__main__":
    # Example usage
    matcher = FinancialSituationMemory()

    # Example data
    example_data = [
        (
            "High inflation rate with rising interest rates and declining consumer spending",
            "Consider defensive sectors like consumer staples and utilities. Review fixed-income portfolio duration.",
        ),
        (
            "Tech sector showing high volatility with increasing institutional selling pressure",
            "Reduce exposure to high-growth tech stocks. Look for value opportunities in established tech companies with strong cash flows.",
        ),
        (
            "Strong dollar affecting emerging markets with increasing forex volatility",
            "Hedge currency exposure in international positions. Consider reducing allocation to emerging market debt.",
        ),
        (
            "Market showing signs of sector rotation with rising yields",
            "Rebalance portfolio to maintain target allocations. Consider increasing exposure to sectors benefiting from higher rates.",
        ),
    ]

    # Add the example situations and recommendations
    matcher.add_situations(example_data)

    # Example query
    current_situation = """
    Market showing increased volatility in tech sector, with institutional investors 
    reducing positions and rising interest rates affecting growth stock valuations
    """

    try:
        recommendations = matcher.get_memories(current_situation, n_matches=2)

        for i, rec in enumerate(recommendations, 1):
            print(f"\nMatch {i}:")
            print(f"Similarity Score: {rec['similarity_score']:.2f}")
            print(f"Matched Situation: {rec['matched_situation']}")
            print(f"Recommendation: {rec['recommendation']}")

    except Exception as e:
        print(f"Error during recommendation: {str(e)}")
