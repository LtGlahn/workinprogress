import pandas as pd 


import lokal_STARTHER
# import lastnedvegnett  
# import skrivdataframe
import nvdbgeotricks
import nvdbapiv3


def  vegsegment2record(v1): 
    """
    Forflater et vegsegment til samme 

    Hentet rått og brutalt fra https://github.com/LtGlahn/nvdbapi-V3/blob/master/nvdbapiv3/nvdbapiv3.py
    Cut-n-paste er da også en form for gjenbrukk... 

    Gjør det slik for å kun behandle dem som tilfredsstiller kriteriene nedenfor (sykkelfelt)
    ---
    Eksporterer søk for vegnett til liste med NVDB api V3 segmentert vegnett, littegrann forflatet
    Vi henter informasjon fra strekning, sideanlegg og kryssystem og legger på rot-nivå, slik at det 
    blir enklere å bruke. 
    ARGUMENTS
        None
    KEYWORDS 
        None 
    Returns
        Liste med segmentert vegnett fra NVDB api V3, forflatet for enklere bruk 
    """


    metadata = v1.pop( 'metadata', { } )
    v1.update( metadata)
    vr = 'vegsystemreferanse'
    vsys = 'vegsystem'
    strek = 'strekning'
    kryss = 'kryssystem'
    sidea = 'sideanlegg'

    struktur = [ 
        { 'navn' : 'medium',    'verdi' : { 'l1' : 'geometri',    'l2' : 'medium'  }}, 
        { 'navn' : 'geometri',  'verdi' : { 'l1' : 'geometri',    'l2' : 'wkt'  }}, # NB! Geometri-dictionary byttes nå ut med WKT-tekststreng!
                                                                                    # Hvis du vil ha mer data ut av geometri-elementet 
                                                                                    # må du gjøre det FØR denne operasjonen (eller ta vare på data eksplisitt)
        { 'navn' : 'vref',      'verdi' : { 'l1' : vr,            'l2' : 'kortform'  }}
    ]

    for mykey in struktur: 
        try: 
                v1[mykey['navn']] = v1[mykey['verdi']['l1']][mykey['verdi']['l2']]
        except KeyError: 
            pass                 

    # Gjør om feltoversikt fra liste-objekt til (kommaseparert) ren tekst 
    try: 
        v1['feltoversikt']  = ', '.join( v1['feltoversikt'])
    except KeyError: 
        pass 

    # Noen av disse verdiene hentes fra strekning, men overskrives med  data
    # fra kryssdel eller sidenanlegg dersom de finnes. 
    # Vi følger python-idomet med å prøve om verdiene er der og ubekymret springe 
    # videre hvis de ikke finnes. 
    struktur = [{ 'navn' : 'vegkategori'     , 'verdi' :  { 'l1' : vr, 'l2' : vsys, 'l3' : 'vegkategori'        }}, 
                { 'navn' : 'fase'            , 'verdi' :  { 'l1' : vr, 'l2' : vsys, 'l3' : 'fase'               }},  
                { 'navn' : 'nummer'          , 'verdi' :  { 'l1' : vr, 'l2' : vsys, 'l3' : 'nummer'             }}, 
                { 'navn' : 'strekning'       , 'verdi' :  { 'l1' : vr, 'l2' : strek, 'l3' : 'strekning'         }}, 
                { 'navn' : 'delstrekning'    , 'verdi' :  { 'l1' : vr, 'l2' : strek, 'l3' : 'delstrekning'      }}, 
                { 'navn' : 'ankerpunktmeter' , 'verdi' :  { 'l1' : vr, 'l2' : strek, 'l3' : 'meter'             }}, 
                { 'navn' : 'kryssdel'        , 'verdi' :  { 'l1' : vr, 'l2' : kryss, 'l3' : 'kryssdel'          }}, 
                { 'navn' : 'sideanleggsdel'  , 'verdi' :  { 'l1' : vr, 'l2' : sidea, 'l3' : 'sideanleggsdel'    }},   
                { 'navn' : 'fra_meter'       , 'verdi' :  { 'l1' : vr, 'l2' : strek, 'l3' : 'fra_meter'         }}, 
                { 'navn' : 'til_meter'       , 'verdi' :  { 'l1' : vr, 'l2' : strek, 'l3' : 'til_meter'         }}, 
                { 'navn' : 'trafikantgruppe' , 'verdi' :  { 'l1' : vr, 'l2' : strek, 'l3' : 'trafikantgruppe'   }}, 
                { 'navn' : 'fra_meter'       , 'verdi' :  { 'l1' : vr, 'l2' : kryss, 'l3' : 'fra_meter'         }}, 
                { 'navn' : 'til_meter'       , 'verdi' :  { 'l1' : vr, 'l2' : kryss, 'l3' : 'til_meter'         }}, 
                { 'navn' : 'trafikantgruppe' , 'verdi' :  { 'l1' : vr, 'l2' : kryss, 'l3' : 'trafikantgruppe'   }}, 
                { 'navn' : 'fra_meter'       , 'verdi' :  { 'l1' : vr, 'l2' : sidea, 'l3' : 'fra_meter'         }}, 
                { 'navn' : 'til_meter'       , 'verdi' :  { 'l1' : vr, 'l2' : sidea, 'l3' : 'til_meter'         }}, 
                { 'navn' : 'trafikantgruppe' , 'verdi' :  { 'l1' : vr, 'l2' : sidea, 'l3' : 'trafikantgruppe'   }}, 
                { 'navn' : 'adskilte_lop'    , 'verdi' :  { 'l1' : vr, 'l2' : strek, 'l3' : 'adskilte_løp'      }}
                ]

    for mykey in struktur: 
        try: 
            v1[mykey['navn']] = v1[mykey['verdi']['l1']][mykey['verdi']['l2']][mykey['verdi']['l3']]
        except KeyError: 
            pass 
    
    v1.pop( 'kontraktsområder', None)
    v1.pop( 'riksvegruter', None)

    return v1



mittfilter= {   'trafikantgruppe'       : 'G', 
                'detaljniva'            : 'VT,VTKB',
                # 'adskiltelop'           : 'med,nei',
                # 'historisk'             : 'true', 
                'vegsystemreferanse'    : 'Ev,Rv'
                # 'veglenketype'          : 'hoved', 
                # 'typeveg'               : 'kanalisertVeg,enkelBilveg,rampe,rundkjøring,gangOgSykkelveg,sykkelveg,gangveg,gatetun'
                }
if __name__ == __main_:
    # v = nvdbapiv3.nvdbVegnett(  )
    # v.filter( mittfilter )
    # data =  v.to_records()

    # nvdbgeotricks.records2gpkg( data,  'sykkelveg.gpkg', 'gangsykkelveg' )

    v2 = nvdbapiv3.nvdbVegnett()
    v2.filter( {'detaljniva' : 'VT,VTKB', 'vegsystemreferanse' : 'Ev,Rv'})

    data2 = []
    for segment in v2: 

        if 'feltoversikt' in segment: 
            sykkelfelt = [ x for x in segment['feltoversikt'] if 'S' in x ]
            if len( sykkelfelt ) > 0: 
                segment2 = vegsegment2record( segment )

                data2.append( segment2 )

    nvdbgeotricks.records2gpkg( data2, 'sykkelveg.gpkg', 'vegnett_m_sykkelfelt')