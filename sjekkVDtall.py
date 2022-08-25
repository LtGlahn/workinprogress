import pandas as pd
import geopandas as gpd

import STARTHER
import nvdbapiv3
import nvdbgeotricks


if __name__ == '__main__': 

    # Lengde G/S 
    tider = ['2020-12-31', '2021-12-31', '2022-08-04']
    for tidspunkt in tider: 
        print(f'\n##################################################\n#\n# tidspunkt {tidspunkt}' )

        v = nvdbapiv3.nvdbVegnett()
        v.filter( { 'tidspunkt' : tidspunkt, 'trafikantgruppe' : 'G', 'vegsystemreferanse' : 'Ev,Rv', 'veglenketype' : 'hoved'})
        minDf = pd.DataFrame( v.to_records())

        ## Kommentert vekk litt utforskende dataanalyse 
        # minGdf['type'].value_counts()
        # minDf['type'].value_counts()
        # %run sjekkVDtall.py
        # minDf['type'].value_counts()
        # minDf
        # minDf['detaljnivå'].value_counts()
        # minDf['typeVeg'].value_counts()
        # minDf['adskilte_lop'].value_counts()
        print( f"Lengde vegnett for gående og syklende {tidspunkt}: { round( minDf['lengde'].sum()/1000 )}km")
        print( f"Fordeling av G/S på ulike typer veg {tidspunkt}:")
        print( minDf.groupby( ['typeVeg'] ).agg( { 'lengde' : 'sum' } ) )
        print( "\n\n")

        # Midtrekkverk og midtdeler
        rv = nvdbapiv3.nvdbFagdata( 5 )
        rv.filter( { 'tidspunkt' : tidspunkt, 'trafikantgruppe' : 'K', 'vegsystemreferanse' : 'Ev,Rv' })
        rekk = pd.DataFrame( rv.to_records())    
        
        rekk = rekk[ rekk['adskilte_lop'] != 'Mot']

        midtdeler = rekk[ rekk['Bruksområde'] == 'Midtdeler']
        midtrekk = rekk[ rekk['Bruksområde'] == 'Midtrekkverk']
        lenge_midtrekkverk = midtrekk['segmentlengde'].sum() + midtdeler['segmentlengde'].sum()
        print( f"Lengde vegnett med midtdeler / midtrekkverk {tidspunkt}: {round( lenge_midtrekkverk / 1000 )}km "  )

        # Firefelt-rapport
        firefeltGdf = nvdbgeotricks.firefeltrapport( mittfilter={'tidspunkt' : tidspunkt, 'vegsystemreferanse' : 'Ev,Rv'})
        print( f"Lengde firefelts Europa- og riksveg {tidspunkt} {round( firefeltGdf['lengde'].sum()/1000)} ")


