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

# Fra kap 2.4 i arkiveringsplan... 
#Bru (060)
#2. Bygning (065)
#3. Ferjeleie (064)
#4. Fjellrom (147)
#5. Skredmagasin (625)
#6. Skredoverbygg (066)
#7. Støttemyr (062)
#8. Tunnel (581)
#9. Tunnelløp (067)
#10. Tunnelløp uten trafikk (447)
#11. Tunnelportal (069)
#12. Tunnelsjakt (448)

datatypes = [ 60, 65, 64, 147, 625, 66, 62, 581, 67, 447, 69, 448 ]



for objtype in datatypes: 
    fname = outputdir + '/nvdb' + str(objtype) + '.json'
    print( 'Henter objekttype: ', str(objtype))
    
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
        
        # Datakatalogen
        dakat = sok.anrope( 'vegobjekttyper/' + str( objtype) )
        with open( outputdir + '/dakat' + str(objtype) + '.json', 'w', encoding='utf-8') as f2: 
            json.dump( dakat, f2, ensure_ascii=False, indent=4)
        print( 'Lagret obj.type', str(objtype), 'med', sok.antall, 'forekomster')
    else: 
        print( 'Fikk ingen objekter for obj.type', ettobj)