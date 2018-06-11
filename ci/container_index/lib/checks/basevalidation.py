from ci.container_index.lib.utils import IndexCIMessage
import os


class Validator(object):

    def __init__(self, validation_data, file_name):
        self.message = IndexCIMessage(validation_data)
        self.validation_data = validation_data
        self.file_name = file_name
        self.file_base_name = os.path.basename(self.file_name)

    def _invalidate(self, err):
        self.message.success = False
        self.message.errors.append(err)

    def _warn(self, warn):
        self.message.warnings.append(warn)

    def _perform_validation(self):
        """
        Validation logic of the validator resides here.
        Subclass must override
        """
        raise NotImplementedError

    def validate(self):
        """
        Runs the validator to validate based on provided data.
        :return: Returns a flag to indicate success or falure
        and an IndexCIMessage object.
        """
        self._perform_validation()
        return self.message


class BasicSchemaValidator(Validator):

    def __init__(self, validation_data, file_name):
        super(BasicSchemaValidator, self).__init__(validation_data, file_name)
        self.field_name = ""

    def _perform_validation(self):
        if not self.validation_data.get(self.field_name):
            self._invalidate(
                str.format(
                    "Missing required field {}",
                    self.field_name
                )
            )
            return
        self._extra_validation()

    def _extra_validation(self):
        pass


class StringFieldValidator(BasicSchemaValidator):

    def __init__(self, validation_data, file_name):
        super(StringFieldValidator, self).__init__(validation_data, file_name)
        self.field_name = ""

    def _extra_validation_1(self):
        pass

    def _extra_validation(self):
        if not isinstance(
            self.validation_data.get(self.field_name), str
        ):
            self._invalidate(
                str.format(
                    "{} field must be a string",
                    self.field_name
                )
            )
            return
        if len(self.validation_data.get(self.field_name)) <= 0:
            self._invalidate(
                str.format(
                    "{} field cannot be a zero length string",
                    self.field_name
                )
            )
            return
        self._extra_validation_1()
