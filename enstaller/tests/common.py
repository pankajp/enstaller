from okonomiyaki.repositories.enpkg import EnpkgS3IndexEntry

import enstaller.config

from enstaller.utils import PY_VER

def patched_read(**kw):
    config = {}
    config.update(enstaller.config.default)
    config.update(**kw)
    return config

def dummy_enpkg_entry_factory(name, version, build):
    data = {"egg_basename": name, "packages": [], "python": PY_VER,
            "size": 1024, "version": version, "build": build,
            "available": True}
    return EnpkgS3IndexEntry.from_data(data)
