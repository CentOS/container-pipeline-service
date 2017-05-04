from ci.tests.base import BaseTestCase
import os
import server.cccp_reader as cccp_reader
import yaml


def touch_file(file_path):
    with open(file_path, 'a'):
        os.utime(file_path, None)


def _print_test_msg(msg):
    print "=" * len(msg)
    print msg
    print "=" * len(msg)


class Test01CCCPReader(BaseTestCase):

    @staticmethod
    def _generate_cccp_yaml(jobid, test_skip, test_script, build_script, delivery_script,
                            none_is_empty=False):
        cccp_yml = {
            "job-id": jobid
        }

        if not none_is_empty:
            cccp_yml["test-skip"] = test_skip
            cccp_yml["test-script"]= test_script
            cccp_yml["build-script"] = build_script
            cccp_yml["delivery-script"] = delivery_script
        else:
            if test_script:
                cccp_yml["test-script"] = test_script
            if build_script:
                cccp_yml["build-script"] = build_script
            if delivery_script:
                cccp_yml["delivery-script"] = delivery_script

        return cccp_yml

    def setUp(self, cccp_yml_data=None):
        super(Test01CCCPReader, self).setUp()
        self._target_file = "./test_file"
        self._cccp_mock = "./mock_cccp.yml"
        self._current_dir = os.getcwd()
        self._build_script_path = None
        self._test_script_path = None
        self._delivery_script_path = None
        touch_file(self._target_file)

        if cccp_yml_data:
            touch_file(self._cccp_mock)
            with open(self._cccp_mock, "w") as f:
                yaml.dump(cccp_yml_data, f)

            if "build-script" in cccp_yml_data and cccp_yml_data["build-script"]:
                self._build_script_path = os.path.join(self._current_dir, cccp_yml_data["build-script"])
            if "test-script" in cccp_yml_data and cccp_yml_data["test-script"]:
                self._test_script_path = os.path.join(self._current_dir, cccp_yml_data["test-script"])
            if "delivery-script" in cccp_yml_data and cccp_yml_data["delivery-script"]:
                self._delivery_script_path = os.path.join(self._current_dir, cccp_yml_data["delivery-script"])

    def tearDown(self):
        if os.path.exists(self._target_file):
            os.remove(self._target_file)
        if os.path.exists(self._cccp_mock):
            os.remove(self._cccp_mock)
        if os.path.exists("/test_scripts"):
            os.remove("/test_scripts")
        if os.path.exists("/build_script"):
            os.remove("/build_script")
        if os.path.exists("/delivery_script"):
            os.remove("/delivery_script")

    def test_00_teardown_leftovers(self):
        self.setUp()
        self.tearDown()

    def test_01_echo_scripts_works_correctly(self):
        _print_test_msg("Test if echo scripts writes correct entry into file")
        phase = "build"
        self.setUp()
        cccp_reader.echo_scripts(self._target_file, phase)
        expected = "echo \""+phase+"Script not present\""
        with open(self._target_file, "r") as f:
            self.assertTrue(expected in f.readlines())
        self.tearDown()

    def test_02_add_build_script_adds_correct_run_entry(self):
        _print_test_msg("Test if add_build_script adds correct RUN entry to file")
        self.setUp()
        step = "RUN ln -s /build_script /usr/bin/build_script"
        cccp_reader.add_build_steps(self._target_file, step)

        with open(self._target_file, "r") as f:
            self.assertTrue(step + "\n" in f.readlines())
        self.tearDown()

    def test_03_target_generated_correctly_if_all_fields_provided_and_test_skip_false(self):
        _print_test_msg("Test if the target file is generated correctly if all parameters are passed and test-skip is false")
        cccp_yml_data = self._generate_cccp_yaml("test", False, "mytest", "mybuild", "mydelivery")
        self.setUp(cccp_yml_data)
        cccp_reader.main(self._target_file, True)
        with open(self._target_file, "r") as f:
            lines = f.readlines()
            self.assertTrue(
                "RUN ln -s "+self._build_script_path+" /usr/bin/build_script\n" in lines and
                "RUN ln -s "+self._test_script_path+" /usr/bin/test_script\n" in lines and
                "RUN ln -s "+self._delivery_script_path+" /usr/bin/delivery_script\n" in lines
            )

        self.tearDown()

    def test_04_target_generated_correctly_if_test_skip_true(self):
        _print_test_msg("Test if correct target file generated if test skip is True")
        cccp_yml_data = self._generate_cccp_yaml("test", True, "mytest", "mybuild", "mydelivery")
        self.setUp(cccp_yml_data)
        cccp_reader.main(self._target_file, True)
        with open(self._target_file, "r") as f:
            lines = f.readlines()
            self.assertTrue(
                "RUN ln -s /test_script /usr/bin/test_script\n" in lines
            )
        self.tearDown()

    def test_05_target_generated_correctly_missing_build_script(self):
        _print_test_msg("Test if target is generated correctly if no build script is given")
        cccp_yml_data = self._generate_cccp_yaml("test", True, "mytest", None, "mydelivery")
        self.setUp(cccp_yml_data)
        cccp_reader.main(self._target_file, True)
        with open(self._target_file, "r") as f:
            lines = f.readlines()
            self.assertTrue(
                "RUN ln -s /build_script /usr/bin/build_script\n" in lines
            )
        self.tearDown()

    def test_06_target_generation_fails_missing_test_script_and_test_skip_false(self):
        _print_test_msg("Test if target generation fails if no test script is given while test skip is false")
        cccp_yml_data = self._generate_cccp_yaml("test", False, None, "mybuild", "mydelivery")
        self.setUp(cccp_yml_data)
        ex = None
        try:
            cccp_reader.main(self._target_file, True)
        except Exception as ex:
            pass
        self.assertTrue(ex.message == "None or empty test script provided")
        self.tearDown()

    def test_07_target_generated_correctly_missing_delivery_script(self):
        _print_test_msg("Test if target is generated correctly if no delivery script is given")
        cccp_yml_data = self._generate_cccp_yaml("test", False, "mytest", "mybuild", None)
        self.setUp(cccp_yml_data)
        cccp_reader.main(self._target_file, True)
        with open(self._target_file, "r") as f:
            lines = f.readlines()
            self.assertTrue(
                "RUN ln -s /delivery_script /usr/bin/delivery_script\n" in lines
            )
        self.tearDown()

    def test_08_target_generation_fails_missing_job_id(self):
        _print_test_msg("Test if target generation fails if job id is missing in cccp yml")
        cccp_yml_data = self._generate_cccp_yaml(None, False, "mytest", "mybuild", "mydelivery")
        self.setUp(cccp_yml_data)
        ex = None
        try:
            cccp_reader.main(self._target_file, True)
        except Exception as ex:
            pass
        self.assertTrue(ex.message == "Missing or empty job-id field")
        self.tearDown()