# Demo, analyser historisk vegnett via objekttype 532 vegreferanse

Demonstrasjon av hvordan du kan hente historiske data / tidsutvikling. Eksemplet bruker data for Jæren. 

![Kart over dagens europa- og riksveger på Jæren](./pics/jaeren_dagensvegnett.png)

se [analyse av vegnett](./README.md) for analyse av historisk vegnett. Dette er enklere enn analyse av 532 vegreferanse, og fungerer veldig bra for endringer etter november 2019, da vi tok i bruk det nye vegreferansesystemet. 

For endringer før november 2019 blir noen av analysene ufullstendige. For eksempel mangler data om trafikantgruppe for endringer før november 2019. Da er det vanskelig å skille mellom gang/sykkelveger og vanlige bilveger. Heldigvis kan analyse av 532 vegreferanse kaste lys over problemet. 


... to be written... 

# Historiske data 


**Startdato 1950-01-01** har ingenting med vegutbygging å gjøre - den forteller kun at data om denne vegen eller objektet er eldre enn NVDB.  **Måledato** forteller oss at vegen ble innmålt i 1974. Dette er trolig byggeår - det er jo naturlig å måle inn vegen mens den bygges, men for å være skråsikker bør man bekrefte dette med andre kilder. Vegen het E18 fra byggeår og fram til 1997, da vi byttet navn til E39. Og i år 2000 bygget vi ny E39 lengre vest, denne her ble da fylkesveg. 

> 'v' - en i Ev18 og Ev39 betyr _veg som er del av operativt vegnett_ . Denne 'v' - en pleier vi utelate når vi snakker om europaveger (E18, E39), men vi pleier ta den med når vi snakker om fylkesveger og riksveger (Fv44, Rv)


# Første historikkbrudd - forvaltningsreformen 2010

Mange tusen kilometer med riksveg ble i 2010 overført fra staten til fylkeskommunen gjennom forvaltningsreformen i 2010.

# Andre historikkbrudd - regionreformen 2020

Vi måtte gjøre drastiske endringer i NVDB-systemet ved forvaltningsreformen i 2020. Da gikk vi fra 19 til 11 fylker, og det gamle vegreferansesystemet - med fylkesnummer - ble dermed ubrukelig, og vi måtte lage et nytt. Du kan lese litt om overgang fra gammelt til nytt vegreferansesystem [her](https://www.vegvesen.no/fag/teknologi/nasjonal+vegdatabank/vegreferansesystem) og [her](https://www.vegdata.no/ofte-stilte-sporsmal/hva-ma-jeg-vite-om-vegsystemreferanse/). Vi har også laget [oversettelse mellom gammelt og nytt system](https://www.vegdata.no/ofte-stilte-sporsmal/oversette-mellom-ny-og-gammel-vegreferanse/).

Vi tok i bruk det nye vegreferansesystemet i november 2019. Det gamle systemet lever fremdeles parallelt med det nye frem til [august 2021](https://www.vegdata.no/info-utfasing-nvdb-klassisk/), slik som vist i [vegkart klassis](https://vegkart-2019.atlas.vegvesen.no/). Uttak av vegnettsdata med sluttdato før november 2019 gir litt mangelfulle data, blant annet mangler du informasjon om trafikantgruppe. Dermed er det vrient å skille mellom veg for kjørende (trafikantgruppe K) og gående/syklende (trafikantgruppe G). De eldste dataene vil heller ikke være metrert etter det nye systemet. 

Hvis gamle data for trafikantgruppe eller metrering er relevant må du hente ut data for objekttypen [532 vegreferanse](https://datakatalogen.vegdata.no/532-Vegreferanse). Vi håper å lage eksempel på en slik analyse snart. 

# Tredje historikkbrudd kommer i august 

Etter planen slutter vi å vedlikeholde det gamle vegreferanseobjektet (dvs objekttype 532 vegreferanse) i august 2021. Den analysen her kan dermed ikke anvendes på data nyere enn august 2021. 

# Filtrere på start- og sluttdato 

I dette datasettet har vi lagt til rette for en enkel datofiltering som bør fungere i de fleste systemer. Start- og sluttdato er lagret som  et heltall mellom 19500101 og 99991231 i variablene (kolonnene) `stardato_num, sluttdato_num`. Dermed kan du bruke operatorene _mindre enn_ eller _strørre enn_ for å filtrere datasettet (dvs >, <, >= og <=). Tallet 99991231 erstatter såkalt _**åpen sluttdato**_, som er det normale for objekter gyldige i dag. 

For å få det vegnettet som er gyldig i dag kan du f.eks. gjøre slik: 

```
historisk_e_r.sluttdato_num > 20210416 
```

For å få det vegnettet som var gyldig like før regionreformen i 2010: 

```
historis_e_r.startdato <= 20091231 AND historisk_e_r.sluttdato > 20091231
```
Merk at i NVDB er konvensjonen [gyldig fra og med, gyldig til>, dvs ikke "til og med". Derfor >= operatoren på startdato. 

# Innstallasjon og kjøring

For å kjøre dette programmet må du ha python med geopandas installert. Vår soleklare anbefaling er [anaconda sin python-installasjon](https://www.anaconda.com), følg "download" lenkene der. Så installerer du geopandas kjapt og greit med 

```bash
conda install geopandas
```

Så må du hente [dette biblioteket](https://github.com/LtGlahn/nvdbapi-V3) og lagre det lokalt. PRO-tip: editer fila **starther** slik at mappen for nvdbapi-V3 havner på python søkestien din. 


Deretter er du klar til å kjøre python-scriptet `hentrv532.py` 

# Todo 

Lage ferdig eksempel på analyse av historiske objekter 532 vegreferanse.