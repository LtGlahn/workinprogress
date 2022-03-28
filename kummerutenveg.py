import pandas as pd
from shapely import wkt

import STARTHER
import nvdbapiv3
import hentgalekummer
kumliste = hentgalekummer.kumliste()

def hentkum( kumId, finnNaboer=False, minApiforbindelse=None  ): 
    kum = ap.les( '/vegobjekt', params={'id' : kumId } ).json()

    svar = { 'nvdbId'           : kumId, 
            'startdato'         : kum['metadata']['startdato'], 
            'sluttdato'         : '',
            'sist_modifisert'   : kum['metadata']['sist_modifisert'], 
            'stedfesting'    : 'NEI', 
            'lokasjon'       : 'niks'
            'hargeometri'       : 'NEI',
            'geometri'          : '',
            'egenskaper'        : 'NEI', 
            'hvilkeEgenskaper'  : '',
            'objektdata'        : kum }

    if 'egenskaper' in kum and len( kum['egenskaper']) > 0: 
        svar['egenskaper'] = 'JA'

        egliste = []
        for eg in kum['egenskaper']: 
            egliste.append( eg['navn'] )
        egliste.sort()
        svar['hvilkeEgenskaper'] = ','.join( egliste )

    if 'lokasjon' in kum: 
        svar['lokasjon'] = kum['lokasjon']
        if 'stedfestinger' in kum['lokasjon'] and \
        isinstance( kum['lokasjon']['stedfestinger'], list ) and len( kum['lokasjon']['stedfestinger'] ) > 0 and \
        'veglenkesekvensid' in kum['lokasjon']['stedfestinger'][0]: 

        svar['stedfesting'] = 'JA'

    if 'geometri' in kum and 'wkt' in kum['geometri']:
        svar['geometri'] =  kum['geometri']['wkt']
        mittpunkt = wkt.loads( kum['geometri']['wkt'] )
        x1 = mittpunkt.x - bboxRadius
        y1 = mittpunkt.y - bboxRadius
        x2 = mittpunkt.x + bboxRadius
        y2 = mittpunkt.y + bboxRadius

        svar['hargeometri'] = 'JA'




if not minApiforbindelse: 
    minApiforbindelse = nvdbapiv3.apiforbindelse( miljo='prodles' )
ap = minApiforbindelse

allesvar = [ ]
bboxRadius = 5

for kumId in kumliste: 
    (svar, nabokum) = hentkum( kumId, )
    allesvar.append( svar )        


ap = nvdbapiv3.apiforbindelse( miljo='prodles' )

data = pd.DataFrame( allesvar )
