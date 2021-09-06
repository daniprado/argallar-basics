from os import path, listdir
from os import environ as osenv

from pynvim import attach
import click

DEFAULT_SOCKET_PATH = '/tmp'


@click.command()
@click.option('--sock', type=click.Path(exists=True, file_okay=False), help='path where scoket files are')
@click.argument('cmd')
def cli(sock, cmd):
    socket_path = sock if sock else osenv.get('XDG_TEMP_HOME', DEFAULT_SOCKET_PATH)
    for file in listdir(path.expanduser(socket_path)):
        if file.startswith('nvimsocket_'):
            nvim = attach('socket', path=path.join(socket_path, file))
            nvim.command(cmd)

