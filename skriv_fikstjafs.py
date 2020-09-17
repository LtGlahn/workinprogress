from datetime import datetime

import STARTHER
import skrivnvdb
import apiforbindelse 

endringID = [ 'd88cffdb-d179-4ff1-ae7c-a418599d65d8', 'ddb94547-9917-4bc2-a676-a827166ddbfa', 'aecbdeae-a470-43fa-94d6-2c591b75b94f', '960ad060-b165-4448-b053-015f18cf4f60', 
'2e180d20-868b-4c4a-a047-722abc406184', '9fbe8057-98b4-4dfb-a2e1-04b444fdbc98', 'da226d43-7200-402b-b6b8-bd98f3e6cce8', 'ec2d523f-13f9-47de-bcd9-ded2fef43c53', 
'251eb458-9007-4c58-b2c2-f6a9d290d81a', '442930c8-4811-4b5b-ae28-9984ff36782c', 'e4f4e47b-29d3-4a48-adfa-b887f3d73e07', '903c0e74-adb7-4b1f-9846-e91eda4b413c', 
'ef1a651a-7cad-4bce-a780-ac7185796066', '0e8caec4-8401-46e5-aed0-9db5f14b960b', 'ab7c9eee-b539-435d-89d3-0cae58f84755', '4dedf9b5-8044-49c3-9d93-8f1294e81ee8', 
'1c3d9b94-ad6b-414b-9b8a-7c7fa95255be', 'a2781a0f-7e57-4486-925c-b411ab60408b', '0a4bf19f-cc38-45be-a993-18857f801eba', '0599c513-9877-444d-9dfa-e6facdd07d22', 
'1a260e5d-80fa-4220-9c29-640c284b3359' ]

url = 'https://www.vegvesen.no/nvdb/apiskriv/rest/v3/endringssett/'
# endr = endringID[0]

forb = apiforbindelse.apiforbindelse()
forb.klientinfo( 'fikstjafs') 
forb.login( miljo='prodskriv' )

skrivtil = skrivnvdb.endringssett( )
skrivtil.forbindelse = forb

for endr in endringID: 
    r = forb.les( url + endr )
    data = r.json( )
    nyendring = skrivnvdb.endringssett_mal( operasjon='delvisOppdater')
    for obj in data['delvisOppdater']['vegobjekter']: 
        obj['gyldighetsperiode']['startdato'] = datetime.now().strftime("%Y-%m-%d")
        nyendring['delvisOppdater']['vegobjekter'].append( obj )

    skrivtil.data= nyendring 
    skrivtil.registrer( dryrun=False)
    skrivtil.startskriving()
