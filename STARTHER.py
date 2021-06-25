# -*- coding: utf-8 -*-
"""
Setter opp søkestien slik at du finner NVDB-api funksjonene 
for dette biblioteket
https://github.com/LtGlahn/nvdbapi-V3

Merk at hvis du velger "Code -> download zip"  og pakker ut med 
filutforsker høyreklikk "Pakk ut her" så får du "mappe-inni-mappe" fenomenet. 

Dvs nvdbapi-V3-master.zip pakkes ut til mappen 
nvdbapi-V3-master/nvdbapi-V3-master/filer.du.vil.ha 
"""

import sys
import os 

if not [ k for k in sys.path if 'nvdbapi' in k]: 
    print( "Legger NVDB api til søkestien")
    # sys.path.append( 'c:/minedata/jobb/nvdbapi-V3-master/nvdbapi-V3-master' )

    # Merk at hvis du bruker standard windows skråstreker mellom mappenavn så 
    # må du skrive TO streker mellom mappenavn, ikke bare en. Slik: 
    #   
    # sys.path.append( 'C:\\minedata\\jobb\\nvdbapi-V3-master\\nvdbapi-V3-master' )

