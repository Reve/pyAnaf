import sys
from decimal import Decimal
from pathlib import Path
from typing import List, Optional
from xml.etree import ElementTree as ET

# Allow importing the local package without relying on editable installs.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pyAnaf.einvoice import Einvoice, EinvoiceEntity, EinvoiceItem, XMLBuilder


def _entity(name: str, cui: str) -> EinvoiceEntity:
    return EinvoiceEntity(
        name=name,
        cui=cui,
        country="RO",
        county="B",
        city="Bucharest",
        postal_code="010101",
        address="Intrarea Exemplu 1",
        email="contact@example.com",
        iban="RO49AAAA1B31007593840000",
    )


def _build_invoice(
    *,
    number: str,
    date: str,
    due_date: str,
    seller: EinvoiceEntity,
    buyer: EinvoiceEntity,
    items: List[EinvoiceItem],
    total: Decimal,
    total_vat: Decimal,
    net_total: Decimal,
    vat: Decimal,
    storno_id: Optional[str] = None,
    storno_date: Optional[str] = None,
) -> Einvoice:
    return Einvoice(
        invoice_number=number,
        date=date,
        due_date=due_date,
        seller=seller,
        buyer=buyer,
        items=items,
        currency="RON",
        total=total,
        total_vat=total_vat,
        net_total=net_total,
        vat=vat,
        storno_id=storno_id,
        storno_date=storno_date,
    )


def _first(elem: ET.Element, path: str) -> Optional[ET.Element]:
    current: Optional[ET.Element] = elem
    for token in path.split("/"):
        if not token:
            continue
        if current is None:
            return None
        current = next((child for child in current if child.tag == token), None)
    return current


def _text(elem: ET.Element, path: str) -> Optional[str]:
    node = _first(elem, path)
    return node.text if node is not None else None


def test_build_invoice_xml_standard_with_vat():
    seller = _entity("Seller SRL", "RO12345678")
    buyer = _entity("Buyer SRL", "RO87654321")
    items = [
        EinvoiceItem(
            name="Consulting",
            quantity=Decimal("2"),
            price=Decimal("100.00"),
            vat=Decimal("19.00"),
            net_total=Decimal("200.00"),
        )
    ]
    invoice = _build_invoice(
        number="INV-001",
        date="2023-01-05",
        due_date="2023-01-20",
        seller=seller,
        buyer=buyer,
        items=items,
        total=Decimal("238.00"),
        total_vat=Decimal("38.00"),
        net_total=Decimal("200.00"),
        vat=Decimal("19.00"),
    )

    xml_root = XMLBuilder.build_invoice_xml(invoice)

    assert _text(xml_root, "cbc:ID") == "INV-001"

    tax_total = _first(xml_root, "cac:TaxTotal")
    assert tax_total is not None
    assert _text(tax_total, "cbc:TaxAmount") == "38.00"

    tax_subtotal = _first(tax_total, "cac:TaxSubtotal")
    assert tax_subtotal is not None
    assert _text(tax_subtotal, "cbc:TaxableAmount") == "200.00"
    assert _text(tax_subtotal, "cbc:TaxAmount") == "38.00"
    assert _text(tax_subtotal, "cac:TaxCategory/cbc:Percent") == "19.00"

    supplier_tax_id = _text(
        xml_root,
        "cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID",
    )
    assert supplier_tax_id == "RO12345678"

    line = _first(xml_root, "cac:InvoiceLine")
    assert line is not None
    assert _text(line, "cbc:LineExtensionAmount") == "200.00"
    assert _text(line, "cac:Item/cac:ClassifiedTaxCategory/cbc:ID") == "S"
    assert _text(line, "cac:Item/cac:ClassifiedTaxCategory/cbc:Percent") == "19.00"


def test_build_invoice_xml_standard_without_vat():
    seller = _entity("Seller SRL", "RO12345678")
    buyer = _entity("Buyer SRL", "RO87654321")
    items = [
        EinvoiceItem(
            name="Training",
            quantity=Decimal("1"),
            price=Decimal("150.00"),
            vat=Decimal("0.00"),
            net_total=Decimal("150.00"),
        )
    ]
    invoice = _build_invoice(
        number="INV-002",
        date="2023-02-10",
        due_date="2023-02-25",
        seller=seller,
        buyer=buyer,
        items=items,
        total=Decimal("150.00"),
        total_vat=Decimal("0.00"),
        net_total=Decimal("150.00"),
        vat=Decimal("0.00"),
    )

    xml_root = XMLBuilder.build_invoice_xml(invoice)

    tax_total = _first(xml_root, "cac:TaxTotal")
    assert tax_total is not None
    assert _text(tax_total, "cbc:TaxAmount") == "0.00"

    tax_subtotal = _first(tax_total, "cac:TaxSubtotal")
    assert tax_subtotal is not None
    assert _text(tax_subtotal, "cbc:TaxableAmount") == "150.00"
    assert _text(tax_subtotal, "cbc:TaxAmount") == "0.00"
    assert _text(tax_subtotal, "cac:TaxCategory/cbc:ID") == "O"
    assert _first(tax_subtotal, "cac:TaxCategory/cbc:Percent") is None

    party_ident = _text(
        xml_root,
        "cac:AccountingSupplierParty/cac:Party/cac:PartyIdentification/cbc:ID",
    )
    assert party_ident == "12345678"
    assert (
        _first(xml_root, "cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme")
        is None
    )

    line = _first(xml_root, "cac:InvoiceLine")
    assert line is not None
    assert _text(line, "cbc:LineExtensionAmount") == "150.00"
    assert _text(line, "cac:Item/cac:ClassifiedTaxCategory/cbc:ID") == "O"
    assert _first(line, "cac:Item/cac:ClassifiedTaxCategory/cbc:Percent") is None


def test_build_invoice_xml_storno_with_vat():
    seller = _entity("Seller SRL", "RO12345678")
    buyer = _entity("Buyer SRL", "RO87654321")
    items = [
        EinvoiceItem(
            name="Consulting",
            quantity=Decimal("2"),
            price=Decimal("100.00"),
            vat=Decimal("19.00"),
            net_total=Decimal("200.00"),
        )
    ]
    invoice = _build_invoice(
        number="CN-001",
        date="2023-03-10",
        due_date="2023-03-10",
        seller=seller,
        buyer=buyer,
        items=items,
        total=Decimal("-238.00"),
        total_vat=Decimal("-38.00"),
        net_total=Decimal("-200.00"),
        vat=Decimal("19.00"),
        storno_id="INV-001",
        storno_date="2023-01-05",
    )

    xml_root = XMLBuilder.build_invoice_xml(invoice)

    assert _text(
        xml_root,
        "cac:BillingReference/cac:InvoiceDocumentReference/cbc:ID",
    ) == "INV-001"
    assert _text(
        xml_root,
        "cac:BillingReference/cac:InvoiceDocumentReference/cbc:IssueDate",
    ) == "2023-01-05"

    tax_total = _first(xml_root, "cac:TaxTotal")
    assert tax_total is not None
    assert _text(tax_total, "cbc:TaxAmount") == "-38.00"

    line = _first(xml_root, "cac:InvoiceLine")
    assert line is not None
    assert _text(line, "cbc:LineExtensionAmount") == "-200.00"
    assert _text(line, "cac:Item/cac:ClassifiedTaxCategory/cbc:Percent") == "19.00"

    legal_totals = _first(xml_root, "cac:LegalMonetaryTotal")
    assert legal_totals is not None
    assert _text(legal_totals, "cbc:TaxExclusiveAmount") == "-200.00"
    assert _text(legal_totals, "cbc:TaxInclusiveAmount") == "-238.00"
    assert _text(legal_totals, "cbc:PayableAmount") == "-238.00"


def test_build_invoice_xml_storno_without_vat():
    seller = _entity("Seller SRL", "RO12345678")
    buyer = _entity("Buyer SRL", "RO87654321")
    items = [
        EinvoiceItem(
            name="Training",
            quantity=Decimal("1"),
            price=Decimal("150.00"),
            vat=Decimal("0.00"),
            net_total=Decimal("150.00"),
        )
    ]
    invoice = _build_invoice(
        number="CN-002",
        date="2023-04-15",
        due_date="2023-04-15",
        seller=seller,
        buyer=buyer,
        items=items,
        total=Decimal("-150.00"),
        total_vat=Decimal("0.00"),
        net_total=Decimal("-150.00"),
        vat=Decimal("0.00"),
        storno_id="INV-002",
        storno_date="2023-02-10",
    )

    xml_root = XMLBuilder.build_invoice_xml(invoice)

    tax_total = _first(xml_root, "cac:TaxTotal")
    assert tax_total is not None
    assert _text(tax_total, "cbc:TaxAmount") == "0.00"

    tax_subtotal = _first(tax_total, "cac:TaxSubtotal")
    assert tax_subtotal is not None
    assert _text(tax_subtotal, "cbc:TaxableAmount") == "-150.00"
    assert _text(tax_subtotal, "cbc:TaxAmount") == "0.00"
    assert _text(tax_subtotal, "cac:TaxCategory/cbc:ID") == "O"
    assert _text(
        tax_subtotal, "cac:TaxCategory/cbc:TaxExemptionReasonCode"
    ) == "VATEX-EU-O"

    assert (
        _first(xml_root, "cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme")
        is None
    )

    line = _first(xml_root, "cac:InvoiceLine")
    assert line is not None
    assert _text(line, "cbc:LineExtensionAmount") == "-150.00"
    assert _text(line, "cac:Item/cac:ClassifiedTaxCategory/cbc:ID") == "O"
    assert _first(line, "cac:Item/cac:ClassifiedTaxCategory/cbc:Percent") is None

    legal_totals = _first(xml_root, "cac:LegalMonetaryTotal")
    assert legal_totals is not None
    assert _text(legal_totals, "cbc:TaxExclusiveAmount") == "-150.00"
    assert _text(legal_totals, "cbc:TaxInclusiveAmount") == "-150.00"
    assert _text(legal_totals, "cbc:PayableAmount") == "-150.00"
