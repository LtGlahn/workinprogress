# -*- coding: utf-8 -*-
"""
Created on Wed Oct 10 09:41:16 2018

@author: jajens
"""



import json
from copy import deepcopy
import datetime
from time import sleep

import ipdb
import fiona


import skrivnvdb

def finnskrivelag( endringssett, gpkglayer): 
    
    with open( 'svarteliste.json' ) as f: 
        svarteliste = json.load( f)
    
    for feat in gpkglayer: 
        if 'SKRIV_NSR_QUAY_ID_11310' in feat['properties'] and \
            feat['properties']['SKRIV_NSR_QUAY_ID_11310'] and \
            feat['properties']['vegobjektid'] not in svarteliste: 
                
            prop = feat['properties']
            
            nye_egenskaper = [  { 'typeId' : 11310, 
                                 'verdi' : [ prop['SKRIV_NSR_QUAY_ID_11310'] ], 
                                 'operasjon' : 'oppdater' 
                                 } ]
            
            
            
            if prop['NSR_Stopplace_Navn'] != prop['entur_morstopp_stop_name']:
                nye_egenskaper.append(  { 'typeId' : 10885, 
                                         'verdi' : [prop['entur_morstopp_stop_name']], 
                                         'operasjon' : 'oppdater' 
                                        }  )
    
            if prop['NSR_Stopplace_ID']  != prop['entur_parent_station']: 
                nye_egenskaper.append( { 'typeId' : 11309, 
                                        'verdi' : [prop['entur_parent_station']], 
                                        'operasjon' : 'oppdater' 
                                        })
            
            # print( prop['vegobjektid'], prop['versjonid'], \
            #      nye_egenskaper)
    
            nyttobj = { 'typeId' : 487, 
                       'nvdbId' : prop['vegobjektid'], 
                       'versjon' : prop['versjonid'], 
                        'egenskaper' : nye_egenskaper
                    }
            
            if prop['vegobjektid'] in endringssett: 
                print( prop['vegobjektid'], 'er allere i endringssett!' )
            
            endringssett[prop['vegobjektid']] = { 'endringssett' : {  
                                                      'datakatalogversjon' : '2.14',
                                                      'effektDato': datetime.datetime.today().strftime('%Y-%m-%d'),
                                                      'delvisOppdater': {'vegObjekter': [ nyttobj ] }
                                                    }  
                                                }
                
            
             
    
    return endringssett

if __name__ == '__main__':
    
    
    mydataset = '../data/resultater_Norge_v2.gpkg'
    endringssett = {}
    
    
    for layername in fiona.listlayers( mydataset): 
        with fiona.open(mydataset, layer=layername ) as src: 
            print( layername, len(src))
            
            # Søker etter egenskapsnavn med ordet SKRIV
            if [k for k in src.schema['properties'] if 'SKRIV' in k]: 
                endringssett = finnskrivelag( endringssett, src)

#%% Pålogging UTV 
                
    miljo = 'utv'
    skriveapiUTV = skrivnvdb.apiskrivforbindelse(miljo=miljo)
    skriveapiUTV.login( username='jajens', pw='skr.vNvdb3mye', miljo=miljo, klient='487test')
    skriv = skrivnvdb.endringssett( )
    skriv.lag_forbindelse( apiskriv=skriveapiUTV)

#%% Pålogging TESTPROD
    testprod = skrivnvdb.apiskrivforbindelse(miljo=miljo)
    testprod.login( username='jajens', pw='skr.vNvdb3mye', miljo='test', klient='487test')
    endrTEST = skrivnvdb.endringssett( )
    endrTEST.lag_forbindelse( apiskriv=testprod)

    
#%% Pålogging PROD
#    skriv = skrivnvdb.endringssett()
#    skriv.lag_forbindelse( )
    skriv.forbindelse.login( username='jajens', pw='***', miljo='prod', klient='487fiksNSRid_v1')
    
#%% ## Skriveprosess
                
    for komm in endringssett: 
        pass
    
        # komm = 'Flesberg'
        skriv.data = endringssett[komm]['endringssett']
        skriv.registrer()
        skriv.startskriving()
#        skriv.sjekkfremdrift()
#        endringssett[komm]['fremdrift'] = skriv.status
        endringssett[komm]['skrivurl'] = skriv.minlenke
#        endringssett[komm]['sistsjekket'] = datetime.datetime.today().isoformat()
#        r = skriveapi.les( skriv.minlenke )    
#        b = r.json()
#        endringssett[komm]['detaljertstatus'] = b['status']
    
    fn = '../data/endringssett/fiksNSRid_v1_' + miljo + '_' + datetime.datetime.today().strftime('%Y-%m-%d') + '.json'
    with open(fn, 'w', encoding='utf-8') as f: 
        json.dump( endringssett, f, ensure_ascii=False, indent=4)
    
#    {'datakatalogversjon': '2.13',
#                  'effektDato': {'datakatalogversjon': '2.13',
#                  'effektDato': datetime.datetime.today().strftime('%Y-%m-%d'),
#                  'delvisOppdater': {'vegObjekter': []
#                      }
#                  }
#                      }
#                  }
#    
        
#%% Ser igjennom status
        
    with open( fn, encoding='utf-8') as f: 
        skrivelser = json.load( fn)
    
    skrevet = 0
    avvist = 0
    venter = 0
    anna = 0 
    
    for komm in skrivelser: 
        if skrivelser[komm][fremdrift] == "'UTFØRT": 
            skrevet += 1
        elif skrivelser[komm]['fremdrift'] in [ '"VENTER"', '"BEHANDLES"' ]: 
            venter += 1
        elif skrivelser[komm][fremdrift] == "'AVVIST": 
            avvist += 1
        else: 
            anna += 1
            
#%% Logger inn 
    skriveapi.login( username='jajens', pw='skr.vNvdb3mye', miljo=miljo)
#%% Oppdaterer statistikk
    with open( fn, encoding='utf-8') as f: 
        skrivelser = json.load( f)
    
    
    for komm in skrivelser: 
#        if not skrivelser[komm]["fremdrift"] in ['UTFØRT', 'AVVIST' ]: 
        r = skriveapi.les( skrivelser[komm]['skrivurl'])
        b = r.json()
        endringssett[komm]['detaljertstatus'] = b['status']
        endringssett[komm]['sistsjekket'] = datetime.datetime.today().isoformat()
        endringssett[komm]['fremdrift'] = b['status']['fremdrift']
            
    with open(fn, 'w', encoding='utf-8') as f: 
        json.dump( endringssett, f, ensure_ascii=False, indent=4)

#%% Sjekker dem som er avvist: 
    with open( fn, encoding='utf-8') as f: 
        skriverier = json.load( f)

    avviste = []
    for komm in skriverier: 
        if 'AVVIST'  in skriverier[komm]["fremdrift"]: 
            avviste.append( skriverier[komm] )
    
    advarsler = []
    av = avviste[2]
    for vo in av['detaljertstatus']['resultat']['vegObjekter']: 
        if vo['feil']: 
            print( vo['nvdbId'], vo['feil'] )
            
        for adv in vo['advarsel']: 
            if adv['melding'] not in advarsler: 
                advarsler.append( adv['melding'])
            

#%% Finner ikke ut av ett av endringssettene, prøver ett og ett
## https://www.utv.vegvesen.no/nvdb/apiskriv/rest/v2/endringssett/41cc300e-3828-4d2a-b0d6-8b5df12eb3dc

    nyttskriv = skrivnvdb.endringssett()
    nyttskriv.lag_forbindelse()
    nyttskriv.forbindelse.login( username='jajens', pw='skr.vNvdb3mye', miljo='utv')
    
#%% Kjører på... 
    for vo in av['endringssett']['delvisOppdater']['vegObjekter']: 
        nyttskriv.data = {    "delvisOppdater": { "vegObjekter": [ vo ]}, 
            "effektDato": datetime.datetime.today().strftime('%Y-%m-%d'),
            "datakatalogversjon": "2.15"
        }    
        nyttskriv.registrer()
        nyttskriv.startskriving()
        sleep(2)    
    
#%% Avvist pga versjonskonflikt eller endringsdato, skriver disse på ny: 

avvist = ['https://www.vegvesen.no/nvdb/apiskriv/rest/v2/endringssett/6a4acf51-cbe5-4cb2-a17b-0644612b6034',
'https://www.vegvesen.no/nvdb/apiskriv/rest/v2/endringssett/caaf686a-d445-45cf-91bb-1cb3a5ab3e48',
'https://www.vegvesen.no/nvdb/apiskriv/rest/v2/endringssett/47340e41-9924-4642-8d8e-d6952898169f',
'https://www.vegvesen.no/nvdb/apiskriv/rest/v2/endringssett/1f8789dc-1e8f-457f-9dea-bd21ed21d669',
'https://www.vegvesen.no/nvdb/apiskriv/rest/v2/endringssett/62242cb0-acec-4b83-af5e-ec5a693ee2ad',
'https://www.vegvesen.no/nvdb/apiskriv/rest/v2/endringssett/24d2f2de-b742-478e-b04e-0eb6265630c1',
'https://www.vegvesen.no/nvdb/apiskriv/rest/v2/endringssett/2c3cb367-14a0-4d5c-9c0a-91f968d1f17e',
'https://www.vegvesen.no/nvdb/apiskriv/rest/v2/endringssett/ed33692a-1e91-4b09-a669-aedcccc91085',
'https://www.vegvesen.no/nvdb/apiskriv/rest/v2/endringssett/15a3330e-f760-44cd-b478-99c19ac00adb',
'https://www.vegvesen.no/nvdb/apiskriv/rest/v2/endringssett/433ed522-104d-443e-9095-ffca2b422f9a',
'https://www.vegvesen.no/nvdb/apiskriv/rest/v2/endringssett/3a609e75-b234-4a48-81e6-83bce14f556f',
'https://www.vegvesen.no/nvdb/apiskriv/rest/v2/endringssett/2dd53375-a9b2-412b-8139-9de867229953',
'https://www.vegvesen.no/nvdb/apiskriv/rest/v2/endringssett/8ddd3721-b491-4477-9d68-27f3da8f3ad5',
'https://www.vegvesen.no/nvdb/apiskriv/rest/v2/endringssett/2affe45d-8191-4cda-adb3-72a9eacf4a05' ]

# avvist.pop(0 )
# avvist.pop(0)
for minav in avvist: 
    r = skriv.forbindelse.les( minav)
    av = r.json()
    minid = av['delvisOppdater']['vegObjekter'][0]['nvdbId']
    r = skriv.forbindelse.les( skriv.forbindelse.apiurl + '/nvdb/api/v2/vegobjekter/487/' + str( minid)) 
    minversjon = r.json()['metadata']['versjon']
    # print( av['delvisOppdater'])
    av['delvisOppdater']['vegObjekter'][0]['versjon'] = minversjon
    skriv.data = {  
                      'datakatalogversjon' : '2.14',
                      'effektDato': datetime.datetime.today().strftime('%Y-%m-%d'),
                      'delvisOppdater': av['delvisOppdater']
                    }  
    
    skriv.registrer()
    skriv.startskriving()

#%% Låser. 
    
    
# Låser for 487fiksNSRid_v1
venter_v1 = [ '0b50e1aa-b4c4-4684-ad29-cb231619210a',
'19280243-7b3f-46ec-917d-bde297a094d9',
'8ce9a452-64d0-497f-b01b-c14f16f8ae45',
'e840716d-7d94-4c65-b879-a4823e6aae2d',
'6239ce1f-9f59-4f1d-969c-ec57b7301f4a',
'49d967e7-46ce-49db-9567-2bc25b000b32',
'ac22e1e4-d2cc-481f-a583-077f89c789af',
'ce362e9f-6f8f-46f0-8fd7-9c1f64f44a74',
'4f3cca00-854c-47e1-bd29-5db52eb35df0',
'cee0d308-f64f-48b0-b9dc-41433dc94e6a',
'7efbd267-3f4c-4ba8-b76c-a07896c3b9fc',
'db044fb1-48fe-4178-8d4a-7b1cddf800c6',
'418077ee-bde5-44a3-a5f3-2bbfbe80031d',
'1beb8f84-53eb-42f0-aac4-15d82a5c0b09',
'12cd5c20-ef5b-45e7-b1b0-fcb2d652490f',
'7022a3b1-a5fd-45a6-9914-d91110073014',
'4885f6ae-ab14-4e45-8937-f5c6b57b788d',
'13555a25-979c-4c10-bb90-f713ceece952' ]

# Låser for 487fiksNSRid_v0
venter_v0 = [ '973e9af0-6e96-4c55-ae9c-6810e194f5b1',
'711fa3e7-54e0-4514-bf9e-98dade57ebc6',
'a8fbb36c-8531-4210-8e58-c8e7e1e86c0e',
'0936598a-3ce7-4672-9f2f-4ad0ffc1e714',
'6ec2f944-f352-4f64-ab16-11b90578720a',
'ee3bf39d-1378-49ff-b52f-cdd56b1e871b',
'8f9545f6-3f43-451d-a40b-513a03f6487d' ]

venter = venter_v1 + venter_v0


godkjent = "84dee3b9-714e-46ce-9a23-ed5564241cd0"
# https://www.vegvesen.no/nvdb/apiskriv/rest/v2/endringssett/84dee3b9-714e-46ce-9a23-ed5564241cd0

r = skriv.forbindelse.les( skriv.forbindelse.apiurl + '/nvdb/apiskriv/rest/v2/endringssett/' + godkjent)
b = r.json()

venteliste = []

for vent in venter: 
    r = skriv.forbindelse.les( skriv.forbindelse.apiurl + '/nvdb/apiskriv/rest/v2/endringssett/' + vent)
    b = r.json()
    if not b['status']['fremdrift'] == 'UTFØRT': 
        for vegobj in b['delvisOppdater']['vegObjekter']: 
            venteliste.append( vegobj['nvdbId'] )

print( len( venteliste), 'objekter på venteliste')

with open( 'venteliste.json', 'w') as f: 
    json.dump( venteliste, f, indent=4)