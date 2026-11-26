# Commit style: decision and evidence

Decision reviewed on 2026-11-26: default generated projects to `commit_style=gitmoji`, with an
explicit `plain` alternative. The expected benefit is modest: easier visual scanning of changes
and a persistent, bounded instruction for coding agents. It is reasonable for this template,
not a universal recommendation or a claim that popular projects prove improved productivity.

## Primary sources

- [FastAPI's contribution guide](https://github.com/fastapi/fastapi/blob/05e6df7e906c3decba377c37548019973f40bf15/docs/en/docs/contributing.md)
  links to [the maintainer's contribution instructions](https://tiangolo.com/open-source/contributing/).
  Those pages do not prescribe emoji subjects for every contributor commit.
- [FastAPI organization management instructions](https://tiangolo.com/open-source/management-tasks/#edit-pr-titles)
  explicitly tell maintainers to prefix **PR titles** with a Unicode Gitmoji and use a descriptive
  imperative. The following section explains that `latest-changes` uses PR **labels** to select
  release-note sections. Automation comes from that action and metadata, not the emoji alone.
- The [12 latest FastAPI main commits available at review time](https://github.com/fastapi/fastapi/commits/05e6df7e906c3decba377c37548019973f40bf15/)
  (November 16–18) have emoji subjects, including release-note commits without PR suffixes.
  [PR #16784](https://github.com/fastapi/fastapi/pull/16784) has an emoji title and one emoji-prefixed
  branch commit; its [final commit](https://github.com/fastapi/fastapi/commit/b0a616d9fa301a50bf5809c64f97e5f2d6ae941d)
  has one parent, a different SHA, and retains the PR title plus its number. This is consistent
  with squash merging, not a two-parent merge. [PR #16779's two commits](https://github.com/fastapi/fastapi/pull/16779/commits)
  separately classify refactoring and tests; the
  [single final commit](https://github.com/fastapi/fastapi/commit/2d64371a2b1a57dc70bcb52b720a313de900b243)
  summarizes the refactoring. These are observations, not a documented rule for every branch commit.
- [Gitmoji's specification](https://gitmoji.dev/specification) defines an intention emoji, optional
  scope and brief message. It permits Unicode or shortcodes and discusses their rendering
  tradeoffs. Its [category list](https://gitmoji.dev/) is much larger than this template needs.
- [Angular's contribution rules](https://github.com/angular/angular/blob/main/CONTRIBUTING.md#commit-message-guidelines)
  require textual type/scope subjects and connect their tooling to release notes. This is a
  relevant alternative to FastAPI's PR-title policy.
  [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) defines textual
  types and breaking-change syntax with SemVer meaning. Gitmoji alone supplies neither that
  grammar nor a versioning engine; `plain` here is an unprefixed summary, not Conventional Commits.
- [GitHub's squash configuration](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/configuring-commit-squashing-for-pull-requests)
  can derive the default subject from an individual commit or the PR title, depending on settings
  and commit count. A styled PR title alone does not guarantee a styled main history.

The repository and docs were consulted live, but this is a small, recent sample, not an audit of
all contributions or a controlled study of agent performance. Live guides can change. No
cross-platform font or screen-reader usability study was performed for this decision.

## Criteria and tradeoffs for agent-led projects

| Criterion | Benefit | Cost and response |
| --- | --- | --- |
| History readability | A familiar prefix can help a reviewer scan change intent. | Symbols can be ambiguous; the English summary must carry the full meaning. |
| Classification | A short list gives agents a predictable choice. | Mixed changes invite disagreement; classify the main result, not all touched files. |
| Consistency | Rendered instructions survive context loss across agents and updates. | Instructions are not enforcement; review the PR and explicit squash subject. |
| Accessibility | Nothing essential needs to be inferred from the symbol. | Screen readers may announce distracting symbol names; `plain` is a first-class choice. |
| Maintenance | Eight categories require no installed tools or hooks. | A large taxonomy would create churn; keep the subset small and allow a maintenance fallback. |
| Tool compatibility | Unicode is stored directly in Git and shown by GitHub. | Fonts, terminals and parsers vary; offer plain text and do not claim Conventional Commits compatibility. |
| Release automation | Existing release machinery remains usable. | Emoji alone cannot determine SemVer or changelogs; any parser needs a separate explicit design. |

On balance, the low implementation and ongoing cost makes the visual cue worth offering as the
default here. Agents have little typing cost, but still need explicit category rules. Plain text
remains equally valid when the team prefers it or its tools/accessibility needs call for it.

## Resulting contract

The generated `AGENTS.md` owns the small category table and examples. Gitmoji subjects use one
Unicode emoji, one space and an English imperative summary without a trailing period. Plain
subjects use the summary alone. For example: `🐛 Reject expired sessions` or
`Fix expired session handling`. Bodies describe context and breaking changes in words.

Agents follow the selected style for new commits and PR titles. The PR title describes the whole
change; `ship-a-change` passes that final title via `--subject` for both immediate and automatic
squash merges, then checks the merged subject. Bot commits and historical commits are not rewritten.
No hooks, commit-message linter, Gitmoji CLI or new project dependency is introduced.

## Generation and migration

```bash
copier copy --defaults --data commit_style=plain gh:ebotiab/full-stack-blueprint my-project
# In a generated project with a clean worktree:
copier update --defaults --data commit_style=plain
```

Use `--data commit_style=gitmoji` to switch back. Copier persists the answer in
`.copier-answers.yml`; commit it with the rendered instructions so subsequent default updates
retain the choice. Projects without the answer take the new `gitmoji` default. To retain their
previous plain style, supply `--data commit_style=plain` on the first update. Project-specific
instruction edits may conflict and need review. No operation rewrites past commits.
