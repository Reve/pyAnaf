
class AnafResultEntry(object):

    def __init__(self, result):
        self.cui = result['cui']
        self.date = result['data']
        self.is_active = not result['statusInactivi']
        self.name = result['denumire']
        self.address = result['adresa']
        self.vat_eligible = result['scpTVA']
        self.vat_split_eligible = result['statusSplitTVA']
        self.vat_collection_eligible = result['statusTvaIncasare']


    def __str__(self):
        return "CUI: %s, Name: %s" % (self.cui,self.name)
