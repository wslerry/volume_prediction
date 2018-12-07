# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CanopyHeightModel
                                 A QGIS plugin
 This plugins will generate CHM from grid data
                             -------------------
        begin                : 2018-11-30
        copyright            : (C) 2018 by Lerry William
        email                : wslerry2@hotmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load CanopyHeightModel class from file CanopyHeightModel.

    :param iface: A QGIS interface instance.
    :type iface: QgisInterface
    """
    #
    from .canopy_height_model import CanopyHeightModel
    return CanopyHeightModel(iface)
