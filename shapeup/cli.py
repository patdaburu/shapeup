#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
.. currentmodule:: shapeup.cli
.. moduleauthor:: Pat Daburu <pat@daburu.net>

This is the entry point for the command-line interface (CLI) application.  It
can be used as a handy facility for running the task from a command line.

.. note::

    To learn more about Click visit the
    `project website <http://click.pocoo.org/5/>`_.  There is also a very
    helpful `tutorial video <https://www.youtube.com/watch?v=kNke39OZ2k0>`_.

    To learn more about running Luigi, visit the Luigi project's
    `Read-The-Docs <http://luigi.readthedocs.io/en/stable/>`_ page.
"""
import logging
from pathlib import Path
import click
import matplotlib.pyplot as plt
import mplleaflet
from .__init__ import __version__
from .geometry import SrPoint
from .sr import Sr

LOGGING_LEVELS = {
    0: logging.NOTSET,
    1: logging.ERROR,
    2: logging.WARN,
    3: logging.INFO,
    4: logging.DEBUG
}  #: a mapping of `verbose` option counts to logging levels


class Info(object):
    """
    This is an information object that can be used to pass data between CLI functions.
    """
    def __init__(self):  # Note that this object must have an empty constructor.
        self.verbose: int = 0


# pass_info is a decorator for functions that pass 'Info' objects.
#: pylint: disable=invalid-name
pass_info = click.make_pass_decorator(
    Info,
    ensure=True
)


# Change the options to below to suit the actual options for your task (or
# tasks).
@click.group()
@click.option('--verbose', '-v', count=True, help="Enable verbose output.")
@pass_info
def cli(info: Info,
        verbose: int):
    """
    Run shapeup.
    """
    # Use the verbosity count to determine the logging level...
    if verbose > 0:
        logging.basicConfig(
            level=LOGGING_LEVELS[verbose]
            if verbose in LOGGING_LEVELS
            else logging.DEBUG
        )
        click.echo(
            click.style(
                f'Verbose logging is enabled. '
                f'(LEVEL={logging.getLogger().getEffectiveLevel()})',
                fg='yellow'
            )
        )
    info.verbose = verbose

@cli.command()
@pass_info
def hello(_: Info):
    """
    Say 'hello' to the nice people.
    """
    click.echo(f"shapeup says 'hello'")


@cli.command()
@pass_info
@click.option('-x', help="the X coordinate", type=click.FLOAT, required=True)
@click.option('-y', help='the Y coordinate', type=click.FLOAT, required=True)
@click.option('--srid', '-s', help='the SRID', type=click.INT, required=True)
def plotxy(info, x, y, srid):

    # https://github.com/jwass/mplleaflet
    # https://matplotlib.org/3.1.0/api/_as_gen/matplotlib.pyplot.plot.html

    sr = Sr(srid=srid)
    point = SrPoint.from_coords(x=x, y=y, sr=sr)
    wgs84 = point.as_wgs84()

    plt.plot(
        wgs84.x,
        wgs84.y,
        color='red',
        marker='o',
        markersize=14
    )
    # Use leaflet to show it.
    mplleaflet.show()


@cli.command()
def version():
    """
    Get the library version.
    """
    click.echo(click.style(f'{__version__}', bold=True))
