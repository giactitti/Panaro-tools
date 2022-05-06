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

#import geopandas as gd

# pd.set_option('display.max_columns', 20)
# #pd.set_option('display.max_rows', 20)
# from IPython.display import display
import tempfile


class taneAlgorithm(QgsProcessingAlgorithm):
    INPUT_TZERO = 'INPUT_TZERO'
    INPUT_TUNO = 'INPUT_TUNO'
    FIELD_ID = 'FIELD_ID'
    FIELD_TUNO = 'FIELD_TUNO'
    #STRING1 = 'field2'
    #STRING2 = 'id'
    #INPUT1 = 'Slope'
    #EXTENT = 'Extension'
    #NUMBER = 'testN'
    #NUMBER1 = 'minSlopeAcceptable'
    OUTPUT_FOLDER = 'OUTPUT_FOLDER'
    #OUTPUT1 = 'OUTPUT1'
    #OUTPUT2 = 'OUTPUT2'
    #OUTPUT3 = 'OUTPUT3'

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
            'ID field',
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
        
        parameters['field_tuno'] = self.parameterAsFields(parameters, self.FIELD_TUNO, context)
        if parameters['field_tuno'] is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.FIELD_TUNO))

        parameters['folder'] = self.parameterAsString(parameters, self.OUTPUT_FOLDER, context)
        if parameters['folder'] is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.OUTPUT_FOLDER))

        alg_params = {
            'tzero': parameters['tzero'],
            'tuno': parameters['tuno'],
            'id' : parameters['id'],
            'field_tuno':parameters['field_tuno']
        }
        outputs['layers'],outputs['crs']=self.load(alg_params)


        alg_params = {
            'CRS': outputs['crs'],
            'LAYERS': outputs['layers'],
            'OUTPUT': parameters['folder']+'merged_vectors.gpkg'
        }
        #outputs['out'] = processing.run('native:mergevectorlayers', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
 
        #print(outputs['out'])
        # alg_params = {
        #         'tzero': parameters['tzero'],
        #         'df': outputs['df'],
        #         'crs': outputs['crs'],
        #         'folder':parameters['folder']
        #     }
        # parameters['out']=self.save(alg_params)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        results['out'] = []

        # fileName = outputs['out']['OUTPUT']
        # layer1 = QgsVectorLayer(fileName,"test","ogr")
        # subLayers =layer1.dataProvider().subLayers()

        # for subLayer in subLayers:
        #     name = subLayer.split('!!::!!')[1]
        #     print(name,'name')
        #     uri = "%s|layername=%s" % (fileName, name,)
        #     print(uri,'uri')
        #     # Create layer
        #     sub_vlayer = QgsVectorLayer(uri, name, 'ogr')
        #     if not sub_vlayer.isValid():
        #         print('layer failed to load')
        #     # Add layer to map
        #     context.temporaryLayerStore().addMapLayer(sub_vlayer)
        #     context.addLayerToLoadOnCompletion(sub_vlayer.id(), QgsProcessingContext.LayerDetails('test', context.project(),'LAYER1'))


        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        return results

    def load(self,parameters):
        
        layer_t0 = QgsVectorLayer(parameters['tzero'], '', 'ogr')
        
    #     features = layer_t0.getFeatures()
    #     index=[]
    #     for feature in features:
    #         index.append(parameters['id'])
    #     max_id=max(index)

    #     df_0,nomi,crs=self.vector2df(layer_t0,parameters['id'],max_id)

    #     #############################

        layer_t1 = QgsVectorLayer(parameters['tuno'], '', 'ogr')
    #     df_1,nomi_1,crs_1=self.vector2df(layer_t1,id,max_id,parameters['field_tuno'])


    #     df = pd.concat([df_0,df_1], sort=False)

    #     return df,crs



    # def vector2df(self,layer,id,max_id,fields=None):

    #     crs=layer.crs()
    #     campi=[]
    #     for field in layer.fields():
    #         campi.append(field.name())
    #     campi.append('geom')
    #     gdp=pd.DataFrame(columns=campi,dtype=float)
    #     features = layer.getFeatures()
    #     count=0
    #     feat=[]
    #     for feature in features:
    #         attr=feature.attributes()
    #         attr=[str(x) for x in attr]
    #         print(attr,'attr')
    #         geom = feature.geometry()
    #         feat=attr+[str(geom.asWkt())]
    #         gdp.loc[len(gdp)] = feat
    #         count=+ 1
    #     print(gdp.to_string())
    #     # print(gdp.astype('string'))
    #     print(self.f+'/file.csv')
    #     # print(ciao)
    #     gdp.to_csv(self.f+'/file.csv',header=True, index=False, encoding='utf-8')
    #     del gdp

    #     gdp=pd.read_csv(self.f+'/file.csv')
    #     if fields == None:
    #         df=gdp
    #     else:
    #         df=gdp[fields]
    #         gdp['IDD']=max_id+np.arange(1,len(gdp.iloc[:,0])+1)
    #         df[id]=gdp['IDD']
        
    #     nomi=list(df.head())
        
    #     df['geom']=gdp['geom']

    #     return df,nomi,crs





        

        #new_field = QgsField( 'ID', QVariant.Int)
        #layer_t1.dataProvider().addAttributes([new_field])
        #layer_t1.updateFields()

        #idx=layer_t0.fieldNameIndex(parameters['ID'])
        #max_id=layer_t0.maximumValue(idx)

        # attr1=layer_t1.fields().names()
        # print(attr1,'names t1')
        # print(parameters['id'],'id')
        # if not parameters['id'] in attr1:
        #     new_field = QgsField(parameters['id'][0], QVariant.Int)
        #     layer_t1.dataProvider().addAttributes([new_field])
        #     layer_t1.updateFields()


        #attr0=layer_t1.getFeature(1).attributes()


        # features = layer_t0.getFeatures()
        # print(features)

        crs=layer_t0.crs()

        index=[]
        for feature in layer_t0.getFeatures():
            index.append(feature[parameters['id'][0]])
        max_id=max(index)


        # features_t1 = layer_t1.getFeatures()
        # print(features_t1)
        
        id=max_id

        for feature in layer_t1.getFeatures():
            feat = QgsFeature(layer_t0.fields())
            for field in parameters['field_tuno']:
                feat.setAttribute(field, feature[field])
            feat.setGeometry(feature.geometry())
            id+=1
            feat[parameters['id'][0]]= id

            (res, outFeats) = layer_t0.dataProvider().addFeatures([feat])


        layers=[layer_t0,layer_t1]
        #campi=parameters['id']+parameters['field_tuno']
        #print(id)
        # with edit(layer_t1):
        #     for feature in layer_t1.getFeatures():
        #         #     #attr=feature.attributes()
        #         id+=1
        #         feature[parameters['id'][0]]= 13
        #         layer_t1.updateFeature(feature)
        #     #     print(id,'id')
        #     #     feature[parameters['id'][0]]=id
        #     #     print(feature[parameters['id'][0]],'feat')

        # # with edit(layer_t1):
        # #     feat = next(layer_t1.getFeatures())
        # #     feat[parameters['id'][0]]=3
        # #     layer_t1.updateFeature(feat)
        
        # layer_t1.updateFields()
        # #layer_t1.updateExtents()
        # iface.mapCanvas().refresh()






        # feat = QgsFeature()
        # feat.addAttribute(0,100)
        # feat.setGeometry(QgsGeometry.fromPoint(QgsPoint(123,456)))
        # layer_t0.dataProvider.addFeature(feat)
        # print('ciao')
        
        # layer_t0.updateFields()
        # layer_t0.updateExtents()
        # iface.mapCanvas().refresh()
        return(layers,crs)

        
    
    #def save_base_layer(self,parameters):


    def save(self,parameters):

        #print(parameters['nomi'])
        df=parameters['df']
        nomi=list(df.head())
        # define fields for feature attributes. A QgsFields object is needed
        fields = QgsFields()

        #fields.append(QgsField('ID', QVariant.Int))
        layer=QgsVectorLayer(parameters['tzero'], '', 'ogr')



        for field in layer.fields():
            type=field.typeName()
            print(type)
            fields.append(QgsField(field.name(), type))

        #crs = QgsProject.instance().crs()
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

        # delete the writer to flush features to disk
        del writer
        return parameters['folder']+'/out.gpkg'

    def addmap(self,parameters):
        context=parameters()
        fileName = parameters['trainout']
        layer = QgsVectorLayer(fileName,"train","ogr")
        subLayers =layer.dataProvider().subLayers()

        for subLayer in subLayers:
            name = subLayer.split('!!::!!')[1]
            print(name,'name')
            uri = "%s|layername=%s" % (fileName, name,)
            print(uri,'uri')
            # Create layer
            sub_vlayer = QgsVectorLayer(uri, name, 'ogr')
            if not sub_vlayer.isValid():
                print('layer failed to load')
            # Add layer to map
            context.temporaryLayerStore().addMapLayer(sub_vlayer)
            context.addLayerToLoadOnCompletion(sub_vlayer.id(), QgsProcessingContext.LayerDetails('layer', context.project(),'LAYER'))

            #QgsProject.instance().addMapLayer(sub_vlayer)
            #iface.mapCanvas().refresh()


        # fileName = parameters['out']
        # layer = QgsVectorLayer(fileName,"test","ogr")
        # subLayers =layer.dataProvider().subLayers()
        #
        # for subLayer in subLayers:
        #     name = subLayer.split('!!::!!')[1]
        #     uri = "%s|layername=%s" % (fileName, name,)
        #     # Create layer
        #     sub_vlayer = QgsVectorLayer(uri, name, 'ogr')
        #     if not sub_vlayer.isValid():
        #         print('layer failed to load')
        #     # Add layer to map
        #     QgsProject.instance().addMapLayer(sub_vlayer)
