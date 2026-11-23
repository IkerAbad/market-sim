# FAQ

## Why does a noise-only model pass the six rows?

Because the persistent activity state multiplies every demand, including the
noise demand.  The activity process supplies the volatility clustering and the
fat tails.  See [the ablation study](ablations.md).

## Why does GARCH also pass the five price facts?

Because the five facts are not unique to an agent-based model.  A GARCH(1,1)
process produces fat tails and volatility clustering.  At the original
thresholds GARCH passes all five facts in 100 of 100 samples.  The original
kurtosis and tail-ratio thresholds are weak: Gaussian samples pass them about
half of the time.  With kurtosis above 5 and tail ratio above 10 the model
passes all five in 46 of 50 seeds and GARCH in 5 of 100.  The agent-based model
adds an endogenous volume and explicit behavioural rules.  See
[the benchmarks](benchmarks.md) and [the pass rates](benchmark_rates.md).

## Why keep the three agent types if they are not necessary?

They shape the price level and the return autocorrelation.  Fundamentalists
anchor the price, chartists add trend feedback and noise traders supply random
demand.  The ablation shows that the statistical facts do not require all
three, which is a limitation, not a hidden assumption.

## Why is the fundamental value constant?

The model is a controlled experiment about return statistics, not a model of
news or long-run valuation.  A constant fundamental keeps the price stationary
and makes the diagnostics easier to interpret.  It is listed in the
limitations.

## Why is kurtosis unstable?

Kurtosis is dominated by rare large returns.  Different seeds and sample
lengths sample different extremes.  The 50-seed hold-out has a median of 6.304
and a maximum of 406.5.  The direction of the fact is robust, the magnitude is
not.

## Why is the volume correlation partly mechanical?

Volume is gross demand and the return is proportional to net demand.  Both are
driven by the same demands, so a positive correlation is built into the
accounting.  See [the main results](../README.md#reading-the-table).

## Why does the kurtosis criterion pass Gaussian samples?

The criterion is kurtosis above 3, and the sample kurtosis of Gaussian returns
is noisy around 3.  In 100 Gaussian samples of 100,000 returns, 52 pass.  The
tail-ratio criterion is similarly weak, with 47 of 100 Gaussian samples
passing.  With kurtosis above 5 and tail ratio above 10 no Gaussian sample
passes, the model passes 46 of 50 seeds and GARCH passes 5 of 100.  The main
table keeps the original thresholds because they were fixed before the
benchmark-rate runs.  See [the pass rates](benchmark_rates.md).

## What does "seed hold-out" mean?

The baseline parameters were chosen while looking at one seed.  The hold-out
uses seeds that were not used for that choice.  It measures sampling variation,
not variation in the model specification.

## Why is the absolute-return autocorrelation not true long memory?

The slow decay comes from a mixture of AR(1) activity processes with different
memories.  Each process decays exponentially.  The mixture looks slow over the
simulated window but is not a power law.

## Is the result driven by one episode?

No for the baseline run.  `docs/stability.md` splits the 100,000-step window
into ten contiguous blocks and recomputes the six statistics in each block.
Every statistic meets its criterion in all ten blocks.  `docs/block_ensemble.md`
repeats the split on 20 hold-out seeds, which gives 200 blocks.  Five statistics
pass in all 200 blocks and the return autocorrelation passes in 199.  The single
failure is seed 1020, block 10, with -0.05138 against a limit of 0.05.

## How do I use my own data?

Put a return column, or a price column, in a CSV and run
`scripts/compare_real_data.py`.  The data are not committed.  See the
"Bring your own data" section of the [README](../README.md#bring-your-own-data).

## What is not modeled?

No order book, wealth update, dividends, news, transaction costs, leverage
effect, gain/loss asymmetry or volume lead-lag.  The full list is in the
[limitations](../README.md#limitations).
