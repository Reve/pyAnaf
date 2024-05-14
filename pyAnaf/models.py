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


class AnafEinvoiceMessage:
    class MessageType:
        ACCEPTED = "FACTURA TRIMISA"
        ERROR = "ERORI FACTURA"

    def __init__(self, result):
        self.id = result["id"]
        self.type = result["tip"]
        self.date = result["data_creare"]
        self.cif = result["cif"]
        self.req_id = result["id_solicitare"]
        self.details = result["detalii"]

    def __str__(self):
        return f"Message ID: {self.id}, Message Type: {self.type}"


class AnafEinvoiceListMessagesEntry:
    def __init__(self, result):
        self.title = result["titlu"]
        self.error = result.get("eroare", None)
        self.serial = result.get("serial", None)
        self.cui = result.get("cui", None)
        self.messages = [AnafEinvoiceMessage(entry) for entry in result.get("mesaje", [])]

    def __str__(self):
        return f"Serial: {self.serial}, CUI: {self.cui}, Title: {self.title}"


class AnafEinvoicePaginatedMessages:
    def __init__(self, result):
        self.title = result["titlu"]
        self.error = result.get("eroare", None)
        self.count_in_page = result.get("numar_ingregistrari_in_pagina", 0)
        self.limit = result.get("numar_total_inregistrari_per_pagina", 500)
        self.count = result.get("numar_total_inregistrari", 0)
        self.total_pages = result.get("numar_total_pagini", 0)
        self.current_page = result.get("index_pagina_curenta", 0)
        self.serial = result.get("serial", None)
        self.cui = result.get("cui", None)
        self.messages = [AnafEinvoiceMessage(entry) for entry in result.get("mesaje", [])]

    def __str__(self):
        return f"Serial: {self.serial}, CUI: {self.cui}, Title: {self.title}"
