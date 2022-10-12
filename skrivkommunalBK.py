"""
Fyller hull i bruksklasser på kommunalt vegnett

Manglende bruksklasse-data blir funnet med script i NVDB-databasen og rapportene publiseres på 
https://nvdb-datakontroll.atlas.vegvesen.no/ Disse rapportene blir dekodet av "mangelrapport.py" 

Såfremt ikke kommunen spesifikt angir noe annet, så skal disse hullene på kommunalt vegnett
fylles med "sekkepost-verdier", dvs den kombinasjonen av 
bruksklasse-verdier som brukes til oppføringen "Øvrige veger". Dette er den mest vanlige
dataverdi-kombinasjonen innafor den kommunen, og vegene her skal IKKE ha strekningsbeskrivelse. 
(Strekningsbeskrivelse brukes til å skille ut kommunalveger det er noe ekstra med, enten ved at de har
avvikene BK eller for at en viktig veg fremheves med sin egen oppføring i veglistene)

Så logikken her blir følgende: 

    1) Finn sekkepost-dataverdiene for kommunen 
       a. Last ned strekningsløse BK for kommunalveg med filteret 
                    { 'vegsystemreferanse' : 'Kv', 
                      'egenskap=<ID for strekningsbeskrivelse-egenskap> = null'
                      'trafikantgruppe' : 'K' }

       b. Analyser: Datasett.groupby( ['BK-verdiene' ])
          b1) Hvilken kombinasjon av bruksklasse, maks tillatt vogntoglengde etc er det flest av?
          b2) Er det mer enn 1 - en - slik kommbinasjon? I så fall er det datafeil som bør rettes. 
                Loggføres til senere QA. 
                
                Hvis en kommunal veg har annen BK enn det som gjelder for
                den kommunens sekkepost så skal / bør denne BK-verdien også ha en strekningsbeskrivelse
                (men vi kan godta at gatenavnet brukes i stedet; veglistene har denne logikken innebygd). 
                Denne vurderingen overlater jeg til faggruppe vegliste, til senere QA. 


    2) Konstruer endringssett som skal sendes til SKRIV. Her kan vi velge å starte med kun et subsett (de enkleste
    og mest skuddsikre tilfellene) av de feilene som rapporteres. Vi prøver oss litt fram, basert på hvilke dataverdier
    vi møter 

    Ett mulig scenario er å starte med de strekningene som starter med veglenkeposisjon 0 og slutter med veglenkeposisjon 1. 
    Jeg tror at dette er helt nye veger som er kommet til uten at noen har rukket å etablere BK-verdier på dem. 
    Dette utgjør cirka 40% av mangelrapportene på kommunal veg. Oslo har 1066 slike rader, 
    fulgt av kommune 4204 med 483 rader og 3030 med 110. 

    Krav til endringssett: 
        - Oppretter tre nye objekter per veg: Normaltransport, spesialtransport og tømmertransport
        - BK + BK vinter er identisk for de tre objekttypene, og BK normaltransport er styrende
        for hvilken dataverdi dette skal være
        - Tillatt vogntoglengde er nesten identisk: Den _*kan*_ ha de større verdiene 22 og 24 m på BK tømmer, ellers er den lik 
        på tvers av de tre objekttypene. 
        - BK Spesilaltransport har i tillegg egenskapen Veggruppe (A, B, IKKE - eventuelt mangler data). 
          og "mangler data" er tydeligvis en OK verdi, sjekk f.eks "øvrige veger" for Kristiansand og Vennesla 
          vegliste Spesialtransport. 
        - BK Tømmertransport kan som før nevnt ha større verdi 22m og 24m på egenskapen "Maks tillatt vogntoglengde". 
          I tillegg kommer egenskapene 
                - "maks totalvekt" (som stort sett er identisk med tall nr 2 i BK-verdien, men 
          for Bk10/50 er også verdien 60tonn tillatt.)  
                - "Tillatt for modulvogntog 1 og 2 med sporingskrav" (Ja eller Nei) 

    Dette må vi gjøre for to varianter: BK offisiell og BK uoffisiell.

    Ved god bruk av datakatalogen og unngå hardkoding så skal vi få dette til på en elegant måte, tror jeg.
    Med 2 * 3 = 6 objekttyper og en håndfull egenskaper per objekttype så er kaospotensialet absolutt til stede, 
    så det er absolutt mye å hente på å lage en god, datakatalog-drevet løsning. 


"""

from copy import deepcopy
import pdb
from datetime import datetime

import pandas as pd
import geopandas as gpd 
import fiona

import warnings # Ignorerer den irriterende meldingen fra geopandas.from_file()
warnings.filterwarnings("ignore", message="Sequential read of iterator was interrupted. Resetting iterator. This can negatively impact the performance.")
warnings.filterwarnings("ignore", message="The spaces in these column names will not be changed. In pandas versions < 0.14, spaces were converted to underscores.")

import STARTHER
import skrivnvdb 
from nvdbapiv3 import  nvdbFagdata, apiforbindelse 
from nvdbgeotricks import finnoverlapp 


def wrap_finnoverlapp( dfA, dfB, prefixA=None, prefixB=None ):
    """
    Finner overlapp mellom to (geo)dataframe; brukes til å sjekke at vi har reell overlapp og ikke berøring (slik NVDBAPI LES gir oss)

    Wrapper rundt funksjonen finnoverlapp i https://github.com/LtGlahn/nvdbapi-V3/blob/master/nvdbgeotricks.py 

    Forutsetter at dfA har disse kolonnene, som så døpes om til de navnene finnoverlapp foretrekker 
        sqldump_vlenkid           int64
        sqldump_frapos          float64
        sqldump_tilpos          float64

    """
    dfAcopy = dfA.copy()
    dfAcopy['veglenkesekvensid'] = dfAcopy['sqldump_vlenkid']
    dfAcopy['startposisjon']     = dfAcopy['sqldump_frapos']
    dfAcopy['sluttposisjon']     = dfAcopy['sqldump_tilpos']

    dfAcopy = dfAcopy[['veglenkesekvensid', 'startposisjon', 'sluttposisjon', 'sqldump_datarad', 'vref' ]]

    return finnoverlapp( dfAcopy, dfB, prefixB=prefixB )

def finnSekkepost( kommunenummer, inkluder_offisiell=True, inkluder_uoffisiell=False, miljo='prodles', username='jajens', pw='', forb=None  ): 
    """
    Finner sekkepost-fordelig av bruksklasseverdier på vegnett i en kommune

    Leser BK offisiell og uoffisiell for normal, tømmer og spesialtransport-klassene. 
    Sjekker at disse er inbyrdes enige om hva som er gode sekkepost-verdier, skriver ADVARSEL dersom 
    de er innbyrdes uenige

    Logikken her må ta høyde for at egenskapsverdier som strengt tatt skal inngå i veglistene _*ikke finnes*_ for 
    den kommunen du vurderer. F.eks. Veggruppe er ikke valgt for "Øvrige veger i Kristiansand, men 
    i Vennesla er det veggruppe A. Og "Bruksklasse vinter" er ofte fraværende, men ikke alltid. 

    Eksakt hvilke data som returneres avhenger av hva du ber om med nøkkeordene inkluder_offisiell og inkluder_uoffisiell, 
    samt hva som finnes av data i denne kommunen.

      inkluder_offisiell=True : Hent offisielle data for BK normal, tømmer- og spesialtransport (NVDB objekttype 904, 900 og 902)

      inkluder_uoffisiell=True : Hent uoffisielle data for BK normal, tømmer- og spesialtransport (NVDB objekttype 904, 900 og 902)

    ARGUMENTS 
      kommunenummer : int, kommunenummer

    KEYWORDS 
      inkluder_offisiell : Bool, True (default) eller False 
      
      inkluder_uoffisiell : Bool, True eller False (default) 

      miljo : string, en av 'prodles' (default), 'testles' eller 'utvles'. Hvilket miljø (produksjon, test eller utvikling) som vi henter data fra 

      username : string, default 'jajens' Brukernavn som brukes til innlogging NVDB api LES, for angitt miljø

      pw : string, default ''. IKKE SKRIV PASSORD I KODE SOM DELES! Passord for å logge inn i det driftsmiljøet som er angitt med parameter miljo

      forb : Instans av nvdbapiv3.apiforbindelse. Default None. Slik kan du logge inn i driftsmiljø APILES én og kun gang, og deretter
                       dele ferdig innlogget apiforbindelse-objekt med dem som trenger det   

    RETURNS
      skrivemal : Dictionary med de dataverdiene som skal skrives til NVDBAPISKRIV for de stedene der vi mangler 
      BK på kommunal veg. 

      Eksempel for normaltransport i Vennesla: 
      python> skrivemal = finnSekkepost( 4223, inkluder_offisiell=True, inkluder_uoffisiell=False )     
      python> skrivemal['normal'] 

              {
                "normal": {
                          "metadata": {
                              "type": {
                                  "id": 904,
                                  "navn": "Bruksklasse, normaltransport"
                              }
                          },
                          "egenskaper": [
                              {
                                  "id": 10901,
                                  "navn": "Bruksklasse",
                                  "verdi": "Bk10 - 50 tonn"
                              },
                              {
                                  "id": 10913,
                                  "navn": "Maks vogntoglengde",
                                  "verdi": "19,50"
                              },
                              {
                                  "id": 11210,
                                  "navn": "Vegliste gjelder alltid",
                                  "verdi": "Se www.vegvesen.no/veglister"
                              }
                          ]
                  }
              }

    """

    # Henter datakatalog-definisjoner 
    if not forb: 
      forb = apiforbindelse()

    dakat = { }

    if inkluder_offisiell:

        dakat['normal'] = forb.les( '/vegobjekttyper/904').json()
        dakat['tommer'] = forb.les( '/vegobjekttyper/900').json()
        dakat['spesial'] = forb.les( '/vegobjekttyper/902').json()

    if inkluder_uoffisiell: 
        if hasattr( forb, 'loginrespons' ) and forb.loginrespons.ok:
            pass
        else:  
            print( f"Logg inn i nvdb api les driftsmiljø {miljo} ")
            forb.login( miljo='prodles', username=username, pw=pw)

        dakat['uoff_normal'] = forb.les( '/vegobjekttyper/905').json()
        dakat['uoff_tommer'] = forb.les( '/vegobjekttyper/901').json()
        dakat['uoff_spesial'] = forb.les( '/vegobjekttyper/903').json()

    temp_dataframes = []
    resultat = []
    skrivemal = { }
    objtyper = list( dakat.keys() )

    for objtype in objtyper: 

        skrivemal[objtype] = {  'metadata' : {  'type': { 
                                                          'id': dakat[objtype]['id'],
                                                          'navn':  dakat[objtype]['navn']  
                                                        }
                                              },
                                'egenskaper' : [ ]
                              }

        egenskap_strekningsbeskrivelse = [ x for x in dakat[objtype]['egenskapstyper'] \
                                            if x['navn'] == 'Strekningsbeskrivelse'  ][0]
    
        mittsok = nvdbFagdata( dakat[objtype]['id'] )
        mittsok.forbindelse = forb 
        mittsok.filter( { 'vegsystemreferanse' : 'Kv', 
                           'kommune' : kommunenummer, 
                           'egenskap' : f"({egenskap_strekningsbeskrivelse['id']}=null)", 
                           'trafikantgruppe' : 'K' })
        mindf = pd.DataFrame( mittsok.to_records() )
        temp_dataframes.append( mindf )

        # Dataverdier som inngår i veglistene, og som brukes til å finne grupperingen "øvrige veger"
        # Merk at logikken tar høyde for at noen egenskaper, f.eks. "Bruksklasse vinter", ikke har data
        # for angjeldende kommune. Dermed kan vi også klare oss med 1 - en - felles definisjon for de 
        # tre bruksklasse-variantene våre. 
        vegliste_egenskaper = [ 'Bruksklasse', 'Bruksklasse, vinter',               # felles, men BK normal bestemmer
                                'Maks vogntoglengde',                               # Kan avvike for 22m og 24m BK tømmer
                                'Tillatt for modulvogntog 1 og 2 med sporingskrav', # Kun BK tømmer
                                 'Veggruppe' ]                                     # Kun BK spesial 

        temp = deepcopy( mindf )
        temp.fillna( '<null>', inplace=True )
        vegliste_egenskaper_subset = [ col for col in vegliste_egenskaper if col in temp.columns ]
        sekkepost = temp.groupby( vegliste_egenskaper_subset ).agg( { 'nvdbId' : 'count', 'segmentlengde' : sum } ).reset_index() 
        sekkepost.sort_values( by=['segmentlengde'], inplace=True, ascending=False  )
        sekkepost.reset_index( inplace=True, drop=True )

        if len( sekkepost ) > 1: 
            print( f"i kommunne {kommunenummer} finnes flere verdier for {dakat[objtype]['id']} "  
                                f"{dakat[objtype]['navn']} uten strekningsbeskrivelse" )

            print( sekkepost )

        # Føyer på standard vegkart disclaimer for BK offisiell:
        if dakat[objtype]['id'] in [900, 902, 904]: 
            sekkepost['Vegliste gjelder alltid'] = 'Se www.vegvesen.no/veglister'

        # Lager mal for egenskaper som brukes til SKRIV 
        for egenskap in sekkepost.columns: 
            if egenskap not in ['nvdbId', 'segmentlengde'] and sekkepost[egenskap].iloc[0] != '<null>':
                eg = [ x for x in dakat[objtype]['egenskapstyper'] if x['navn'] == egenskap  ][0]
                skrivemal[objtype]['egenskaper'].append( { 'id' : eg['id'], 'navn' : eg['navn'], 'verdi' : sekkepost[egenskap].iloc[0]  } )

        resultat.append( sekkepost )

    # Kvalitetssjekk - har vi like dataverdier i de tre eller seks BK-variantene våre? 
    if len( resultat ) > 0:
        mintestmal = dict( resultat[0].iloc[0] )
        mintestmal.pop( 'nvdbId', None)
        mintestmal.pop( 'segmentlengde', None)
        for idx, sjekk in enumerate( resultat[1:] ):
            for verdi in mintestmal.keys(): 
                if verdi in sjekk.columns and sjekk[verdi].iloc[0] != mintestmal[verdi]: 
                    print( f"ADVARSEL kommune {kommunenummer} for {objtyper[0]} vs {objtyper[idx+1]}, ulik sekkepost-verdi {verdi}:  {mintestmal[verdi]} vs {sjekk[verdi].iloc[0]} ")
    else: 
        print( "Tomt resultatsett - har du angitt både inkluder_offisiell=False og inkluder_offisiell=False i funksjonskallet?")


    ## for debugging
    # from IPython import embed; embed()

    return skrivemal




def __lagskrivemal( skrivemal ): 
    """
    Intern funksjon for å lage maler som brukes til å komponere gyldige endringssett med ulike bruksklasser til NVDBAPISKRIV 

    leser skrivemal-dictionary (som er dataverdier for sekkepost-BK'ene innafor en kommune) og lager 
    samsvarende dictionary-struktur som er tilpasset det vi sender til NVDBAPISKRIV  

    ARGUMENTS
    skrivemal: Dictionary med minst én av BK-klassene 'normal', 'tommer', 'spesial', 
                                                        'uoff_normal', 'uoff_tommer', 'uoff_spesial' 

                Som igjen er dataeksempler med egenskapsverdier for sekkepost-BK-verdiene for den kommunen
                

    KEYWORDS
    N/A

    RETURNS
    (endringsettmal, skrivemaler)

    endringsettmal: Den ytre konvolutten der nye vegobjekter blir puttet inn, med den 
            tomme listen 'registrer' { 'vegobjekter : []}, riktig datakatalog-versjon m.m. 

    Skrivemaler: Dictionary med samme elementer som innkommende element "skrivemal", men der hvert element er 
                    oversatt til den strukturen som NVDB APISKRIV kan motta
                    Dvs elementet "normal" har egenskapsverdiene og metadata for registrering av nytt vegobjekt 
                    av type 904 Bruksklasse normaltransport


    """
    endringsettmal = dict( )
    skrivemaler = dict( )
    for count, bk in enumerate( skrivemal.keys()): 
        mal_overordnet = skrivnvdb.fagdata2skrivemal( skrivemal[bk], operasjon='registrer' )
        skrivemaler[bk] = deepcopy( mal_overordnet['registrer']['vegobjekter'][0] )

        if count == 0:
            endringsettmal = deepcopy( mal_overordnet )
            endringsettmal['registrer']['vegobjekter'] = []
        
    return (endringsettmal, skrivemaler )


def tetthull_lagendringssett( kommunenummer, filnavn='mangelrapport.gpkg', inkluder_offisiell=True, inkluder_uoffisiell=False, 
                              miljo='prodles', username='jajens', pw='', forb=None ): 
    """
    Leser analyserte mangelrapport-data og lager endringssett som kan sendes til NVDB APISKRIV for å tette (noen av) hullene på kommunalveg i NVDB

    Bruker "sekkepost"-logikk for å finne de dataverdiene som skal brukes der det er hull. 

    ARGUMENTS 
        kommunenummer : Int, kommunenummer

    KEYWORDS 
        filnavn : string, filnavn på mangelrapport. Default 'mangelrapport.gpkg'

        inkluder_offisiell : Bool, default True. Tar med offisielle verdier for BK normal, tømmer, spesial

        inkluder_uoffisiell : Bool, default False. Tar med Uoffisiell-verdier for BK normal, tømmer, spesial 

        miljo : string, default 'prodles', men kan også ha verdiene 'testles' og 'utvles'. Angir hvilket driftsmiljø vi henter 
                        data fra.  

        username : string. Brukernavn for å logge inn i LES (kun aktuelt dersom inkluder_uoffisiell=True). Kan droppes, du 
                        blir i så fall spurt interaktivt på kommandolinja eller i notebook 

        pw : string. Passord for å logge inn i LES. ALDRI SKRIV PASSORDET DITT I KILDEKODE SOM DELES! Du blir interaktivt spurt om 
                passordet på kommandolinja eller i notebook. Kun aktuelt dersom inkluder_uoffisiell=True 

        forb : Instans av nvdbapiv3.apiforbindelse, default None. Bruksområde er at du et annet sted i koden (f.eks i et annet script) 
                logger inn i NVDB api LES for det driftsmiljøet du vil lese data fra, og så sender det ferdig innloggede 
                apiforbindelse-objektet inn som argument til de funksjonene som trenger det. Dette gjør det f.eks enklere
                å unngå at denne koden ved en feil plutselig inneholder passordet ditt - det kan du ha i et annet script som IKKE deles videre.

    RETURNS
        (retthull, endringssett): Tuple med disse datene 

            retthull: Geodataframe med de hullene vi lukker med endringssettet (og data om mangelrapporten de er henta fra)
        
            endringssett: Liste med endringssett der hvert endringssett har passe mange vegobjekter (Opptil ca 500 stk per endringssett). 

    """

    print( f"Tetter (noen av) hullene i kommune {kommunenummer} ")
    layerlist = fiona.listlayers( filnavn )
    mittlag = [ x for x in layerlist if '904' in x and 'debug' in x ][0]

    bkhull = gpd.read_file( filnavn, layer=mittlag )

    # Finner dem vi skal rette på 
    retthull = bkhull[ bkhull['vegkategori'] == 'K']
    retthull = retthull[ retthull['trafikantgruppe'] == 'K']
    retthull = retthull[ retthull['kommune'] == kommunenummer ]
    retthull = retthull[ retthull['sqldump_length'] > 2 ]
    # retthull = retthull[ retthull['kortform'].str.contains( '0.0-1.0' )]

    # filtrerer ut dem som har avvikende veglenkesekvens ID 
    retthull['vlenkid'] = retthull['kortform'].apply( lambda x : int( x.split('@')[-1] ) )
    galt = retthull[ retthull['vlenkid'] != retthull['sqldump_vlenkid'] ] 
    if len( galt ) > 0: 
        print( f"Fant {len(galt)} avvikende veglenkesekvensID, dropper disse radene: ")
        print( print( galt[[  'vref', 'sqldump_vref', 'kortform', 'sqldump_datarad' ]] ) )
        retthull = retthull[ retthull['vlenkid'] == retthull['sqldump_vlenkid'] ]

    # Lager kortform av sqldump-veglenkeposisjsonene: 
    retthull['sqldump_kortform'] = retthull['sqldump_frapos'].astype(str) + '-' + retthull['sqldump_tilpos'].astype(str) + '@' + retthull['sqldump_vlenkid'].astype(str)

    # Sjekker om vi har data på disse veglenkene. En del falske innslag i mangelrapporten. Hvor mange?
    # Legger alle kortform-stedfesting-tekstene (eks '0-1@1234) i liste. Slår sammen "passe mange" slike kortformer 
    # til kommaseparert liste som brukes som søkefilter i api les: 'veglenkesekvenser=0-1@1234,0-1@9999' 
    veglenker = list( set( list( retthull['sqldump_kortform'] )))  
    idx = list( range( 0, len( veglenker ), 25))
    idx.append( None )
    finnerdata = []
    sjekkObjekttyper = []
    if not forb:
        forb = apiforbindelse()
    if inkluder_offisiell: 
        sjekkObjekttyper.extend( [904, 902, 900 ] )

    if inkluder_uoffisiell: 
        sjekkObjekttyper.extend( [905, 903, 901 ] )
        if not  'Authorization' in forb.headers:
            print( "Logg inn i NVDB leseapi driftsmiljø", miljo)
            forb.login( miljo=miljo, username=username, pw=pw )

    for objektType in sjekkObjekttyper:  
        print( f"Sjekker om det finnes data for {objektType} der mangelrapport sier det er hull ")
        for ix in range(1, len( idx )):
            sok = nvdbFagdata( objektType )
            sok.filter( { 'veglenkesekvens' : ','.join( veglenker[idx[ix-1] : idx[ix] ] )  })
            sok.forbindelse = forb 
            finnerdata.extend( sok.to_records() )

    if len( finnerdata ) > 0: 
        print( f"Har hentet {len( finnerdata)} strekninger med bruksklassedata fra LES der mangelrapport sier det mangler data i kommune {kommunenummer}, sjekker om det er reelt:")

        finnerdf = pd.DataFrame( finnerdata )
        finnerdf['kortform'] = finnerdf['startposisjon'].astype(str) + '-' + finnerdf['sluttposisjon'].astype(str) + '@' + finnerdf['veglenkesekvensid'].astype(str)
        finnerdf.fillna('', inplace=True )
        if 'Tillatt for modulvogntog 1 og 2 med sporingskrav' in finnerdf.columns: 
            finnerdf.rename( columns={ 'Tillatt for modulvogntog 1 og 2 med sporingskrav' : 'Modulvogntog'}, inplace=True )
        # col = [ 'kommune', 'objekttype', 'vref', 'trafikantgruppe' ]
        # bkcol = [ 'Strekningsbeskrivelse', 'Bruksklasse', 'Maks vogntoglengde', 'Maks totalvekt', 'Veggruppe', 'Modulvogntog', 'kortform'  ]
        col = [ 'objekttype', 'vref' ]
        bkcol = [ 'Bruksklasse', 'Strekningsbeskrivelse'  ]
        col.extend( [x for x in bkcol if x in finnerdf.columns ]   )
        # print( finnerdf[col].sort_values( 'vref'))
        # for ix, row in finnerdf[col].sort_values('vref').iterrows():
        #     tempstring = ''
        #     for cc in col: 
        #         tempstring += str( row[cc] )
        #         tempstring += '    '
        #     print( tempstring )

        # sjekker om dette er reelt overlapp, eller kun at objektene berører den tomme strekningen (LES gir oss data som berører)
        reel_overlapp = wrap_finnoverlapp( retthull, finnerdf, prefixA=None, prefixB='B_' )

        # Debug
        retthullkopi = retthull.copy()

        if len( reel_overlapp ) > 0: 
            col2 =  { 'B_'+x : x  for x in col if not 'vref' in x }
            reel_overlapp.rename( columns=col2, inplace=True )
            reel_overlapp = reel_overlapp.drop_duplicates( subset=['sqldump_datarad', 'objekttype'])
            print( f"Fant {len(reel_overlapp)} tilfeller med reell overlapp, overskriver IKKE disse ")
            for ix, row in reel_overlapp[col].sort_values('vref').iterrows(): 
                tempstring = ''
                for cc in col: 
                    tempstring += str( row[cc] )
                    tempstring += '    '
                print( tempstring )

            feiler_reelt = retthull[  retthull['sqldump_datarad'].isin(  list( reel_overlapp['sqldump_datarad'] )) ].copy()
            retthull     = retthull[ ~retthull['sqldump_datarad'].isin(  list( reel_overlapp['sqldump_datarad'] )) ]
        else: 
            print( "Fant ingen reell overlapp, kun berøring mellom der vi mangler data og der vi har bruksklasse-data. ")

    # from IPython import embed; embed() # For debugging 


    # Sjekker at lenkene faktisk finnes. Kan droppes i PROD? (Ideelt sett, iallfall)
    forkast = []
    # print( f"Sjekker om alle {len( list(set(list(retthull['sqldump_vlenkid'] ))) )} lenkene i mangelrapport faktisk finnes (kan potensielt droppes når vi går mot PROD?")
    for lenke in set( list( retthull['sqldump_vlenkid'] )): 
        r = forb.les(   '/vegnett/veglenkesekvenser/segmentert/' + str( lenke )  )
        if not r.ok: 
            forkast.append( int( lenke ))

    if len( forkast ) > 0: 
        junk = retthull[ retthull['sqldump_vlenkid'].isin( forkast ) ]
        print( f"Mangler totalt {len(forkast)} lenker i miljo {forb.miljo}, fjerner {len(junk)} rader med BK-data for disse lenkene ")
        retthull = retthull[ ~retthull['sqldump_vlenkid'].isin( forkast ) ]


    # Lager kopi av retthull hvor vi fjerner duplikater pga segmentering, 0-1@veglenkesekvensId er gjerne brutt opp i flere biter
    skrivdisse = retthull.drop_duplicates( subset=['sqldump_vlenkid', 'sqldump_frapos', 'sqldump_tilpos'  ] )

    print( f"Lager sekkepost, henter alle BK-varianter uten strekningsbeskrivelse på kommunalveg i kommune {kommunenummer} ")
    sekkepostegenskaper = finnSekkepost( kommunenummer, inkluder_offisiell=inkluder_offisiell, inkluder_uoffisiell=inkluder_uoffisiell, 
                                            miljo=miljo, username=username, pw=pw, forb=forb  )
    (endringsettmal, skrivemaler ) = __lagskrivemal( sekkepostegenskaper )

    # Liste med endringssett som sendes separat til skriv, ikke alt samlet (potensielt for mye data)
    endringssett = []
    # mal_overordnet = skrivnvdb.fagdata2skrivemal( skrivemal['normal'], operasjon='registrer' )
    # mal_normal = deepcopy( mal_overordnet['registrer']['vegobjekter'][0] )
    # mal_overordnet['registrer']['vegobjekter'] = []
    tempId = -10000

    print( f"Lager endringssett for {len( skrivdisse)} strekninger for kommune {kommunenummer}")

    maks_endringer = 500
    count = 0 
    for idx, row in skrivdisse.iterrows():

        for bkType in sekkepostegenskaper.keys():
            tempId = tempId - 1
            count  += 1 
            nyttBkObjekt  = deepcopy( skrivemaler[bkType] )
            nyttBkObjekt['tempId'] = str( tempId )
            nyttBkObjekt['stedfesting'] = { 'linje' : [ { 'fra' : row['sqldump_frapos'], 'til' : row['sqldump_tilpos'], 'veglenkesekvensNvdbId' : row['sqldump_vlenkid'] }   ]   }
            endringsettmal['registrer']['vegobjekter'].append( nyttBkObjekt )

        if count >= maks_endringer: 
            endringssett.append( deepcopy( endringsettmal ))
            endringsettmal['registrer']['vegobjekter'] = []
            count = 0

    # Ferdig med alle iterasjoner, føyer til den aller siste gjengen (evt den aller første, hvis vi har færre enn maks_endringer )
    if len( endringsettmal['registrer']['vegobjekter'] ) > 0: 
        endringssett.append( deepcopy( endringsettmal ))
    return ( deepcopy(retthull), endringssett ) 


def retthull_skrivnvdb(   kommunenummer, filnavn='mangelrapport.gpkg', loggskrivfilnavn='loggskriv.gpkg', inkluder_offisiell=True, inkluder_uoffisiell=False, 
                              miljo='prodles', skrivmiljo='testskriv', dryrun=True, username='jajens', pw='', forb=None, skrivforb=None  ): 
    """
    Leser analyserte mangelrapport-data og skriver til NVDB APISKRIV for å tette (noen av) hullene på kommunalveg i NVDB

    Bruker "sekkepost"-logikk for å finne de dataverdiene som skal brukes der det er hull. 

    ARGUMENTS 
        kommunenummer : Int, kommunenummer

    KEYWORDS 
        filnavn : string, filnavn på mangelrapport. Default 'mangelrapport.gpkg'

        loggskrivfilnavn : string, filnavn på GPKG-fil der vi lagrer kartvisning av hvor vi har skrevet nye BK-verdier. 
                            Navnet på kartlaget = klientinfo som er brukt ved skriving til NVDB

        inkluder_offisiell : Bool, default True. Tar med offisielle verdier for BK normal, tømmer, spesial

        inkluder_uoffisiell : Bool, default False. Tar med Uoffisiell-verdier for BK normal, tømmer, spesial 

        miljo : string, default 'prodles', men kan også ha verdiene 'testles' og 'utvles'. Angir hvilket driftsmiljø vi henter 
                        data fra.  

        skrivmiljo : string, default 'prodskriv', men kan også  ha verdiene 'testskriv' og 'utvskriv'. Angir hvilket driftsmiljø
                        vi skriver data til 

        dryrun : Bool, default True. Testskriving uten commit til databasen.

        username : string. Brukernavn for å logge inn i LES (kun aktuelt dersom inkluder_uoffisiell=True). Kan droppes, du 
                        blir i så fall spurt interaktivt på kommandolinja eller i notebook 

        pw : string. Passord for å logge inn i LES. ALDRI SKRIV PASSORDET DITT I KILDEKODE SOM DELES! Du blir interaktivt spurt om 
                passordet på kommandolinja eller i notebook. Kun aktuelt dersom inkluder_uoffisiell=True 

        forb : Instans av nvdbapiv3.apiforbindelse, default None, som brukes til å lese fra NVDB API LES 
        
        skriforb : Instans av nvdbapiv3.apiforbindelse, default None, som brukes til å skrive til  NVDB API LES 
        
        Bruksområde for forb og skrivforb er at du et annet sted i koden (f.eks i et annet script) 
        logger inn i NVDB api LES eller SKRIV for det driftsmiljøet du vil lese data fra (eller skrive til), og så sender det 
        ferdig innloggede apiforbindelse-objektet inn som argument til de funksjonene som trenger det. Dette gjør det f.eks enklere
        å unngå at denne koden ved en feil plutselig inneholder passordet ditt - det kan du ha i et annet script som IKKE deles videre.

    RETURNS
        N/A

    """


    (retthull, endringssett) = tetthull_lagendringssett( kommunenummer, filnavn=filnavn, inkluder_offisiell=inkluder_offisiell, inkluder_uoffisiell=inkluder_uoffisiell, 
                              miljo=miljo, username='jajens', pw=pw, forb=forb )

    
    if not skrivforb:
        skrivforb = apiforbindelse()

    if not 'Authorization' in skrivforb.headers:
        print( f"Logg inn i skriveapi driftsmiljø {skrivmiljo} " ) 
        skrivforb.login( miljo=skrivmiljo, username=username, pw=pw )

    # Konstruerer klientinfo
    minklient = 'sekkeBK_v3_' + str( kommunenummer )

    if dryrun: 
        minklient += '_dryrun'

    retthull['klientinfo'] = minklient
    skrivforb.klientinfo( minklient )

    for enEndring in endringssett: 

        skrivtil = skrivnvdb.endringssett( enEndring )
        skrivtil.forbindelse = skrivforb 
        skrivtil.registrer( dryrun=dryrun)
        if skrivtil.status == 'registrert': 
            skrivtil.startskriving( )


    # Lagrer til fil det vi skreiv
    if len( retthull ) > 0: 
        retthull.to_file( loggskrivfilnavn, layer=minklient, driver='GPKG')

def retthelefylket(  fylkesnummer, filnavn='mangelrapport.gpkg', loggskrivfilnavn='loggskriv.gpkg', inkluder_offisiell=True, inkluder_uoffisiell=False, 
                              miljo='prodles', skrivmiljo='testskriv', dryrun=True, username='jajens', pw='', forb=None, skrivforb=None ):
    """
    Oppdaterer sekkepost-verdier for alle kommuner i et helt fylke. Se dokumentasjonen for retthull_skrivnvdb
    """

    tempforb = apiforbindelse( 'prodles')
    allekommuner = tempforb.les('/omrader/kommuner' ).json()
    kommuner = [ x for x in allekommuner if x['fylke'] == fylkesnummer ]
    # kommuner = [ x for x in kommuner if x['nummer'] > 3434  ]

    for kommune in kommuner: 
        print( f"Tetter hull i sekkepostverdier for kommune {kommune['nummer']} {kommune['navn']} ")
        retthull_skrivnvdb( kommune['nummer'], filnavn=filnavn, loggskrivfilnavn=loggskrivfilnavn, inkluder_offisiell=inkluder_offisiell, 
                        inkluder_uoffisiell=inkluder_uoffisiell, miljo=miljo, skrivmiljo=skrivmiljo, dryrun=dryrun, username=username, pw=pw, forb=forb, skrivforb=skrivforb )


# from IPython import embed; embed() # For debugging 
if __name__ == '__main__': 
    t0 = datetime.now()
    # resultat = finnSekkepost( 4204 )
    # (retthull, endringssett) = tetthull_lagendringssett( 4223, inkluder_uoffisiell=False )
    # retthull_skrivnvdb( 4204, inkluder_uoffisiell=True, dryrun=False, miljo='prodles', skrivmiljo='prodskriv', pw=''  )
    # retthull_skrivnvdb( 4203, inkluder_uoffisiell=True, dryrun=False, miljo='prodles', skrivmiljo='prodskriv', pw=''  )
    # retthull_skrivnvdb( 301, inkluder_uoffisiell=True, dryrun=False, miljo='testles', skrivmiljo='testskriv', pw=''   )
    # retthull_skrivnvdb( 301, inkluder_uoffisiell=True, dryrun=False, miljo='testles' )
    # retthelefylket( 15, inkluder_uoffisiell=True, dryrun=False, miljo='prodles', skrivmiljo='prodskriv', pw=''  )

    print(f"Total kjøretid:  {datetime.now()-t0}")