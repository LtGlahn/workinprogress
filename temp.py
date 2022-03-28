import numpy as np

import STARTHER
import spesialrapporter

def finnBKfeil( brutusBK, nvdbBk ): 
    """
    Sammenligner bruksklasse fra Brutus med bruksklasse fra NVDB og returnerer tekststreng 
    """

    tempBrutusBk = spesialrapporter.splitBruksklasse_vekt( brutusBK )
    tempNvdbBK   = spesialrapporter.splitBruksklasse_vekt( nvdbBk )

    result = 'FEIK'
    if np.isnan( tempBrutusBk[0]) or np.isnan( tempBrutusBk[1] ) or np.isnan( tempNvdbBK[0]) or np.isnan( tempNvdbBK[1]):
        result = 'Ugyldige data'
    elif tempBrutusBk[0] < tempNvdbBK[0] or tempBrutusBk[1] < tempNvdbBK[1]:
        result = 'ALARM: Brutus BK < NVDB'
    else: 
        result = 'OK: Brutus BK >= NVDB'

    return result 