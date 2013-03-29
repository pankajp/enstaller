# Author: Ilan Schnell <ischnell@enthought.com>
"""\
enstaller is a managing tool for egginst-based installs, and the CLI is
called enpkg which calls out to egginst to do the actual install.
enpkg can access distributions from local and HTTP repositories.
"""
import os
import re
import sys
import site
import errno
import string
import datetime
import textwrap
from argparse import ArgumentParser
from os.path import isfile, join

from egginst.utils import bin_dir_name, rel_site_packages
from enstaller import __version__
import enstaller.config as config
from enstaller.proxy.api import setup_proxy
from enstaller.utils import abs_expanduser, fill_url, exit_if_sudo_on_venv

from enstaller.eggcollect import EggCollection
from enstaller.enpkg import Enpkg, EnpkgError, create_joined_store
from enstaller.resolve import Req, comparable_info
from enstaller.egg_meta import is_valid_eggname, split_eggname


FMT = '%-20s %-20s %s'
VB_FMT = '%(version)s-%(build)s'
FMT4 = '%-20s %-20s %-20s %s'


def env_option(prefixes):
    print "Prefixes:"
    for p in prefixes:
        print '    %s%s' % (p, ['', ' (sys)'][p == sys.prefix])
    print

    cmd = ('export', 'set')[sys.platform == 'win32']
    print "%s PATH=%s" % (cmd, os.pathsep.join(
                                 join(p, bin_dir_name) for p in prefixes))
    if len(prefixes) > 1:
        print "%s PYTHONPATH=%s" % (cmd, os.pathsep.join(
                            join(p, rel_site_packages) for p in prefixes))

    if sys.platform != 'win32':
        if sys.platform == 'darwin':
            name = 'DYLD_LIBRARY_PATH'
        else:
            name = 'LD_LIBRARY_PATH'
        print "%s %s=%s" % (cmd, name, os.pathsep.join(
                                 join(p, 'lib') for p in prefixes))


def disp_store_info(info):
    sl = info.get('store_location')
    if not sl:
        return '-'
    for rm in 'http://', 'https://', 'www', '.enthought.com', '/repo/':
        sl = sl.replace(rm, '')
    return sl.replace('/eggs/', ' ').strip('/')


def name_egg(egg):
    return split_eggname(egg)[0]


def print_install_time(enpkg, name):
    for key, info in enpkg.ec.query(name=name):
        print '%s was installed on: %s' % (key, info['ctime'])


def info_option(enpkg, name):
    name = name.lower()
    print 'Package:', name
    print_install_time(enpkg, name)
    pad = 4*' '
    for info in enpkg.info_list_name(name):
        print 'Version: ' + VB_FMT % info
        print pad + 'Product: %s' % info.get('product', '')
        print pad + 'Available: %s' % info.get('available', '')
        print pad + 'Python version: %s' % info.get('python', '')
        print pad + 'Store location: %s' % info.get('store_location', '')
        mtime = info.get('mtime', '')
        if mtime:
            mtime = datetime.datetime.fromtimestamp(mtime)
        print pad + 'Last modified: %s' % mtime
        print pad + 'Type: %s' % info.get('type', '')
        print pad + 'MD5: %s' % info.get('md5', '')
        print pad + 'Size: %s' % info.get('size', '')
        reqs = set(r for r in info['packages'])
        print pad + "Requirements: %s" % (', '.join(sorted(reqs)) or None)


def print_installed(prefix, hook=False, pat=None):
    print FMT % ('Name', 'Version', 'Store')
    print 60 * '='
    ec = EggCollection(prefix, hook)
    for egg, info in ec.query():
        if pat and not pat.search(info['name']):
            continue
        print FMT % (name_egg(egg), VB_FMT % info, disp_store_info(info))


def list_option(prefixes, hook=False, pat=None):
    for prefix in reversed(prefixes):
        print "prefix:", prefix
        print_installed(prefix, hook, pat)
        print


def parse_list(fn):
    pat = re.compile(r'([\w.]+)\s+([\w.]+-\d+)')
    res = set()
    for line in open(fn):
        line = line.strip()
        m = pat.match(line)
        if m:
            res.add(m.expand(r'\1-\2.egg'))
            continue
        if is_valid_eggname(line):
            res.add(line)
    return res


def imports_option(enpkg, pat=None):
    print FMT % ('Name', 'Version', 'Location')
    print 60 * "="

    names = set(info['name'] for _, info in enpkg.query_installed())
    for name in sorted(names, key=string.lower):
        if pat and not pat.search(name):
            continue
        for c in reversed(enpkg.ec.collections):
            index = dict(c.query(name=name))
            if index:
                info = index.values()[0]
                loc = 'sys' if c.prefix == sys.prefix else 'user'
        print FMT % (name, VB_FMT % info, loc)


def search(enpkg, pat=None):
    """
    Print the packages that are available in the (remote) KVS.
    """
    # Flag indicating if the user received any 'not subscribed to'
    # messages
    SUBSCRIBED = True

    print FMT4 % ('Name', '  Versions', 'Product', 'Note')
    print 80 * '='

    names = {}
    for key, info in enpkg.query_remote():
        names[info['name']] = name_egg(key)

    installed = {}
    for key, info in enpkg.query_installed():
        installed[info['name']] = VB_FMT % info

    for name in sorted(names, key=string.lower):
        if pat and not pat.search(name):
            continue
        disp_name = names[name]
        installed_version = installed.get(name)
        for info in enpkg.info_list_name(name):
            version = VB_FMT % info
            disp_ver = (('* ' if installed_version == version else '  ') +
                        version)
            available = info.get('available', True)
            product = info.get('product', '')
            if not(available):
                SUBSCRIBED = False
            print FMT4 % (disp_name, disp_ver, product,
                   '' if available else 'not subscribed to')
            disp_name = ''

    # if the user's search returns any packages that are not available
    # to them, attempt to authenticate and print out their subscriber
    # level
    if config.get('use_webservice') and not(SUBSCRIBED):
        user = {}
        try:
            user = config.authenticate(config.get_auth())
        except Exception as e:
            print e.message
        print config.subscription_message(user)


def updates_check(enpkg):
    updates = []
    EPD_update = []
    for key, info in enpkg.query_installed():
        av_infos = enpkg.info_list_name(info['name'])
        if len(av_infos) == 0:
            continue
        av_info = av_infos[-1]
        if comparable_info(av_info) > comparable_info(info):
            if info['name'] == "epd":
                EPD_update.append({'current': info, 'update': av_info})
            else:
                updates.append({'current': info, 'update': av_info})
    return updates, EPD_update


def whats_new(enpkg):
    updates, EPD_update = updates_check(enpkg)
    if not (updates or EPD_update):
        print "no new version of any installed package is available"
    else:
        if EPD_update:
            new_EPD_version = VB_FMT % EPD_update[0]['update']
            print "EPD", new_EPD_version, "is now available. " \
                "Run enpkg --upgrade-epd to update to the latest version of EPD"
        if updates:
            print FMT % ('Name', 'installed', 'available')
            print 60 * "="
            for update in updates:
                print FMT % (name_egg(update['current']['key']), VB_FMT % update['current'],
                             VB_FMT % update['update'])


def update_all(enpkg, args):
    updates, EPD_update = updates_check(enpkg)
    if not (updates or EPD_update):
        print "No new version of any installed package is available"
    else:
        if EPD_update:
            new_EPD_version = VB_FMT % EPD_update[0]['update']
            print "EPD", new_EPD_version, "is now available. " \
                "Run enpkg --upgrade-epd to update to the latest version of EPD"
        if updates:
            print "The following updates and their dependencies will be installed"
            print FMT % ('Name', 'installed', 'available')
            print 60 * "="
            for update in updates:
                print FMT % (name_egg(update['current']['key']), VB_FMT % update['current'],
                             VB_FMT % update['update'])
            for update in updates:
                install_req(enpkg, update['current']['name'], args)


def upgrade_epd(enpkg, args):
    updates, EPD_update = updates_check(enpkg)
    if EPD_update:
        new_EPD_version = VB_FMT % EPD_update[0]['update']
        current_EPD_version = VB_FMT % EPD_update[0]['current']
        print "EPD", current_EPD_version, "will be updated to version", new_EPD_version
        install_req(enpkg, EPD_update[0]['current']['name'], args)
    else:
        print "No new version of EPD is available"


def add_url(url, verbose):
    url = fill_url(url)
    if url in config.get('IndexedRepos'):
        print "Already configured:", url
        return
    config.prepend_url(url)

def pretty_print_packages(info_list):
    packages = {}
    for info in info_list:
        version = info['version']
        available = info.get('available', True)
        packages[version] = packages.get(version, False) or available
    pad = 4*' '
    descriptions = [version+(' (no subscription)' if not available else '')
        for version, available in sorted(packages.items())]
    return pad + '\n    '.join(textwrap.wrap(', '.join(descriptions)))

def install_req(enpkg, req, opts):
    """
    Try to execute the install actions.

    If 'use_webservice', check the user's credentials and prompt the
    user to input them if not authenticated.
    """
    # Below is a slightly complicated state machine that attempts to "do
    # the right thing" if the install initially fails.  Basically, the
    # flow is to try the install, prompt the user for credentials if "No
    # subscription" for the package and the user isn't authenticated,
    # then try the install once more if the credentials are valid.

    # Unix exit-status codes
    FAILURE = 1
    SUCCESS = 0

    def _perform_install(last_try=False):
        """
        Try to perform the install.

        If 'use_webservice' and the install fails, check the user's
        credentials (_check_auth), else _done.
        """
        try:
            mode = 'root' if opts.no_deps else 'recur'
            actions = enpkg.install_actions(
                    req,
                    mode=mode,
                    force=opts.force, forceall=opts.forceall)
            enpkg.execute(actions)
            if len(actions) == 0:
                print "No update necessary, %r is up-to-date." % req.name
                print_install_time(enpkg, req.name)
                _done(SUCCESS)
        except EnpkgError, e:
            if mode == 'root' or e.req is None or e.req == req:
                # trying to install just one requirement - try to give more info
                info_list = enpkg.info_list_name(req.name)
                if info_list:
                    print "Versions for package %r are:\n%s" % (req.name,
                        pretty_print_packages(info_list))
                    if any(not i.get('available', True) for i in info_list):
                        if config.get('use_webservice') and not(last_try):
                            _check_auth()
                        else:
                            _done(FAILURE)
                else:
                    print e.message
                    _done(FAILURE)
            elif mode == 'recur':
                print e.message
                print '\n'.join(textwrap.wrap("You may be able to force an install of just this " + \
                    "egg by using the --no-deps enpkg commandline argument " + \
                    "after installing another version of the dependency. "))
                if e.req:
                    info_list = enpkg.info_list_name(e.req.name)
                    if info_list:
                        print "Available versions of the required package %r are:\n%s" % (
                            e.req.name, pretty_print_packages(info_list))
                        if any(not i.get('available', True) for i in info_list):
                            if config.get('use_webservice') and not(last_try):
                                _check_auth()
                            else:
                                _done(FAILURE)
            _done(FAILURE)
        except OSError as e:
            if e.errno == errno.EACCES and sys.platform == 'darwin':
                print "Install failed. OSX install requires admin privileges."
                print "You should add 'sudo ' before the 'enpkg' command."
                _done(FAILURE)
            else:
                raise

    def _check_auth():
        """
        Check the user's credentials against the web API.
        """
        user = {}
        try:
            user = config.authenticate(config.get_auth())
            assert(user['is_authenticated'])
            # An EPD Free user who is trying to install a package not in
            # EPD free.  Print out subscription level and fail.
            print config.subscription_message(user)
            _done(FAILURE)
        except Exception as e:
            print e.message
            # No credentials.
            print ""
            _prompt_for_auth()

    def _prompt_for_auth():
        """
        Prompt the user for credentials and save them and retry the
        install if the credentials validate.
        """
        # prompt for username and password
        username, password = config.input_auth()
        user = config.checked_change_auth(username, password)
        # FIXME: This is a hack...  shouldn't have to change
        # enpkg.userpass or enpkg._connected manually
        if user:
            enpkg.userpass = (username, password)
            enpkg._connected = False
            _perform_install(last_try=True)
        else:
            _done(FAILURE)

    def _done(exit_status):
        sys.exit(exit_status)

    # kick off the state machine
    _perform_install()


def update_enstaller(enpkg, opts):
    """
    Check if Enstaller is up to date, and if not, ask the user if he
    wants to update.  Return boolean indicating whether enstaller was
    updated.
    """
    updated = False
    # exit early if autoupdate=False
    if not config.get('autoupdate', True):
        return updated
    try:
        if len(enpkg.install_actions('enstaller')) > 0:
            yn = raw_input("Enstaller is out of date.  Update? ([y]/n) ")
            if yn in set(['y', 'Y', '', None]):
                install_req(enpkg, 'enstaller', opts)
                updated = True
    except EnpkgError as e:
        print "Can't update enstaller:", e
    return updated


def main():
    try:
        user_base = site.USER_BASE
    except AttributeError:
        user_base = abs_expanduser('~/.local')

    p = ArgumentParser(description=__doc__)
    p.add_argument('cnames', metavar='NAME', nargs='*',
                   help='package(s) to work on')
    p.add_argument("--add-url", metavar='URL',
                   help="add a repository URL to the configuration file")
    p.add_argument("--config", action="store_true",
                   help="display the configuration and exit")
    p.add_argument('-f', "--force", action="store_true",
                   help="force install the main package "
                        "(not it's dependencies, see --forceall)")
    p.add_argument("--forceall", action="store_true",
                   help="force install of all packages "
                        "(i.e. including dependencies)")
    p.add_argument("--hook", action="store_true",
                   help="don't install into site-packages (experimental)")
    p.add_argument("--imports", action="store_true",
                   help="show which packages can be imported")
    p.add_argument('-i', "--info", action="store_true",
                   help="show information about a package")
    p.add_argument("--log", action="store_true", help="print revision log")
    p.add_argument('-l', "--list", action="store_true",
                   help="list the packages currently installed on the system")
    p.add_argument('-n', "--dry-run", action="store_true",
               help="show what would have been downloaded/removed/installed")
    p.add_argument('-N', "--no-deps", action="store_true",
                   help="neither download nor install dependencies")
    p.add_argument("--env", action="store_true",
                   help="based on the configuration, display how to set the "
                        "some environment variables")
    p.add_argument("--prefix", metavar='PATH',
                   help="install prefix (disregarding of any settings in "
                        "the config file)")
    p.add_argument("--proxy", metavar='URL', help="use a proxy for downloads")
    p.add_argument("--remove", action="store_true", help="remove a package")
    p.add_argument("--remove-enstaller", action="store_true", help="remove enstaller (will break enpkg)")
    p.add_argument("--revert", metavar="REV",
                   help="revert to a previous set of packages")
    p.add_argument('-s', "--search", action="store_true",
                   help="search the index in the repo of packages "
                        "and display versions available.")
    p.add_argument("--sys-config", action="store_true",
                   help="use <sys.prefix>/.enstaller4rc (even when "
                        "~/.enstaller4rc exists)")
    p.add_argument("--sys-prefix", action="store_true",
                   help="use sys.prefix as the install prefix")
    p.add_argument("--update-all", action="store_true",
                   help="update all installed packages")
    p.add_argument("--user", action="store_true",
               help="install into user prefix, i.e. --prefix=%r" % user_base)
    p.add_argument("--userpass", action="store_true",
                   help="change EPD authentication in configuration file")
    p.add_argument('-v', "--verbose", action="store_true")
    p.add_argument('--version', action="version",
                   version='enstaller version: ' + __version__)
    p.add_argument("--whats-new", action="store_true",
                   help="display to which installed packages updates are "
                        "available")
    p.add_argument("--upgrade-epd", action="store_true",
                   help="Upgrade to a newer version of EPD")

    args = p.parse_args()

    if len(args.cnames) > 0 and (args.config or args.env or args.userpass or
                                 args.revert or args.log or args.whats_new or
                                 args.update_all or args.remove_enstaller or
                                 args.upgrade_epd):
        p.error("Option takes no arguments")

    if args.user:
        args.prefix = user_base

    if args.prefix and args.sys_prefix:
        p.error("Options --prefix and --sys-prefix exclude each other")

    if args.force and args.forceall:
        p.error("Options --force and --forceall exclude each other")

    pat = None
    if (args.list or args.search) and args.cnames:
        pat = re.compile(args.cnames[0], re.I)

    # make prefix
    if args.sys_prefix:
        prefix = sys.prefix
    elif args.prefix:
        prefix = args.prefix
    else:
        prefix = config.get('prefix', sys.prefix)

    # now make prefixes
    if prefix == sys.prefix:
        prefixes = [sys.prefix]
    else:
        prefixes = [prefix, sys.prefix]

    exit_if_sudo_on_venv(prefix)

    if args.verbose:
        print "Prefixes:"
        for p in prefixes:
            print '    %s%s' % (p, ['', ' (sys)'][p == sys.prefix])
        print

    if args.env:                                  # --env
        env_option(prefixes)
        return

    if args.log:                                  # --log
        if args.hook:
            raise NotImplementedError
        from history import History
        h = History(prefix)
        h.update()
        h.print_log()
        return

    if args.sys_config:                           # --sys-config
        config.get_path = lambda: config.system_config_path

    if args.list:                                 # --list
        list_option(prefixes, args.hook, pat)
        return

    if args.proxy:                                # --proxy
        setup_proxy(args.proxy)
    elif config.get('proxy'):
        setup_proxy(config.get('proxy'))
    else:
        setup_proxy()

    if 0: # for testing event manager only
        from encore.events.api import EventManager
        from encore.terminal.api import ProgressDisplay
        evt_mgr = EventManager()
        display = ProgressDisplay(evt_mgr)
    else:
        evt_mgr = None

    if config.get('use_webservice'):
        remote = None # Enpkg will create the default
    else:
        urls = [fill_url(u) for u in config.get('IndexedRepos')]
        remote = create_joined_store(urls)

    enpkg = Enpkg(remote, prefixes=prefixes, hook=args.hook,
                  evt_mgr=evt_mgr, verbose=args.verbose)

    if args.config:                               # --config
        config.print_config(enpkg.remote, prefixes[0])
        return

    if args.userpass:                             # --userpass
        username, password = config.input_auth()
        config.checked_change_auth(username, password, enpkg.remote)
        return

    if args.dry_run:
        def print_actions(actions):
            for item in actions:
                print '%-8s %s' % item
        enpkg.execute = print_actions

    if args.imports:                              # --imports
        assert not args.hook
        imports_option(enpkg, pat)
        return

    if args.add_url:                              # --add-url
        add_url(args.add_url, args.verbose)
        return

    if args.revert:                               # --revert
        if isfile(args.revert):
            arg = parse_list(args.revert)
        else:
            arg = args.revert
        try:
            actions = enpkg.revert_actions(arg)
            if not actions:
                print "Nothing to do"
                return
            enpkg.execute(actions)
        except EnpkgError as e:
            print e.message
        return

    # Try to auto-update enstaller
    if update_enstaller(enpkg, args):
        print "Enstaller has been updated.", \
            "Please re-run your previous command."
        return

    if args.search:                               # --search
        search(enpkg, pat)
        return

    if args.info:                                 # --info
        if len(args.cnames) != 1:
            p.error("Option requires one argument (name of package)")
        info_option(enpkg, args.cnames[0])
        return

    if args.whats_new:                            # --whats-new
        whats_new(enpkg)
        return

    if args.update_all:                           # --update-all
        update_all(enpkg, args)
        return

    if args.upgrade_epd:                          # --upgrade-epd
        upgrade_epd(enpkg, args)
        return

    if len(args.cnames) == 0 and not args.remove_enstaller:
        p.error("Requirement(s) missing")
    elif len(args.cnames) == 2:
        pat = re.compile(r'\d+\.\d+')
        if pat.match(args.cnames[1]):
            args.cnames = ['-'.join(args.cnames)]

    reqs = []
    for arg in args.cnames:
        if '-' in arg:
            name, version = arg.split('-', 1)
            reqs.append(Req(name + ' ' + version))
        else:
            reqs.append(Req(arg))

    if args.verbose:
        print "Requirements:"
        for req in reqs:
            print '    %r' % req
        print

    print "prefix:", prefix

    if args.remove:
        if any(req.name == 'enstaller' for req in reqs):
            print "Removing enstaller package will break enpkg and is not recommended."
            print "If you are sure you wish to remove enstaller, use:"
            print "    enpkg --remove-enstaller"
            return

    if args.remove_enstaller:
        print "Removing enstaller package will break enpkg and is not recommended."
        yn = raw_input("Really remove enstaller? (y/[n]) ")
        if yn.lower() in set(['y', 'yes']):
            args.remove = True
            reqs = [Req('enstaller')]

    for req in reqs:
        if args.remove:                               # --remove
            try:
                enpkg.execute(enpkg.remove_actions(req))
            except EnpkgError as e:
                print e.message
        else:
            install_req(enpkg, req, args)             # install (default)


if __name__ == '__main__':
    main()
