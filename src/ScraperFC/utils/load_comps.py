import yaml
from rootutils import find_root

def load_comps() -> dict:
    with open(find_root() / "src" / "ScraperFC" / "comps.yaml", "r") as f:
        comps = yaml.safe_load(f)
    return comps
