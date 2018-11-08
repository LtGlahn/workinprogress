# -*- coding: utf-8 -*-
"""
Created on Thu Nov  8 11:53:26 2018

@author: jajens

Rutiner for å lagre unna NVDB-informasjon til riksarkivet
"""

import json 

import STARTHER
import nvdbapi 

outputdir = 'riksarkivdata'

datatypes = [ 45 ]

for objtype in datatypes: 
    fname = outputdir + '/nvdb' + str(objtype) + '.json'
    
    sok = nvdbapi.nvdbFagdata( objtype)
    ettobj = sok.nesteForekomst()
    if ettobj: 
        f = open( fname, 'w', encoding='utf-8')
        f.write( '[\n')

        while ettobj: 
            jsonstring = json.dumps(ettobj, ensure_ascii=False)            
            f.write( jsonstring + '\n')
           
            ettobj = sok.nesteForekomst()
                
        f.write( ']\n')
        f.close()
        
    else: 
        print( 'Fikk ingen objekter for type', ettobj)