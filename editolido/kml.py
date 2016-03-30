# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from collections import OrderedDict
import os

from editolido.constants import PINS, GOOGLE_ICONS, PIN_NONE

default_linestyle = """
    <Style id='{0}'>
        <LineStyle>
            <width>3</width>
            <color>{{{0}_color}}</color>
        </LineStyle>
    </Style>
"""
default_iconstyle="""
    <Style id='{0}'>
        <IconStyle>
            <Icon>
                <href><![CDATA[{1}]]></href>
            </Icon>
            <hotSpot x="0.5"  y="0.0" xunits="fraction" yunits="fraction"/>
        </IconStyle>
    </Style>
"""

class KMLGenerator(object):
    def __init__(self, template=None, point_template=None, line_template=None,
                 folder_template=None, style_template=default_linestyle,
                 icon_template=default_iconstyle):
        datadir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'data')
        self.template = template
        if template is None:
            with open(os.path.join(datadir, 'mapsme_template.kml')) as f:
                self.template = f.read().decode()
        self.point_template = point_template
        if point_template is None:
            with open(os.path.join(datadir, 'mapsme_point_tpl.kml')) as f:
                self.point_template = f.read().decode()
        self.line_template = line_template
        if line_template is None:
            with open(os.path.join(datadir, 'mapsme_line_tpl.kml')) as f:
                self.line_template = f.read().decode()
        self.folder_template = folder_template
        if folder_template is None:
            with open(os.path.join(datadir, 'mapsme_folder_tpl.kml')) as f:
                self.folder_template = f.read().decode()
        self.style_template = style_template
        self.icon_template = icon_template
        self.folders = OrderedDict()
        self.styles = OrderedDict()

    @staticmethod
    def escape(text):
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace("&", "&amp;")
        text = text.replace("\"", "&quot;")
        return text

    def add_folder(self, name, pin=None):
        self.folders[name] = []
        style = self.style_template.format(name)
        if pin is not None and pin != PIN_NONE:
            style += self.icon_template.format(
                PINS[pin][1:], GOOGLE_ICONS[pin])
        self.styles[name] = style

    def add_folders(self, *values):
        for value in values:
            try:
                name, pin = value
            except ValueError:
                name = value
                pin = PIN_NONE
            self.add_folder(name, pin)

    @staticmethod
    def _update_kwargs(folder, kwargs):
        """
        Apply style value based on context
        - if style is not set, uses folder name
        - if style is integer, replace with the style's name
        :param folder: str
        :param kwargs: list
        """
        style = kwargs.get('style', None)
        if style is None:
            kwargs['style'] = '#' + folder
        elif isinstance(style, (long, int)):
            kwargs['style'] = PINS[style]

    def add_line(self, folder, route, **kwargs):
        """
        Add a route as a LineString in the .kml
        :param folder: folder name
        :param route: Route
        :param kwargs: optional args passed to the renderer
        """
        self._update_kwargs(folder, kwargs)
        coordinates = []
        for p in route:
            coordinates.append(
                "{lng:.6f},{lat:.6f}".format(lat=p.latitude, lng=p.longitude))
        variables = dict(
            name=route.name or '',
            description=route.description or '')
        variables.update(kwargs)
        self.folders[folder].append(self.line_template.format(
            coordinates=' '.join(coordinates),
            **variables))

    def add_points(self, folder, route, excluded=None, **kwargs):
        """
        Add a route as a Points in the .kml
        :param folder: folder name
        :param route: Route
        :param excluded: list of GeoPoint to exclude from rendering
        :param kwargs: optional args passed to the renderer
        """
        self._update_kwargs(folder, kwargs)
        excluded = excluded or []
        for geopoint in route:
            if geopoint not in excluded:
                self.add_point(folder, geopoint, **kwargs)

    def add_point(self, folder, geopoint, **kwargs):
        """
        Add a GeoPoint in the .kml
        :param folder: folder name
        :param geopoint: GeoPoint
        :param kwargs: optional args passed to the renderer
        """
        self._update_kwargs(folder, kwargs)
        coordinates = "{lng:.6f},{lat:.6f}".format(
            lat=geopoint.latitude, lng=geopoint.longitude)
        variables = dict(
            name=geopoint.name or '',
            description=geopoint.description or '')
        variables.update(kwargs)
        self.folders[folder].append(self.point_template.format(
            coordinates=coordinates,
            **variables))

    def render(self, **kwargs):
        """
        Render the full .kml
        :param kwargs:
        :return: unicode
        """
        return self.template.format(
            styles=''.join(self.styles.values()).format(**kwargs),
            folders=self.render_folders(),
            **kwargs
        )

    def render_folder(self, folder):
        """
        Render a folder content
        :param folder:
        :return: str
        """
        return self.folder_template.format(
            name=folder,
            open=1,
            content='\n'.join(self.folders[folder]),
        )

    def render_folders(self):
        """
        Render all folders
        :return: str
        """
        return '\n'.join(
            [self.render_folder(folder) for folder in self.folders])
