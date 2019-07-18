workflow "Publish Python package" {
  on = "push"
  resolves = ["publish"]
}

action "Install" {
  uses = "abatilo/actions-poetry@3.7.3"
  args = ["install"]
}

action "Run black" {
  needs = "Install"
  uses = "abatilo/actions-poetry@3.7.3"
  args = ["run", "python", "-m", "black", "--check", "."]
}

action "Run pylint" {
  needs = "Install"
  uses = "abatilo/actions-poetry@3.7.3"
  args = ["run", "python", "-m", "pylint", "src"]
}

action "Master branch" {
  needs = ["Run pylint", "Run black"]
  uses = "actions/bin/filter@master"
  args = "branch master"
}

action "publish" {
  needs = "Master branch"
  uses = "abatilo/actions-poetry@3.7.3"
  secrets = ["PYPI_USERNAME", "PYPI_PASSWORD"]
  args = ["publish", "--build", "--no-interaction", "-vv", "--username", "$PYPI_USERNAME", "--password", "$PYPI_PASSWORD"]
}
