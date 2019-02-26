from ccp.lib.clients.base import CmdClient
from os import path, rmdir, getcwd, chdir
from ccp.lib.utils.command import run_command_exception_on_stderr, run_command\
    , CommandOutputError
import random
import string


class GitClient(CmdClient):

    def __init__(self, git_url, git_branch, clone_location="/var/index/repo"):
        super(GitClient, self).__init__(base_command="git")
        self.git_url = git_url
        self.git_branch = git_branch
        self.clone_location = clone_location

    def cleanup_clone(self):
        if path.exists(self.clone_location):
            rmdir(self.clone_location)

    def clone(self):
        cmd = "{base_cmd} clone {repo_url} {clone_location}".format(
            base_cmd=self.base_command,
            repo_url=self.git_url,
            clone_location=self.clone_location
        )
        run_command_exception_on_stderr(cmd=cmd, shell=True)

    def checkout_branch(self):
        if path.exists(self.clone_location):
            get_back = getcwd()
            chdir(self.clone_location)
            cmd1 = "{base_command} fetch --all".format(
                base_command=self.base_command
            )
            _, e = run_command(
                cmd=cmd1,
                shell=True
            )
            no_err = str.format(
                "Cloning into '{}'...\n", self.clone_location
            )
            if e and e != no_err:
                raise CommandOutputError(e)
            #need to fix this properly git checkout sends the output to
            #stderr, but it can result in missing on actual error
            cmd2 = "{base_command} checkout -b {branch_name}" \
                   " origin/{branch_name}".format(
                base_command=self.base_command,
                branch_name=self.git_branch
            )
            o, e = run_command(
                cmd=cmd2,
                shell=True
            )
            chdir(get_back)

    def pull_remote(self):
        if path.exists(self.clone_location):
            self.checkout_branch()
            get_back = getcwd()
            chdir(self.clone_location)
            cmd1 = "{base_command} pull origin/{branch_name}".format(
                base_command=self.base_command, branch_name=self.git_branch
            )
            o, e = run_command(cmd = cmd1, shell=True)
            chdir(get_back)
        else:
            self.clone()
            self.checkout_branch()

    def fresh_clone(self):
        self.cleanup_clone()
        self.clone()
        self.checkout_branch()
