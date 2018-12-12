# A wrapper API of ANAF web services


## Compatibility
>=Python 2.6
Tested on python 2.6, 3.4, 3.5 and 3.6

## Installation

    $ pip install pyAnaf


## Usage

##### From Python:

```python
import datetime
from pyAnaf.api import Anaf

anaf = Anaf()
anaf.setLimit(500) #optional

# adding a list of CUIs and an optional query date
anaf.setCUIList( [36804251, 2785503], date =  datetime.date.today())

# adding a CUI one by one
anaf.addCUI(36804251)
anaf.addCUI(2785503)

# submit the request to ANAF and hope for the best
anaf.Request()

# printing the json returned from ANAF
print (anaf.result)

# or doing more programmatic stuff
first_cui = anaf.getCUIData(36804251)
print (first_cui.cui)
print (first_cui.name)
print (first_cui.address)
print (first_cui.is_active)
print (first_cui.vat_eligible)
print (first_cui.vat_split_eligible)
print (first_cui.vat_collection_eligible)

```

##### From the console:

	$ pyanaf <list_of_CUIs> <max_limit>

For python3 you might have to set python encoding for your environment (e.g. export PYTHONIOENCODING=utf-8)

E.g.:

    $ pyanaf 36804251,2785503 500
    $ {   'adresa': '',
    'cui': 34434,
    'data': '2018-12-12',
    'dataActualizareTvaInc': '',
    'dataAnulareSplitTVA': '',
    'dataInactivare': ' ',
    'dataInceputSplitTVA': '',
    'dataInceputTvaInc': '',
    'dataPublicare': ' ',
    'dataPublicareTvaInc': '',
    'dataRadiere': ' ',
    'dataReactivare': ' ',
    'dataSfarsitTvaInc': '',
    'data_anul_imp_ScpTVA': '',
    'data_inceput_ScpTVA': '',
    'data_sfarsit_ScpTVA': '',
    'denumire': '',
    'mesaj_ScpTVA': '',
    'scpTVA': False,
    'statusInactivi': False,
    'statusSplitTVA': False,
    'statusTvaIncasare': False,
    'tipActTvaInc': ''}
	{   'adresa': '',
    'cui': 2,
    'data': '2018-12-12',
    'dataActualizareTvaInc': '',
    'dataAnulareSplitTVA': '',
    'dataInactivare': ' ',
    'dataInceputSplitTVA': '',
    'dataInceputTvaInc': '',
    'dataPublicare': ' ',
    'dataPublicareTvaInc': '',
    'dataRadiere': ' ',
    'dataReactivare': ' ',
    'dataSfarsitTvaInc': '',
    'data_anul_imp_ScpTVA': '',
    'data_inceput_ScpTVA': '',
    'data_sfarsit_ScpTVA': '',
    'denumire': '',
    'mesaj_ScpTVA': '',
    'scpTVA': False,
    'statusInactivi': False,
    'statusSplitTVA': False,
    'statusTvaIncasare': False,
    'tipActTvaInc': ''}
