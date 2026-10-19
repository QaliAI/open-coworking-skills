# Launch day

Order matters. The repository has to be public before the posts that link it.

1. Confirm CI on the commit you are tagging. Accept only the known Dependency Review settings failure, and only if the log still says the feature is unsupported rather than naming a vulnerable package.
2. Merge to `main`. Make the repository public. Enable the dependency graph, discussions, topics, and branch protection.
3. Tag `v0.1.0` and publish the GitHub release notes.
4. From a clean directory, run the public `--list` install. If it fails, fix the docs before posting the command.
5. Post the founder LinkedIn note and the X thread from the account that owns the work. Disclose that you built it.
6. Hold Reddit, Product Hunt, and Show HN until you have read the current rules and the public install command works.
7. Send the operator beta invite only to people you actually know or who asked. One question, not a blast.
8. Vendor notes go out as "please correct our mapping," not as "we integrated you."

If something in the public README is wrong, fix `main` before the thread. A wrong occupancy example is worse than a late post.
