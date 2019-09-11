#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created on 5/8/19 by Pat Daburu
"""
.. currentmodule:: shapeup.distance
.. moduleauthor:: Pat Daburu <pat@daburu.net>
This module deals with linear distance measurements.
"""
from enum import Enum
from typing import Dict


class Units(Enum):
    """
    These are common distance units.
    """
    METERS = 'meters'  #: meters
    KILOMETERS = 'kilometers'  #: kilometers


_meter_conversions: Dict[Units, float] = {
    Units.METERS: 1.0,
    Units.KILOMETERS: 1000.0
}  #: conversion factors from meters to other linear distance units


def meters(n: float, units: Units) -> float:
    """
    Convert a linear distance to its equivalent in meters.
    :param n: the quantity
    :param units: the units in which the distance is expressed
    :return: the equivalent quantity in meters
    .. seealso::
        :py:class:`Units`
    """
    return n/_meter_conversions[units]
