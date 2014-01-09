def close_file_or_response(fp):
    if hasattr(fp, "close"):
        fp.close()
    else:
        # Compat shim for requests < 2
        fp._fp.close()
