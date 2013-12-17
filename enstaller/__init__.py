try:
    from enstaller._version import full_version as __version__
except ImportError as e:
    __version__ = "no-built"
