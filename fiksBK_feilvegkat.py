import STARTHER
import nvdbapiv3
from copy import deepcopy 


if __name__ == '__main__': 

    vegkategori = 'F'
    vegobjekttype = 904
    minefilter = { 'kartutsnitt' : '-30363,6634094,-30176,6634265', 'vegsystemreferanse' :  vegkategori + 'v'}    

    bk = nvdbapiv3.nvdbFagdata(vegobjekttype)
    bk.filter( minefilter )
    bk.add_request_arguments( { 'segmentering' : False } )

    bk1 = bk.nesteForekomst()
    
    seg1 = None
    while bk1: 

        for seg in bk1['vegsegmenter']: 
            if seg['vegsystemreferanse']['vegsystem']['vegkategori'] != vegkategori and not 'sluttdato' in seg.keys(): 
                print( "Avviker fra vegkategori", vegkategori, seg['vegsystemreferanse']['kortform'] )
                seg1 = deepcopy( seg ) 

        bk1 = bk.nesteForekomst( )