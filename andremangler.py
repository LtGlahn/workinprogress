"""
Diverse håndtering av andre typer mangelrapporter 
"""

import pandas as pd
import geopandas as gpd
from shapely import wkt
from deepdiff import DeepDiff

import STARTHER
import nvdbapiv3
import mangelrapport

def konverterdato( datostr ): 
    """Konverter datoformat med punktum 2022.03.24 => ISO 2022-03-24"""
    if datostr and isinstance( datostr, str): 
        datostr = datostr.replace( '.', '-')
    return datostr 


def sammenlignegenskaper( egenskaper1:list, egenskaper2:list ): 
    """
    Sammenligner egenskapverdier for to ulike objekt(versjon)er fra NVDB api
    

    ARGUMENTS
        egenskaper1, egenskaper2: Liste med egenskapverdier hentet rått fra NVDB api LES. Antar at egenskaper2 er den nyeste 
        og sannsynligvis den som er verdt å ta vare på. Så data som finnes i egenskaper2, men ikke i egenskaper1 regnes som 
        et svært positivt resultat. 

    RETURNS
        TBD - work in progress. Trolig tuple med (Boolean, diverse aggregeringer av differanser)
        p.t (ddiff, eg1, eg2 )

        der ddiff : Resultat fra deepdiff - sammenligning av dictionary
        eg1, eg2 : Dictionary med egenskapsverdier  
    """

    eg1 = { x['id'] : x for x in egenskaper1 }
    eg2 = { x['id'] : x for x in egenskaper2 }

    ddiff = DeepDiff( eg1, eg2)
    # eg1set = set( eg1.keys())
    # eg2set = set( eg2.keys())

    # kunEg1 = eg1set.difference( eg2 )
    # kunEg2 = eg2set.difference( eg1 )

    if not ddiff: 
        identiske = True 
    else: 
        identiske = False

    return( ddiff, eg1, eg2 )


def ddiff_klassifiseregenskap( ddiff_key:str, ddiff_val:dict, eg1:dict, eg2:dict  ):
    pass

def relasjonstre2gpkg( gisObjekter:list, filnavn ):
    """
    Lagrer liste med "gisvennlige" objekter fra skrivRelasjonstre som geopackage 
    """

    assert isinstance( gisObjekter, list), "Feil format - inputdata må være en liste"
    assert len( gisObjekter ) > 0, "Tom liste med inputdata"
    assert isinstance( gisObjekter[0], dict ), "Feil inputformat, må være liste med dictionary"
    # assert 'geometri' in gisObjekter[0], "Feil inputformat, dictionary i liste må ha geometri"
    assert 'kartlag' in gisObjekter[0], "Feil inputformat, dictionary må ha egenskap 'kartlag' "
    assert isinstance( filnavn, str), "Filnavn må være en tekststreng"
    assert '.gpkg' in filnavn[-6:].lower(), "Filnavn må ha filetternavn .gpkg (geopackage filformat)"

    alleKartlag = set( [ x['kartlag'] for x in gisObjekter ] )

    for kartlag in alleKartlag: 
        data = [x for x in gisObjekter if 'kartlag' in x and x['kartlag'] == kartlag ]
        myDf = pd.DataFrame( data )
        myDf['geometry'] = myDf['geometri'].apply( wkt.loads )  
        likerIkke = ['geometri', 'vegsegmenter', 'kontraktsområder', 'relasjoner']
        for fjern in likerIkke: 
            if fjern in myDf.columns: 
                myDf.drop( columns=fjern, inplace=True )
        
        myGdf = gpd.GeoDataFrame( myDf, geometry='geometry', crs=5973 )
        myGdf.to_file( filnavn, layer=kartlag, driver='GPKG')


def skrivRelasjonsTre( obj:dict, forb=None, label='' ): 
    """
    Skriver hele relasjonstre fra objektes mor og nedover

    ARGUMENTS
        obj: Dictionary med vegobjekt fra NVDB api LES 

    KEYWORDS: 
        N/A

    RETURNS
        None 
    """
    if not forb: 
        forb = nvdbapiv3.apiforbindelse()

    if isinstance( obj, int): 
        r = forb.les( '/vegobjekt', params={'id' : obj})
        if r.ok: 
            temp = r.json()
            r = forb.les( temp['href'], params={'dybde' : 10, 'inkluder' : 'alle' })
            if r.ok: 
                obj = r.json()
            else: 
                print( f"Kan ikke hente objekt med href {r.url} {r.status_code} {r.text[0:500]} ")
        else: 
            print( f"Kan ikke hente objekt med ID {obj} {r.status_code} {r.text[0:500]} ")

    assert isinstance( obj, dict), f"Argument må være dictionary eller heltall med ID til et NVDB objekt"
    assert 'id' in obj, f"Ikke gyldig NVDB objekt (må ha ID)"
    assert 'metadata' in obj, f"Ikke gyldig NVDB objekt (må ha metadata)"

    if 'relasjoner' in obj: 
        if 'foreldre' in obj['relasjoner']: 
            if len( obj['relasjoner']['foreldre'] ) > 1: 
                print( f"ADVARSEL - objekt ID {obj['id']} versjon {obj['metadata']['versjon']} "
                                    f" har {len(obj['relasjoner']['foreldre'])} av ulik type")
            for forelder in obj['relasjoner']['foreldre']: 
                if len( forelder['vegobjekter']) > 1: 
                    print( f"ADVARSEL - objekt ID {obj['id']} versjon {obj['metadata']['versjon']} "
                                              f"har {len(forelder['vegobjekter'])} av type "
                                              f"{forelder['type']['id']} {forelder['type']['navn']}  ")
                    
                for enForelderId in forelder['vegobjekter']: 

                    r = forb.les( '/vegobjekt', params={'id' : str( enForelderId ) } )
                    if r.ok: 
                        mor = r.json()
                        sluttdato = '----      '
                        if 'sluttdato' in mor['metadata']:
                            sluttdato = mor['metadata']['sluttdato'] 
                        print( f"Mor-objekt {mor['id']} versjon {mor['metadata']['versjon']}"
                              f" {mor['metadata']['startdato']} {sluttdato} {mor['metadata']['type']['id']} {mor['metadata']['type']['navn']} " )

                    else: 
                        print( f"Kan ikke hente morobjekt {enForelderId} av type f{forelder['type']['id']} {forelder['type']['navn']}  ")

        else: 
            print( f"(Ingen foreldre for objekt ID {obj['id']} versjon {obj['metadata']['versjon']} )")

        
        gisData =  skrivBarnRelasjon( obj, label=label ) 

    else: 
        print( f"Objekt ID {obj['id']} har ingen relasjoner" )

    return gisData

def skrivBarnRelasjon( obj:dict, level=0, forb=None, label='' ):
    """
    Rekursivt skriver ut relasjonstre, for dette objektet og så rekursivt for alle barn 
    """
    gisData = []

    if not forb: 
        forb = nvdbapiv3.apiforbindelse()

    

    assert isinstance( obj, dict), f"Argument må være dictionary"
    assert 'id' in obj, f"Ikke gyldig NVDB objekt (må ha ID)"
    assert 'metadata' in obj, f"Ikke gyldig NVDB objekt (må ha metadata)"

    sluttdato = '----      '
    if 'sluttdato' in obj['metadata']: 
        sluttdato = obj['metadata']['sluttdato'] 


    # prefix = '    '
    # for i in range( 0, level): 
    #     prefix += '    '
    # print( f"{prefix}{label} {obj['metadata']['startdato']} {sluttdato}" )

    label +=  f"{obj['metadata']['type']['id']} {obj['metadata']['type']['navn']} {obj['id']} v{obj['metadata']['versjon']} "
    print( f"{label}{obj['metadata']['startdato']} {sluttdato}" )

    gisvennligVegobjekt = nvdbapiv3.nvdbfagdata2records( obj, vegsegmenter=False, geometri=True, relasjoner=False  )[0]
    gisvennligVegobjekt['relasjontre'] = label
    if '=>' in label: 
        gisvennligVegobjekt['tagg'] = label.split( '=>')[0] + '-> ' + label.split( '=>')[-1]
        gisvennligVegobjekt['kartlag'] = label.split( '=>')[0] + '-> ' + ' '.join( label.split('=>')[-1].split()[0:-2])
    else: 
        gisvennligVegobjekt['tagg'] = label
        gisvennligVegobjekt['kartlag'] = label
    gisData.append( gisvennligVegobjekt )

    # prefix += '    '
    if 'relasjoner' in obj and 'barn' in obj['relasjoner']: 
        for barn in obj['relasjoner']['barn']: 
            # print( f"{prefix}=> {len( barn['vegobjekter'])} døtre av typen {barn['type']['id']} {barn['type']['navn']} ")
            for vegobjekt in barn['vegobjekter']: 
                if not isinstance( vegobjekt, dict):                     
                    r = forb.les( '/vegobjekt', params={'id': str( vegobjekt )})
                    if r.ok: 
                        tmp = r.json()
                        r = forb.les( tmp['href'], params={'dybde' : 10 }) 
                        if r.ok: 
                            vegobjekt = r.json()
                        else: 
                            print( f"Feil ved henting av data {r.url} {r.status_code}")
                            break 
                nylabel = label+f"=> "

                temp = skrivBarnRelasjon( vegobjekt, level=level+1, forb=forb, label=nylabel )
                gisData.extend( temp )
    return gisData


def skrivAlleRelasjonstre( objektId:int, forb=None, skrivGPKG=False, gpkgfilnavn='' ): 
    """
    Skriver ut relasjonstrær for de ulike versjonene av et objekt 

    ARGUMENTS
        objektId - int: NVDB ID til objektet som skal undersøkes

    KEYWORDS
        forb : None eller et objekt av typen nvdbapiv3.apiforbindelse, som håndterer kommunikasjon mot LES 
    
    RETURNS
        none 

    """
    
    if not forb: 
        forb = nvdbapiv3.apiforbindelse()

    if isinstance( objektId, float): 
        objektId = int( objektId )

    assert isinstance( objektId, int), "Argument objektId må være heltall"

    gisData = []

    r = forb.les( '/vegobjekt', params={'id' : str( objektId ) } )

    if r.ok: 
        siste_objdata = r.json()

        if 'href' in siste_objdata: 
            siste_objektversjon = int( siste_objdata['href'].split('/')[-1] )
            data = []
            for vid in range( 1, siste_objektversjon+1): 
                r2 = forb.les( '/vegobjekter/' + str( siste_objdata['metadata']['type']['id'] ) + '/' + 
                                str( objektId) + '/' + str(vid), params={'dybde' : 10, 'inkluder' : 'alle' } )
                if r2.ok: 
                    data.append( r2.json() )
                else: 
                    print( f"Fant ikke data: {r2.url}")
                    data.append( { 'id' : objektId, 'href' : '',  'metadata' : { 'startdato' : '---- -- -- ---- -- -- <= MANGLER / trolig fjernet?', 'versjon' : vid } }  )

            # Ser om det ligger noen høyere versjoner på lur, vet aldri? 
            for vid in range( siste_objektversjon+1, siste_objektversjon+2):
                r2 = forb.les( '/vegobjekt/' + str( siste_objdata['metadata']['type']['id'] ) + '/' + str( objektId) )
                if r2.ok: 
                    data.append( r2.json() )
                

            print( f"Versjoner for NVDB objektid {objektId} type { siste_objdata['metadata']['type']['id']} {siste_objdata['metadata']['type']['navn']}  ")
            navneliste = [ 'Anders ', 'Beate ', 'Cecilie ', 'David ', 'Einar ', 'Fride ', 'Gunnar ', 'Hilde ', 'Ingunn ', 'Katrine ']

            for i, obj in enumerate(data): 
                print( obj['href'])
                temp = skrivRelasjonsTre( obj, forb=forb, label = f"{navneliste[i]} " )
                gisData.extend( temp ) 

        else: 
            print( f"Ugyldig svar på spørring {r.url} \n{r.text[:250]}.... ")
    else: 
        print( f"Kan ikke hente NVDB objekt {objektId} : http { dekodLesFeilmelding( r ) } ")

    if skrivGPKG: 
        if not gpkgfilnavn: 
            gpkgfilnavn = f"relasjonstre{str(siste_objdata['metadata']['type']['id'])}_{str(siste_objdata['id'])}_alleversjoner.gpkg"
        
        relasjonstre2gpkg( gisData, gpkgfilnavn )

    return gisData


if __name__ == '__main__': 

    mydf = pd.DataFrame( mangelrapport.lesLoggfil( 'doubleVersions_20220610.LOG'  )   )

    # Fjerner spor- og jevnhetsmålinger
    mydf = mydf[ mydf['FeatureTypeId'] != 524 ]
    mydf = mydf[ mydf['FeatureTypeId'] != 525 ]


    data = []
    url = 'https://nvdbapiles-v3.atlas.vegvesen.no/vegobjekter/' 
    params = { 'inkluder' : 'alle' }


    forb = nvdbapiv3.apiforbindelse()
    forb.login( miljo='prodles' )

    utenDuplikat = mydf.drop_duplicates( subset=['FeatureId', 'VersionId'] ).copy()
    utenDuplikat.sort_values( by=[ 'FeatureId', 'VersionId'], ascending=True, inplace=True )    


    mineID = mydf['FeatureId'].unique()

    for minId in mineID: 
        temp = utenDuplikat[ utenDuplikat['FeatureId'] == minId ]
        if len( temp ) != 2: 
            print( f"Fant {len(temp)} rader med FeatureID {minId} ")
        objekttype = temp.iloc[0]['FeatureTypeId']
        eldste_versjon = temp.iloc[0]['VersionId']
        eldste_start = konverterdato( temp.iloc[0]['sdate'] )
        eldste_slutt = konverterdato( temp.iloc[0]['sdate'] ) 
        eldste = forb.les( url + str( objekttype ) + '/' + str(minId) + '/' + str(eldste_versjon), params=params  ).json()
        
        nyeste_versjon = temp.iloc[1]['VersionId']
        nyeste_start = konverterdato( temp.iloc[1]['sdate'] )
        nyeste_slutt = konverterdato( temp.iloc[1]['sdate'] ) 
        nyeste = forb.les( url + str( objekttype ) + '/' + str(minId) + '/' + str(nyeste_versjon), params=params  ).json()

        retval = { 'objekttype' : objekttype, 'objektId' : minId, 'eldste versjon' : eldste_versjon, 'nyeste versjon' : nyeste_versjon   }

        (ddiff, eg1, eg2) = sammenlignegenskaper( eldste['egenskaper'], nyeste['egenskaper'])

        if not ddiff: 
            retval['differanser'] = 'HELT identisk'

        else: 
            retval['differanser'] = ','.join(   list( ddiff.keys() ) )

        retval['ddiff'] = ddiff
        retval['eg1'] = eg1
        retval['eg2'] = eg2  

        data.append( retval )



