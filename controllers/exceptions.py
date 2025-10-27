# Breaking out of flows via exception
class QuitFlow(Exception):
    """Raise to immediately quit the current flow or operation"""
    pass