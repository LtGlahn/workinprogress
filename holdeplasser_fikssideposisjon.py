# -*- coding: utf-8 -*-
"""
Created on Wed Oct 10 09:41:16 2018

@author: jajens
"""

import json
from copy import deepcopy
import datetime
from time import sleep

import ipdb
import fiona
import pandas as pd

import skrivnvdb
import nvdbapi

#%% 
hlp = pd.read_excel( '../data/fikssidepos/DuplikatHoldeplass_v0.xlsx')

#%% 

for i in hlp.index: 
    p = nvdbapi.nvdbFagObjekt( nvdbapi.finnid( hlp.get_value(i, 'FID1'), kunfagdata=True)) 
    print( p.id, p.egenskapverdi(11309 ), p.egenskapverdi( 11310), p.egenskapverdi(10885))

#%% 

endringssett =  {
      "delvisOppdater": {
            "vegObjekter": []
           },
     "effektDato": datetime.datetime.today().strftime('%Y-%m-%d'),
     "datakatalogversjon": "2.14"
 }

for i in hlp.index: 
    konfliktside = hlp.get_value( i, 'SPOS2')
    if konfliktside == 1: 
        rettside = 'H'
        skip = False
    elif konfliktside == 2: 
        rettside = 'V'
        skip = False
    else: 
        print( 'FEIL')
        skip = True
    
    if not skip: 
        nvdbid = hlp.get_value( i, 'FID1')
        b = nvdbapi.finnid( nvdbid, kunfagdata=True )
        linje = []
        
        for veg in b['lokasjon']['stedfestinger']: 
            linje.append( { 'fra' :  round( veg['fra_posisjon'], 8 ), 
                            'til' : round( veg['til_posisjon'], 8 ),
                            'sidePosisjon' : rettside, 
                            'lenkeId' : int( veg['veglenkeid']) 
                            })
        

        nyttobj = { "typeId": int( 487),
        "nvdbId": int( nvdbid),
       "versjon" : b['metadata']['versjon'],
        "lokasjon": {
          "linje": linje, 
        "operasjon" : "oppdater"
        }
      }
    endringssett['delvisOppdater']['vegObjekter'].append( nyttobj)


    
# "linje": [
#            {
#              "fra": 0.65422,
#              "til": 0.65715,
#              "sidePosisjon": "H",
#              "lenkeId": 521439
#            }
#%% 
miljo = 'utv'
# skriveapi = skrivnvdb.apiskrivforbindelse(miljo=miljo)
# skriv = skrivnvdb.endringssett(endringssett )
skriv.data = endringssett
# skriv.lag_forbindelse( apiskriv=skriveapi)
# skriv.forbindelse.login( username='jajens', pw='skr.vNvdb3mye', miljo=miljo)

#%% 
skriv.registrer()


#%% SkrivPROD
skrivPROD = skrivnvdb.endringssett(endringssett)
skrivPROD.lag_forbindelse()
skrivPROD.forbindelse.login( miljo='prod', username='jajens', pw='***')

