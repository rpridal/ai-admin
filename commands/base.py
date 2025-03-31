class BaseCommand:
    def __init__(self, action, session_id):
        self.action = action
        self.session_id = session_id

    def execute(self):
        raise NotImplementedError