import json
import sys
from pathlib import Path

# Allow importing the local package without relying on editable installs.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pyAnaf.einvoice_tool import main as tool_main
from pyAnaf.einvoice_tool import render_invoice_from_json_payload


def _base_payload() -> dict:
    return {
        "invoice_number": "INV-500",
        "date": "2024-01-10",
        "due_date": "2024-01-25",
        "currency": "RON",
        "total": "119.00",
        "total_vat": "19.00",
        "net_total": "100.00",
        "vat": "19.00",
        "seller": {
            "name": "Seller SRL",
            "cui": "RO12345678",
            "country": "RO",
            "county": "B",
            "city": "Bucharest",
            "postal_code": "010101",
            "address": "Intrarea Exemplu 1",
            "email": "seller@example.com",
            "iban": "RO49AAAA1B31007593840000",
        },
        "buyer": {
            "name": "Buyer SRL",
            "cui": "RO87654321",
            "country": "RO",
            "county": "CJ",
            "city": "Cluj-Napoca",
            "postal_code": "400000",
            "address": "Strada Exemplu 2",
            "email": "buyer@example.com",
            "iban": "RO09BBBB1B31007593840000",
        },
        "items": [
            {
                "name": "Subscription",
                "quantity": "1",
                "price": "100.00",
                "vat": "19.00",
                "net_total": "100.00",
            }
        ],
    }


def test_render_invoice_from_json_payload_standard_invoice():
    payload = _base_payload()

    xml = render_invoice_from_json_payload(payload)

    assert "<cbc:ID>INV-500</cbc:ID>" in xml
    assert 'cbc:TaxAmount currencyID="RON">19.00' in xml
    assert 'cbc:TaxInclusiveAmount currencyID="RON">119.00' in xml


def test_render_invoice_from_json_payload_storno_invoice():
    payload = _base_payload()
    payload.update(
        {
            "invoice_number": "CN-500",
            "total": "-119.00",
            "total_vat": "-19.00",
            "net_total": "-100.00",
            "storno_id": "INV-400",
            "storno_date": "2023-12-15",
        }
    )

    xml = render_invoice_from_json_payload(payload, pretty=True)

    assert "<cbc:ID>CN-500</cbc:ID>" in xml
    assert 'cbc:TaxAmount currencyID="RON">-19.00' in xml
    assert "<cbc:IssueDate>2023-12-15</cbc:IssueDate>" in xml
    # Pretty output should contain indentation whitespace.
    assert "\n  <cbc:ID>CN-500</cbc:ID>" in xml


def test_cli_reads_payload_from_input_flag(tmp_path, capsys):
    payload = _base_payload()
    payload["invoice_number"] = "CLI-001"
    json_path = tmp_path / "invoice.json"
    json_path.write_text(json.dumps(payload), encoding="utf-8")

    tool_main(["--input", str(json_path)])

    output = capsys.readouterr().out
    assert "<cbc:ID>CLI-001</cbc:ID>" in output


def test_cli_allows_json_flag_with_path(tmp_path, capsys):
    payload = _base_payload()
    payload["invoice_number"] = "CLI-JSON"
    json_path = tmp_path / "invoice.json"
    json_path.write_text(json.dumps(payload), encoding="utf-8")

    tool_main(["--json", str(json_path), "--pretty"])

    output = capsys.readouterr().out
    assert "<cbc:ID>CLI-JSON</cbc:ID>" in output
