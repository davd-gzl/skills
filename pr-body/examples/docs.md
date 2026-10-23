# The docs body behind the skeleton

```markdown
`-gas-fee` is the whole fee for a transaction. The chain deducts it as it stands, whatever the transaction ends up using. Four pages, the glossary among them, described the flag as a price per unit of gas, and every fee they recommend follows from that reading. Deploying the quickstart realm and calling it twice therefore asks the reader for 3.3 GNOT. The chain accepts 0.30 GNOT, and all but 9000ugnot of that is a storage deposit, locked rather than spent. Every command now sets `-gas-fee` to its own `-gas-wanted` divided by 1000, the minimum at the initial price of 1ugnot per 1000 gas.

The seven sample receipts were written before storage deposits existed. None shows a `STORAGE DELTA`, `STORAGE FEE` or `TOTAL TX COST` line. None shows the `INFO:` line `gnokey` always prints. The same transaction hash sits on three receipts for three different transactions. All seven are now pasted from real runs.

Two examples could not run at all. The `hello_world` deploy allows 200000 gas and needs 2590046. `BalanceOf` is called with `maketx call`, which now fails on any non-crossing function, so the page queries it with `vm/qeval` instead.

Three smaller repairs ride along. Nine standard-library and reference entries were missing or wrong. A footnote pointed at a closed issue as the live tracker for `errors.As`. And acd01fa29 deleted a storage section in `effective-gno.md` that four links still point at, so this restores it.
```

Provenance: the body of [gno#6099](https://github.com/gnolang/gno/pull/6099), as it stands there.
