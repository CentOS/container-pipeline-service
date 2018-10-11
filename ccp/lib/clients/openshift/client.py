from ccp.lib.clients.base import CmdClient
from ccp.lib.utils.retry import retry
from os import path
from ccp.lib.utils.command import run_command


class OpenShiftCmdClient(CmdClient):
    """
    Client for interacting with Openshift.
    """

    def __init__(self):
        super(OpenShiftCmdClient, self).__init__(
            "/usr/bin/oc"
        )

    @retry(tries=10, delay=3, backoff=2)
    def get_sa_token_from_openshift(self, namespace, sa="sa/jenkins"):
        """
        Gets service account token assuming user is already logged in
        :param namespace: The namespace of the service account.
        :type namespace str
        :param sa: Default sa/jenkins: The service account whose token is
        needed
        :type sa str
        :return: The token, if it was able to successfully retrieve it
        :rtype: str
        :raises Exception
        :raises subprocess.CalledProcessError
        :raises ccp.lib.exceptions.CommandOutputError
        """
        c1 = "%s get %s -n %s --template='{{range .secrets}}" % \
             (self.base_command, sa, namespace)
        c1 = c1 + "{{ .name }} {{end}}' "
        c2 = "xargs -n 1 %s get secret -n %s --template=" \
             % (self.base_command, namespace)
        c2 = c2 + "'{{ if .data.token }}{{ .data.token }}{{end}}'"
        c3 = "head -n 1"
        c4 = "base64 -d -"
        command = "{} | {} | {} | {}".format(
            c1, c2, c3, c4
        )
        return run_command(command, shell=True)

    @retry(tries=5, delay=3, backoff=3)
    def get_token_from_mounted_secret(
            self, secret_mount_path="/tmp/jenkins-secret"
    ):
        """
        Get token from a mounted secret.
        :param secret_mount_path: The path where the secret is mounted
        :return: The token, if it was able to retrieve it.
        """
        token_location = secret_mount_path + "/token"
        if not path.exists(token_location):
            raise Exception(
                "Could not find token at {}".format(
                    secret_mount_path
                )
            )
        with open(token_location, "r") as f:
            return "".join(f.readlines())

    @retry(tries=10, delay=2, backoff=2)
    def login(self, server=None, token=None, username=None, password=None):
        """
        Logs into an openshift cluster with token or username and password.
        :param server: Default None: The openshift server to log into. If none
        is provided then we assume oc is already aware which server it needs
        to log into
        :type server str
        :param token: Default None: The token to login with. Overrides username
        and password as preferred login method
        :type token str
        :param username: Default none : The username to login with. Use only if
        token is not used.
        :type username str
        :param password: The password to login with. Use only if token is not
        provided. Not recommended
        :type password str
        :return: output of executed command
        :rtype str
        :raises Exception
        :raises subprocess.CalledProcessError
        :raises ccp.lib.exceptions.CommandOutputError
        """
        command = str.format(
            "{base_command} login{token_param}{user_param}{server_param}",
            base_command=self.base_command,
            token_param="" if not token else " --token={}".format(
                token
            ),
            user_param="" if token else " -u {} -p {}".format(
                username,
                password
            ),
            server_param="" if not server else str(server)
        )
        return run_command(cmd=command)

    @retry(tries=10, delay=3, backoff=2)
    def process_template(
            self, template_path, params, namespace, apply_template=True
    ):
        """
        Processes a specified template, and applies to to a namespace
        :param template_path: The path to the template file to process
        :param params: The key value pair of parameters with which the template
        is to be processed
        :param namespace: The namespace in which the template is to be applied
        :param apply_template: Default True: Apply the template
        :type template_path str
        :type params dict
        :type namespace str
        :type apply_template bool
        :returns output of executed command
        :rtype str
        :raises Exception
        :raises subprocess.CalledProcessError
        :raises ccp.lib.exceptions.CommandOutputError
        """
        if not path.exists(template_path):
            raise Exception(
                "Invalid path of template file at {}".format(
                    template_path
                )
            )
        p = ""
        for k, v in params:
            p = p + " -p {param_name}={param_value}".format(
                param_name=k,
                param_value=v
            )
        command = str.format(
            "{base_command} process{params} -f {template_path}{apply_cmd}",
            base_command=self.base_command,
            params=p,
            template_path=template_path,
            apply_cmd=" | {base_command} apply -n {ns} -f -".format(
                base_command=self.base_command,
                ns=namespace
            ) if apply_template else ""
        )
        return run_command(cmd=command, shell=True)

    @retry(tries=10, delay=3, backoff=2)
    def start_build(self, namespace, bc):
        """
        Starts build on a BuildConfig with build_name in specified
        namespace
        :param namespace: The namespace in which the build is to be
        started
        :param bc: The name of the BuildConfig
        :type namespace str
        :type bc str
        :return: The output of the executed command
        :rtype str
        :raises Exception
        :raises subprocess.CalledProcessError
        :raises ccp.lib.exceptions.CommandOutputError
        """
        command = "{base_cmd} start-build {build_name} -n {namespace}".format(
            base_cmd=self.base_command, build_name=bc, namespace=namespace
        )
        return run_command(cmd=command, shell=False)

    @retry(tries=10, delay=3, backoff=2)
    def delete_build_config(self, namespace, bc):
        """
        Deletes a specified BuildConfig in a specified namespace
        :param namespace: The namespcae from which the BuildConfig is to be
        removed
        :param bc: The name of the BuildConfig to delete
        :type namespace str
        :type bc str
        :return: output of executed command
        :rtype str
        :raises Exception
        :raises subprocess.CalledProcessError
        :raises ccp.lib.exceptions.CommandOutputError
        """
        command = "{base_command} delete -n {namespace} bc {bc}".format(
            base_command=self.base_command,
            namespace=namespace,
            bc=bc,
        )
        return run_command(cmd=command, shell=False)

    @retry(tries=10, delay=3, backoff=2)
    def list_build_configs(self, namespace, filter_out=None, selectors=None):
        """
        Lists all the BuildConfigs in specified namespace except those
        requested to be filtered out.
        :param namespace: The namespace from which to get the build configs.
        :param filter_out: Default None: A list of BuildConfig names to filter
        out.
        :param selectors Filter by selectors, provides list of labels
        :type namespace str
        :type filter_out list
        :type selectors dict
        :return: A list of BuildConfigs in namespace, after filtering
        :rtype list
        :raises Exception
        :raises subprocess.CalledProcessError
        :raises ccp.lib.exceptions.CommandOutputError
        """
        if not filter_out or not isinstance(filter_out, list):
            filter_out = []
        selector_params = ""
        for k, v in selectors:
            selector_params = selector_params + " --selector {k}={v}".format(
                k=k,
                v=v
            )
        command = "{base_command} get bc -o name -n {namespace}{s}".format(
            base_command=self.base_command,
            namespace=namespace,
            s=selector_params
        )
        out = run_command(cmd=command)
        if not out.strip():
            return []
        out = out.strip().split('\n')
        return [each for each in out if each not in filter_out]

    def list_builds(self, namespace, status_filter=None, filter_out=None):
        """
        Lists builds in a particular namespace, after filtering by status and
        name.
        :param namespace: The namespace from which to get the builds
        :param status_filter: Default None : List of statuses to look for. If
        provided, only builds with specified statuses are returned.
        :param filter_out: Default None : List of builds to filter out.
        :type namespace str
        :type status_filter list
        :type filter_out list
        :return: List of builds that matched all conditions
        :rtype list
        :raises Exception
        :raises subprocess.CalledProcessError
        :raises ccp.lib.exceptions.CommandOutputError
        """
        filter_str = ""
        close_str = "{{end}}"

        if not filter_out:
            filter_out = []

        if status_filter:
            conditional = '(ne .status.phase "{}") '
            condition = ''
            for phase in status_filter:
                condition = condition + conditional.format(phase)
            filter_str = "{{if and %s }}" % condition
            close_str = close_str * 2

        template_str = "{}{}{}".format(
            "{{range .items }}",
            filter_str,
            "{{.metadata.name}}:{{.status.phase}} " + close_str
        )
        command = str.format(
            "{base_command} get builds -n {namespace} -o name --template='{t}'",
            base_command=self.base_command,
            namespace=namespace,
            t=template_str
        )
        out = run_command(cmd=command, shell=True)
        if not out.strip():
            return []
        out = out.strip().split(' ')
        return [each for each in out
                if not each.startswith(tuple(filter_out)) and each]
