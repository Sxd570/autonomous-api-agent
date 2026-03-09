import os
from dotenv import load_dotenv
from strands.models.openai import OpenAIModel
from pydantic import BaseModel, Field

load_dotenv()

    
class LMStudioAIConfig(BaseModel):
    model_name: str = Field(..., description="Model name or ID")
    base_url: str = Field(..., description="Base URL of the LM Studio instance")
    port: int = Field(..., description="Port number of the LM Studio instance")
    temperature: float = Field(..., description="Temperature for model responses")
    api_key: str = Field(..., description="API key for authentication")
    version: str = Field(..., description="API version for LM Studio")



class LMStudioAIService:
    def __init__(self):
        self.config = self.get_config()
        self.llm = None


    def get_config(self) -> LMStudioAIConfig:
        return LMStudioAIConfig(
            model_name = os.getenv("MODEL_NAME"),
            base_url = os.getenv("LM_STUDIO_BASE_URL"),
            port = int(os.getenv("LM_STUDIO_PORT")),
            temperature = float(os.getenv("MODEL_TEMPERATURE")),
            api_key = os.getenv("API_KEY"),
            version = os.getenv("LM_STUDIO_API_VERSION")
        )
    
    def initialize_llm(self):
        try:
            if not self.llm:
                self.llm = OpenAIModel(
                    model_id = self.config.model_name,
                    client_args = {
                        "base_url": f"{self.config.base_url}:{self.config.port}/{self.config.version}",
                        "api_key": self.config.api_key
                    },
                    temperature = self.config.temperature
                )
            return self.llm
        except Exception as e:
            print(f"Error initializing LLM: {e}")
            return None

# if __name__ == '__main__':
#     lm_studio = LMStudioAIService()
#     config = lm_studio.get_config()
#     print("config", config)

