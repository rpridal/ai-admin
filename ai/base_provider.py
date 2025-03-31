class BaseAIProvider:
    def query(self, messages: list[dict], mode: str = "fast") -> str:
        raise NotImplementedError()