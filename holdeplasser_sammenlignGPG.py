# -*- coding: utf-8 -*-
"""
Created on Wed Oct 10 09:41:16 2018

@author: jajens
"""


import sys
import os 

if not [ k for k in sys.path if 'nvdbapi' in k]: 
    print( "Legger NVDB api til søkestien")
    # sys.path.append( '../nvdbapi-V2' )
    
    dir_path = os.getcwd().split(sep='\\')
    dir_path[-1] = 'nvdbapi-V2'
    sys.path.append( '/'.join(dir_path ))



import json
from copy import deepcopy
import datetime
from time import sleep

import ipdb
import fiona


import skrivnvdb

def finnskrivelag( endringssett, gpkglayer): 
    
    with open( 'svarteliste.json' ) as f: 
        svarteliste = json.load( f)
    
    for feat in gpkglayer: 
        if 'SKRIV_NSR_QUAY_ID_11310' in feat['properties'] and \
            feat['properties']['SKRIV_NSR_QUAY_ID_11310'] and \
            feat['properties']['vegobjektid'] not in svarteliste: 
                
            prop = feat['properties']
            
            nye_egenskaper = [  { 'typeId' : 11310, 
                                 'verdi' : [ prop['SKRIV_NSR_QUAY_ID_11310'] ], 
                                 'operasjon' : 'oppdater' 
                                 } ]
            
            
            
            if prop['NSR_Stopplace_Navn'] != prop['entur_morstopp_stop_name']:
                nye_egenskaper.append(  { 'typeId' : 10885, 
                                         'verdi' : [prop['entur_morstopp_stop_name']], 
                                         'operasjon' : 'oppdater' 
                                        }  )
    
            if prop['NSR_Stopplace_ID']  != prop['entur_parent_station']: 
                nye_egenskaper.append( { 'typeId' : 11309, 
                                        'verdi' : [prop['entur_parent_station']], 
                                        'operasjon' : 'oppdater' 
                                        })
            
            # print( prop['vegobjektid'], prop['versjonid'], \
            #      nye_egenskaper)
    
            nyttobj = { 'typeId' : 487, 
                       'nvdbId' : prop['vegobjektid'], 
                       'versjon' : prop['versjonid'], 
                        'egenskaper' : nye_egenskaper
                    }
            
            if prop['vegobjektid'] in endringssett: 
                print( prop['vegobjektid'], 'er allere i endringssett!' )
            
            endringssett[prop['vegobjektid']] = { 'endringssett' : {  
                                                      'datakatalogversjon' : '2.14',
                                                      'effektDato': datetime.datetime.today().strftime('%Y-%m-%d'),
                                                      'delvisOppdater': {'vegObjekter': [ nyttobj ] }
                                                    }  
                                                }
                
            
             
    
    return endringssett

if __name__ == '__main__':
    
    
    mydataset = '../data/resultater_Norge_v2 _2018_10_23.gpkg'
    endringssett23 = {}
    
    
    for layername in fiona.listlayers( mydataset): 
        with fiona.open(mydataset, layer=layername ) as src: 
            print( layername, len(src))
            
            # Søker etter egenskapsnavn med ordet SKRIV
            if [k for k in src.schema['properties'] if 'SKRIV' in k]: 
                endringssett23 = finnskrivelag( endringssett23, src)


    mydataset = '../data/resultater_Norge_v2_2018_10_22.gpkg'
    endringssett22 = {}
    
    
    for layername in fiona.listlayers( mydataset): 
        with fiona.open(mydataset, layer=layername ) as src: 
            print( layername, len(src))
            
            # Søker etter egenskapsnavn med ordet SKRIV
            if [k for k in src.schema['properties'] if 'SKRIV' in k]: 
                endringssett22 = finnskrivelag( endringssett22, src)


#%% sammenligner
                
    end23 = list(  endringssett23.keys() )
    end22 = list(  endringssett22.keys() )
    
    intersect = list( set(end22) & set(end23)  )

#%% 
    
    for ii in intersect: 
        if endringssett22[ ii ] != endringssett23[ ii ]: 
            print( ii)