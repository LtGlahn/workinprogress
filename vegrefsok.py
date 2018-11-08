# -*- coding: utf-8 -*-
import nvdbapi



vegref = {
	"fylke": 12,
	"kommune": 0,
	"kategori": "E",
	"status": "V",
	"nummer": 39,
	"hp": 26,
	"fra_meter": 8961,
	"til_meter": 9186,
	"kortform": "1200 Ev39 hp26 m8961-9186"
}

def vegref2string( vegref ): 
    """
    Formatterer vegreferanse-spørring mot NVDB api ut fra kjent objekt
    
    http://api.vegdata.no/parameter/lokasjonsfilter.html
    http://api.vegdata.no/verdi/vegreferanse.html 
    
    Arguments: vegref. En dictionary med et objekts vegreferanse, på den 
        strukturen som NVDB api serverer
        
    Keywords: None
    
    Returns: En tekststreng som kan brukes i vegreferanse-søk 
    """
        
    vegrefstring = str( vegref['fylke']).zfill(2) + \
                str(vegref['kommune']).zfill(2) + \
                vegref['kategori'] + vegref['status'] + \
                str( vegref['nummer']) + 'hp' + str( vegref['hp'] ) + \
                'm' + str( vegref['fra_meter']) + '-' + \
                str( vegref['til_meter'])
                
    return vegrefstring                
                
# params = { 'fylke' : vegref['fylke'], 'vegreferanse' : vegrefstring }
vegrefstring = vegref2string( vegref)
params = { 'vegreferanse' :  vegrefstring}

ul = nvdbapi.nvdbFagdata(570)
ul.addfilter_geo( params)
enulykke = ul.nesteForekomst()
print( ul.antall, 'ulykker på', vegrefstring )

# Mer komplekst eksempel, sammensatte vegreferanser. 
# Her tunnelløp for Kvisvstullenne
kvivstunn = nvdbapi.finnid( 359579733 )
vegrefsok = []
for vegrefelement in kvivstunn['lokasjon']['vegreferanser']: 
    vegrefsok.append( vegref2string( vegrefelement))
    
params = { 'vegreferanse' : vegrefsok }

ul = nvdbapi.nvdbFagdata(570)
ul.addfilter_geo( params)
enulykke = ul.nesteForekomst()
print( ul.antall, "ulykker Kvistunnellen på strekningen", ','.join( vegrefsok ))


# Repeterer for Jernfjelltunnellen
jernfjelltunn = nvdbapi.finnid( 82294662, kunfagdata=True)
vegrefsok = []
for vegrefelement in jernfjelltunn['lokasjon']['vegreferanser']: 
    vegrefsok.append( vegref2string( vegrefelement))
ul = nvdbapi.nvdbFagdata(570)
ul.addfilter_geo( { 'vegreferanse' : vegrefsok })
enulykke = ul.nesteForekomst()
print( ul.antall, "ulykker Jernfjelltunnellen på strekningen", ','.join( vegrefsok ))


# Og til sist for Sandviktunnelen
sandvikstunn = nvdbapi.finnid( 82295058, kunfagdata=True)
vegrefsok = []
for vegrefelement in sandvikstunn['lokasjon']['vegreferanser']: 
    vegrefsok.append( vegref2string( vegrefelement))

ul = nvdbapi.nvdbFagdata(570)
ul.addfilter_geo( { 'vegreferanse' : vegrefsok })
enulykke = ul.nesteForekomst()
print( ul.antall, "ulykker Sandvikstunnellen på strekningen", ','.join( vegrefsok ))
