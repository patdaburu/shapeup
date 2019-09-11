#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created on 9/11/19 by Pat Daburu
"""
.. currentmodule:: geometry
.. moduleauthor:: Pat Daburu <pat@daburu.net>

Geometries start here.
"""
import copy
from typing import Any, cast, Mapping, Union
from shapely.geometry import mapping, LineString, Point, Polygon, shape
from shapely.geometry.base import BaseGeometry, BaseMultipartGeometry
from shapely.ops import transform
from ..distance import meters, Units
from ..sr import Sr, WGS_84, utm, transform_fn
from ..types import pycls as cls_, pyfqn
from ..xchg import Exportable


class SrGeometry(Exportable):
    """
    Represents a spatially referenced geometry by combining a
    `Shapely <https://bit.ly/2QovaiU>`_ base geometry with a
    :py:class:`spatial reference <Sr>`.
    """
    __slots__ = ['_base_geometry', '_sr']

    def __init__(
            self,
            base_geometry: Union[BaseGeometry, BaseMultipartGeometry, Mapping],
            sr_: Sr = WGS_84
    ):
        # The base geometry we store is the one passed in at the constructor
        # unless the caller passed us a `Mapping` that isn't a base geometry.
        # In that case we'll try to create a geometry from the mapping.
        self._base_geometry = (
            base_geometry if isinstance(
                base_geometry,
                (BaseGeometry, BaseMultipartGeometry)
            )
            else shape(base_geometry)
        )  #: the base (Shapely) geometry
        self._sr = sr_  #: the spatial reference (SR)

    @property
    def base_geometry(self) -> Union[BaseGeometry, BaseMultipartGeometry]:
        """
        Get the base geometry.
        """
        return self._base_geometry

    @property
    def sr(self) -> Sr:
        """
        Get the spatial reference.
        """
        return self._sr

    @property
    def srid(self) -> int:
        """
        Get the `SRID <https://bit.ly/2vLtVSY>`_ of the spatial reference (SR).
        """
        return self._sr.srid

    def location(self) -> 'SrPoint':
        """
        Get a single point that best represents the location of this geometry
        as a single point.

        :return: the point
        """
        return SrPoint(
            base_geometry=self.base_geometry.centroid,
            sr_=self._sr
        )

    def mapping(self) -> Mapping[str, Any]:
        """
        Get a GeoJSON-like mapping of the base geometry.

        :return: the mapping
        """
        return mapping(self.base_geometry)

    def as_wgs84(self) -> 'SrGeometry':
        """
        Get this geometry as a WGS84 geometry.

        :return:  an equivalent geometry in the WGS-84 coordinate system (or the
            original object if it is already in the WGS-84 coordinate system)

        .. note::

            If the geometry is already in the WGS84 coordinate system, the
            method may return the original object.
        """
        if self._sr == WGS_84:
            return self
        return self.transform(sr_=WGS_84)

    def as_utm(self) -> 'SrGeometry':
        """
        Get this geometry as a UTM geometry.

        :return:  an equivalent geometry in a UTM coordinate system (or the
            original object if it is already in a UTM coordinate system)

        .. note::

            If the geometry is already in a UTM coordinate system, the method
            may return the original object.
        """
        # If the geometry is in WGS-84...
        if self._sr == WGS_84:
            # ... we can get its representative point (which should be defined
            # as latitude and longitude) directly.
            rp: Point = self.base_geometry.representative_point()
        else:
            # Otherwise, we need to transform it to WGS-84...
            wgs84_geom = self.transform(sr_=WGS_84)
            # ...so that we can get a representative point defined by a
            # latitude and a longitude.
            rp: Point = wgs84_geom.base_geometry.representative_point()
        # Get the UTM zone for the latitude and longitude.
        utm_sr = utm(lat=rp.y, lon=rp.x)
        # If the UTM zone matches this geometry's spatial reference (SR)...
        if utm_sr == self._sr:
            return self
        # Transform this geometry's base geometry to the UTM zone.
        return self.transform(sr_=utm_sr)

    def transform(self, sr_: Sr, copy_: bool = True) -> 'SrGeometry':
        """
        Transform this geometry to

        :param sr_: the target spatial reference
        :param copy_: `True` (the default) to make a copy of the geometry if
            the target spatial reference is the same as the current spatial
            reference; when `False` the instance will return itself
        :return: an :py:class:`SrGeometry` in the target spatial reference
        """
        # If the target spatial reference (SR) is this geometry's spatial
        # reference, just return this geometry.
        if sr_ == self._sr:
            return copy.copy(self) if copy_ else self
        # Get the transformation function.
        _transform_fn = transform_fn(from_=self._sr, to=sr_)
        # Perform the transformation to get the new base geometry.
        transformed_geometry = transform(_transform_fn, self._base_geometry)
        # Create the new `SrGeometry` using the transformed base geometry and
        # the spatial reference the caller supplied.
        return SrGeometry(
            base_geometry=transformed_geometry,
            sr_=sr_
        )

    def buffer(
            self,
            n: int or float,
            units: Units = Units.METERS
    ) -> 'SrGeometry':
        """
        Buffer the geometry by `n` meters.

        :param n: the radius
        :param units: the radius distance units
        :return: the buffered geometry
        """
        # Get the geometry in a UTM coordinate system.
        base_utm = self.as_utm()
        # Buffer the base geometry.
        base_utm_buf = base_utm.base_geometry.buffer(meters(n, units))
        # Create a new `SrGeometry` with the buffered base geometry and the
        # UTM spatial reference.
        sr_geom_buf = SrGeometry(
            base_geometry=base_utm_buf,
            sr_=base_utm.sr
        )
        # Transform the buffered `SrGeometry` to the original coordinate system
        # and return it.
        return sr_geom_buf.transform(self._sr)

    def export(self) -> Mapping[str, Any]:
        """
        Export the instance as a mapping of simple types.

        :return: the mapping
        """
        return {
            '__type__': pyfqn(self),
            'base_geometry': mapping(self._base_geometry),
            'sr_': self._sr._asdict()
        }

    @classmethod
    def load(cls, data: Mapping[str, Any]) -> 'SrGeometry' or None:
        """
        Create an instance from a mapping.

        :param data: the data
        :return: the instance
        """
        # If we didn't receive any data...
        if not data:
            # ...then the answer is nothing.
            return None
        try:
            _cls = cls_(data['__type__'])
        except KeyError:
            _cls = cls

        return _cls(
            **{
                'base_geometry': shape(data.get('base_geometry')),
                'sr_': Sr(**data.get('sr_'))
            }
        )

    def __copy__(self):
        return self.__class__(
            base_geometry=copy.deepcopy(self._base_geometry),
            sr_=self._sr
        )

    def __getstate__(self):
        return {
            '_base_geometry': mapping(self._base_geometry),
            '_sr': self._sr
        }

    def __setstate__(self, state):
        self._base_geometry = shape(state.get('_base_geometry'))
        self._sr = state.get('_sr')

    def __eq__(self, other):
        # If the other object is None (or empty), the equality check fails.
        if not other:
            return False
        try:
            # If the spatial references don't match...
            if not self._sr == getattr(other, '_sr'):
                return False  # ... no match!
            # If this object has no base geometry...
            if not self._base_geometry:
                # ...it's only equal if the other object also lacks a base
                # geometry.
                return not getattr(other, '_base_geometry')
            # Otherwise, compare this instance's base geometry to the other's
            # as the final equality test.
            return self._base_geometry.equals(getattr(other, '_base_geometry'))
        except AttributeError:
            # Missing attributes are a clear sign that the other object doesn't
            # equal this one.
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"base_geometry={repr(self.mapping())}, "
            f"sr_={repr(self._sr)})"
        )

    def __str__(self):
        return (
            f"{self.__class__.__name__}(SRID={self._sr.srid})"
            f"@{hex(id(self))}"
        )


class SrPoint(SrGeometry):
    """
    A spatially referenced point geometry.
    """
    def __init__(
            self,
            base_geometry: Union[Point, Mapping],
            sr_: Sr = WGS_84
    ):
        super().__init__(base_geometry=base_geometry, sr_=sr_)

    @property
    def point(self) -> Point:
        """
        Get the base geometry as a `shapely.geometry.Point`.
        """
        return self._base_geometry

    def location(self) -> 'SrPoint':
        """
        Get a single point that best represents the location of this geometry
        as a single point.

        :return: the current instance
        """
        # Return the point in the center of the line.
        return self

    def buffer(
            self,
            n: int or float,
            units: Units = Units.METERS
    ) -> 'SrPolygon':
        """
        Buffer the geometry by `n` meters.

        :param n: the radius
        :param units: the radius distance units
        :return: the buffered geometry
        """
        return cast(SrPolygon, super().buffer(n=n, units=units))

    @classmethod
    def from_lat_lon(cls, lat: float, lon: float):
        """
        Create a point from a latitude and longitude.

        :param lat: the latitude
        :param lon: the longitude
        :return: the point

        .. seealso::

            :py:attr:`shapeup.sr.WGS_84`
        """
        base_geometry = Point(lon, lat)
        return SrPoint(
            base_geometry=base_geometry,
            sr_=WGS_84
        )


class SrPolygon(SrGeometry):
    """
    A spatially referenced polygon geometry.
    """
    def __init__(
            self,
            base_geometry: Union[Polygon, Mapping],
            sr_: Sr = WGS_84
    ):
        super().__init__(base_geometry=base_geometry, sr_=sr_)

    @property
    def polygon(self) -> Polygon:
        """
        Get the base geometry as a `shapely.geometry.Polygon`.
        """
        return self._base_geometry


class SrPolyline(SrGeometry):
    """
    A spatially referenced polyline geometry.
    """
    def __init__(
            self,
            base_geometry: Union[LineString, Mapping],
            sr_: Sr = WGS_84
    ):
        super().__init__(base_geometry=base_geometry, sr_=sr_)

    @property
    def polyline(self) -> LineString:
        """
        Get the base geometry as a `shapely.geometry.Polygon`.
        """
        return self._base_geometry

    def location(self) -> 'SrPoint':
        """
        Get a single point that best represents the location of this geometry
        as a single point.

        :return: the point
        """
        # Return the point in the center of the line.
        return SrPoint(
            base_geometry=self.base_geometry.interpolate(0.5, normalized=True),
            sr_=self._sr
        )


SrLinestring = SrPolyline  #: This is an alias for :py:class:`SrPolyline`
