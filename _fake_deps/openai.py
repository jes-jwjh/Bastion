class OpenAI:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.chat = None
        self.embeddings = None
