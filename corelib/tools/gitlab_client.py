import requests
from datetime import datetime


class GitLabClient(object):
    """
    gitlab相关接口封装
    """

    def __init__(self, gitlab_api_url_base, gitlab_private_token, *args, **kwargs):
        self.url_base = gitlab_api_url_base
        self.header_base = {'PRIVATE-TOKEN': gitlab_private_token}

    def get_project_id(self, code_repo):
        """
        通过项目名和代码库ssh地址匹配获取项目ID
        """
        project_name = code_repo.split('/')[-1].split('.')[0]
        url_project_search = f"{self.url_base}/projects?search={project_name}"
        res = requests.get(url=url_project_search, headers=self.header_base, verify=False)
        if res.status_code != 200:
            raise Exception(f"ERROR: Failed to get project id gitlab api return status Code: {res.status_code}")
        projects = res.json()
        project_id = None
        for project in projects:
            if project['ssh_url_to_repo'] == code_repo:
                project_id = project['id']
                break
        if not project_id:
            raise Exception(f"错误：在gitlab中没有找到项目{project_name}，请检查项目名和代码库是否匹配")
        return project_id

    def get_commit(self, project_id, code_branch):
        """
        获取项目commit列表
        """
        url_commit_get = f"{self.url_base}/projects/{project_id}/repository/commits?ref_name={code_branch}"
        res = requests.get(url=url_commit_get, headers=self.header_base, verify=False)
        if res.status_code != 200:
            raise Exception(f"ERROR: Failed to get commit gitlab api return status Code: {res.status_code}")
        commit_res = res.json()
        commits = []
        for commit in commit_res:
            commits.append({
                "short_id": commit["id"][:8],
                "commit_id": commit["id"],
                "committer_name": commit["committer_name"],
                "committed_date": self._time_format(commit["committed_date"]),
            })
        return commits

    def get_tag(self, project_id, code_branch):
        """
        获取项目tag列表
        """
        url_tag_get = f"{self.url_base}/projects/{project_id}/repository/tags"
        res = requests.get(url=url_tag_get, headers=self.header_base, verify=False)
        if res.status_code != 200:
            raise Exception(f"ERROR: Failed to get tag gitlab api return status Code: {res.status_code}")
        tags_res = res.json()
        # 保留当前branch的tag
        commits = self.get_commit(project_id, code_branch)
        commits_set = set([item["commit_id"] for item in commits])
        tags = []
        for tag in tags_res:
            if tag["commit"]["id"] in commits_set:
                tags.append({
                    "tag_name": tag["name"],
                    "short_id": tag["commit"]["id"][:8],
                    "commit_id": tag["commit"]["id"],
                    "committer_name": tag["commit"]["committer_name"],
                    "committed_date": self._time_format(tag["commit"]["committed_date"]),
                })
        return tags

    def _time_format(self, time):
        """
        格式化时间
        """
        tmp = datetime.strptime(time.split("+")[0], "%Y-%m-%dT%H:%M:%S.%f")
        return datetime.strftime(tmp, "%Y-%m-%d %H:%M:%S")

    def add_project_hook(self, project_id=None, url=None, push_events_branch_filter=None, push_events=False, tag_push_events=False, *args, **kwargs):
        """
        添加项目hook
        Attribute 	                    Type 	        Required 	Description
        confidential_issues_events 	    boolean 	    no 	        Trigger hook on confidential issues events
        confidential_note_events 	    boolean 	    no 	        Trigger hook on confidential note events
        deployment_events 	            boolean 	    no 	        Trigger hook on deployment events
        enable_ssl_verification 	    boolean 	    no 	        Do SSL verification when triggering the hook
        id 	                            integer/string 	yes 	    The ID or URL-encoded path of the project
        issues_events 	                boolean 	    no 	        Trigger hook on issues events
        job_events 	                    boolean 	    no 	        Trigger hook on job     events
        merge_requests_events 	        boolean 	    no 	        Trigger hook on merge requests events
        note_events 	                boolean 	    no 	        Trigger hook on note events
        pipeline_events 	            boolean 	    no 	        Trigger hook on pipeline events
        push_events_branch_filter 	    string 	        no 	        Trigger hook on push events for matching branches only
        push_events 	                boolean 	    no 	        Trigger hook on push events
        tag_push_events 	            boolean 	    no 	        Trigger hook on tag push events
        token 	                        string 	        no 	        Secret token to validate received payloads; this is not returned in the response
        url 	                        string 	        yes 	    The hook URL
        wiki_page_events 	            boolean 	    no 	        Trigger hook on wiki events
        """
        url_add_hook = f"{self.url_base}/projects/{project_id}/hooks"
        data = {"url": url, "push_events": push_events, "tag_push_events": tag_push_events}
        if push_events_branch_filter:
            data.update({"push_events_branch_filter": push_events_branch_filter})
        if kwargs:
            data.update(kwargs)
        res = requests.post(url=url_add_hook, headers=self.header_base, data=data, verify=False)
        hook_res = res.json()
        if hook_res.get("id"):
            return True
        elif hook_res.get("message"):
            print(hook_res.get("message"))
        else:
            print(hook_res.get("error"))
        return False

    def list_project_hook(self, project_id=None):
        """
        获取项目hook列表
        """
        url_list_hook = f"{self.url_base}/projects/{project_id}/hooks"
        res = requests.get(url=url_list_hook, headers=self.header_base, verify=False)
        if res.status_code != 200:
            raise Exception(f"ERROR: Failed to get project list gitlab api return status Code: {res.status_code}")
        return res.json()

    def delete_project_hook(self, project_id=None, code_branch=None, hook_url=None):
        """
        删除项目hook
        """
        hooks = self.list_project_hook(project_id=project_id)
        hook_id = None
        for hook in hooks:
            if hook["url"] == hook_url:
                if hook["push_events"] and hook["push_events_branch_filter"] == code_branch:
                    # push hook
                    hook_id = hook["id"]
                    break
                else:
                    # tag hook
                    hook_id = hook["id"]
                    break
        print(f"[GitlabClient.delete_project_hook()] hook_id: {hook_id}")
        if hook_id:
            url_delete_hook = f"{self.url_base}/projects/{project_id}/hooks/{hook_id}"
            res = requests.delete(url=url_delete_hook, headers=self.header_base, verify=False)
            if res.status_code == 204:
                return True
            else:
                print(f"[GitlabClient.delete_project_hook()] gitlab api response, status_code: {res.status_code}")
                print(f"[GitlabClient.delete_project_hook()] gitlab api response, status_code: {res.text}")
        return False

    def get_branches(self, project_id, search=None):
        """
        获取分支列表
        """
        url_list_branch = f"{self.url_base}/projects/{project_id}/repository/branches"
        if search:
            url_list_branch += f"?search={search}"
        res = requests.get(url=url_list_branch, headers=self.header_base, verify=False)
        if res.status_code != 200:
            raise Exception(f"ERROR: Failed to get branch gitlab api return status Code: {res.status_code}")
        branches_res = res.json()
        branches = []
        for branch in branches_res:
            branches.append({
                "branch_name": branch["name"]
            })
        return branches
        