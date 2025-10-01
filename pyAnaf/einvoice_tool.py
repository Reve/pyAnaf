import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from xml.dom import minidom
from xml.etree import ElementTree as ET

# Allow invoking the script directly (e.g. `python pyAnaf/einvoice_tool.py`).
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pyAnaf.einvoice import Einvoice, EinvoiceEntity, EinvoiceItem, XMLBuilder


def _decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _load_entity(payload: Dict[str, Any]) -> EinvoiceEntity:
    required = [
        "name",
        "cui",
        "country",
        "county",
        "city",
        "postal_code",
        "address",
        "email",
        "iban",
    ]
    missing = [key for key in required if key not in payload]
    if missing:
        raise ValueError(f"Missing seller/buyer fields: {', '.join(missing)}")

    return EinvoiceEntity(
        name=payload["name"],
        cui=payload["cui"],
        country=payload["country"],
        county=payload["county"],
        city=payload["city"],
        postal_code=payload["postal_code"],
        address=payload["address"],
        email=payload["email"],
        iban=payload["iban"],
    )


def _load_items(entries: Iterable[Dict[str, Any]]) -> List[EinvoiceItem]:
    items: List[EinvoiceItem] = []
    for idx, item in enumerate(entries, start=1):
        for field in ["name", "quantity", "price", "vat", "net_total"]:
            if field not in item:
                raise ValueError(f"Item {idx} missing field '{field}'")
        items.append(
            EinvoiceItem(
                name=item["name"],
                quantity=_decimal(item["quantity"]),
                price=_decimal(item["price"]),
                vat=_decimal(item["vat"]),
                net_total=_decimal(item["net_total"]),
            )
        )
    if not items:
        raise ValueError("Invoice must contain at least one item")
    return items


def invoice_from_json_dict(data: Dict[str, Any]) -> Einvoice:
    seller = _load_entity(data.get("seller", {}))
    buyer = _load_entity(data.get("buyer", {}))
    items = _load_items(data.get("items", []))

    required_invoice_fields = [
        "invoice_number",
        "date",
        "due_date",
        "currency",
        "total",
        "total_vat",
        "net_total",
        "vat",
    ]
    missing_invoice = [key for key in required_invoice_fields if key not in data]
    if missing_invoice:
        raise ValueError(f"Missing invoice fields: {', '.join(missing_invoice)}")

    return Einvoice(
        invoice_number=data["invoice_number"],
        date=data["date"],
        due_date=data["due_date"],
        seller=seller,
        buyer=buyer,
        items=items,
        currency=data.get("currency", "RON"),
        total=_decimal(data["total"]),
        total_vat=_decimal(data["total_vat"]),
        net_total=_decimal(data["net_total"]),
        vat=_decimal(data["vat"]),
        storno_id=data.get("storno_id"),
        storno_date=data.get("storno_date"),
    )


def render_invoice_xml(invoice: Einvoice, pretty: bool = False) -> str:
    root = XMLBuilder.build_invoice_xml(invoice)
    xml_bytes = ET.tostring(root, encoding="utf-8")
    if not pretty:
        return xml_bytes.decode("utf-8")

    parsed = minidom.parseString(xml_bytes)
    return parsed.toprettyxml(indent="  ")


def render_invoice_from_json_payload(payload: Dict[str, Any], pretty: bool = False) -> str:
    invoice = invoice_from_json_dict(payload)
    return render_invoice_xml(invoice, pretty=pretty)


def _load_json_from_source(path: Optional[str], json_text: Optional[str]) -> Dict[str, Any]:
    if path:
        data_source = Path(path)
        data = data_source.read_text(encoding="utf-8")
    elif json_text:
        candidate_path = Path(json_text)
        if candidate_path.exists():
            data = candidate_path.read_text(encoding="utf-8")
        else:
            data = json_text
    else:
        data = sys.stdin.read()

    try:
        return json.loads(data)
    except json.JSONDecodeError as exc:  # pragma: no cover - exercised via CLI call
        raise ValueError(f"Invalid JSON payload: {exc}") from exc


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        description="Render a test e-invoice XML payload using the local XMLBuilder",
    )
    parser.add_argument(
        "--input",
        "-i",
        dest="input_path",
        help="Path to JSON file describing the invoice",
    )
    parser.add_argument(
        "--json",
        dest="json_text",
        help="Inline JSON string for the invoice payload",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty print the resulting XML",
    )
    args = parser.parse_args(argv)

    if not args.input_path and not args.json_text:
        parser.print_help()
        raise SystemExit(1)

    try:
        payload = _load_json_from_source(args.input_path, args.json_text)
    except ValueError as exc:
        parser.error(str(exc))
    xml_output = render_invoice_from_json_payload(payload, pretty=args.pretty)
    print(xml_output)


if __name__ == "__main__":  # pragma: no cover
    main()
