# -*- coding: utf-8 -*-
"""
Setter opp søkestien slik at du finner NVDB-api funksjonene 
Antar at dette biblioteket finnes et hakk opp i filtreet, 
i mappen ../nvdbapi-V3/

"""

import sys
import os 

if not [ k for k in sys.path if 'nvdbapi' in k]: 
    print( "Legger NVDB api til søkestien")
    sys.path.append( '/mnt/c/data/leveranser/nvdbapi-V3' )
    
