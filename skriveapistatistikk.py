import STARTHER
import skrivnvdb
import pandas as pd


def hentendringssett( apiskrivforbindelse, filnavn='test.csv', sokestreng='geosum', antall = 1000, stopp = False): 
    url = 'https://www.vegvesen.no/nvdb/apiskriv/rest/v3/endringssett'
    myparams = { 'max' : antall, 'skip' : 0, 'reverse' : 'false', 'userOrClient' : sokestreng } 
    
    antallTotalt = 1e5 
    firstRound = True
    iterasjon = 0 
    mydata = []
    
    while antallTotalt >  antall * iterasjon: 
    
        myparams['skip'] = antall * iterasjon 
        r0 = apiskrivforbindelse.les( url, params=myparams).json() 
        if iterasjon == 0: 
            antallTotalt = r0['antallTotalt']
    
        if stopp: 
            
            return r0 
            
    
        for rad in r0['endringssett']: 
            minrad = dict( id=rad['id'], datakatalogversjon=rad['datakatalogversjon'], 
                            mottatt=rad['status']['mottatt'], fremdrift=rad['status']['fremdrift'], 
                            eier=rad['status']['eier'], klient=rad['status']['klient'], apiversjon=rad['status']['apiversjon'], 
                            oppdragId=''
                             ) 
            if 'oppdragId' in rad['status']['transaksjon'].keys():
                minrad['oppdragId'] = rad['status']['transaksjon']['oppdragId'] 
                
            mydata.append( minrad)
            
        iterasjon += 1
        if iterasjon % 10 == 0:
            print( "iterasjon:", iterasjon, "av", antallTotalt / antall )
    
    mydf = pd.DataFrame( mydata) 
    mydf.to_csv(filnavn, sep=';', quoting=1, index=False)
    
    #return mydata

#  max=10&skip=0&reverse=true&userOrClient=sinus

if __name__ == '__main__': 
    pass
    
    