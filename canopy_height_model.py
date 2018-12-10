# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CanopyHeightModel
                                 A QGIS plugin
 This plugins will generate CHM from grid data
                              -------------------
        begin                : 2018-11-30
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Lerry William
        email                : wslerry2@hotmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from PyQt4.QtCore import *  # QSettings, QTranslator, qVersion, QCoreApplication, QFileInfo
from PyQt4.QtGui import *  # QAction, QIcon, QFileDialog
from qgis.core import *  # QgsRasterLayer, QgsMapLayerRegistry
from qgis.gui import *  # QgsMapLayerProxyModel , QgsDoubleSpinBox
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from canopy_height_model_dialog import CanopyHeightModelDialog
import os.path
from osgeo import gdal
import numpy as np


class CanopyHeightModel:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'CanopyHeightModel_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = CanopyHeightModelDialog()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Canopy Height Model')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'CanopyHeightModel')
        self.toolbar.setObjectName(u'CanopyHeightModel')

        self.dlg.pushButton.clicked.connect(self.save_chm)
        self.dlg.pushButton_2.clicked.connect(self.save_volume)

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('CanopyHeightModel', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ":/plugins/CanopyHeightModel/icons/icon.png"
        self.add_action(
            icon_path,
            text=self.tr(u'CHM'),
            callback=self.run,
            parent=self.iface.mainWindow())

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Canopy Height Model'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def save_chm(self):
        file_name = QFileDialog.getSaveFileName(self.dlg, "Select output file ", "", 'GeoTiff (*.tif *.tiff)')
        self.dlg.lineEdit.setText(file_name)
        if len(file_name) is 0:
            return 0

    def save_volume(self):
        file_name = QFileDialog.getSaveFileName(self.dlg, "Select output file ", "", 'GeoTiff (*.tif *.tiff)')
        self.dlg.lineEdit_2.setText(file_name)
        if len(file_name) is 0:
            return 0

    def run(self):
        """Run method that performs all the real work"""
        self.dlg.mMapLayerComboBox1.clear()
        self.dlg.mMapLayerComboBox2.clear()
        self.dlg.lineEdit.clear()
        self.dlg.lineEdit_2.clear()

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            layer = QgsMapLayerComboBox()
            layer.setFilters(QgsMapLayerProxyModel.RasterLayer)
            dsm_path = self.dlg.mMapLayerComboBox1.currentLayer().source()
            if len(dsm_path) is 0:
                return
            dtm_path = self.dlg.mMapLayerComboBox2.currentLayer().source()
            if len(dtm_path) is 0:
                return

            dsm_data = gdal.Open(dsm_path)
            dsm_band = dsm_data.GetRasterBand(1)
            array_dsm = dsm_band.ReadAsArray()
            cols = array_dsm.shape[1]
            rows = array_dsm.shape[0]
            # dsm = dsm_data.ReadAsArray()
            dsm = np.array(array_dsm, dtype=float)

            # size_x = dsm_data.RasterXSize
            # size_y = dsm_data.RasterYSize
            projection = dsm_data.GetProjection()
            geo_ref = dsm_data.GetGeoTransform()

            dtm_data = gdal.Open(dtm_path)
            dtm_band = dtm_data.GetRasterBand(1)
            array_dtm = dtm_band.ReadAsArray()
            # dtm = dtm_data.ReadAsArray()
            dtm = np.array(array_dtm, dtype=float)

            min_height = self.dlg.doubleSpinBox.value()

            # Normalize CHM
            chm = ((((dsm - dtm) / (dsm + dtm)) * dsm) > min_height) * (((dsm - dtm) / (dsm + dtm)) * dsm)

            # predict DBH
            dbh = 9.91242 + (0.62590 * chm)

            # predict volume
            volume = np.exp(-10.070491) * ((dbh ** 2) * chm) ** 0.972005

            # new chm raster
            chm_file_name = self.dlg.lineEdit.text()
            vol_file_name = self.dlg.lineEdit_2.text()

            driver = gdal.GetDriverByName('GTiff')
            output_chm = driver.Create(chm_file_name, cols, rows, 1, gdal.GDT_Float32)
            output_chm.GetRasterBand(1).WriteArray(chm)
            output_chm.SetProjection(projection)
            output_chm.SetGeoTransform(geo_ref)
            output_chm.FlushCache()
            output_chm = None

            output_vol = driver.Create(vol_file_name, cols, rows, 1, gdal.GDT_Float32)
            output_vol.GetRasterBand(1).WriteArray(volume)
            output_vol.SetProjection(projection)
            output_vol.SetGeoTransform(geo_ref)
            output_vol.FlushCache()
            output_vol = None

            # add result to canvas
            if self.dlg.checkBox.isChecked():
                file_info1 = QFileInfo(chm_file_name)
                base_name1 = file_info1.baseName()
                new_layer1 = QgsRasterLayer(chm_file_name, base_name1)
                QgsMapLayerRegistry.instance().addMapLayer(new_layer1)

            if self.dlg.checkBox_2.isChecked():
                file_info2 = QFileInfo(vol_file_name)
                base_name2 = file_info2.baseName()
                new_layer2 = QgsRasterLayer(vol_file_name, base_name2)
                QgsMapLayerRegistry.instance().addMapLayer(new_layer2)
