# Domain 2, the recorded run

Two files from the viability benchmark's recorded Domain 2 run of 2026-10-12 (`20261012T052348Z-4a0ea5d`), the run its [docs/domain2.md](https://github.com/contextwindowarchitecture/benchmark/blob/main/docs/domain2.md) reports. The benchmark commits the run's model cache, not its results, so Lab C reads this copy and needs neither the benchmark nor its toolchains.

- `20261012T052348Z-4a0ea5d/S2-summary.json`: `domain2/results/d2/20261012T052348Z-4a0ea5d/suites/S2/summary.json`, the scripted-conversation suite, every arm with its aptitude, interval, fact-in-payload counts and paired difference from `truncate-pinned`.
- `20261012T052348Z-4a0ea5d/manifest.json`: the run's manifest, with the command line that set its size.

Copied unchanged from a run made at benchmark commit `3b215a29fb` or earlier. To read a newer run, replay one at the benchmark root and pass `domain2_read.py --sibling`.
