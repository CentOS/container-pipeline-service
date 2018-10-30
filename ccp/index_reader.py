"""
This script parses the container index specified and
creates the Jenkins pipeline projects from entries of index.
"""

import sys
import time

from ccp.lib.processors.index.index_reader import IndexReader
from ccp.lib.utils.print_out import print_out
from ccp.lib.utils.command import run_command
from ccp.lib.utils.retry import retry


class BuildConfigManager(object):
    """
    This class represents utilities to manage
    deployment configs on openshift as used
    by pipeline service
    """

    def __init__(self, registry_url, namespace, from_address, smtp_server,
                 ccp_openshift_slave_image, notify_cc_emails,
                 registry_alias, master_job_cpu, master_job_memory):
        self.registry_url = registry_url
        self.namespace = namespace
        self.from_address = from_address
        self.smtp_server = smtp_server
        self.ccp_openshift_slave_image = ccp_openshift_slave_image
        self.notify_cc_emails = notify_cc_emails
        self.registry_alias = registry_alias
        self.master_job_cpu = master_job_cpu
        self.master_job_memory = master_job_memory

        self.template_params = """\
-p GIT_URL={git_url} \
-p GIT_PATH={git_path} \
-p GIT_BRANCH={git_branch} \
-p TARGET_FILE={target_file} \
-p BUILD_CONTEXT={build_context} \
-p DESIRED_TAG={desired_tag} \
-p DEPENDS_ON={depends_on} \
-p NOTIFY_EMAIL={notify_email} \
-p NOTIFY_CC_EMAILS={notify_cc_emails} \
-p REGISTRY_ALIAS={registry_alias} \
-p MASTER_JOB_CPU={master_job_cpu} \
-p MASTER_JOB_MEMORY={master_job_memory} \
-p PIPELINE_NAME={pipeline_name} \
-p APP_ID={app_id} \
-p JOB_ID={job_id} \
-p PRE_BUILD_CONTEXT={pre_build_context} \
-p PRE_BUILD_SCRIPT={pre_build_script} \
-p NAMESPACE={namespace} \
-p REGISTRY_URL={registry_url} \
-p FROM_ADDRESS={from_address} \
-p SMTP_SERVER={smtp_server} \
-p CCP_OPENSHIFT_SLAVE_IMAGE={ccp_openshift_slave_image}"""

        self.weekly_scan_template_params = """\
-p NAMESPACE={namespace} \
-p PIPELINE_NAME=wscan-{pipeline_name} \
-p REGISTRY_URL={registry_url} \
-p NOTIFY_EMAIL={notify_email} \
-p NOTIFY_CC_EMAILS={notify_cc_emails} \
-p REGISTRY_ALIAS={registry_alias} \
-p APP_ID={app_id} \
-p JOB_ID={job_id} \
-p DESIRED_TAG={desired_tag} \
-p FROM_ADDRESS={from_address} \
-p SMTP_SERVER={smtp_server} \
-p CCP_OPENSHIFT_SLAVE_IMAGE={ccp_openshift_slave_image}"""

    @retry(tries=10, delay=3, backoff=2)
    def list_all_buildConfigs(self):
        """
        List all available buildConfigs
        returns list of buildConfigs available
        """
        command = "oc get bc -o name -n {}".format(self.namespace)
        bcs, _ = run_command(command, shell=True)
        if not bcs.strip():
            return []
        else:
            return bcs.strip().split("\n")

    @retry(tries=10, delay=3, backoff=2)
    def apply_build_job(self,
                        project,
                        template_location="seed-job/template.yaml"
                        ):
        """
        Applies the build job template that creates pipeline to build
        image, and trigger first time build as well.
        :param project: The name of project, where the template is to be
                        applied
        :param template_location: The location of the template file.
        """
        oc_process = "oc process -f {0} {1}".format(
            template_location,
            self.template_params
        )

        oc_apply = "oc apply -n {} -f -".format(self.namespace)

        # oc process and oc apply command combined with a shell pipe
        command = oc_process + " | " + oc_apply

        # format the command with project params
        command = command.format(
            git_url=project.git_url,
            git_path=project.git_path,
            git_branch=project.git_branch,
            target_file=project.target_file,
            build_context=project.build_context,
            desired_tag=project.desired_tag,
            depends_on=project.depends_on,
            notify_email=project.notify_email,
            pipeline_name=project.pipeline_name,
            app_id=project.app_id,
            job_id=project.job_id,
            pre_build_context=project.pre_build_context,
            pre_build_script=project.pre_build_script,
            namespace=self.namespace,
            registry_url=self.registry_url,
            from_address=self.from_address,
            smtp_server=self.smtp_server,
            ccp_openshift_slave_image=self.ccp_openshift_slave_image,
            notify_cc_emails=self.notify_cc_emails,
            registry_alias=self.registry_alias,
            master_job_cpu=self.master_job_cpu,
            master_job_memory=self.master_job_memory
        )
        # process and apply buildconfig
        output, _ = run_command(command, shell=True)
        print_out(output)

        # if a buildConfig has config update, oc apply returns
        # "buildconfig.build.openshift.io "$PIPELINE_NAME" configured"
        # possible values are ["unchanged", "created", "configured"]
        # we are looking for "configured" string for updated pipeline
        # templates.
        # Update: 21 Sept 2018 :
        # We are seeing hundreds of build triggered due to configChange,
        # which is unnecessary, because configChange can merely be
        # any parameter change in the template.
        # The parameters we care about for re-triggering builds are
        # taken care already by master-job, SCM polling, where each index
        # entry's git-url and git-branch are already being monitored.
        # Thus stopping the behavior to start-build of configured pipelines.
        # if "configured" in output:
        #    _print("{} is updated, starting build..".format(
        #        project.pipeline_name))
        #    self.start_build(project.pipeline_name)

    @retry(tries=10, delay=3, backoff=2)
    def apply_weekly_scan(self,
                          project,
                          template_location="weekly-scan/template.yaml"
                          ):
        """
        Applies the weekly scan template, creating a pipeline for same
        :param project: The name of the project where the template is to be
        applied.
        :param template_location: The location of template file.
        """
        oc_process = "oc process -f {0} {1}".format(
            template_location,
            self.weekly_scan_template_params
        )

        oc_apply = "oc apply -n {} -f -".format(self.namespace)

        # oc process and oc apply command combined with a shell pipe
        command = oc_process + " | " + oc_apply

        # format the command with project params
        command = command.format(
            namespace=self.namespace,
            git_url=project.git_url,
            git_branch=project.git_branch,
            desired_tag=project.desired_tag,
            notify_email=project.notify_email,
            pipeline_name=project.pipeline_name,
            app_id=project.app_id,
            job_id=project.job_id,
            registry_url=self.registry_url,
            from_address=self.from_address,
            smtp_server=self.smtp_server,
            ccp_openshift_slave_image=self.ccp_openshift_slave_image,
            notify_cc_emails=self.notify_cc_emails,
            registry_alias=self.registry_alias,
        )
        # process and apply buildconfig
        output, _ = run_command(command, shell=True)
        print_out(output)

    @retry(tries=10, delay=3, backoff=2)
    def apply_buildconfigs(self,
                           project,
                           ):
        """
        Given a project object representing a project in container index,
        process the seed-job template for same and oc apply changes
        if needed, also performs `oc start-build` for updated project
        """
        self.apply_build_job(project)
        self.apply_weekly_scan(project)

    @retry(tries=10, delay=3, backoff=2)
    def start_build(self, pipeline_name):
        """
        Given a pipeline name, start the build for same
        """
        command = "oc start-build {} -n {}".format(
            pipeline_name, self.namespace)
        out, _ = run_command(command, shell=True)
        print_out(out)

    @retry(tries=10, delay=3, backoff=2)
    def delete_buildconfigs(self, bcs, wait_between_delete=5):
        """
        Deletes the given list of bcs
        """
        command = ("oc delete -n {} bc {} --ignore-not-found=true "
                   "--now=true --include-uninitialized=true")

        for bc in bcs:
            print_out("Deleting buildConfig {}".format(bc))
            run_command(command.format(self.namespace, bc), shell=True)
            time.sleep(wait_between_delete)

    @retry(tries=5, delay=3, backoff=2)
    def list_all_builds(self):
        """
        List all the builds
        """
        command = """\
oc get builds -o name -o template \
--template='{{range .items }}{{.metadata.name}}:{{.status.phase}} {{end}}'"""
        output, _ = run_command(command, shell=True)
        return output.strip().split()

    @retry(tries=10, delay=3, backoff=2)
    def list_builds_except(
            self,
            status=["Complete", "Failed"],
            filter_builds=["seed-job"]):
        """
        List the builds except the phase(s) provided
        default status=["Complete", "Failed"] <-- This will return
        all the builds except the status.phase in ["Complete", "Failed"].
        If provided a list of $filter_builds, it will filter mentioned builds
        from outstanding builds. The builds name has build number string
        appended, for eg seed-job-1, seed-job-2, thus filtering checks
        if outstanding build name starts with given $filter_builds.

        If status=[], return all the builds

        :arg status: Status of outstanding builds to filter
        :type status: List
        :arg filter_builds: Builds to filter from outstanding builds
        :type filter_builds: List
        :return: List of outstanding builds
        :rtype: List
        """
        if not status:
            return self.list_all_builds()

        conditional = '(ne .status.phase "{}") '
        condition = ''
        for phase in status:
            condition = condition + conditional.format(phase)

        command = """\
oc get builds -o name -o template --template='{{range .items }} \
{{if and %s }} {{.metadata.name}}:{{.status.phase}} \
{{end}}{{end}}'""" % condition

        output, _ = run_command(command, shell=True)
        output = output.strip().split(' ')
        output = [each for each in output
                  if not each.startswith(tuple(filter_builds))
                  and each]
        return output


class Index(object):
    """
    The orchestrator class to process operations
    in container index.
    """

    def __init__(self, index, registry_url, namespace,
                 from_address, smtp_server,
                 ccp_openshift_slave_image,
                 notify_cc_emails,
                 registry_alias,
                 master_job_cpu, master_job_memory,
                 infra_projects=["seed-job"],
                 ci_projects=["ci-success-job", "ci-failure-job"]):

        # create index reader object
        self.index_reader = IndexReader(index, namespace)

        # create bc_manager object
        self.bc_manager = BuildConfigManager(
            registry_url, namespace, from_address, smtp_server,
            ccp_openshift_slave_image, notify_cc_emails,
            registry_alias, master_job_cpu, master_job_memory)

        # set the infra_projects and ci_projects to be filtered
        # out while removing the stale jobs
        self.infra_projects = infra_projects
        self.ci_projects = ci_projects

    def find_stale_jobs(self, os_projects, index_projects, ci_projects):
        """
        Given oc projects and index projects, figure out stale
        projects and return.
        This method also has provision to take take exception lists.
        The exception list has names of projects which will be removed
        from found stale jobs and won't be removed from OpenShift.
        The desired target for exception list is for: ci-job

        :arg os_projects: Projects list in OpenShift
        :type os_projects: List
        :arg index_projects: Projects list read from index
        :type index_projects: List
        :arg ci_projects: CI projects list to be filtered from stale_projects
        :type ci_projects: List
        :return: Stale jobs list to be removed, [] if None
        :rtype: List

        """
        # diff existing oc projects from index projects

        stale_jobs = list(set(os_projects) - set(index_projects))

        if stale_jobs:
            # remove the exception list from found stale jobs
            print ("Removing CI job(s) {} from found stale jobs, "
                   "mentioned jobs won't be removed from OpenShift..".format(
                       ci_projects))
            return list(set(stale_jobs) - set(ci_projects))
        return stale_jobs

    def run(self, batch_size, polling_interval,
            batch_outstanding_builds_cap):
        """
        Orchestrate container index processing and performs
        following operations
         - reads the projects in the container index
         - reads the pipeline projects from OpenShift
         - finds diff between Index projects vs OpenShift projects
         - removes stale projects diff
         - creates new jobs based on diff
         - updates and triggers jobs having updated configs
         - creates/updates weekly scan projects
         - triggers batch processing method for above operations
        """
        # list all jobs in index, list of project objects
        index_projects = self.index_reader.read_projects()

        print_out("Number of projects in index {}".format(len(index_projects)))

        # list existing jobs in openshift
        os_projects = self.bc_manager.list_all_buildConfigs()

        # filter out infra projects + CI projects and return only pipeline name
        # bc names are like buildconfig.build.openshift.io/app_id-jobiid-dt
        # filtering will make sure, the count of openshift
        # projects listed is right
        filter_list = self.infra_projects + self.ci_projects

        os_projects = [bc.split("/")[1] for bc in os_projects
                       if bc.split("/")[1] not in filter_list]

        print_out("Number of projects in OpenShift {}".format(len(os_projects)))

        # names of pipelines for all projects in container index
        index_project_names = [project.pipeline_name for project in
                               index_projects]
        # Adding weekly scan project names
        index_project_names_with_wscan = []
        for item in index_project_names:
            index_project_names_with_wscan.append(item)
            index_project_names_with_wscan.append("wscan-" + item)

        # find stale projects based on pipeline-name
        stale_projects = self.find_stale_jobs(
            os_projects, index_project_names_with_wscan, self.ci_projects
        )

        if stale_projects:
            print_out("List of stale projects:\n{}".format(
                "\n".join(stale_projects)))
            # delete all the stal projects/buildconfigs
            self.bc_manager.delete_buildconfigs(stale_projects)

        print_out("Number of projects to be updated/created: {}".format(
            len(index_projects)))

        self.batch_process_projects(
            index_projects,
            batch_size,
            polling_interval,
            batch_outstanding_builds_cap
        )

    def batch(self, target_list, batch_size):
        """
        Returns a generator object yielding chunks of list
        of length=batch_size from target list
        """
        for i in range(0, len(target_list), batch_size):
            yield target_list[i:i + batch_size]

    def batch_process_projects(self,
                               index_projects, batch_size, polling_interval,
                               batch_outstanding_builds_cap):
        """
        Given a list of projects, oc apply the buildconfigs
        in batches of size $batch_size and oc apply the weekly
        scan jobs at the end.
        Watch the outstanding builds at $polling_interval and
        schedule next batch if current outstanding jobs are
        less than or equal to $batch_outstanding_builds_cap.
        """
        # Split the projects to process in equal sized chunks
        generator_obj = self.batch(index_projects, batch_size)

        print_out("Starting index processing with\n"
               "Batch size={}\nBatch polling Interval (in seconds)={}\n"
               "Batch outstndaing builds cap count={}\n".format(
                   batch_size,
                   polling_interval,
                   batch_outstanding_builds_cap))
        # iterate over batches of projects to be processed
        for batch in generator_obj:
            # Check if builds are in status.phase other than Complete
            # or Failed. We dont care about builds which are failed
            # or complete to queue up next batch of jobs to process
            outstanding_builds = self.bc_manager.list_builds_except(
                status=["Complete", "Failed", "Cancelled"],
                filter_builds=self.infra_projects)

            # wait until current outstanding builds are more than
            # configured cap for outstanding builds
            while len(outstanding_builds) > batch_outstanding_builds_cap:
                print_out("Waiting for completion of builds {}\n".format(
                    outstanding_builds))
                time.sleep(polling_interval)

                outstanding_builds = self.bc_manager.list_builds_except(
                    status=["Complete", "Failed", "Cancelled"],
                    filter_builds=self.infra_projects)

            print_out("Processing projects batch: {}\n".format(
                [each.pipeline_name for each in batch]))

            for project in batch:
                # oc process and oc apply to all fresh and existing jobs
                try:
                    self.bc_manager.apply_build_job(project)
                except Exception as e:
                    print_out("Error applying/creating build config for {}. "
                           "Moving on.".format(project.pipeline_name))
                    print_out("Error: {}".format(str(e)))
                else:
                    # grace period of 1 sec between configuring jobs
                    time.sleep(1)

        print_out("Processing weekly scan projects..")
        for project in index_projects:
            try:
                self.bc_manager.apply_weekly_scan(project)
            except Exception as e:
                print_out("Error applying/creating weekly scan build config "
                       "for {}. Moving on.".format(project.pipeline_name))
                print_out("Error: {}".format(str(e)))
            else:
                # grace period of 1 sec between configuring jobs
                time.sleep(1)


if __name__ == "__main__":
    if len(sys.argv) != 14:
        print_out("Incomplete set of input variables, please refer README.")
        sys.exit(1)

    index = sys.argv[1].strip()
    registry_url = sys.argv[2].strip()
    namespace = sys.argv[3].strip()
    from_address = sys.argv[4].strip()
    smtp_server = sys.argv[5].strip()
    batch_size = int(sys.argv[6].strip())
    batch_polling_interval = int(sys.argv[7].strip())
    batch_outstanding_builds_cap = int(sys.argv[8].strip())
    ccp_openshift_slave_image = sys.argv[9].strip()
    notify_cc_emails = sys.argv[10].strip()
    registry_alias = sys.argv[11].strip()
    master_job_cpu = sys.argv[12].strip()
    master_job_memory = sys.argv[13].strip()

    index_object = Index(
        index, registry_url, namespace,
        from_address, smtp_server, ccp_openshift_slave_image,
        notify_cc_emails, registry_alias, master_job_cpu, master_job_memory
    )

    index_object.run(
        batch_size,
        batch_polling_interval,
        batch_outstanding_builds_cap)

