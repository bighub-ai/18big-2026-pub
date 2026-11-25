# Session 8 — Data governance

**Syllabus:** topic 5 (governance) · **Layer:** cross-cutting

## Goal

Students understand governance principles (not an enterprise tool) and can apply them: a data
contract, sensitivity/PII classification, masking, and how it ties to lineage.

## Theory (~40 min)

- **Security & access control** (grant, row/column-level) – conceptually.
- **Sensitivity & PII, data classification** – what is PII, why it matters (GDPR).
- **Sharing models** – how to share data safely (masked/pseudonymized shares).
- **Masking / pseudonymization** – stable hashing so you can still join without exposing PII.
- **Data lineage & SLA**, and the **data contract** as a governance artifact.
- Deliberately **no OpenMetadata/DataHub** – we teach the principle, not an enterprise install.

## Practice (~45 min)

You fill in the `# TODO`s:

1. `src/eshop/governance/masking.py` – pseudonymize the PII columns with a stable hash.
2. `src/eshop/governance/contract.py` – find contract-declared columns missing from the data.
3. `src/eshop/governance/contract.py` – find non-metadata columns present but not declared (extra).
4. **(harder)** `src/eshop/governance/contract.py` – detect type mismatches (declared type vs.
   actual dtype family).

Then run governance over the Silver customers:

```bash
uv run eshop silver          # if needed
uv run eshop governance      # validates the contract, writes a masked shareable copy
```

## Deliverable / checkpoint

- Contract validation passes; a PII-masked `data/lake/gold/customers_shared.parquet` is produced
  (email/name pseudonymized, still join-able).
- **checkpoint-08** = this state.
