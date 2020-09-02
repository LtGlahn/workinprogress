import STARTHER
import nvdbapiv3

if __name__ == '__main__': 
    print( "Sjekker at vi kan bruke NVDB api") 
    b = nvdbapiv3.nvdbFagdata(45)
    b1 = b.nesteNvdbFagObjekt()
    print( b1.id, b1.egenskapverdi('navn bomstasjon'), b1.egenskapverdi('takst liten bil') )