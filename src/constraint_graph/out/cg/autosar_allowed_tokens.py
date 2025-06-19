"""prefix_allowed_tokens_fn stub ¨C ALWAYS allow all tokens.
Replace with DFA transition table lookup generated from .fsm file."""
def allowed(*_):
    return None  # returning None means "no restriction" in vLLM
