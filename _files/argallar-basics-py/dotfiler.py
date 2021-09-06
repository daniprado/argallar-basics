"""
Inspired by the wonderful: https://www.gnu.org/software/stow
"""

from os import path, walk, getlogin, listdir
from os import environ as osenv
from socket import gethostname
from re import sub
from subprocess import call
from pathlib import Path
import json

import click

cli = click.Group()

BANNED_DIRS = ".git,_files,__pycache__,.stfolder,backup"
BANNED_FILES = ".git,.gitignore,init.sh,init.json,install.sh,LICENSE,README.md"

S_CHAR = '@'
D_LINK = f"l{S_CHAR}"
F_USER = f"u{S_CHAR}"
F_HOST = f"h{S_CHAR}"


def _echo(msg, err=False):
    if not osenv['AG_FAKE']:
        click.echo(msg, err=err)


class PathElem(object):
    def __init__(self, dest):
        self.dest = dest

    @staticmethod
    def getdests(items: list) -> list:
        return [i.dest for i in items if isinstance(i, PathElem)]


class PathLink(PathElem):
    def __init__(self, src, dest):
        super().__init__(dest)
        self.src = src

    def getcreate(self, rsrc, rdest):
        return [
            'ln',
            '-s',
            path.normpath(f"{rsrc}/{self.src}"),
            path.normpath(f"{rdest}/{self.dest}")
        ]

    def getremove(self, rdest):
        return ['rm', path.normpath(f"{rdest}/{self.dest}")]

    @staticmethod
    def getsrcs(items: list) -> list:
        return [i.src for i in items if isinstance(i, PathLink)]


class PathDir(PathElem):
    def getcreate(self, rsrc, rdest):
        return ['mkdir', '-p', path.normpath(f"{rdest}/{self.dest}")]

    def getremove(self, rdest):
        return []
        # return ['rmdir', path.normpath(f"{rdest}/{self.dest}")]


def _calcsplit(filename: str, token: str, default_res: str, sep_char: str):
    res, fn = default_res, filename
    if filename.startswith(token):
        res, fn = filename.split(token)[1].split(sep_char)
    return res, fn


def _getpathelems(init_path: str, init_user: str, init_host: str,
        ban_dirs: set, ban_files: set, sep_char: str) -> list:

    result = []
    bdirs = ban_dirs
    for root, dirs, files in walk(init_path):

        rfolder = sub(rf"^{init_path}[/]?", '', root, 1)
        rpath = f"{rfolder}/" if rfolder else ''

        bdirs.update(f"{rpath}{d}" for d in dirs if d in bdirs)
        if rfolder in bdirs:
            bdirs.update(f"{rpath}{d}" for d in dirs)
            continue

        if rfolder not in PathLink.getsrcs(result):
            result.append(PathDir(rpath))

        dlinks = [
            PathLink(f"{rpath}{d}", f"{rpath}{d.split(D_LINK)[1]}")
            for d in dirs if d.startswith(D_LINK)
        ]
        result.extend(dlinks)
        bdirs.update(PathLink.getsrcs(dlinks))

        for f in [f for f in files if f not in ban_files]:
            user, fu = _calcsplit(f, F_USER, init_user, sep_char)
            host, fh = _calcsplit(f, F_HOST, init_host, sep_char)
            fn = fu if fu != f else fh
            if user == init_user and host == init_host:
                result.append(PathLink(f"{rpath}{f}", f"{rpath}{fn}"))

    return result


@cli.command()
@click.option('--op', type=click.Choice(['create', 'recreate', 'remove'], case_sensitive=False), default='create', help='operation to execute')
@click.option('--dest', type=click.Path(exists=True, file_okay=False, writable=True), default=Path.home(), help='destination root path')
@click.option('--user', default=getlogin(), help='username to use as reference')
@click.option('--host', default=gethostname(), help='hostname to use as reference')
@click.option('--strict', type=click.BOOL, default=False, help='Halt on command error')
@click.option('--fake', type=click.BOOL, default=False, help='list commands but do not execute them')
@click.option('--ban_dirs', default=BANNED_DIRS, help='list of folder names to ignore')
@click.option('--ban_files', default=BANNED_FILES, help='list of filenames to ignore')
@click.option('--sep_char', default=S_CHAR, help='char to be used as user/host/dirAsLink filename token separator')
@click.argument('src', type=click.Path(exists=True, file_okay=False))
def linker(op, dest, user, host, strict, fake, ban_dirs, ban_files, sep_char, src):

    bdirs = set(ban_dirs.split(','))
    bfiles = set(ban_files.split(','))
    osenv['AG_FAKE'] = '1' if fake else ''
    osenv['AG_STRICT'] = '1' if strict else ''

    cmds = []
    if op in ('remove', 'recreate'):
        cmds.extend([p.getremove(dest) for p in _getpathelems(src, user, host, bdirs, bfiles, sep_char)])
    if op in ('create', 'recreate'):
        cmds.extend([p.getcreate(src, dest) for p in _getpathelems(src, user, host, bdirs, bfiles, sep_char)])

    for cmd in [c for c in cmds if c]:
        click.echo(f"{' '.join(cmd)}")
        if not fake:
            result = call(cmd)
            if strict and result != 0:
                click.echo("Command failed... HALT!", err=True)
                exit(1)


URL_DOTFILES = '~/dotfiles'
CFG_FILE = 'dotfiler.json'
INST_FILE = '_files/init.sh'
UNINST_FILE = '_files/uninst.sh'


class App(object):

    def __init__(self, name):
        self.name = name
        self.ctx = click.get_current_context()
        self.path = f"{self.ctx.params['src']}/{name}"

    def install(self):
        _echo(f"--> Installing {self.name} [{self.path}]...")
        self._invokelinker('create')
        self._execscript(f"{self.path}/{INST_FILE}")
        _echo(f"--> Installed {self.name}...")

    def uninstall(self):
        _echo(f"--> Uninstalling {self.name} [{self.path}]...")
        self._invokelinker('remove')
        self._execscript(f"{self.path}/{UNINST_FILE}")
        _echo(f"--> Uninstalled {self.name}.")

    def _invokelinker(self, operation):
        self.ctx.invoke(
            linker,
            op=operation,
            src=self.path,
            dest=self.ctx.params['dest'],
            user=self.ctx.params['user'],
            host=self.ctx.params['host'],
            strict=self.ctx.params['strict'],
            fake=self.ctx.params['fake'],
        )

    def _execscript(self, script):
        if path.isfile(script):
            _echo(f"---> Executing {script} script...")
            res = call(script)
            if self.ctx.params['strict'] and res != 0:
                _echo("Command failed... HALT!", err=True)
                exit(1)
        else:
            _echo(f"---> Not found {script} script...")



class AppGroup(App):

    def __init__(self, name, apps=[]):
        super(self.__class__, self).__init__(name)
        self.apps = apps

    def install(self):
        _echo(f"-> Installing {self.name} [{self.path}]...")
        for app in self.apps:
            app.install()
        _echo(f"-> Installed {self.name}...")
    
    def uninstall(self):
        _echo(f"-> Uninstalling {self.name} [{self.path}]...")
        for app in self.apps:
            app.uninstall()
        _echo(f"-> Uninstalled {self.name}.")


def _load_apps(src):

    apps = {dir: App(dir) for dir in listdir(src)}

    cfg = {}
    conf_path = f"{src}/{CFG_FILE}"
    if path.isfile(conf_path):
        with open(conf_path) as cfg_file:
            cfg = json.loads(cfg_file.read())

    for group in cfg.keys():
        apps.update({
            app: App(app)
            for app in cfg[group] if app not in apps.keys()
        })

        try:
            gapps = [apps[a] for a in cfg[group]]
        except KeyError as key:
            _echo(f"Error processing {group}: App {key} not found", err=True)
            exit(1)
        apps[group] = AppGroup(group, gapps)

    return apps


@cli.command()
@click.option('--op', type=click.Choice(['install', 'reinstall', 'uninstall'], case_sensitive=False), default='install', help='operation to execute')
@click.option('--src', type=click.Path(exists=True, file_okay=False), default=path.expanduser(URL_DOTFILES), help='source path of dotfiles')
@click.option('--dest', type=click.Path(exists=True, file_okay=False, writable=True), default=Path.home(), help='destination root path')
@click.option('--user', default=getlogin(), help='username to use as reference')
@click.option('--host', default=gethostname(), help='hostname to use as reference')
@click.option('--strict', type=click.BOOL, default=False, help='Halt on command error')
@click.option('--fake', type=click.BOOL, default=False, help='list commands but do not execute them')
@click.argument('apps', nargs=-1)
def dotfiler(op, src, dest, user, host, strict, fake, apps):

    osenv['AG_FAKE'] = '1' if fake else ''
    osenv['AG_STRICT'] = '1' if strict else ''

    cfg_apps = _load_apps(src)
    for app in apps:
      if app in cfg_apps.keys():
        if op in ('uninstall', 'reinstall'):
            cfg_apps[app].uninstall()
        if op in ('install', 'reinstall'):
            cfg_apps[app].install()
      else:
        _echo(f"Application {app} not found!")
        if strict:
          exit(1)

