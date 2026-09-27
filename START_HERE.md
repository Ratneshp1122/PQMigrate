# PQMigrate — start here

Use these files in this order:

1. `PQMIGRATE_FULL_GUIDE.md` — beginner explanation, original-project history, current architecture, algorithmic analysis, mathematical model, commands, outputs, and limitations.
2. `PQMIGRATE_D0_D11_REPRODUCTION.md` — fresh setup and one-command validation for D0–D11.
3. `README.md` — concise project overview and common commands.

Run the complete validation from this directory:

```bash
scripts/validate_d0_d11.sh
```

The current honest result is `PASS_WITH_DECLARED_PARTIAL`: D4 Go regex detection works, but the planned Go AST/dataflow resolver is not implemented.
