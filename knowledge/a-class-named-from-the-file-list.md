# A class named from the file list is not a class

Triage read off the names of the changed files rounds up, because a list of
unrelated-looking files looks like interacting mechanisms and a list cannot show
that they do not interact.

- A pull request adding a generated index, a deploy-workflow bump and a
  link-check config rewrite was called complex on "two mechanisms interact". The
  diff refutes it in one line: the same change gitignores the generated file, so
  no checker ever reads it.
- The same round's triage stage, reading the files rather than their names,
  called it normal and named what a second reading buys, the reach of a removed
  ignore pattern across every published post.
- The rounding-up is one-way. Nobody calls a change trivial from a file list.

Source: https://github.com/gnolang/blog/pull/161

Changes: naming a class carries the quoted line that makes one reading
insufficient, and without that line the class is normal.
