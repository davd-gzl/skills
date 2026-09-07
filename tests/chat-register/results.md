| metric (median over prompts) | none | plugin | rule | rule2 | rule3 | rule4 | rule5 |
|---|---|---|---|---|---|---|---|
| answer tokens | 901.5 | 634.5 | 765.5 | 665.0 | 651.5 | 600.0 | 701.5 |
| prose words, code excluded | 272.0 | 107.5 | 186.0 | 125.0 | 108.0 | 108.0 | 128.5 |
| articles per 100 words | 12.4 | 0.0 | 0.0 | 0.6 | 0.0 | 0.4 | 0.9 |
| filler per 100 words | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| hedges per 100 words | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| pleasantries, count | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| words per sentence | 12.5 | 5.5 | 6.6 | 6.8 | 6.0 | 6.3 | 6.9 |
| code blocks | 1.0 | 1.0 | 2.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| seconds | 25.6 | 13.9 | 22.0 | 17.3 | 19.5 | 18.6 | 26.4 |


judged sets: 16

| condition | pass1 mean | substance mean | mean rank | ranked first | answers judged |
|---|---|---|---|---|---|
| none | 4.80 | 4.40 | 1.13 | 13 | 15 |
| rule5 | 4.00 | 4.64 | 2.21 | 1 | 14 |
| rule4 | 3.86 | 4.64 | 2.50 | 2 | 14 |
| plugin | 2.87 | 4.13 | 3.73 | 0 | 15 |

notes:
async-refactor t1: Dropped articles and verbs in A ("Promisify without bind lose this, pool drivers break") and D's leading with an assumption that contradicts the callback-style original forced re-reads, while B and C used complete sentences with clear step order.
async-refactor t2: Answer A's telegraphic phrasing with dropped verbs and articles forced re-reading, while D's opening line contradicted the callback variant that followed.
auth-middleware-fix t1: Answer B never answers the question, ending on a raw tool-call payload the reader must decode, while Answer A's clipped article-dropping style forces occasional re-reads of otherwise complete content.
error-boundary t1: Answer A's dropped articles and verbs (\"so child not throw again\", \"React expose error hooks only on classes\") force re-reads, while B uses complete sentences with clear step order.
git-rebase-merge t1: Dropped verbs and articles in B ("History keep both lines", "Conflicts maybe per replayed commit") force the reader to reconstruct sentences, while C and D's fragments stay parseable and A's full sentences plus diagram read cleanly once.
git-rebase-merge t2: Telegraphic fragments with dropped articles and verbs in B and C (e.g. \"Long branch, many conflicts, pain repeats\", \"Branch shared/pushed. Others build on it.\") force the reader to reconstruct the sentence before the point lands.
microservices-monolith t1: Dropped articles, verbs, and plural agreement (worst in D, e.g. 'Split fix org problems', 'Each service own its DB') force the reader to reconstruct sentences, and A's closing clause 'structural limit horizontal scaling and caching cannot clear' needs a second read.
microservices-monolith t2: Dropped verbs and articles ("Find where time go", "In-process call become network hop", "split buy nothing") force re-reads in C, while A and B's telegraphic fragments mostly parse but occasionally lose subject or ordering; D's full sentences read cleanly at the cost of some tool-level specifics.
postgres-pool t1: B, C, and D drop articles and verbs into telegraphic fragments ("Leaked client = pool exhaust = every request hang"), and D's comment about release(true) contradicts the code that calls release() with no argument, forcing a re-read; B's reliance on the private client._ending property is unexplained.
postgres-pool t2: Telegraphic fragments with dropped verbs and articles (worst in D, some in B) forced re-reading, and B and D describe release(true)/release(err) in comments without using it, creating ambiguity about what the code actually does.
pr-security-review t1: Telegraphic bullets with dropped verbs and articles ("Any caller fetch any user", "Missing user return null", "whatever table holds") force re-reads in A, B, and C, while D's full sentences read cleanly once.
pr-security-review t2: Dropped articles and verbs in telegraphic fragments, worst in A's closing lines like 'Parameterized query kill injection', force the reader to reconstruct sentences instead of reading them once.
race-condition-debug t1: Dropped articles and verbs in A and B (e.g. 'Each request get unique value', 'FOR UPDATE block other readers') forced re-reads and B's claim that FOR UPDATE blocks plain readers is also wrong, while D's full sentences read cleanly once.
race-condition-debug t2: B's dropped verbs and articles ("Endpoint do", "row lock serialize", "If need") force the reader to reconstruct sentences, while A is only mildly telegraphic and also explains the single-client-from-pool pitfall.
react-rerender t1: Telegraphic fragments with dropped verbs and articles in A and B ("Props irrelevant", "Shallow compare fail") force the reader to reconstruct sentences, while D's only blemish is an irrelevant opening line about the workspace.
react-rerender t2: Dropped articles and verbs ("React memo compare by reference", "child see") and A's misleading "memo bails out" forced re-reads, while B also introduces the memo requirement after the memo-specific explanation, muddling the step order.
exit 0
