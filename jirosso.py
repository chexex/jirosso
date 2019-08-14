# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import re
import sys

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
            if e.response and e.response.text:
                click.ClickException.show(click.ClickException(e.response.text))
            sys.exit(click.ClickException.exit_code)
        else:
            return res
    return wrapper


class JiraHelper(object):

    def __init__(self):
        self.config = {
            'timeout': 5.001,
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
    def projects(self):
        return sorted(self.jira.projects())

    @lazyproperty
    def issue(self):
        return self.jira.issue(self.config['issue'])

    @handle_jira_exception
    def add_worklog(self, time, message, **kwargs):
        """
        Proxies `add_worklog` to jira adding exception handler.
        """
        self.jira.add_worklog(self.issue, timeSpent=time, comment=message, **kwargs)

    @handle_jira_exception
    def add_comment(self, message, **kwargs):
        """
        Proxies `add_comment` to jira adding exception handler.
        """
        self.jira.add_comment(self.issue, body=message, **kwargs)

    @handle_jira_exception
    def add_remote_link(self):
        """
        Proxies `add_remote_link` to jira adding exception handler.
        """
        self.jira.add_remote_link(self.issue)

    @handle_jira_exception
    def create_issue(self, **kwargs):
        """
        Proxies `create_issue` to jira adding exception handler.
        """
        return self.jira.create_issue(**kwargs)

    @handle_jira_exception
    def assign_issue(self):
        return self.jira.assign_issue(self.issue, self.config['username'])

    def __repr__(self):
        return '<JiraHelper {!r}>'.format(self.config['jira_server'])


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


def validate_issue_num(ctx, param, value):
    if not value:
        return

    if not re.search(r'\w+-\d+', value):
        raise click.BadParameter(
            'Issue has to be in the `\\w+-\\d+` format.'
        )
    return value


def validate_time(ctx, param, value):
    if not value:
        return

    if not re.search(r'\d+[mhdw]', value):
        raise click.BadParameter(
            'Time has to be in the `\\w+-\\d+` format.'
        )
    return value


@cli.command()
@click.option(
    '--issue-num',
    prompt=True,
    callback=validate_issue_num,
    help='JIRA issue to update. Format: \\w+-\\d+',
)
@click.option(
    '--time',
    prompt=True,
    default='',
    callback=validate_time,
    required=False,
    help='Time spent on the task which will be committed to JIRA. '
         'Format: \\d+[mhdw]. '
         'If not provided, jirosso will skip time commitment.',
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
    if not time:
        click.echo('Skipped time commit')
        sys.exit(0)

    jira_helper.set_config('issue', issue_num)

    if dry_run:
        click.echo('Running in dry run mode')
    else:
        jira_helper.add_worklog(time, message)
        jira_helper.add_comment(message)

    click.echo('Successfully committed time to JIRA')
    click.echo('Issue: {0}'.format(click.style(jira_helper.issue.permalink(), underline=True, fg='blue')))
    click.echo('Time spent: {0}'.format(click.style(time, fg='red')))
    sys.exit(0)


def get_jira_projects(ctx, args, incomplete):
    return [k for k in ctx.obj.projects if incomplete in k]


@cli.command()
@click.option(
    '--project',
    type=click.STRING,
    autocompletion=get_jira_projects,
    help='JIRA project where issue will be created',
)
@click.option(
    '--issuetype',
    prompt=True,
    type=click.Choice(('История', 'Ошибка'), case_sensitive=False),
    help='Type of the issue.',
)
@click.option(
    '--summary',
    prompt=True,
    help='Title of the issue',
)
@click.option(
    '--description',
    prompt=True,
    help='Description of the issue',
)
@click.option(
    '--message',
    prompt=True,
    help='Comment message to the issue',
)
@click.option(
    '--issue-to-link',
    callback=validate_issue_num,
    prompt=True,
    default='',
    help='Issue that will be linked in the new issue',
)
@click.option(
    '--dry-run',
    is_flag=True,
    default=False,
    help='Disable actual create of issue in JIRA.',
)
@pass_jira_helper
def create_issue(jira_helper, project, issuetype, summary, description, message, issue_to_link, dry_run):
    """
    Command to create issue from a command line.
    """
    if dry_run:
        click.echo('Running in dry run mode. Issue wont be created')
        click.echo('Test')
        sys.exit(0)

    new_issue = jira_helper.create_issue(
        project=project,
        summary=summary,
        description=description,
        issuetype=issuetype.title(),
        prefetch=True
    )
    jira_helper.set_config('issue', new_issue)

    jira_helper.assign_issue()
    jira_helper.add_comment(message)

    if issue_to_link:
        jira_helper.add_remote_link(jira_helper.jira.issue(issue_to_link))

    click.echo('Successfully created a new issue in JIRA')
    click.echo('Issue: {0}'.format(click.style(new_issue.permalink(), underline=True, fg='blue')))
    click.echo(new_issue.key)
    sys.exit(0)


if __name__ == '__main__':
    cli()
