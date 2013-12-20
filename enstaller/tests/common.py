import enstaller.config

def patched_read(**kw):
    config = {}
    config.update(enstaller.config.default)
    config.update(**kw)
    return config

