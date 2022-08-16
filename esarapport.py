from copy import deepcopy 
import pdb 
from datetime import datetime

import requests

from shapely import wkt 
import pandas as pd 
import geopandas as gpd 

import STARTHER
import nvdbapiv3
import nvdbgeotricks

def strakavegen( row ): 
    """
    Sjekker om en dictionary eller en rad i dataframe tilhører hovedløpet (i den ene retningen) 
    eller om det er kryssdel, sideanlegg m.m. 

    Rundkjøringer regnes som del av hovedløpet (i full lengde), men ikke andre kryssdeler
    """

    utenom = 'Til side for hovedløp'

    rakveg = 'Hovedløp'
    if 'SD' in row['vref']: # Sideanlegg:
        rakveg = utenom
    elif 'KD' in row['vref'] and row['typeVeg'] != 'Rundkjøring': # Kryssdel som ikke er rundkjøring
        rakveg = utenom

    if row['typeVeg'] == 'Bilferje': 
        rakveg = 'Bilferje'

    return rakveg

def lagvegnr( row ):
    """
    Lager vegnummer ut fra vegkategori, fase og vegnummer
    """
    return row['vegkategori'] + row['fase'].lower() + str( row['nummer'])

def finnriksvegrute( mineruter:list ): 

    if len(mineruter) > 0: 

        navneliste =  [ x['navn'] + ' ' +  x['periode'] for x in mineruter ]   
        navn = ','.join( navneliste)

        if 'RUTE 7' in navn: 
            navn = navn.replace( 'RUTE 7', 'RUTE7')
            print( 'Endrer navn RUTE 7 => RUTE7')

    else: 
        navn = 'Mangler riksvegrute'

    return navn 

def prosesserDF( mittfilter ): 
    """
    Returnerer dataFrame med geometrikolonne 
    """

    veg = nvdbapiv3.nvdbVegnett()
    veg.filter( mittfilter )

    mindf = pd.DataFrame( veg.to_records( droppRiksvegruter=False ) ) 


    col = ['kortform', 'type', 'detaljnivå', 'typeVeg', 'feltoversikt', 'lengde', 'fylke', 'kommune',
            'medium', 'vref', 'vegkategori', 'fase', 'nummer', 'strekning', 'delstrekning', 'trafikantgruppe', 'adskilte_lop', 'hovedløp', 'riksvegruter', 'antallRuter',
             'geometry', 'veglenkesekvensid', 'startposisjon', 'sluttposisjon' ]

    mindf['geometry'] = mindf['geometri'].apply( wkt.loads )


    # Fjerner gang- og sykkelveg
    mindf = mindf[ mindf['trafikantgruppe'] != 'G'  ].copy()

    mindf['antallRuter'] = mindf['riksvegruter'].apply( lambda x : len( x ) )
    mindf['riksvegruter'] =  mindf['riksvegruter'].apply( lambda x : finnriksvegrute( x ) )

    mindf['hovedløp'] = mindf.apply( strakavegen, axis=1)
    mindf['Vegnr'] = mindf.apply( lagvegnr, axis=1)

    return mindf[col]


if __name__ == '__main__': 

    gpkgfile = 'esarapport.gpkg'

    t0 = datetime.now( )
    minefilter = { 'vegsystemreferanse' : 'Ev,Rv', 
                   # 'trafikantgruppe' : 'K', 
                    'veglenketype' : 'hoved', 
                    'adskiltelop' : 'med,nei' }
    # minefilter['kartutsnitt'] = '230367.375,6627530.373,232732.755,6630768.879'  if len(x) > 0 else 'Mangler riksvegrute' 

    minDF = prosesserDF( minefilter )    
    minGdf = gpd.GeoDataFrame( minDF, geometry='geometry', crs=5973 )
    minGdf = gpd.GeoDataFrame( minDF, geometry='geometry', crs=5973 )
    minGdf[ minGdf['antallRuter'] == 1 ].to_file( gpkgfile, layer='riksvegruter', driver="GPKG")  
    minGdf[ minGdf['antallRuter'] != 1 ].to_file( gpkgfile, layer='riksvegruter-avvik', driver="GPKG")  


    # komponerer navn + beskrivelse + periode i samme tekststreng 
    ruter = requests.get( 'https://nvdbapiles-v3.atlas.vegvesen.no/omrader/riksvegruter.json').json()
    mapdict_rutebeskrivelse = { x['navn'] : x['beskrivelse'] for x in ruter }
    minGdf['rutenavn'] = minGdf['riksvegruter'].apply( lambda x : x.split()[0])
    minGdf['ruteperiode'] = minGdf['riksvegruter'].apply( lambda x : ' '.join( x.split()[1:]))
    minGdf['rutebeskrivelse'] = minGdf['rutenavn'].map(mapdict_rutebeskrivelse)
    minGdf['riksvegruter'] = minGdf['rutenavn'] + ' ' + minGdf['rutebeskrivelse'] + ' ' + minGdf['ruteperiode']

    # Henter motorveg-data
    motorDF = pd.DataFrame( nvdbapiv3.nvdbFagdata( 595 ).to_records())
    motorDF['geometry'] = motorDF['geometri'].apply( wkt.loads )
    motorGdf = gpd.GeoDataFrame( motorDF, geometry='geometry', crs=5973 )
    motorGdf.to_file( gpkgfile, layer='motorveg', driver='GPKG' )
    
    # Blander riksvegruter med motorveg
    # Vi har ikke left join, kun inner join! For å lage left join må vi føye til de elementene som ikke er med i inner join så vi lager en - og kopierer index inn i en variabel, slik at vi kan "joine" de som ikke er med
    # Dette skal funke på de stedene der det enten er full overlapp eller null overlapp mellom de to datasettene. Men det blir hull på de stedene der det er delvis overlapp (dvs den biten av et vegnettsegment som 
    # IKKE overlapper med motorveg vil mangle. Men det er det beste vi får til akkurat nå... Tar kontrolltelling for å se på hvor stort dette avviket blir)
    minGdf['tmp_index'] = minGdf.index
    joined = nvdbgeotricks.finnoverlapp( minGdf, motorGdf, prefixB='motor_'  )
    joined['geometry'] = joined['geometry'].apply( wkt.loads )
    joined = gpd.GeoDataFrame( joined, geometry='geometry', crs=5973 )

    # Blander dem basert på tmp_index
    tmp = pd.concat( [ joined, minGdf[ ~minGdf['tmp_index'].isin( joined['tmp_index'] ) ]  ]  )
    medMotorveg = gpd.GeoDataFrame( tmp, geometry='geometry', crs=5973 )

    # Lager mapping motorveg, motortrafikkveg vs ikke motorveg
    medMotorveg['Motorvegtype'] = medMotorveg['motor_Motorvegtype'].map( { 'Motorveg' : 'Motorveg', 'Motortrafikkveg' : 'Motortrafikkveg' }   ).fillna( 'Ikke motorveg')
    medMotorveg['Motorveg u Motortrafikkveg'] = medMotorveg['motor_Motorvegtype'].map( { 'Motorveg' : 'Motorveg', 'Motortrafikkveg' : 'Ikke motorveg' }   ).fillna( 'Ikke motorveg')
    medMotorveg['Motorveg pluss Motortrafikkveg'] = medMotorveg['motor_Motorvegtype'].map( { 'Motorveg' : 'Motor- eller Motortrafikkveg', 'Motortrafikkveg' : 'Motor- eller Motortrafikkveg' }   ).fillna( 'Ikke motorveg')
    medMotorveg.to_file( gpkgfile, layer='Motorveganalyse', driver='GPKG')

    # Lager ulike typer statistikk: 
    minGdf['lengde [km]'] = minGdf['lengde'] / 1000 
    per_riksvegrute = minGdf[ minGdf['antallRuter'] == 1].groupby([ 'riksvegruter' ]).agg( {'lengde [km]' : 'sum' } ).reset_index() 
    per_riksvegrute['lengde [km]'] = per_riksvegrute['lengde [km]'].apply( lambda x : round( x, 1) )

    medMotorveg['lengde [km]'] = medMotorveg['geometry'].length / 1000 
    per_riksvegrute_motorveg = medMotorveg[ medMotorveg['antallRuter'] == 1 ] .groupby(['riksvegruter', 'Motorvegtype']  ).agg( {'lengde [km]' : 'sum'}  ).reset_index( )
    per_riksvegrute_motorveg['lengde [km]'] = per_riksvegrute_motorveg['lengde [km]'].apply( lambda x : round( x, 1) )

    # Lengdene vi får med eller uten motorveg-tagging skal ideelt sett være identiske, men er det ikke
    kontroll = medMotorveg[ medMotorveg['antallRuter'] == 1 ] .groupby(['riksvegruter' ]  ).agg( {'lengde [km]' : 'sum'}  ).reset_index( )
    sammenlign = pd.merge( per_riksvegrute, kontroll, on='riksvegruter' )
    sammenlign['differanse'] = sammenlign['lengde [km]_x'] - sammenlign['lengde [km]_y']
    sammenlign['avvik prosent'] = 100 * sammenlign['differanse'] / sammenlign['lengde [km]_x']

    # Skriver Excel 
    metadata = pd.DataFrame( [ [ "Lengde vegnett per riksvegrute med tilknytninger", "inklusive bilferjer, armer, ramper og kryss men ikke sideanlegg"  ], 
                                [ "Kun bilveg, ikke gang/sykkelveg", ""],  
                                [ f"Motorveg: Objekttype 595 Motorveg koblet med vegnett", f"Usikker på om motortrafikkveg skal være med"  ],
                                [ f" ", f"Ideelt sett så skal ikke totallengden påvirkes av at du blander inn data for 595 Motorveg"  ],
                                [ f" ", f'Men - jeg får avvik på 0 - 1.2%, oppsummert i fanen "kontrollregning lengder"'  ],
                                [ f"Pythonscript kjørt {datetime.date(datetime.now())} ", 
                                     'https://github.com/LtGlahn/workinprogress/tree/rapportering_ESA_vegsikkerhetsforskrift' ]
                              ], columns=['metadata', 'Riksvegrute rapport'] )
    

    nvdbgeotricks.skrivexcel( 'riksveglengder.xlsx', [per_riksvegrute, per_riksvegrute_motorveg, sammenlign, metadata] , 
                                sheet_nameListe=[ 'Lengde per riksvegrute', 'Lenge riksvegrute motorveg', 'kontrollregning lengder', 'metadata' ]  )

    tidsbruk = datetime.now( ) - t0 
    print( "tidsbruk:", tidsbruk.total_seconds( ), "sekunder")

