"""
Unified LLM Provider — wraps Gemini, OpenAI GPT-4o, and Anthropic Claude
with a single interface. Every call is real — no mocks, no fallbacks to demos.
If an API key is missing, raises a clear ConfigurationError immediately.
"""

import os
import json
from typing import Optional


class LLMConfigurationError(Exception):
    """Raised when a required API key is not configured."""
    pass


class LLMProvider:
    """
    Unified interface for Gemini, OpenAI GPT-4o, and Anthropic Claude.
    
    Usage:
        provider = LLMProvider(model="gemini")
        response = provider.generate(prompt)
    """

    SUPPORTED_MODELS = {
        "gemini": {
            "display_name": "Google Gemini 3.6 Flash",
            "env_key": "GEMINI_API_KEY",
            "model_id": "gemini-3.6-flash",
        },
        "gpt4o": {
            "display_name": "OpenAI GPT-4o",
            "env_key": "OPENAI_API_KEY",
            "model_id": "gpt-4o",
        },
        "claude": {
            "display_name": "Anthropic Claude 3.5 Sonnet",
            "env_key": "ANTHROPIC_API_KEY",
            "model_id": "claude-3-5-sonnet-20241022",
        },
    }

    def __init__(self, model: str = "gemini"):
        model = model.lower().strip()
        if model not in self.SUPPORTED_MODELS:
            raise ValueError(
                f"Unsupported model '{model}'. Choose from: {list(self.SUPPORTED_MODELS.keys())}"
            )
        self.model_key = model
        self.config = self.SUPPORTED_MODELS[model]
        self.api_key = os.getenv(self.config["env_key"])

        if not self.api_key:
            raise LLMConfigurationError(
                f"API key for '{self.config['display_name']}' is not set. "
                f"Please set the environment variable '{self.config['env_key']}' in your .env file."
            )

    @classmethod
    def get_available_models(cls) -> list:
        """Returns list of model configs with availability status."""
        result = []
        for key, cfg in cls.SUPPORTED_MODELS.items():
            api_key = os.getenv(cfg["env_key"])
            result.append({
                "key": key,
                "display_name": cfg["display_name"],
                "model_id": cfg["model_id"],
                "env_key": cfg["env_key"],
                "available": bool(api_key),
            })
        return result

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate a response from the selected LLM.
        Returns raw text string. Raises on any API error.
        """
        if self.model_key == "gemini":
            return self._call_gemini(prompt, system_prompt)
        elif self.model_key == "gpt4o":
            return self._call_openai(prompt, system_prompt)
        elif self.model_key == "claude":
            return self._call_anthropic(prompt, system_prompt)
        else:
            raise ValueError(f"Unhandled model key: {self.model_key}")

    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> any:
        """
        Generate and parse a JSON response. Strips markdown code fences if present.
        """
        text = self.generate(prompt, system_prompt)
        text = text.strip()
        # Strip markdown code fences
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first line (```json or ```) and last line (```)
            text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        text = text.strip()
        return json.loads(text)

    def _call_gemini(self, prompt: str, system_prompt: Optional[str]) -> str:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.api_key)

        contents = []
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        else:
            full_prompt = prompt

        response = client.models.generate_content(
            model=self.config["model_id"],
            contents=full_prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=4096,
            )
        )
        return response.text

    def _call_openai(self, prompt: str, system_prompt: Optional[str]) -> str:
        import openai

        client = openai.OpenAI(api_key=self.api_key)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=self.config["model_id"],
            messages=messages,
            temperature=0.3,
            max_tokens=4096,
        )
        return response.choices[0].message.content

    def _call_anthropic(self, prompt: str, system_prompt: Optional[str]) -> str:
        import anthropic

        client = anthropic.Anthropic(api_key=self.api_key)

        kwargs = {
            "model": self.config["model_id"],
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        response = client.messages.create(**kwargs)
        return response.content[0].text
