# Jirosso

Jirosso is a command line tool to manipulate JIRA tasks.

## Basic setup

Install the requirements:
```bash
$ pip install -r requirements.txt
```

#### List of available commands:

  * commit-time –– Update task with the time spent on it
  * create-issue –– Create new issue

#### Run the application:
```bash
$ python -m jirosso --help
```

#### Make the application being available system wide
```bash
$ pip install -e .
$ ln -s /usr/local/bin/jirosso jirosso
```

#### Make the application being executable on git commit
```bash
$ cp git_hooks/prepare-commit-msg your_project/.git/hooks
$ chmod +x your_project/.git/hooks/prepare-commit-msg
```

#### To run the tests:
```bash
$ pytest tests
```
