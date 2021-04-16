# Demo, hent historisk vegreferanse 

Demonstrasjon av hvordan du kan hente historiske data / tidsutvikling. Eksemplet bruker data for Jæren. 

![Kart over dagens europa- og riksveger på Jæren](./pics/jaeren_dagensvegnett.png)

Data per 16.04.2021 situasjon er lagret i fila **[dagens_riksveger.zip](https://github.com/LtGlahn/workinprogress/raw/historisk-riksveg/dagens_riksveger.zip)**. Fila er i [geopackage-format](https://www.geopackage.org/), som kan leses av de fleste moderne kartsystemer. 




# Innstallasjon og kjøring

For å kjøre dette programmet må du ha python med geopandas installert. Vår soleklare anbefaling er [anaconda sin python-installasjon](https://www.anaconda.com), følg "download" lenkene der. Så installerer du geopandas kjapt og greit med 

```bash
conda install geopandas
```

Deretter kjører du python-scriptet `hentrv.py` 

# Todo 

Kommer snart forklaring på hvordan du henter historiske vegnettsdata fra de eldste krinkelkrokene i NVDB. 