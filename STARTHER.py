# -*- coding: utf-8 -*-
"""
Setter opp søkestien slik at du finner NVDB-api funksjonene 


"""

import sys
import os 

if not [ k for k in sys.path if 'nvdbapi' in k]: 
    print( "Legger NVDB api til søkestien")
    sys.path.append( '/home/jan/jobb/nvdbapi-V3' )
    
