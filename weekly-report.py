import os
from collections import defaultdict
import datetime
import gitlab
import markdown


project_info = {
    "test/test": 'master'
}

commit_author_name = 'yang gang'

days_of_commit = 7


def get_project_commit_info(commits, project_name, branch_name, author_name, until_date, days):
     
    project = gl.projects.get(project_name)
    since_date = until_date - datetime.timedelta(days)
    since_date_str = since_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    until_date_str = until_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    index = 1
    for commit in project.commits.list(since=since_date_str, until =until_date_str, ref_name=branch_name, get_all=True)[::-1]:
        if commit.author_name == author_name:
            if '[#' in commit.title:
                string = commit.title
                issue_id = string.split("[#")[1].split("]")[0]
                issue = project.issues.get(id=issue_id)
            # commits[project_name].append(f'[{branch_name}] [{commit.created_at[0:19]}] {"#"+issue_id.zfill(4)} {str(index)+"."} {issue.title}')
            commits[project_name].append(f'{str(index)+"."} {"#"+issue_id.zfill(4)} {issue.title}')
            index+=1

def generate_report(project_commits):
    html_string = ''
    for project, commits in project_commits.items():
        html_string += f"\n## {project}"
        for commit in commits:
            html_string += f"\n* {commit} "
    return html_string
 
if __name__ == "__main__":
    gl = gitlab.Gitlab('https://gitlab.com/', private_token='xxxxx-xxxxx-x-x-xxxxxxxxxx', api_version='4')
    gl.auth()
    commits = defaultdict(list)
    
    for key in project_info:
      get_project_commit_info(commits, key, project_info[key], commit_author_name, datetime.datetime.now(), days_of_commit)

    reports = generate_report(commits)
    print(reports)