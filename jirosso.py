import re
from functools import wraps

import click
from jira import JIRA
from jira.exceptions import JIRAError


class lazyproperty:
    def __init__(self, func):
            self.func = func

    def __get__(self, instance, cls):
        if instance is None:
            return self
        else:
            value = self.func(instance)
            setattr(instance, self.func.__name__, value)
            return value


def handle_jira_exception(f):
    """
    Handles `JIRAError` exceptions by
    wrapping function with try except.

    If exception occurs error will be showed in console.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            res = f(*args, **kwargs)
        except JIRAError as e:
            click.ClickException.show(click.ClickException(e.text))
            exit(click.ClickException.exit_code)
        else:
            return res
    return wrapper


class JiraHelper(object):

    def __init__(self):
        self.config = {
            'timeout': 3.001,
            'jira_server': None,
            'username': None,
            'password': None,
            'issue': None,
        }

    def set_config(self, key, value):
        self.config[key] = value

    @lazyproperty
    def jira(self):
        config = self.config
        return JIRA(
            server=config['jira_server'],
            basic_auth=(
                (
                    config['username'],
                    config['password'],
                )
            ),
            timeout=config['timeout']
        )

    @lazyproperty
    def issue(self):
        return self.jira.issue(self.config['issue'])

    @handle_jira_exception
    def add_worklog(self, time, message, **kwargs):
        """
        Proxies `add_worklog` with adding jira exception handler.
        """
        self.jira.add_worklog(self.config['issue'], timeSpent=time, comment=message, **kwargs)

    @handle_jira_exception
    def add_comment(self, message, **kwargs):
        """
        Proxies `add_comment` with adding jira exception handler.
        """
        self.jira.add_comment(self.config['issue'], body=message, **kwargs)

    def __repr__(self):
        return '<JiraHelper {config[jira_server]!r} {config[issue]!r}>'.format(
            config=self.config
        )


pass_jira_helper = click.make_pass_decorator(JiraHelper)


@click.group()
@click.option(
    '--jira-server',
    prompt=True,
    envvar='JIRA_SERVER',
    help='Your JIRA server host',
)
@click.option(
    '--username',
    prompt=True,
    envvar='JIRA_USERNAME',
    help='Your JIRA username. Example: a.opalev',
)
@click.password_option(
    envvar='JIRA_PASSWORD',
    help='Your JIRA password',
)
@click.version_option('1.0.0')
@click.pass_context
def cli(ctx, jira_server, username, password):
    """
    Jirosso is a command line tool for manipulating JIRA tasks.

    Variables that can be used from environment:

    \b
      * JIRA_SERVER
      * JIRA_USER
      * JIRA_PASSWORD

    Current list of commands:

    \b
      * `commit-time` -- Update task with its worklog

    ln -s /usr/local/bin/jirosso jirosso
    """
    ctx.obj = JiraHelper()
    for option in ('jira_server', 'username', 'password'):
        ctx.obj.set_config(option, locals()[option])


@cli.command()
@click.option(
    '--issue-num',
    prompt=True,
    help='JIRA issue to update',
)
@click.option(
    '--time',
    prompt=True,
    help='Time spent on the task which will be committed to JIRA',
)
@click.option(
    '--message',
    prompt=True,
    help='Comment message to the issue',
)
@click.option(
    '--dry-run',
    is_flag=True,
    default=False,
    help='Disable actual commit to JIRA',
)
@pass_jira_helper
def commit_time(jira_helper, issue_num, time, message, dry_run):
    """
    Command to commit time to JIRA.

    Best way to use `commit-time` command is to put
    git_hooks/prepare-commit-msg into the project's .git/hooks directory.

    Dont forget to evaluate
    `chmod +x .git/hooks/prepare-commit-msg`
    """
    # If the time is something other than JIRA desired time format,
    # we will skip time commitment at all.
    if not re.search(r'\d+[mhdw]', time):
        click.echo('Skipped time commit')
        return 0

    jira_helper.set_config('issue', issue_num)

    if dry_run:
        click.echo('Running in dry run mode')
    else:
        jira_helper.add_worklog(time, message)
        jira_helper.add_comment(message)

    click.echo('Successfully committed time to JIRA')
    click.echo('Issue: {0}'.format(click.style(jira_helper.issue.permalink(), underline=True, fg='blue')))
    click.echo('Time spent: {0}'.format(click.style(time, fg='red')))
    return 0


if __name__ == '__main__':
    cli()
