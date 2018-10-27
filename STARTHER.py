# -*- coding: utf-8 -*-
"""
Setter opp søkestien slik at du finner NVDB-api funksjonene 

Created on Wed Oct 24 11:43:16 2018

@author: jajens
"""

import sys
import os 

if not [ k for k in sys.path if 'nvdbapi' in k]: 
    print( "Legger NVDB api til søkestien")
    # sys.path.append( '../nvdbapi-V2' )
    
    if sys.platform == 'linux': 
        mysep = '/'
    else: 
        mysep = '\\'
    
    dir_path = os.getcwd().split(sep=mysep)
    dir_path[-1] = 'nvdbapi-V2'
    sys.path.append( '/'.join(dir_path ))


