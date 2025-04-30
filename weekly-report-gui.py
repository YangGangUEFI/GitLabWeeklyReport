import os
from collections import defaultdict
import datetime
import gitlab
import tkinter as tk
import re
import json
from tkinter import filedialog, messagebox

def get_project_commit_info(gl, commits, project_name, branch, user_name, end_time, days):
    try:
        project = gl.projects.get(project_name)
        commits_list = project.commits.list(all=True, query_parameters={'ref_name': branch})
    except Exception as e:
        print(f"Error fetching commits for {project_name}:{branch} -> {e}")
        return

    print(f"Project Name: {project.name}")
    print(f"Default Branch: {project.default_branch}")

    index = 1
    pre_issue = 0
    for commit in commits_list:
        try:
            commit_date = datetime.datetime.strptime(commit.committed_date, "%Y-%m-%dT%H:%M:%S.%f%z").replace(tzinfo=None)
        except ValueError:
            continue
        delta = end_time - commit_date
        if delta.days < 0 or delta.days >= days:
            continue

        # print(f"{commit.title} / {commit.author_name} / {commit.author_email}")
        if commit.author_name == user_name or commit.author_email == user_name + email_postfix_var.get():
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
            if 'Release' in issue.labels or 'Release' in issue.title:
                commits_desc = commit.title
            else:
                commits_desc = issue.title
            commits[branch+"@"+project_name].append(f'{str(index)+"."} {"#"+issue_id.zfill(4)} {FixStr} {commits_desc}')
            index+=1

def get_and_gen_report():
    gl = gitlab.Gitlab(gitlab_addr_var.get(), private_token=access_token_var.get(), api_version='4')
    gl.auth()
    user = gl.user
    print(f"username: {user.username}")
    print(f"userid: {user.id}")

    commits = defaultdict(list)
    end_time = datetime.datetime.now()
    days = int(days_var.get())
    user_name = user_name_var.get()

    lines = repos_info.get("1.0", "end").strip().split("\n")
    for line in lines:
        if '#' in line:
            project, branches = line.split("#", 1)
            branch_list = [b.strip() for b in branches.split(",") if b.strip()]
            for branch in branch_list:
                get_project_commit_info(gl, commits, project.strip(), branch, user_name, end_time, days)

    if not commits:
        return

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

def save_config():
    config = {
        "gitlab_addr": gitlab_addr_var.get(),
        "user_name": user_name_var.get(),
        "email_postfix": email_postfix_var.get(),
        "access_token": access_token_var.get(),
        "days": days_var.get(),
        "repos_info": []
    }

    lines = repos_info.get("1.0", "end").strip().split("\n")
    for line in lines:
        if '#' in line:
            project, branches = line.split("#", 1)
            branch_list = [b.strip() for b in branches.split(",") if b.strip()]
            config["repos_info"].append({
                "project": project.strip(),
                "branches": branch_list
            })

    file_path = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("JSON Files", "*.json")],
        title="Save Configuration File"
    )
    if file_path:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        messagebox.showinfo("Success", f"Config saved to {file_path}")

def load_config():
    file_path = filedialog.askopenfilename(
        filetypes=[("JSON Files", "*.json")],
        title="Select Configuration File"
    )
    if not file_path:
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load config: {e}")
        return

    gitlab_addr_var.set(config.get("gitlab_addr", ""))
    user_name_var.set(config.get("user_name", ""))
    email_postfix_var.set(config.get("email_postfix", ""))
    access_token_var.set(config.get("access_token", ""))
    days_var.set(config.get("days", "5"))

    repos_info.delete("1.0", "end")
    for item in config.get("repos_info", []):
        repos_info.insert("end", item["project"] + "#" + ",".join(item["branches"]) + "\n")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Automatic Weekly Work Reports")
    root.geometry('1024x500')
    current_dir = getattr(os.sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    root.iconbitmap(default=os.path.join(current_dir, './images/icon.ico'))

    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {
            "gitlab_addr": "https://gitlab.com/",
            "user_name": "Yang Gang",
            "email_postfix": "@example.com",
            "access_token": "xxxxx-xxxxx-x-x-xxxxxxxxxx",
            "days": "5",
            "repos_info": [
              {
                "project": "testgroup/testproject",
                "branches": ["main"]
              }
            ]
        }

    gitlab_addr_var = tk.StringVar(value=config.get("gitlab_addr", ""))
    user_name_var = tk.StringVar(value=config.get("user_name", ""))
    email_postfix_var = tk.StringVar(value=config.get("email_postfix", ""))
    access_token_var = tk.StringVar(value=config.get("access_token", ""))
    days_var = tk.StringVar(value=config.get("days", "5"))

    tk.Label(root, text='Gitlab Address:').place(x=0, y=10)
    tk.Entry(root, textvariable=gitlab_addr_var).place(x=5, y=35, width=200)
    
    tk.Label(root, text='Commit Author Name:').place(x=0, y=70)
    tk.Entry(root, textvariable=user_name_var).place(x=5, y=95, width=200)
    
    tk.Label(root, text='Commit Author Email Postfix:').place(x=0, y=130)
    tk.Entry(root, textvariable=email_postfix_var).place(x=5, y=155, width=200)
    
    tk.Label(root, text='Personal Access Token:').place(x=0, y=190)
    tk.Entry(root, textvariable=access_token_var).place(x=5, y=215, width=200)
    
    tk.Label(root, text='Number of Days:').place(x=0, y=250)
    tk.Entry(root, textvariable=days_var).place(x=5, y=275, width=200)
    
    tk.Button(root, text="Generate Weekly Work Report", command=get_and_gen_report).place(x=5, y=320)
    tk.Button(root, text="Save Config", command=save_config).place(x=5, y=360)
    tk.Button(root, text="Load Config", command=load_config).place(x=5, y=400)


    tk.Label(root, text='Repos Info (group/project#branch1)').place(x=230, y=10)
    repos_info = tk.Text(root)
    for item in config.get("repos_info", []):
        repos_info.insert("end", item["project"] + "#" + ",".join(item["branches"]) + "\n")
    repos_info.place(x=240, y=30, width=700, height=100)

    commit_info_list = tk.Text(root, state="disabled", height=50, width=100)
    commit_info_list.place(x=240, y=150, width=700, height=300)

    root.mainloop()
