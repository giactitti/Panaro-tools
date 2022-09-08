#!/usr/bin/python
#coding=utf-8
"""
/***************************************************************************
    LRcvAlgorithm
        begin                : 2021-11
        copyright            : (C) 2021 by Giacomo Titti,
                               Padova, November 2021
        email                : giacomotitti@gmail.com
 ***************************************************************************/

/***************************************************************************
    LRcvAlgorithm
    Copyright (C) 2021 by Giacomo Titti, Padova, November 2021

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
 ***************************************************************************/
"""

__author__ = 'Giacomo Titti'
__date__ = '2021-11-01'
__copyright__ = '(C) 2021 by Giacomo Titti'

import sys

sys.setrecursionlimit(100000)
from qgis.PyQt.QtCore import QCoreApplication,QVariant
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterRasterLayer,
                       QgsMessageLog,
                       Qgis,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterFileDestination,
                       QgsProcessingParameterVectorLayer,
                       QgsVectorLayer,
                       QgsRasterLayer,
                       QgsProject,
                       QgsField,
                       QgsFields,
                       QgsVectorFileWriter,
                       QgsWkbTypes,
                       QgsFeature,
                       QgsGeometry,
                       QgsPointXY,
                       QgsProcessingParameterField,
                       QgsProcessingParameterString,
                       QgsProcessingParameterFolderDestination,
                       QgsProcessingParameterField,
                       QgsProcessingParameterVectorDestination,
                       QgsProcessingContext,
                       QgsPoint
                       )
from qgis.core import *
from qgis.utils import iface
from qgis import processing
from osgeo import gdal,ogr,osr
import numpy as np
import math
import operator
import random
from qgis import *
# ##############################
import csv
from processing.algs.gdal.GdalUtils import GdalUtils
import tempfile


class taneAlgorithm(QgsProcessingAlgorithm):
    INPUT_TZERO = 'INPUT_TZERO'
    INPUT_TUNO = 'INPUT_TUNO'
    FIELD_ID = 'FIELD_ID'
    FIELD_ID1 = 'FIELD_ID1'
    FIELD_TUNO = 'FIELD_TUNO'
    OUTPUT_FOLDER = 'OUTPUT_FOLDER'


    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return taneAlgorithm()

    def name(self):
        return 'Tane'

    def displayName(self):
        return self.tr('01 Tane')

    def group(self):
        return self.tr('Panaro')

    def groupId(self):
        return 'panaro'

    def shortHelpString(self):
        return self.tr("This function join point files")

    def initAlgorithm(self, config=None):

        self.addParameter(QgsProcessingParameterVectorLayer(
            self.INPUT_TZERO, self.tr('Input t0'),
            types=[QgsProcessing.TypeVectorPoint],
            defaultValue=None
            ))
        
        self.addParameter(QgsProcessingParameterField(
            self.FIELD_ID,
            'ID field t0',
            parentLayerParameterName=self.INPUT_TZERO,
            defaultValue=None,
            allowMultiple=False,
            type=QgsProcessingParameterField.Any
        ))
        
        self.addParameter(QgsProcessingParameterVectorLayer(
            self.INPUT_TUNO, self.tr('Input t1'),
            types=[QgsProcessing.TypeVectorPoint],
            defaultValue=None
            ))
        
        self.addParameter(QgsProcessingParameterField(
            self.FIELD_ID1,
            'ID field t1',
            parentLayerParameterName=self.INPUT_TUNO,
            defaultValue=None,
            allowMultiple=False,
            type=QgsProcessingParameterField.Any
        ))
        
        self.addParameter(QgsProcessingParameterField(
            self.FIELD_TUNO,
            't1 field',
            parentLayerParameterName=self.INPUT_TUNO,
            defaultValue=None,
            allowMultiple=True,
            type=QgsProcessingParameterField.Any
        ))
        
        self.addParameter(QgsProcessingParameterFolderDestination(
            self.OUTPUT_FOLDER,
            'Outputs folder destination',
            defaultValue=None,
            createByDefault = True
        ))

    def processAlgorithm(self, parameters, context, feedback):
        self.f=tempfile.gettempdir()
        feedback = QgsProcessingMultiStepFeedback(1, feedback)
        results = {}
        outputs = {}

        parameters['tzero'] = self.parameterAsVectorLayer(parameters, self.INPUT_TZERO, context).source()
        if parameters['tzero'] is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT_TZERO))

        parameters['tuno'] = self.parameterAsVectorLayer(parameters, self.INPUT_TUNO, context).source()
        if parameters['tuno'] is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT_TUNO))

        parameters['id'] = self.parameterAsFields(parameters, self.FIELD_ID, context)
        if parameters['id'] is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.FIELD_ID))
        
        parameters['id_tuno'] = self.parameterAsFields(parameters, self.FIELD_ID1, context)
        if parameters['id_tuno'] is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.FIELD_ID1))
        
        parameters['field_tuno'] = self.parameterAsFields(parameters, self.FIELD_TUNO, context)
        if parameters['field_tuno'] is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.FIELD_TUNO))

        parameters['folder'] = self.parameterAsString(parameters, self.OUTPUT_FOLDER, context)
        if parameters['folder'] is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.OUTPUT_FOLDER))



        alg_params = {
            'tzero': parameters['tzero'],
            'folder':parameters['folder']
        }
        outputs['outlayer']=self.copylayer(alg_params)
        
        
        alg_params = {
            'tuno': parameters['tuno'],
            'id' : parameters['id'],
            'field_tuno':parameters['field_tuno'],
            'outlayer':outputs['outlayer']
        }
        outputs['layers'],outputs['crs']=self.union(alg_params)

        alg_params = {
            'tzero': parameters['tzero'],
            'tuno': parameters['tuno'],
            'id_tzero' : parameters['id'],
            'id_tuno':parameters['id_tuno'],
            'Output':parameters['folder']+'/buffer_all.shp',
            'radious': [50,100]
        }
        outputs['outlayer']=self.loop_buffer(alg_params,context,feedback)

 
        # alg_params = {
        #     'CRS': outputs['crs'],
        #     'LAYERS': outputs['layers'],
        #     'OUTPUT': parameters['folder']+'merged_vectors.gpkg'
        # }

        
        #QgsProject.instance().addMapLayer(QgsVectorLayer(outputs['outlayer'], '', 'ogr'))        

        #context.layerToLoadOnCompletionDetails(outputs['outlayer'])

        # alg_params = {
        #     'layer':outputs['outlayer']
        # }
        # self.addmap(alg_params)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        results['Output'] = outputs['outlayer']['OUTPUT']
        return results

    
    def copylayer(self,parameters):
        from qgis.PyQt.QtCore import QVariant
        layerFields = QgsFields()
        layer_t0 = QgsVectorLayer(parameters['tzero'], '', 'ogr')
        for field in layer_t0.fields():
            layerFields.append(field)
        

        writer = QgsVectorFileWriter(parameters['folder']+'/tane_all.shp', 'UTF-8', layerFields, QgsWkbTypes.Point, layer_t0.crs(), 'ESRI Shapefile')

        for feature in layer_t0.getFeatures():
            writer.addFeature(feature)

        del writer
        return(parameters['folder']+'/tane_all.shp')

    def union(self,parameters):
        layer_t1 = QgsVectorLayer(parameters['tuno'], '', 'ogr')
        layer_out = QgsVectorLayer(parameters['outlayer'], '', 'ogr')
        crs=layer_out.crs()

        index=[]
        for feature in layer_out.getFeatures():
            index.append(feature[parameters['id'][0]])
        max_id=max(index)
        
        id=max_id

        for feature in layer_t1.getFeatures():
            feat = QgsFeature(layer_out.fields())
            for field in parameters['field_tuno']:
                feat.setAttribute(field, feature[field])
            feat.setGeometry(feature.geometry())
            id+=1
            feat[parameters['id'][0]]= id

            (res, outFeats) = layer_out.dataProvider().addFeatures([feat])
        layers=[layer_out,layer_t1]
        return(layers,crs)


    def loop_buffer(self,parameters,context,feedback):
        
        count=0
        for rad in parameters['radious']:
            outputs={}
            # Buffer
            alg_params = {
                'DISSOLVE': False,
                'DISTANCE': rad,
                'END_CAP_STYLE': 0,
                'INPUT': parameters['tzero'],
                'JOIN_STYLE': 0,
                'MITER_LIMIT': 2,
                'SEGMENTS': 5,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['Buffer'+str(rad)] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            # Join attributes by location
            alg_params = {
                'DISCARD_NONMATCHING': False,
                'INPUT': outputs['Buffer'+str(rad)]['OUTPUT'],
                'JOIN': parameters['tuno'],
                'JOIN_FIELDS': parameters['id_tuno'],
                'METHOD': 0,
                'PREDICATE': [1],
                'PREFIX': str(rad)+'m_',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['JoinAttributesByLocation'+str(rad)] = processing.run('native:joinattributesbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            #Join attributes by field value
            print(parameters['id_tzero'])
            alg_params = {
                'DISCARD_NONMATCHING': False,
                'FIELD': parameters['id_tzero'][0],
                'FIELDS_TO_COPY': [str(rad)+'m_'+parameters['id_tzero'][0]],
                'FIELD_2': parameters['id_tzero'][0],
                'INPUT': parameters['tzero'],
                'INPUT_2': outputs['JoinAttributesByLocation'+str(rad)]['OUTPUT'],
                'METHOD': 1,
                'PREFIX': '',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['JoinAttributesByFieldValue'+str(rad)] = processing.run('native:joinattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
                # Join attributes by field value ultimo

            if count==0:
                primo_out=outputs['JoinAttributesByFieldValue'+str(rad)]
            else:
                alg_params = {
                    'DISCARD_NONMATCHING': False,
                    'FIELD': parameters['id_tzero'][0],
                    'FIELDS_TO_COPY': [str(rad)+'m_'+parameters['id_tzero'][0]],
                    'FIELD_2': parameters['id_tzero'][0],
                    'INPUT': primo_out['OUTPUT'],
                    'INPUT_2': outputs['JoinAttributesByFieldValue'+str(rad)]['OUTPUT'],
                    'METHOD': 1,
                    'PREFIX': '',
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }
                if count==len(parameters['radious'])-1:
                    alg_params['OUTPUT']=parameters['Output']
                outputs['JoinAttributesByFieldValueUltimo'+str(rad)] = processing.run('native:joinattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
            count+=1
            
        return(outputs['JoinAttributesByFieldValueUltimo'+str(rad)])

    def save(self,parameters):

        df=parameters['df']
        nomi=list(df.head())
        fields = QgsFields()

        layer=QgsVectorLayer(parameters['tzero'], '', 'ogr')

        for field in layer.fields():
            type=field.typeName()
            print(type)
            fields.append(QgsField(field.name(), type))

        transform_context = QgsProject.instance().transformContext()
        save_options = QgsVectorFileWriter.SaveVectorOptions()
        save_options.driverName = 'GPKG'
        save_options.fileEncoding = 'UTF-8'
        writer = QgsVectorFileWriter.create(
          parameters['folder']+'/out.gpkg',
          fields,
          QgsWkbTypes.Polygon,
          parameters['crs'],
          transform_context,
          save_options
        )

        if writer.hasError() != QgsVectorFileWriter.NoError:
            print("Error when creating shapefile: ",  writer.errorMessage())
        for i, row in df.iterrows():
            fet = QgsFeature()
            fet.setGeometry(QgsGeometry.fromWkt(row['geom']))
            fet.setAttributes(list(map(float,list(df.loc[ i, df.columns != 'geom']))))
            writer.addFeature(fet)

        del writer
        return parameters['folder']+'/out.gpkg'

    def addmap(self,parameters):
        context=parameters()
        fileName = parameters['layer']
        layer = QgsVectorLayer(fileName,"train","ogr")
        subLayers =layer.dataProvider().subLayers()

        for subLayer in subLayers:
            name = subLayer.split('!!::!!')[1]
            print(name,'name')
            uri = "%s|layername=%s" % (fileName, name,)
            print(uri,'uri')
            sub_vlayer = QgsVectorLayer(uri, name, 'ogr')
            if not sub_vlayer.isValid():
                print('layer failed to load')
            context.temporaryLayerStore().addMapLayer(sub_vlayer)
            context.addLayerToLoadOnCompletion(sub_vlayer.id(), QgsProcessingContext.LayerDetails('layer', context.project(),'LAYER'))



        
