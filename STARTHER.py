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
    # sys.path.append( '/mnt/c/data/leveranser/nvdbapi-V3' )
    
    if sys.platform == 'linux': 
        mysep = '/'
    else: 
        mysep = '\\'
    
    dir_path = os.getcwd().split(sep=mysep)
    # dir_path[-1] = 'nvdbapi-V2'
    dir_path[-1] = 'nvdbapi-V3'
    sys.path.append( '/'.join(dir_path ))


