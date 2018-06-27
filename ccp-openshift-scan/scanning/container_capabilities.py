#!/usr/bin/env python


def split_by_newline(response):
    """
    Return a list of string split by newline character
    """
    return response.split("\n")

try:
    # Check if the image under scan has a RUN label
    # More info on Dockerfile labels:
    # https://docs.docker.com/engine/reference/builder/#/label
    run_label = check_image_for_run_label(image=IMAGE_NAME)

    # run_object.check_args(run_label)

    out, err = subprocess.Popen(
        [
            "python",
            "run_scanner.py"
        ],
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE
    ).communicate()

    if out is not None:
        json_out["Scan Results"]["Container capabilities"] = out

        if out == "":
            json_out["Summary"] = "No additional capabilities found."
        else:
            json_out["Summary"] = \
                "Container image has few additional capabilities."
    else:
        json_out["Scan Results"]["Container capabilities"] = \
            "This container image doesn't have any special capabilities"
        json_out["Summary"] = "No additional capabilities found."

    json_out["Successful"] = "true"

except RunLabelException as e:
    json_out["Scan Results"]["Container capabilities"] = e.message
    json_out["Successful"] = "false"
    json_out["Summary"] = "Dockerfile for the image doesn't have RUN label."
except Exception as e:
    logger.log(
        level=logging.ERROR,
        msg="Scanner failed: {}".format(e)
    )
    json_out["Summary"] = "Scanner failed."
finally:
    json_out["Finished Time"] = \
        datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')

output_dir = os.path.join(OUTDIR, UUID)
os.makedirs(output_dir)

output_file_relative = "container_capabilities_scanner_results.json"

output_file_absoulte = os.path.join(output_dir, output_file_relative)

with open(output_file_absoulte, "w") as f:
    f.write(json.dumps(json_out, indent=4))
