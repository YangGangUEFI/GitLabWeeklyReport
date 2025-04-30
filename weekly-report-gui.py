import os
from collections import defaultdict
import datetime
import gitlab
import tkinter as tk
import time
import re

project_info = {
    "test/test": 'master'
}

def get_project_commit_info(gl, commits, project_name, branch_name, author_name, until_date, days):
     
    project = gl.projects.get(project_name)
    since_date = until_date - datetime.timedelta(days)
    since_date_str = since_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    until_date_str = until_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    print(f"Project Name: {project.name}")
    print(f"Default Branch: {project.default_branch}")

    index = 1
    pre_issue = 0
    for commit in project.commits.list(since=since_date_str, until=until_date_str, ref_name=branch_name, get_all=True)[::-1]:
        print(f"{commit.title} / {commit.author_name} / {commit.author_email}")
        if commit.author_name == author_name or commit.author_email == author_name+email_postfix.get():
            if '#' in commit.title:
                string = commit.title
                match = re.search(r'#(\d+)', string)
                if match:
                    issue_id = match.group(1)
            else:
                mrs = commit.merge_requests()

                for mr_info in mrs:
                    mr = project.mergerequests.get(mr_info['iid'])

                    match = re.search(r'#(\d+)', mr.description)
                    if match:
                        issue_id = match.group(1)

            issue = project.issues.get(id=issue_id)

            if pre_issue and pre_issue == issue_id:
                   continue
            pre_issue = issue_id
            FixStr = ''
            if 'Bug' in issue.labels:
                FixStr = ' Fix'
            commits[branch_name+"@"+project_name].append(f'{str(index)+"."} {"#"+issue_id.zfill(4)} {FixStr} {issue.title}')
            # commits[project_name].append(f'[{branch_name}] [{commit.created_at[0:19]}] {"msg:"+commit.title} {"#"+issue_id.zfill(4)} {str(index)+"."} {issue.title}')
            index+=1

def get_and_gen_report():
    gl = gitlab.Gitlab(gitlab_addr.get(), private_token=access_token.get(), api_version='4')
    gl.auth()

    user = gl.user
    print(f"username: {user.username}")
    print(f"userid: {user.id}")

    print(f"GitLab server version: {gl.version()}")

    commits = defaultdict(list)

    repos_d = defaultdict()
    repos = repos_info.get("1.0", "end")
    for line in repos.split('\n'):
      if '#' in line:
        key, value = line.split('#')
        repos_d[key.strip()] = value

    for repo in repos_d:
      for branch in repos_d[repo].split(","):
          time.sleep (2)
          get_project_commit_info(gl, commits, repo, branch, user_name.get(), datetime.datetime.now(), int(days.get()))

    commit_info_list.config(state="normal")
    commit_info_list.delete("1.0", "end")

    commit_info_list.insert("end", chars="# Weekly Work Report")
    commit_info_list.insert(tk.INSERT, '\n')
    for project, commits in commits.items():
        commit_info_list.insert("end", chars="## "+project)
        commit_info_list.insert(tk.INSERT, '\n')
        for commit in commits:
            commit_info_list.insert("end", chars=commit)
            commit_info_list.insert(tk.INSERT, '\n')

    # commit_info_list.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Automatic Weekly Work Reports")
    root.geometry('1024x768')
    current_dir = getattr(os.sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    root.iconbitmap(default=os.path.join(current_dir, './images/icon.ico'))

    name = tk.Label(root, text='Gitlab Address:')
    name.place(x=0,y=10)
    gitlab_addr = tk.StringVar()
    gitlab_addr.set('https://gitlab.com/')
    gitlab_addr = tk.Entry(root, textvariable=gitlab_addr)
    gitlab_addr.place(x=5,y=35,width=200)

    name = tk.Label(root, text='Commit Author Name:')
    name.place(x=0,y=70)
    user_name = tk.StringVar()
    user_name.set('Yang Gang')
    user_name = tk.Entry(root, textvariable=user_name)
    user_name.place(x=5,y=95,width=200)

    name = tk.Label(root, text='Commit Author Email Postfix:')
    name.place(x=0,y=130)
    email_postfix = tk.StringVar()
    email_postfix.set('@example.com')
    email_postfix = tk.Entry(root, textvariable=email_postfix)
    email_postfix.place(x=5,y=155,width=200)

    name = tk.Label(root, text='Personal Access Token:')
    name.place(x=0,y=190)
    access_token = tk.StringVar()
    access_token.set('xxxxx-xxxxx-x-x-xxxxxxxxxx')
    access_token = tk.Entry(root, textvariable=access_token)
    access_token.place(x=5,y=215,width=200)

    name = tk.Label(root, text='Number of Days:')
    name.place(x=0,y=250)
    days = tk.StringVar()
    days.set('5')
    days = tk.Entry(root, textvariable=days)
    days.place(x=5,y=275,width=200)

    submit_button = tk.Button (root, text="Generate Weekly Work Report", command=get_and_gen_report)
    submit_button.place(x=5,y=350)

    name = tk.Label(root, text='Repos Info:')
    name.place(x=230, y=10)
    repos_info = tk.Text(root)
    for key in project_info:
      repos_info.insert("end", key+'#'+project_info[key])
      repos_info.insert(tk.INSERT, '\n')
    repos_info.place(x=240,y=30,width=500,height=70)

    commit_info_list = tk.Text(root, state="disabled", height=50, width=100)
    commit_info_list.place(x=230,y=110)

    root.mainloop()