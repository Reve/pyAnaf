class AnafResultEntry:
    def __init__(self, result):
        self.cui = result["date_generale"]["cui"]
        self.date = result["date_generale"]["data"]
        self.is_active = not result["stare_inactiv"]["statusInactivi"]
        self.name = result["date_generale"]["denumire"]
        self.address = result["date_generale"]["adresa"]
        self.vat_eligible = result["inregistrare_scop_Tva"]["scpTVA"]
        self.vat_split_eligible = result["inregistrare_SplitTVA"]["statusSplitTVA"]
        self.vat_collection_eligible = result["inregistrare_RTVAI"]["statusTvaIncasare"]

    def __str__(self):
        return "CUI: %s, Name: %s" % (self.cui, self.name)
