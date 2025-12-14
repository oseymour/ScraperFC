from .load_comps import load_comps

def get_module_comps(module: str) -> dict:
    if not isinstance(module, str):
        raise TypeError('`module` must be a string.')
    comps = load_comps()
    module_comps = dict((k ,v) for k, v in comps.items() if module in v)
    return module_comps
