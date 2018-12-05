# -*- coding: utf-8 -*-
"""
Historikk-spørringer mot visveginfo-tjenesten for et punkt på vegnettet. 
Oppsummerer tidsutviklingen 

Created on Fri Nov 30 13:52:56 2018

@author: Jan Kr. Jensen 
"""

import requests
import xmltodict
import pandas as pd


def veglenkehistorikk( veglenkeid, veglenkeposisjon): 
    """
    Tidsutvikling, vegreferanse for veglenkeID og posisjon på vegnettet
    
    
    """

    url = 'http://visveginfo-static.opentns.org/RoadInfoService/GetRoadReferenceHistoryForNVDBReference'
    params = { 'reflinkOID' : veglenkeid, 
              'relLen' : veglenkeposisjon }

    r = requests.get( url, params)
    data = xmltodict.parse( r.text )
    mydf = pd.DataFrame.from_records( data['ArrayOfRoadPointReferenceWithTimePeriod']['RoadPointReferenceWithTimePeriod'] )
    mydf.sort_values( 'ValidFrom', inplace=True)
    mydf.rename(columns={ 'County' : 'Fylke', 
                         'LaneCode' : 'Felt', 
                         'Municipality' : 'kommune', 
                         'ReflinkOID' : 'veglenkeId', 
                         'RoadCategory' : 'vegkategori',
                         'RoadNumber' : 'vegnr', 
                         'RoadNumberSegment' : 'hp' , 
                         'RoadStatus' : 'status', 
                         'TextualRoadReference' : 'vegref',
                         'Measure' : 'veglenkeposisjon', 
                         'RoadNetPosition': 'geometri', 
                         'RoadNumberSegmentDistance' : 'm' ,
                         'RoadnetHeading' : 'retning', 
                         'ValidFrom' : 'fraDato', 
                         'ValidTo' : 'tilDato' }, inplace=True)
    
    mydf['fraDato' ] = mydf['fraDato'].str.replace('T00:00:00', '' )
    mydf['tilDato' ] = mydf['tilDato'].str.replace('T00:00:00', '' )
    
    print( mydf[['Fylke', 'kommune', 'vegkategori', 'status', 'vegnr', 'hp', 'm', 'fraDato', 'tilDato']] )
    return mydf
    