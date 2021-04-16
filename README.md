# Demo, hent historisk vegreferanse 

Demonstrasjon av hvordan du kan hente historiske data / tidsutvikling. Eksemplet bruker data for Jæren. 

![Kart over dagens europa- og riksveger på Jæren](./pics/jaeren_dagensvegnett.png)

Data per 16.04.2021 situasjon er lagret i fila **[dagens_riksveger.zip](https://github.com/LtGlahn/workinprogress/raw/historisk-riksveg/dagens_riksveger.zip)**. Fila er i [geopackage-format](https://www.geopackage.org/), som kan leses av de fleste moderne kartsystemer. 




# Innstallasjon og kjøring

For å kjøre dette programmet må du ha python med geopandas installert. Vår soleklare anbefaling er [anaconda sin python-installasjon](https://www.anaconda.com), følg "download" lenkene der. Så installerer du geopandas kjapt og greit med 

```bash
conda install geopandas
```

Så må du hente [dette biblioteket](https://github.com/LtGlahn/nvdbapi-V3) og lagre det lokalt. PRO-tip: editer fila **starther** slik at mappen for nvdbapi-V3 havner på python søkestien din. 


Deretter er du klar til å kjøre python-scriptet `hentrv.py` 

# Todo 

Kommer snart forklaring på hvordan du henter historiske vegnettsdata fra de eldste krinkelkrokene i NVDB. 