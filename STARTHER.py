# -*- coding: utf-8 -*-
"""
Gjør ingenting som helst, men erstatter den fila som 
TIL VANLIG legger mappen med nvdbapi-V3/ til søkestien 
via 
import sys
sys.path.append( 'Mappesti/til/nvdbapi-v3' )

"""

try: 
    import nvdbapiv3
except ImportError:  
    print( "Fant ikke nvdbapiv3 på søkestien, sjekk harddisken din")
    print( "Bruk enten \n]: import sys")
    print( "]: sys.path('/mappe/der/du/har/lagt/nvdbapi-V3'")
    print( "Eller flytt scriptet inn i mappen nvdbapi-V3/")
else: 
    print( 'Hurra, vi klarer importere nvdbapiv3')


    

