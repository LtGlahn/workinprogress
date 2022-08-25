import STARTHER

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import nvdbgeotricks

# mittfilter  = { 'kontraktsomrade' : '9401 Trondheim 2020-2025 (t.o.m. 31.08.2023),9402 Steinkjer 2021-2025,9403 Nordmøre 2022-2027 (t.o.m 31.08.2023),9404 Sunnmøre 2023-2028'}

mittfilter = { 'fylke' : [11, 46], 'vegsystemreferanse' : 'E,R' }

nvdbgeotricks.nvdb2gpkg( [ 79, 83], filnavn='stikkrenneDoVvest.gpkg', vegnett=False, mittfilter=mittfilter, vegsegmenter=False, geometri=True   )


