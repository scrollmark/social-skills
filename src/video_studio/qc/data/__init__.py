"""Reference data the QC detectors read at runtime.

Vendored from showwatcher rather than left behind. `prompt_fit` resolves these
through `importlib.resources`, so they must ship INSIDE the package — a path
relative to the repo would be correct in a checkout and absent in a wheel,
which is the failure mode this repo has hit four times.

  taxonomy.csv   SocialBench subcategories and their evaluation targets
  checks.yaml    per-subcategory predicates over metrics the engine already produced

showwatcher's third data file, words.txt.gz (713 KB), is NOT vendored: nothing
in this package reads it.
"""
