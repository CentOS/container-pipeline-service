import yaml

with open("source/projects.yaml") as stream:
    try:
        yml_dict = (yaml.load(stream))
    except yaml.YAMLError as exc:
        print (exc)

oc_apply = "| oc apply -f -"

for entry in yml_dict["Projects"]:
    pipeline_name = entry["app-id"] + "-" + entry["job-id"] + "-" + \
        entry["desired-tag"]
    command = "oc process -f seed-job/template.yaml " + \
        "-p GIT_URL={} ".format(entry["git-url"]) + \
        "-p GIT_PATH={} ".format(entry["git-path"]) + \
        "-p GIT_BRANCH={} ".format(entry["git-branch"]) + \
        "-p DESIRED_TAG={} ".format(entry["desired-tag"]) + \
        "-p NOTIFY_EMAIL={} ".format(entry["notify-email"]) + \
        "-p PIPELINE_NAME={} ".format(pipeline_name) + \
        "-p DEPENDS_ON={} ".format(entry["depends-on"]) + \
        "-p TARGET_FILE={} ".format(entry["target-file"]) + \
        "-p CONTEXT_DIR={} ".format("master-job") + \
        "-p APP_ID={} ".format(entry["app-id"]) + \
        "-p JOB_ID={} ".format(entry["job-id"])

    # there's gotta be a better way to ensure that buildconfigs created by
    # parsing the yaml file get triggered automatically for first run.
    oc_build = "oc start-build {} -n myproject".format(pipeline_name)

    with open("projects.sh", "a+") as f:
        f.write("{} {} && {} \n".format(command, oc_apply, oc_build))
