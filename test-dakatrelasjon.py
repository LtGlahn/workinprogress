"""
Tester hva vi får av data om mor-datter relasjoner fra NVDB api LES, med 4 ulike metoder

Leseapi /vegobjekttyper har en del interessante variasjoner i hvordan data om relasjoner presenteres, 
avhengig av om man bruker data fra vegobjekttype.relasjonstyper eller vegobjekttype.egenskapstyper. 
I tillegg er det variasjon etter om man bruker spørringen 
https://nvdbapiles-v3.atlas.vegvesen.no/vegobjekttyper?inkluder=relasjonstyper 
https://nvdbapiles-v3.atlas.vegvesen.no/vegobjekttyper?inkluder=egenskapstyper
(dvs alle samtidig) 
eller om man henter objekttypedefinisjonen for ett enkelt objekt
https://nvdbapiles-v3.atlas.vegvesen.no/vegobjekttyper/<vegobjekttypeId>

Jeg legger på disse attributtene som gjør det littegrann enklere å sortere og filtrere resultatene: 
    struktur_med_innhold_element (JA eller NEI)
    barnTypeId
    barnTypeNavn
    foreldreTypeId
    foreldreNavn
    orginaldata


"""
import requests
import json
from copy import deepcopy
import pdb
import collections

import pandas as pd 

def flatten(d, parent_key='', sep='.'):
    """
    Flater ut nestet dictionary - struktur 
    Hentet fra https://stackoverflow.com/a/6027615 
    """
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def sjekkrelasjon( rel, foreldreTypeId, foreldreNavn): 
    """
    Ser på variasjon i datastruktur for ulike assosiasjonstyper
    """

    retval = deepcopy( rel )


    if 'innhold' in retval:

        retval['struktur_med_innhold_element']  = 'JA'

        if 'vegobjekttypeid' in retval['innhold']: 
            retval['barnTypeId']                    = retval['innhold']['vegobjekttypeid']
        elif 'type' in retval['innhold']: 
            retval['barnTypeId']                    = retval['innhold']['type']['id']
            retval['barnTypeNavn']                  = retval['innhold']['type']['navn']

    else: 
        retval['struktur_med_innhold_element']  = 'NEI'
        if 'type'  in rel: 
            retval['barnTypeId']                    = retval['type']['id']
            retval['barnTypeNavn']                  = retval['type']['navn']

    retval['foreldreTypeId'] = foreldreTypeId
    retval['foreldreNavn'] = foreldreNavn
    retval['orginaldata'] = rel 

    retval = flatten( deepcopy( retval ) )

    return retval


url = 'https://nvdbapiles-v3.atlas.vegvesen.no/vegobjekttyper.json?inkluder=relasjonstyper,egenskapstyper'
r = requests.get( url )
dakat = r.json()

mylist = []
mylist_egenskaper = []
mylist_relasjoner2 = []
mylist_egenskaper2 = []

for dd in dakat: 
    # if 'relasjonstyper' in dd and 'foreldre' in dd['relasjonstyper']: 
    #     for rel in dd['relasjonstyper']['foreldre']: 
    #         mylist.append( sjekkrelasjon( rel ) )


    if 'relasjonstyper' in dd and 'barn' in dd['relasjonstyper']: 
        for rel in dd['relasjonstyper']['barn']: 
            mylist.append( sjekkrelasjon( rel , dd['id'], dd['navn'] ))

    if 'egenskapstyper' in dd: 
        for eg in dd['egenskapstyper']:
            if eg['id'] > 100000 and eg['id'] not in [500001, 500002]:
                mylist_egenskaper.append( sjekkrelasjon( eg, dd['id'], dd['navn']) )

    # Sjekker hva vi får når vi henter objekttypen direkte 
    print( f'Henter objekttypedefinisjon {dd["id"]} {dd["navn"]} ')
    r2 = requests.get( 'https://nvdbapiles-v3.atlas.vegvesen.no/vegobjekttyper/' + str( dd['id']  ) + '.json?inkluder=alle' )
    dd2 = r2.json()
    if 'relasjonstyper' in dd2 and 'barn' in dd2['relasjonstyper']: 
        for rel in dd2['relasjonstyper']['barn']: 
            mylist_relasjoner2.append( sjekkrelasjon( rel , dd2['id'], dd2['navn'] ))

    if 'egenskapstyper' in dd2: 
        for eg in dd2['egenskapstyper']:
            if eg['id'] > 100000 and eg['id'] not in [500001, 500002]:
                mylist_egenskaper2.append( sjekkrelasjon( eg, dd2['id'], dd2['navn']) )


######################################################### 
#### Dataaanalyse

mydf_relasjon = pd.DataFrame( mylist )
mydf_egenskaper = pd.DataFrame( mylist_egenskaper )
mydf_relasjon2 = pd.DataFrame( mylist_relasjoner2 )
mydf_egenskaper2 = pd.DataFrame( mylist_relasjoner2 )


# Disse 6 elementene har jeg sjøl lagt på (navn og ID mor-relasjon, f.eks)
# Fjernes fra analysen hvor vi sammenligner navn på dataelementer
mycols = { 'struktur_med_innhold_element', 'barnTypeId', 'barnTypeNavn', 'foreldreTypeId', 
            'foreldreNavn', 'orginaldata' }

print( "Sammenligner barn-relasjoner fra vegobjekttype.relasjonstyper hentet fra vegobjekttyper?inkluder=egenskapsverdier vs vegobjekttype/ID")
print( "IDENTISKE kolonnenavn vegobjekttyper?inkluder=egenskapsverdier vs vegobjekttype/ID")
relcol1 = set( list( mydf_relasjon.columns ))  - mycols
relcol2 = set( list( mydf_relasjon2.columns )) - mycols
tmp = [ print( '\t',  x ) for x in sorted(( set.intersection( relcol1, relcol2) )) if not 'orginaldata' in x ]

# Samme resultat uansett metode for å hente data
tmp = [  x  for x in sorted(( set.symmetric_difference( relcol1, relcol2) )) if not 'orginaldata' in x ]
if len( tmp ) == 0: 
    print( 'Ser ut som datastruktur for vegobjekttype.relasjonstyper er identisk når vi henter data fra vegobjekttyper?inkluder=egenskapsverdier vs vegobjekttype/ID')
else: 
    print( "AVVIK kolonnenavn relasjonsdata fra egenskapsverdier for vegobjekttyper?inkluder=egenskapsverdier vs vegobjekttype/ID")
    tmp2 = [ print( '\t',  x ) for x in tmp ]


print( "\n\nSammenligner egenskapsverdier om relasjoner som vi får fra vegobjekttyper?inkluder=egenskapsverdier vs vegobjekttype/ID")
egcol1 = set( list( mydf_egenskaper.columns  )) - mycols
egcol2 = set( list( mydf_egenskaper2.columns )) - mycols 
print( "IDENTISKE kolonnenavn relasjonsdata fra egenskapsverdier for vegobjekttyper?inkluder=egenskapsverdier vs vegobjekttype/ID")
tmp = [ print( '\t',  x ) for x in  sorted( list( set.intersection( egcol2, egcol1) )) if not 'orginaldata' in x  ]
print( "AVVIK kolonnenavn relasjonsdata fra egenskapsverdier for vegobjekttyper?inkluder=egenskapsverdier vs vegobjekttype/ID")
tmp = [ print( '\t',  x ) for x in sorted( list( set.symmetric_difference( egcol2, egcol1) )) if not 'orginaldata' in x ]


# wr = pd.ExcelWriter( 'relasjonsdebug.xlsx' )

# mydf_relasjon.to_excel(   wr, sheet_name='Fra relasjonselement',       index=False )
# mydf_egenskaper.to_excel( wr, sheet_name='Fra egenskaper',             index=False )
# mydf_relasjon2.to_excel(   wr, sheet_name='Fra relasjonselement 2',    index=False )
# mydf_egenskaper2.to_excel( wr, sheet_name='Fra egenskaper 2',          index=False )

# wr.save()
