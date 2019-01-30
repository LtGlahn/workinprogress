#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 30 11:42:31 2019

@author: jan
"""

import STARTHER
import nvdbapi 
import skrivnvdb
import datetime
from copy import deepcopy
#%% Endringssett mal 

endring_mal = {
  "delvisOppdater": {
    "vegObjekter": [ ]
  },
  "effektDato": datetime.datetime.today().strftime('%Y-%m-%d'),
  "datakatalogversjon": "2.15"
}

obj_mal =      {
        "typeId": 45,
        "nvdbId": -1,
        "versjon": -1,
        "egenskaper": [] 
        }
eg_mal =  {
            "typeId": -1,
            "verdi": [ ],
            "operasjon": "oppdater"
          }

#%% 

b = nvdbapi.nvdbFagdata( 45)
b.addfilter_egenskap( '9596=10')

enbom = b.nesteNvdbFagObjekt()

endr = deepcopy( endring_mal)

while enbom:
    
    endrobj = deepcopy( obj_mal)
    endrobj['nvdbId'] = enbom.id
    endrobj['versjon'] = enbom.metadata['versjon']
    
    # Passeringsgruppe
    p1 = deepcopy( eg_mal)
    p1['typeId'] = 10951
    p1['verdi'].append( 100001)
    endrobj['egenskaper'].append( p1)
    
    # Timesregel, varighet
    p2 = deepcopy( eg_mal)
    p2['typeId'] = 10952
    p2['verdi'].append( 60)
    endrobj['egenskaper'].append( p2)

    # Timesregel - ja | nei
    p3 = deepcopy( eg_mal)
    p3['typeId'] = 9412
    p3['verdi'].append( 'Standard timesregel')
    endrobj['egenskaper'].append( p3)


    
    print(enbom.id, enbom.egenskapverdi('Navn bomstasjon'))
    endr['delvisOppdater']['vegObjekter'].append( endrobj)

        
    enbom = b.nesteNvdbFagObjekt()
    