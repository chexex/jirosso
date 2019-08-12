import click
from jira import JIRA
from jira.exceptions import JIRAError


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

    Jirosso connects to JIRA with the provided credentials.

    Variables that can be used from environment
      * JIRA_SERVER
      * JIRA_USER
      * JIRA_PASSWORD  # TODO: leverage password storing

    Current list of commands:
      * `commit-time` -- Update task with its worklog

    ln -s /usr/local/bin/jirosso jirosso
    """
    # TODO: add timeout
    ctx.obj = JIRA(
        server=jira_server,
        basic_auth=(
            (username, password)
        )
    )


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
@click.pass_obj
def commit_time(jira, issue_num, time, message, dry_run):
    """
    Command to commit time to JIRA.

    Best way to use `commit-time` command is to put
    git_hooks/prepare-commit-msg into project's .git/hooks directory.

    Dont forget to evaluate
    `chmod +x .git/hooks/prepare-commit-msg`
    """
    issue = jira.issue(issue_num)
    if dry_run:
        click.echo('Running in dry run mode')
    else:
        try:
            jira.add_worklog(issue, timeSpent=time, comment=message)
            jira.add_comment(issue, body=message)
        except JIRAError as e:
            click.ClickException.show(e)
            return click.ClickException.exit_code

    click.echo('Successfully committed time to JIRA:')
    click.echo('Issue: {0}'.format(click.style(issue.permalink(), underline=True, fg='blue')))
    click.echo('Time spent: {0}'.format(click.style(time, fg='red')))
    return 0


if __name__ == '__main__':
    cli()
