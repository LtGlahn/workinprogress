"""
Fyller hull i bruksklasser på kommunalt vegnett

Manglende bruksklasse-data blir funnet med script i NVDB-databasen og rapportene publiseres på 
https://nvdb-datakontroll.atlas.vegvesen.no/ Disse rapportene blir dekodet av "mangelrapport.py" 

Såfremt ikke kommunen spesifikt angir noe annet, så skal disse hullene på kommunalt vegnett
fylles med "sekkepost-verdier", dvs den kombinasjonen av 
bruksklasse-verdier som brukes til oppføringen "Øvrige veger". Dette er den mest vanlige
dataverdi-kombinasjonen innafor den kommunen, og vegene her skal IKKE ha strekningsbeskrivelse. 
(Strekningsbeskrivelse brukes til å skille ut kommunalveger det er noe ekstra med, enten ved at de har
avvikene BK eller for å fremheve en viktig veg med sin egen )

Så logikken her blir følgende: 

    1) Finn sekkepost-dataverdiene for kommunen 
       a. Last ned strekningsløse BK for kommunalveg med filteret 
                    { 'vegsystemreferanse' : 'Kv', 
                      'egenskap=<ID for strekningsbeskrivelse-egenskap> = null'
                      'trafikantgruppe' : 'K' }

       b. Analyser: Datasett.groupby( ['BK-verdiene' ])
          b1) Hvilken kombinasjon av bruksklasse, maks tillatt vogntoglengde etc er det flest av?
          b2) Er det mer enn 1 - en - slik kommbinasjon? I så fall er det datafeil som bør rettes. 
                Loggføres til senere QA. 
                
                Hvis en kommunal veg har annen BK enn det som gjelder for
                den kommunens sekkepost så skal / bør denne BK-verdien også ha en strekningsbeskrivelse
                (men vi kan godta at gatenavnet brukes i stedet; veglistene har denne logikken innebygd). 
                Denne vurderingen overlater jeg til faggruppe vegliste, til senere QA. 


    2) Konstruer endringssett som skal sendes til SKRIV. Her kan vi velge å starte med kun et subsett (de enkleste
    og mest skuddsikre tilfellene) av de feilene som rapporteres. Vi prøver oss litt fram, basert på hvilke dataverdier
    vi møter 

    Ett mulig scenario er å starte med de strekningene som starter med veglenkeposisjon 0 og slutter med veglenkeposisjon 1. 
    Jeg tror at dette er helt nye veger som er kommet til uten at noen har rukket å etablere BK-verdier på dem. 
    Dette utgjør cirka 40% av mangelrapportene på kommunal veg. Oslo har 1066 slike rader, 
    fulgt av kommune 4204 med 483 rader og 3030 med 110. 

    Krav til endringssett: 
        - Oppretter tre nye objekter per veg: Normaltransport, spesialtransport og tømmertransport
        - BK + BK vinter er identisk for de tre objekttypene, og BK normaltransport er styrende
        for hvilken dataverdi dette skal være
        - Tillatt vogntoglengde er nesten identisk: Den _*kan*_ ha de større verdiene 22 og 24 m på BK tømmer, ellers er den lik 
        på tvers av de tre objekttypene. 
        - BK Spesilaltransport har i tillegg egenskapen Veggruppe (A, B, IKKE )
        - BK Tømmertransport kan som før nevnt ha større verdi 22m og 24m på egenskapen "Maks tillatt vogntoglengde". 
          I tillegg kommer egenskapene 
                - "maks totalvekt" (som stort sett er identisk med tall nr 2 i BK-verdien, men 
          for Bk10/50 er også verdien 60tonn tillatt.)  
                - "Tillatt for modulvogntog 1 og 2 med sporingskrav" (Ja eller Nei) 

    Dette må vi gjøre for to varianter: BK offisiell og BK uoffisiell.

    Ved god bruk av datakatalogen og unngå hardkoding så skal vi få dette til på en elegant måte, tror jeg.
    Med 2 * 3 = 6 objekttyper og en håndfull egenskaper per objekttype så er kaospotensialet absolutt til stede, 
    så det er absolutt mye å hente på å lage en god, datakatalog-drevet løsning. 

"""