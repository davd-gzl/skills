# The example in the doc is a claim

A package doc's own example is a claim the code makes about itself, and running it from a caller outside the package is the check; a fleet of finders told to read the code before the description walks past it.

- Six finders and a critic, 58 candidates, missed that the doc's headline declaration form aborts in every caller but the package itself; one reader alone found it by pasting the doc's example into a probe package, and it decided the verdict.
- The pipeline's own probe built the same value with the package's constructors, which pass, so its "a second caller registers one" candidate confirmed the wrong shape and read as coverage.
- The claims angle already names each shape the prose calls bounded or harmless; a doc example is one of those shapes, and it needs the run from outside the package, since inside it the construction check does not fire.

Source: the blind single-agent round against the pipeline's round on the same pull request in the gno workspace.

Changes: the claims angle runs every doc example from outside the package once before crediting the description; a probe package with one exported entry per variant is the artifact.
