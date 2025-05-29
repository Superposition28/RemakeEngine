def rewrite_author(name, email):
    if name == b"Superposition28":
        return (b"samarixum", email)
    return (name, email)

def rewrite_commit(commit):
    commit.author_name, commit.author_email = rewrite_author(commit.author_name, commit.author_email)
    commit.committer_name, commit.committer_email = rewrite_author(commit.committer_name, commit.committer_email)

import sys
from git_filter_repo import FilterRepo

repo = FilterRepo()
repo.add_commit_callback(rewrite_commit)
repo.run()
