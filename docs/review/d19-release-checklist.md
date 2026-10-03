# D19 — v0.1 release-candidate checklist

- [ ] D0–D20 integration gate passes twice from the same commit.
- [ ] Generated evidence is reviewed and intentional.
- [ ] Worktree is clean.
- [ ] D14–D20 implementation is committed.
- [ ] Commit is pushed to `origin/main`.
- [ ] Faculty/security reviewer accepts the claim boundaries.
- [ ] `v0.1.0` annotated tag is created on the reviewed commit.
- [ ] Tag is pushed only after the commit is present remotely.

The readiness script reports these blockers; it never creates a tag.
