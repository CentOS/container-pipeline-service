import os
import sys
import yaml

CONTAINER_REPO_DIR = sys.argv[1]

with open(os.path.join(CONTAINER_REPO_DIR, "projects.yaml")) as stream:
    try:
        yml_dict = (yaml.load(stream))
    except yaml.YAMLError as exc:
        print (exc)

oc_apply = "| oc apply -f -"

for entry in yml_dict["Projects"]:
    try:
        pipeline_name = entry["app-id"] + "-" + entry["job-id"] + "-" + \
            entry["desired-tag"]
        command = "oc process -f seed-job/template.yaml " + \
            "-p GIT_URL={} ".format(entry["git-url"]) + \
            "-p GIT_PATH={} ".format(entry["git-path"]) + \
            "-p GIT_BRANCH={} ".format(entry["git-branch"]) + \
            "-p DESIRED_TAG={} ".format(entry["desired-tag"]) + \
            "-p NOTIFY_EMAIL={} ".format(entry["notify-email"]) + \
            "-p PIPELINE_NAME={} ".format(pipeline_name) + \
            "-p DEPENDS_ON={depends_on} ".format(
                depends_on=None if entry["depends-on"] is None
                else entry["depends-on"].replace("/", "-").replace(":", "-")
            ) + \
            "-p TARGET_FILE={} ".format(entry["target-file"]) + \
            "-p CONTEXT_DIR={} ".format("master-job") + \
            "-p APP_ID={} ".format(entry["app-id"]) + \
            "-p JOB_ID={} ".format(entry["job-id"]) + \
            "-p REGISTRY_URL={}".format(sys.argv[2])
    except Exception as e:
        print "Error processing entry for {}".format(pipeline_name)
        print "Error was\n{}".format(e)
        continue

    # there's gotta be a better way to ensure that buildconfigs created by
    # parsing the yaml file get triggered automatically for first run.
    oc_build = "oc start-build {} -n myproject".format(pipeline_name)

    with open("projects.sh", "a+") as f:
        f.write("{} {} && {} \n".format(command, oc_apply, oc_build))
