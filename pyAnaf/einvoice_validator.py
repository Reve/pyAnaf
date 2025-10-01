from decimal import Decimal

from pyAnaf.einvoice import Einvoice, _dec

# ---------------------------
# VALIDATOR INTERN E-FACTURA
# ---------------------------

def _allocations_for_storno(einvoice: Einvoice):
    """
    Recalculează alocările de discount ca în build_invoice_xml.
    Returnează: list[Decimal] sau None dacă nu e storno ori nu există discount.
    """
    if not einvoice.storno_id:
        return None

    lines_net_sum = -sum(_dec(it.net_total) for it in einvoice.items)   # ex: -1000
    reported_net = _dec(einvoice.net_total)                             # ex: -700
    discount_total = _dec(abs(lines_net_sum) - abs(reported_net))       # ex: 300

    if discount_total <= 0:
        return None

    base_total = sum(_dec(it.net_total) for it in einvoice.items)       # ex: 1000
    if base_total == Decimal("0.00"):
        return None

    # Repartizare proporțională + corecție la cea mai mare linie
    raw = []
    for it in einvoice.items:
        share = _dec(it.net_total) / base_total
        raw.append(discount_total * share)

    rounded = [_dec(r) for r in raw]
    diff = discount_total - sum(rounded)
    if diff != 0:
        max_idx = max(range(len(einvoice.items)), key=lambda i: _dec(einvoice.items[i].net_total))
        rounded[max_idx] = _dec(rounded[max_idx] + diff)

    return rounded


def _recompute_tax_bases_and_vat(einvoice: Einvoice, allocations):
    """
    Construiește bazele impozabile pe cote și TVA total, în oglindă cu build_invoice_xml.
    Returnează: (taxable_by_rate: dict[Decimal, Decimal], vat_total_sum: Decimal)
    """
    from collections import defaultdict
    taxable_by_rate = defaultdict(Decimal)

    # baze din linii (storno: negative; non-storno: pozitive)
    for it in einvoice.items:
        rate = _dec(it.vat)
        line_base = -_dec(it.net_total) if einvoice.storno_id else _dec(it.net_total)
        taxable_by_rate[rate] += line_base

    # adaugă charge-urile pe linii (pozitive) – dacă avem alocări
    if einvoice.storno_id and allocations:
        for it, alloc in zip(einvoice.items, allocations):
            rate = _dec(it.vat)
            taxable_by_rate[rate] += alloc

    # TVA per cotă (>0)
    vat_total_sum = Decimal("0.00")
    for rate, taxable in taxable_by_rate.items():
        if rate > 0:
            vat_total_sum += _dec(taxable * rate / Decimal("100"))

    return taxable_by_rate, _dec(vat_total_sum)


def validate_einvoice_model(einvoice: Einvoice):
    """
    Validează CONSISTENȚA modelului față de regulile folosite în XML:
    - (storno) alocă discountul pe linii ca AllowanceCharge și verifică net-ul
    - agregă TaxSubtotal pe cote și verifică TaxTotal
    - verifică totalul (net + TVA = total)
    Returnează: list[str] cu erori; [] dacă totul e OK.
    """
    errors = []

    # 0) sanity checks
    if not isinstance(einvoice.items, (list, tuple)) or not einvoice.items:
        errors.append("Nu există linii de factură.")
        return errors

    # 1) recalc alocări storno (dacă e cazul)
    allocations = _allocations_for_storno(einvoice)

    # 2) net (tax exclusive) după logica XML
    #    — pe storno, baza liniei = -(net_post_discount + alloc); suma + charges => -net_post_discount
    if einvoice.storno_id:
        # suma bazelor pre-discount (negativă)
        base_sum = sum(-(_dec(it.net_total) + (alloc or Decimal("0.00")))
                       for it, alloc in zip(einvoice.items, allocations or [Decimal("0.00")] * len(einvoice.items)))
        # suma charges pe linii (pozitivă)
        charges_sum = sum(allocations) if allocations else Decimal("0.00")
        recomputed_net = _dec(base_sum + charges_sum)   # trebuie să iasă egal cu einvoice.net_total (negativ)
    else:
        # non-storno: pur și simplu suma net_total-urilor de pe linii (post-discount)
        recomputed_net = _dec(sum(_dec(it.net_total) for it in einvoice.items))

    if recomputed_net != _dec(einvoice.net_total):
        errors.append(f"TaxExclusive/Net inconsistent: model={_dec(einvoice.net_total)}, "
                      f"recalculat={recomputed_net}")

    # 3) TVA pe cote și total TVA
    taxable_by_rate, recomputed_vat = _recompute_tax_bases_and_vat(einvoice, allocations)
    if recomputed_vat != _dec(einvoice.vat_total):
        # adaugă și detalii pe cote ca să vezi rapid unde e diferența
        details = ", ".join([f"{str(r)}%: baza={_dec(b)}" for r, b in sorted(taxable_by_rate.items(), key=lambda x: x[0])])
        errors.append(f"VAT total inconsistent: model={_dec(einvoice.vat_total)}, "
                      f"recalculat={recomputed_vat} | baze pe cote: {details}")

    # 4) total (payable)
    if _dec(einvoice.net_total) + _dec(einvoice.vat_total) != _dec(einvoice.total):
        errors.append(f"Total inconsistent: net({_dec(einvoice.net_total)}) + "
                      f"VAT({_dec(einvoice.vat_total)}) != total({_dec(einvoice.total)})")

    # 5) semne sănătoase pe storno (opțional dar util)
    if einvoice.storno_id:
        if _dec(einvoice.net_total) >= 0:
            errors.append("Storno: net_total ar trebui să fie negativ.")
        if _dec(einvoice.total) >= 0:
            errors.append("Storno: total (TaxInclusive/Payable) ar trebui să fie negativ.")
        # verifică fiecare linie: baza pre-discount (negativă) + charge (pozitiv)
        if allocations:
            for idx, (it, alloc) in enumerate(zip(einvoice.items, allocations), start=1):
                base_pre_disc = -(_dec(it.net_total) + alloc)
                if base_pre_disc >= 0:
                    errors.append(f"Linia {idx}: baza storno pre-discount ar trebui să fie negativă (e {base_pre_disc}).")
                if alloc < 0:
                    errors.append(f"Linia {idx}: charge-ul (oglinda discountului) ar trebui să fie pozitiv (e {alloc}).")

    return errors


# ---------- EXEMPLE DE UTILIZARE ----------
# errs = validate_einvoice_model(einv)
# if errs:
#     print("VALIDARE EȘUATĂ:")
#     for e in errs:
#         print(" -", e)
# else:
#     print("OK: modelul e consistent cu regulile de generare XML.")

