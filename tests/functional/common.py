import mock

def _dont_write_default_configuration(f):
    return mock.patch("enstaller.main.write_default_config",
                      lambda filename, use_keyring=None: None)(f)

def without_default_configuration(f):
    """
    When this decorator is applied, enstaller.main will behave as if no default
    configuration is found anywhere, and no default configuration will be
    written in $HOME.
    """
    dummy_enstaller = "dummy_config_file_doesnt_exist_nono"
    dec1 = mock.patch("enstaller.main.get_config_filename",
                      lambda ignored: dummy_enstaller)
    return _dont_write_default_configuration(dec1(f))
