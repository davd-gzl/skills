# Bundles, not files

The unit an agent reviews is a bundle of files by category, with a floor and a ceiling; a file read alone gets no review worth the agent.

- A three-line change read alone has no siblings to check calls and invariants against; read beside its package it does.
- A test file joins the code it tests, docs join the code they describe, config and build files form one bundle the danger pass reads first, generated and vendored files form none.
- A bundle under a screen of diff merges into its neighbour by path; one past the context budget splits on package boundaries.

Source: the paper's file bundling; the design settled 2026-09-17.

Changes: `round dispatch` prints the bundles, their files and the skipped ones before the run; agents count bundles, one to four per pull request.
