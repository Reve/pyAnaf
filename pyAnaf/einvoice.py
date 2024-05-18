from xml.etree import ElementTree as ET


class EinvoiceSeller:
    def __init__(self, name, address, city, postal_code, country, vat_number, bank_account):
        self.name = name
        self.address = address
        self.city = city
        self.postal_code = postal_code
        self.country = country
        self.vat_number = vat_number
        self.bank_account = bank_account


class EinvoiceItem:
    def __init__(self, name, quantity, price, vat, net_total):
        self.name = name
        self.quantity = quantity
        self.price = price
        self.vat = vat
        self.net_total = net_total


class Einvoice:
    def __init__(self, invoice_number, date, due_date, currency, net_total, vat_total, total, items, storno=None):
        self.invoice_id = invoice_number
        self.date = date
        self.due_date = due_date
        self.currency = currency
        self.net_total = net_total
        self.vat_total = vat_total
        self.total = total
        self.items = items
        self.storno = storno


class XMLBuilder:
    @staticmethod
    def add_element(parent, tag, text=None, attrib=None):
        """
        Add an element to the parent
        :param parent: Parent element
        :param tag: Tag of the element
        :param text: Text of the element
        :param attrib: Attributes of the element
        :return: Element
        """
        if attrib is None:
            attrib = {}

        element = ET.SubElement(parent, tag, attrib)

        if text:
            element.text = text

        return element

    @staticmethod
    def build_invoice_xml(einvoice):
        """
        Build the XML for the invoice
        :param einvoice: Einvoice object
        :return: XML Element
        """
        invoice = ET.Element(
            "Invoice",
            attrib={
                "xmlns": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
                "xmlns:cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
                "xmlns:cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
                "xmlns:ns4": "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2",
                "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "xsi:schemaLocation": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2 http://docs.oasis-open.org/ubl/os-UBL-2.1/xsd/maindoc/UBL-Invoice-2.1.xsd",
            },
        )

        XMLBuilder.add_element(invoice, "cbc:UBLVersionID", "2.1")
        XMLBuilder.add_element(
            invoice, "cbc:CustomizationID", "urn:cen.eu:en16931:2017#compliant#urn:efactura.mfinante.ro:CIUS-RO:1.0.1"
        )
        XMLBuilder.add_element(invoice, "cbc:ID", einvoice.invoice_number)
        XMLBuilder.add_element(invoice, "cbc:IssueDate", einvoice.date)
        XMLBuilder.add_element(invoice, "cbc:DueDate", einvoice.due_date)
        XMLBuilder.add_element(invoice, "cbc:InvoiceTypeCode", "380")
        XMLBuilder.add_element(invoice, "cbc:DocumentCurrencyCode", einvoice.currency)

        if einvoice.currency != "RON":
            XMLBuilder.add_element(invoice, "cbc:TaxCurrencyCode", "RON")

        if einvoice.storno_id:
            billing_reference = XMLBuilder.add_element(invoice, "cac:BillingReference")
            invoice_document_reference = XMLBuilder.add_element(billing_reference, "cac:InvoiceDocumentReference")
            XMLBuilder.add_element(invoice_document_reference, "cbc:ID", einvoice.storno_id)
            XMLBuilder.add_element(invoice_document_reference, "cbc:IssueDate", einvoice.storno_date)

        XMLBuilder.add_party(invoice, "cac:AccountingSupplierParty", einvoice.seller)
        XMLBuilder.add_party(invoice, "cac:AccountingCustomerParty", einvoice.buyer)

        payment_means = XMLBuilder.add_element(invoice, "cac:PaymentMeans")
        XMLBuilder.add_element(payment_means, "cbc:PaymentMeansCode", "31")
        payee_financial_account = XMLBuilder.add_element(payment_means, "cac:PayeeFinancialAccount")
        XMLBuilder.add_element(payee_financial_account, "cbc:ID", einvoice.seller.iban)

        tax_total = XMLBuilder.add_element(invoice, "cac:TaxTotal")
        XMLBuilder.add_element(tax_total, "cbc:TaxAmount", str(einvoice.total_vat), attrib={"currencyID": "RON"})
        tax_subtotal = XMLBuilder.add_element(tax_total, "cac:TaxSubtotal")
        XMLBuilder.add_element(
            tax_subtotal, "cbc:TaxableAmount", str(einvoice.net_total), attrib={"currencyID": "RON"}
        )
        XMLBuilder.add_element(tax_subtotal, "cbc:TaxAmount", str(einvoice.total_vat), attrib={"currencyID": "RON"})
        tax_category = XMLBuilder.add_element(tax_subtotal, "cac:TaxCategory")
        XMLBuilder.add_element(tax_category, "cbc:ID", "S")
        XMLBuilder.add_element(tax_category, "cbc:Percent", str(einvoice.vat))
        tax_scheme = XMLBuilder.add_element(tax_category, "cac:TaxScheme")
        XMLBuilder.add_element(tax_scheme, "cbc:ID", "VAT")

        legal_monetary_total = XMLBuilder.add_element(invoice, "cac:LegalMonetaryTotal")
        XMLBuilder.add_element(
            legal_monetary_total, "cbc:LineExtensionAmount", str(einvoice.net_total), attrib={"currencyID": "RON"}
        )
        XMLBuilder.add_element(
            legal_monetary_total, "cbc:TaxExclusiveAmount", str(einvoice.net_total), attrib={"currencyID": "RON"}
        )
        XMLBuilder.add_element(
            legal_monetary_total, "cbc:TaxInclusiveAmount", str(einvoice.total), attrib={"currencyID": "RON"}
        )
        XMLBuilder.add_element(
            legal_monetary_total, "cbc:PayableAmount", str(einvoice.total), attrib={"currencyID": "RON"}
        )

        for i, item in enumerate(einvoice.items, start=1):
            invoice_line = XMLBuilder.add_element(invoice, "cac:InvoiceLine")
            XMLBuilder.add_element(invoice_line, "cbc:ID", str(i))
            XMLBuilder.add_element(
                invoice_line, "cbc:InvoicedQuantity", str(item.quantity), attrib={"unitCode": "C61"}
            )
            line_extension_amount = XMLBuilder.add_element(
                invoice_line,
                "cbc:LineExtensionAmount",
                str(item.net_total if not einvoice.storno_id else -item.net_total),
                attrib={"currencyID": "RON"},
            )
            _item = XMLBuilder.add_element(invoice_line, "cac:Item")
            XMLBuilder.add_element(_item, "cbc:Name", item.name)
            classified_tax_category = XMLBuilder.add_element(_item, "cac:ClassifiedTaxCategory")
            XMLBuilder.add_element(classified_tax_category, "cbc:ID", "S")
            XMLBuilder.add_element(classified_tax_category, "cbc:Percent", str(item.vat))
            tax_scheme = XMLBuilder.add_element(classified_tax_category, "cac:TaxScheme")
            XMLBuilder.add_element(tax_scheme, "cbc:ID", "VAT")
            price = XMLBuilder.add_element(invoice_line, "cac:Price")
            XMLBuilder.add_element(price, "cbc:PriceAmount", str(item.price), attrib={"currencyID": "RON"})

        return invoice

    @staticmethod
    def add_party(invoice, party_tag, entity):
        """
        Add the party to the invoice
        :param invoice: Invoice Element
        :param party_tag: Party tag
        :param entity: EinvoiceSeller object
        """

        party = XMLBuilder.add_element(invoice, party_tag)
        party_entity = XMLBuilder.add_element(party, "cac:Party")
        party_name = XMLBuilder.add_element(party_entity, "cac:PartyName")
        XMLBuilder.add_element(party_name, "cbc:Name", entity.name)

        postal_address = XMLBuilder.add_element(party_entity, "cac:PostalAddress")
        XMLBuilder.add_element(postal_address, "cbc:StreetName", entity.address)
        XMLBuilder.add_element(postal_address, "cbc:CityName", entity.city)
        XMLBuilder.add_element(postal_address, "cbc:PostalZone", entity.postal_code)
        XMLBuilder.add_element(postal_address, "cbc:CountrySubentity", entity.county)
        country = XMLBuilder.add_element(postal_address, "cac:Country")
        XMLBuilder.add_element(country, "cbc:IdentificationCode", entity.country)

        party_tax_scheme = XMLBuilder.add_element(party_entity, "cac:PartyTaxScheme")
        XMLBuilder.add_element(party_tax_scheme, "cbc:CompanyID", entity.cui)
        tax_scheme = XMLBuilder.add_element(party_tax_scheme, "cac:TaxScheme")
        XMLBuilder.add_element(tax_scheme, "cbc:ID", "VAT")

        party_legal_entity = XMLBuilder.add_element(party_entity, "cac:PartyLegalEntity")
        XMLBuilder.add_element(party_legal_entity, "cbc:RegistrationName", entity.name)
        XMLBuilder.add_element(party_legal_entity, "cbc:CompanyID", entity.cui)

        contact = XMLBuilder.add_element(party_entity, "cac:Contact")
        XMLBuilder.add_element(contact, "cbc:ElectronicMail", entity.email)
