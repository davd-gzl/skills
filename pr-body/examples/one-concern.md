# The one-concern body behind the skeleton

```markdown
## Problem

On a chain whose [`Block.MaxGas`](https://github.com/gnolang/gno/blob/master/tm2/pkg/bft/types/params.go#L69-L71) is `-1`, the minimum gas price rises by 1 on every block, idle blocks included, and can never come back down. On a chain whose `MaxGas` is 0 or 1, the node panics in `EndBlock` on the first block that uses gas. Both come from [`calcBlockGasPrice`](https://github.com/gnolang/gno/blob/master/tm2/pkg/sdk/auth/keeper.go#L412) deriving its target as `maxGas * TargetGasRatio / 100`, which is `-1` for the "no gas bound" sentinel and 0 for the small values, while nothing on this path maps those spellings to unbounded the way [`getMaximumBlockGas`](https://github.com/gnolang/gno/blob/master/tm2/pkg/sdk/baseapp.go#L300) does.

## Fix

A non-positive target now returns the price unchanged: there is no bound to measure congestion against.

Two smaller changes ride along. The decrease floor is now `max(InitialGasPrice, 1)`, because [`Params.Validate`](https://github.com/gnolang/gno/blob/master/tm2/pkg/sdk/auth/params.go#L115-L117) accepts a zero initial price and a stored price of 0 reads as "pricing disabled" and can never rise again. The int64 overflow panic is now a clamp at `math.MaxInt64`, which sustained congestion reaches at block 1002 at the shipped parameters. A capped chain cannot price any transaction above 1000 gas wanted, so `UpdateGasPrice` logs it at `ERROR`; 407 idle blocks then walk the price back to the floor.

A sweep of 91584 parameter combinations against master puts every one of the 19585 differing outcomes into those three intended causes and finds no other, and master panics in all 14976 cases where this branch does not. Driving the same block sequence through the full ABCI cycle on both binaries at a block gas limit of 1000000 gives identical app hashes at every height.
```

Provenance: the body of [gno#5999](https://github.com/gnolang/gno/pull/5999), which ran without the two headings and the severity line, both added to the rule after it merged, and is shown without its closing ADR pointer, which the rule dropped; [gno#5996](https://github.com/gnolang/gno/pull/5996) is the same shape at half the length.
