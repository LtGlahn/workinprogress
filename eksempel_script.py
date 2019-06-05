import STARTHER
import nvdbapi

if __name__ == '__main__': 
    print( "Sjekker at vi kan bruke NVDB api") 
    b = nvdbapi.nvdbFagdata(45)
    b1 = b.nesteNvdbFagObjekt()
    print( b1.id, b1.egenskapverdi('navn bomstasjon'), b1.egenskapverdi('takst liten bil') )