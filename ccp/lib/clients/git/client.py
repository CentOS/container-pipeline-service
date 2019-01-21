from ccp.lib.clients.base import CmdClient
from os import path, rmdir, getcwd, chdir
from ccp.lib.utils.command import run_command_exception_on_stderr
import random
import string


class GitClient(CmdClient):

    def __init__(self, git_url, git_branch, clone_location="/tmp/git_clone"):
        super(GitClient, self).__init__(base_command="git")
        self.git_url = git_url
        self.git_branch = git_branch
        self.clone_location = clone_location
        self.actual_clone_location = path.join(self.clone_location +
                                               ''.join(
                                                   random.choice(
                                                       string.ascii_uppercase +
                                                       string.digits
                                                   ) for _ in range(6)))

    def cleanup_clone(self):
        if path.exists(self.actual_clone_location):
            rmdir(self.actual_clone_location)

    def clone(self):
        cmd = "{base_cmd} clone {repo_url} {clone_location}".format(
            base_cmd=self.base_command,
            repo_url=self.git_url,
            clone_location=self.actual_clone_location
        )
        run_command_exception_on_stderr(cmd=cmd, shell=True)

    def checkout_branch(self):
        if path.exists(self.actual_clone_location):
            get_back = getcwd()
            chdir(self.actual_clone_location)
            cmd1 = "{base_command} fetch --all".format(
                base_command=self.base_command
            )
            run_command_exception_on_stderr(
                cmd=cmd1,
                shell=True
            )
            #need to fix this properly git checkout sends the output to
            #stderr, but it can result in missing on actual error
            cmd2 = "{base_command} checkout -b {branch_name}" \
                   " origin/{branch_name} 2>&1".format(
                base_command=self.base_command,
                branch_name=self.git_branch
            )
            run_command_exception_on_stderr(
                cmd=cmd2,
                shell=True
            )
            chdir(get_back)

    def fresh_clone(self):
        self.cleanup_clone()
        self.clone()
        self.checkout_branch()
