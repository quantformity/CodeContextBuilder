class BaseLLMProvider:
    def summarize(self, context: str, symbol_code: str) -> str:
        raise NotImplementedError()
