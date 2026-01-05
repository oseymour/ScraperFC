import yaml
from importlib import resources

def load_comps() -> dict:
    data = resources.files("ScraperFC").joinpath("comps.yaml").read_text()
    comps = yaml.safe_load(data)
    return comps
