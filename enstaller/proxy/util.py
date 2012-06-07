#------------------------------------------------------------------------------
# Copyright (c) 2007-2008 by Enthought, Inc.
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD license
# available at http://www.enthought.com/licenses/BSD.txt and may be
# redistributed only under the conditions described in the aforementioned
# license.
#
#------------------------------------------------------------------------------


import os
import urllib2


def get_proxystr(pinfo):
    """ Get proxystr from a dictionary of proxy info.

    """
    host = pinfo.get('host')
    user = pinfo.get('user')

    # Only install a custom opener if a host was actually specified.
    if host is not None and len(host) > 0:

        if user is not None and len(user) > 0:
            proxystr = '%(user)s:%(pass)s@%(host)s:%(port)s' % pinfo
        else:
            proxystr = '%(host)s:%(port)s' % pinfo

    return proxystr

def install_proxy_handlers(pinfo):
    """
    Use a proxy for future urllib2.urlopen commands.

    The specified pinfo should be a dictionary containing the following:
        * host: the servername of the proxy
        * port: the port to use on the proxy server
        * user: (optional) username for authenticating with the proxy server.
        * pass: (optional) password for authenticating with the proxy server.

    """

    proxystr = get_proxystr(pinfo)

    if proxystr:
        proxies = dict(http=proxystr, https=proxystr)
        handler = urllib2.ProxyHandler(proxies)

        # Create a proxy opener and install it.
        opener = urllib2.build_opener(handler)
        urllib2.install_opener(opener)

    return


def get_proxy_info(proxystr=None):
    """
    Get proxy config from string or environment variables.

    If a proxy string is passed in, it overrides whatever might be in the
    environment variables.

    Returns dictionary of identified proxy information.

    Raises ValueError on any configuration error.

    """

    default_port = 80

    # Only check for env variables if no explicit proxy string was provided.
    if proxystr is None or len(proxystr) < 1:
        # FIXME: We should be supporting http_proxy, HTTP_PROXY variables.
        proxy_info = {
            'host' : os.environ.get('PROXY_HOST', None),
            'port' : os.environ.get('PROXY_PORT', default_port),
            'user' : os.environ.get('PROXY_USER', None),
            'pass' : os.environ.get('PROXY_PASS', None)
            }

    # Parse the passed proxy string
    else:
        # XXX Using proxy parsing function from urllib2 to parse proxystr
        _, user, passwd, host_port = urllib2._parse_proxy(proxystr)
        host, port = urllib2.splitport(host_port)
        proxy_info = {
            'host' : host,
            'port' : port or default_port,
            'user' : user,
            'pass' : passwd,
            }

    # If a user was specified, but no password was, prompt for it now.
    user = proxy_info.get('user', None)
    if user is not None and len(user) > 0:
        passwd = proxy_info.get('pass', None)
        if passwd is None or len(passwd) < 1:
            import getpass
            proxy_info['pass'] = getpass.getpass()

    return proxy_info


def setup_proxy(proxystr=''):
    """
    Configure and install proxy support.

    The specified proxy string is parsed via ``get_proxy_info`` and then
    installed via ``install_proxy_handler``.  If proxy settings are detected
    and a handler is installed, then this method returns True.  Otherwise it
    returns False.

    Raises ValueError in the event of any problems.

    """

    installed = False

    info = get_proxy_info(proxystr)

    if info.get('host') is not None:
        install_proxy_handlers(info)
        installed = True

    return installed
