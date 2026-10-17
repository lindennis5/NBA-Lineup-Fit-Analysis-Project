# Publishing the release candidate

1. Read `docs/research_report.md`, including the TL;DR, Knicks illustration and limitations. Review the committed tables and figures alongside it.
2. Run the commands in `docs/REPRODUCING.md`. A fresh download requires access to the public PBP Stats API; existing local caches allow offline reproduction.
3. Review `git status --short` and `git diff origin/main...HEAD`. Keep raw data, virtual environments, scratch files and secrets out of Git. The small benchmark and result tables are retained for review; no blanket right to redistribute the source's bulk data is assumed.
4. Run the configured Windows/Linux checks in GitHub Actions after publication. They have been executed locally on Windows; remote CI status must be checked independently.
5. With approval to publish, push the local release branch without force: `git push -u origin audit/release-candidate`. Open a pull request, review its diff, then merge using the repository's usual process.

The local commit does not publish anything. No remote history rewrite is needed. This is a release candidate for an observational portfolio study, not a causal lineup-selection product.
