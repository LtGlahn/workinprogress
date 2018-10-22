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
            feat['properties']['SKRIV_NSR_QUAY_ID_11310'] and prop['vegobjektid'] not in svarteliste: 
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
            
            if prop['kommune'] not in endringssett.keys():
                endringssett[prop['kommune']] = { 'endringssett' : {  
                                                      'datakatalogversjon' : '2.15',
                                                      'effektDato': datetime.datetime.today().strftime('%Y-%m-%d'),
                                                      'delvisOppdater': {'vegObjekter': [] }
                                                    }  
                                                }
                
            
            endringssett[prop['kommune']]['endringssett']['delvisOppdater']['vegObjekter'].append( nyttobj)
    
    return endringssett

if __name__ == '__main__':
    
    miljo = 'utv'
    skriveapi = skrivnvdb.apiskrivforbindelse(miljo=miljo)
    skriveapi.login( username='jajens', pw='skr.vNvdb3mye', miljo=miljo)
    skriv = skrivnvdb.endringssett( )
    skriv.lag_forbindelse( apiskriv=skriveapi)
    
    
    mydataset = '../data/resultater_Norge_v2.gpkg'
    endringssett = {}
    
    
    for layername in fiona.listlayers( mydataset): 
        with fiona.open(mydataset, layer=layername ) as src: 
            print( layername, len(src))
            
            # Søker etter egenskapsnavn med ordet SKRIV
            if [k for k in src.schema['properties'] if 'SKRIV' in k]: 
                endringssett = finnskrivelag( endringssett, src)
#%% ## Skriveprosess
                
    for komm in endringssett: 
        pass
    
        # komm = 'Flesberg'
        skriv.data = endringssett[komm]['endringssett']
        skriv.registrer()
        skriv.startskriving()
        sleep(30)
        skriv.sjekkfremdrift()
        endringssett[komm]['fremdrift'] = skriv.status
        endringssett[komm]['skrivurl'] = skriv.minlenke
        endringssett[komm]['sistsjekket'] = datetime.datetime.today().isoformat()
        r = skriveapi.les( skriv.minlenke )    
        b = r.json()
        endringssett[komm]['detaljertstatus'] = b['status']
    

#%% Lagre resultater.... 
    fn = '../data/endringssett/skriv_' + miljo + '_' + datetime.datetime.today().strftime('%Y-%m-%d') + '.json'
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
    
#%% 
