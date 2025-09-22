import os
import json
from typing import List, Dict, Any
from langchain.chat_models import init_chat_model
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.constants import PROMPT_TEMPLATE
from app.models import TimingPath


class TimingAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = self._initialize_model()
        self.json_parser = JsonOutputParser()

    def _initialize_model(self):
        """Initialize the Groq model"""
        os.environ["GROQ_API_KEY"] = self.api_key
        return init_chat_model(
            "llama-3.3-70b-versatile",
            model_provider="groq",
            temperature=0.1
        )

    def analyze_paths(self, paths: List[TimingPath]) -> List[Dict[str, Any]]:
        """Analyze timing paths using LLM"""
        results = []
        prompt_template = PromptTemplate.from_template(PROMPT_TEMPLATE)

        for i, path in enumerate(paths):
            try:
                chain = prompt_template | self.model | self.json_parser
                result = chain.invoke({"path_json": json.dumps(path.dict(), indent=2)})

                # Ensure result has required fields
                result.update({
                    "startpoint": path.startpoint,
                    "endpoint": path.endpoint,
                    "path_type": path.path_type,
                    "status": path.status,
                    "slack": path.slack
                })

                results.append(result)

            except Exception as e:
                print(f"Error analyzing path {i}: {e}")
                # Create a basic result for failed analysis
                results.append({
                    "startpoint": path.startpoint,
                    "endpoint": path.endpoint,
                    "path_type": path.path_type,
                    "status": path.status,
                    "slack": path.slack,
                    "root_cause": f"Analysis failed: {str(e)}",
                    "severity": "unknown",
                    "suggestions": [],
                    "estimated_effort": "unknown"
                })

        return results