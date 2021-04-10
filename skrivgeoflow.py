import json
from copy import deepcopy
from datetime import datetime

import pandas as pd 
import geopandas as gpd 


import STARTHER
import nvdbapiv3
import skrivnvdb 

# Laster inn geometri 
geom = gpd.read_file( '../trondheim_sentrum.gpkg')
sentrumwkt          = str( geom[  geom['navn'].str.contains( 'sentrum') ].geometry.iloc[0] )
utenomsentrumwkt    = str( geom[ ~geom['navn'].str.contains( 'sentrum') ].geometry.iloc[0] )

sentrum_egenskaper = [ 
    { "typeId" : 12121, "verdi" : [   "Trondheim sentrum" ] },                      # Navn
    { "typeId" : 12122, "verdi" : [   "Test objekt for GeoFlow test database" ] },  # Beskrivelse
    { "typeId" : 12123, "verdi" : [   "05:00:00" ] }, # Tidsrom_standard1_fra_kl
    { "typeId" : 12124, "verdi" : [   "07:00:00" ] }, # Tidsrom_standard1_til_kl
    { "typeId" : 12125, "verdi" : [   "07:00:00" ] }, # Tidsrom_rush1_fra_kl
    { "typeId" : 12126, "verdi" : [   "09:00:00" ] }, # Tidsrom_rush1_til_kl
    { "typeId" : 12127, "verdi" : [   "09:00:00" ] }, # Tidsrom_standard2_fra_kl
    { "typeId" : 12128, "verdi" : [   "15:00:00" ] }, # Tidsrom_standard2_til_kl
    { "typeId" : 12129, "verdi" : [   "15:00:00" ] }, # Tidsrom_rush2_fra_kl
    { "typeId" : 12130, "verdi" : [   "18:00:00" ] }, # Tidsrom_rush2_til_kl 
    { "typeId" : 12131, "verdi" : [   "18:00:00" ] }, # Tidsrom_standard3_fra_kl
    { "typeId" : 12132, "verdi" : [   "21:00:00" ] }, # Tidsrom_standard3_til_kl
    { "typeId" : 12133, "verdi" : [   "1" ] },        # Km_avgift_standard_kjt_gruppe1
    { "typeId" : 12134, "verdi" : [   "3" ] },        # Takst for kjøring utenfor rushtid (NOK per utkjørt kilometer) for kjøretøygruppe 2
    { "typeId" : 12135, "verdi" : [   "3" ] },        # Km_avgift_rush_kjt_gruppe1
    { "typeId" : 12136, "verdi" : [   "9" ] },        # Km_avgift_rush_kjt_gruppe2
    { "typeId" : 12137, "verdi" : [   "10" ] },       # Innkjøringsavgift_standard_kjt_gruppe1
    { "typeId" : 12138, "verdi" : [   "30" ] },       # Innkjøringsavgift_standard_kjt_gruppe2
    { "typeId" : 12139, "verdi" : [   "20" ] },       # Innkjøringsavgift_rush_kjt_gruppe1
    { "typeId" : 12140, "verdi" : [   "30" ] },        # Innkjøringsavgift_rush_kjt_gruppe2
    { "typeId" : 12141, "verdi" : [  sentrumwkt  ] }      # Geometri, flate
]

sentrum_stedfesting = { "linje": [ {    "fra": 0.80247539, 
                                        "til": 0.82648823,
                                        "veglenkesekvensNvdbId": 72812
                           } ]
                        }

utenfor_stedfesting = { "linje": [ {    "fra": 0.00196773, 
                                        "til": 0.05164728,
                                        "veglenkesekvensNvdbId": 42694
                           } ]
                        }

utenfor_egenskaper = [ 
    { "typeId" : 12121, "verdi" : [   "Trondheim utenfor sentrum" ] },              # Navn
    { "typeId" : 12122, "verdi" : [   "Test objekt for GeoFlow test database" ] },  # Beskrivelse
    { "typeId" : 12123, "verdi" : [   "05:00:00" ] }, # Tidsrom_standard1_fra_kl
    { "typeId" : 12124, "verdi" : [   "07:00:00" ] }, # Tidsrom_standard1_til_kl
    { "typeId" : 12125, "verdi" : [   "07:00:00" ] }, # Tidsrom_rush1_fra_kl
    { "typeId" : 12126, "verdi" : [   "09:00:00" ] }, # Tidsrom_rush1_til_kl
    { "typeId" : 12127, "verdi" : [   "09:00:00" ] }, # Tidsrom_standard2_fra_kl
    { "typeId" : 12128, "verdi" : [   "15:00:00" ] }, # Tidsrom_standard2_til_kl
    { "typeId" : 12129, "verdi" : [   "15:00:00" ] }, # Tidsrom_rush2_fra_kl
    { "typeId" : 12130, "verdi" : [   "18:00:00" ] }, # Tidsrom_rush2_til_kl 
    { "typeId" : 12131, "verdi" : [   "18:00:00" ] }, # Tidsrom_standard3_fra_kl
    { "typeId" : 12132, "verdi" : [   "21:00:00" ] }, # Tidsrom_standard3_til_kl
    { "typeId" : 12133, "verdi" : [   "0.5" ] },      # Km_avgift_standard_kjt_gruppe1
    { "typeId" : 12134, "verdi" : [   "1.5" ] },      # Takst for kjøring utenfor rushtid (NOK per utkjørt kilometer) for kjøretøygruppe 2
    { "typeId" : 12135, "verdi" : [   "1.5" ] },      # Km_avgift_rush_kjt_gruppe1
    { "typeId" : 12136, "verdi" : [   "4.5" ] },      # Km_avgift_rush_kjt_gruppe2
    { "typeId" : 12137, "verdi" : [   "5" ] },        # Innkjøringsavgift_standard_kjt_gruppe1
    { "typeId" : 12138, "verdi" : [   "15" ] },       # Innkjøringsavgift_standard_kjt_gruppe2
    { "typeId" : 12139, "verdi" : [   "10" ] },       # Innkjøringsavgift_rush_kjt_gruppe1
    { "typeId" : 12140, "verdi" : [   "30" ] },        # Innkjøringsavgift_rush_kjt_gruppe2
    { "typeId" : 12141, "verdi" : [  utenomsentrumwkt  ] },        # Geometri, flate
]

tid = datetime.now()

endring_sentrum = { 'stedfesting'           : sentrum_stedfesting, 
                    'gyldighetsperiode'     : {
                                                    "startdato": tid.strftime( '%Y-%m-%d')
                                                },
                    'egenskaper'            : sentrum_egenskaper,
                    'typeId'                : 962, 
                    'tempId'                : 'objekt#1'
                }

endring_utenfor = { 'stedfesting'           : utenfor_stedfesting, 
                    'gyldighetsperiode'     :  {
                                                    "startdato": tid.strftime( '%Y-%m-%d')
                                                },
                    'egenskaper'            : utenfor_egenskaper,
                    'typeId'                : 962, 
                    'tempId'                : 'objekt#2'
                }

endringssett = {    'registrer' : { 
                                    'vegobjekter' : [  endring_sentrum, endring_utenfor  ] 
                                },
                    'datakatalogversjon'    : "2.24" 
                }

skriv = skrivnvdb.endringssett( endringssett )
skriv.forbindelse.velgmiljo( 'stmskriv')
skriv.forbindelse.login( )
skriv.registrer()