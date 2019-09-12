#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import pytest
from shapeup import SrGeometry, SrPoint


@pytest.fixture(scope='module', name='wgs84_point')
def wgs84_point_fix() -> SrPoint:
    """
    Get a WGS-84 `SrPoint`.

    :return: the point
    """
    return SrPoint.from_lat_lon(lat=45.553670, lon=-94.142430)


@pytest.mark.parametrize(
    'sr_point',
    [
        SrPoint.from_lat_lon(lat=45.553670, lon=-94.142430),
    ]
)
def test_export_load(sr_point):
    """
    Arrange: Export an `SrPoint` to JSON.
    Act: Load the export data to create a new `SrPoint`.
    Assert: The loaded `SrPoint` is equivalent to the original.

    :param sr_point: an `SrPoint`
    :return:
    """
    exported = sr_point.export()
    exported_json = json.dumps(exported)
    loaded = SrGeometry.load(json.loads(exported_json))
    assert loaded == sr_point
    assert hash(loaded) == hash(sr_point)
