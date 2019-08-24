from odevalidator import TestCase, ValidatorException
import unittest
import queue
from tests import assert_results

class ValidatorIntegrationTest(unittest.TestCase):
    
    def test_good_file_does_good_things(self):
        data_file = 'tests/testfiles/good.json'
        results = self._validate_file(data_file)
        assert_results(self, results, 0)

    def test_good_bsmTx_file_passes_sequential_checks(self):
        data_file = 'tests/testfiles/good_bsmTx.json'
        config_file = 'odevalidator/configs/config_bsm.ini'
        results = self._validate_file(data_file, config_file)
        assert_results(self, results, 0)

    def test_good_braodcast_tim(self):
        data_file = 'tests/testfiles/good_broadcast_tim.json'
        config_file = 'odevalidator/configs/config_tim.ini'
        results = self._validate_file(data_file, config_file)
        assert_results(self, results, 0)

    def test_good_rxMsg_BSMonly(self):
        data_file = 'tests/testfiles/good_rxMsg_BSMonly.json'
        results = self._validate_file(data_file)
        assert_results(self, results, 0)

    def test_good_json_alt_value(self):
        data_file = 'tests/testfiles/good_altValPercent.json'
        config_file = 'odevalidator/configs/configAltPercent.ini'
        results = self._validate_file(data_file, config_file)
        assert_results(self, results, 0)

    def test_csv_file(self):
        data_file = 'tests/testfiles/good_vsl.csv'
        config_file = 'odevalidator/configs/csvconfig.ini'
        results = self._validate_file(data_file, config_file)
        assert_results(self, results, 0)

    def test_csv_timestamp_file(self):
        data_file = 'tests/testfiles/good_vsl_timestamp.csv'
        config_file = 'odevalidator/configs/csv_timestamp_config.ini'
        results = self._validate_file(data_file, config_file)
        assert_results(self, results, 0)
    
    def test_bad_csv_file(self):
        data_file = 'tests/testfiles/bad_vsl.csv'
        config_file = 'odevalidator/configs/csvconfig.ini'
        results = self._validate_file(data_file, config_file)
        assert_results(self, results, 4)
    
    def test_bad_file_does_bad_things(self):
        data_file = 'tests/testfiles/bad.json'
        results = self._validate_file(data_file)
        assert_results(self, results, 29)

    def test_good_regex(self):
        data_file = 'tests/testfiles/good_regex.csv'
        regex_config = 'odevalidator/configs/regex_config.ini'
        results = self._validate_file(data_file, regex_config)
        assert_results(self, results, 0)

    def test_bad_regex(self):
        data_file = 'tests/testfiles/bad_regex.csv'
        regex_config = 'odevalidator/configs/regex_config.ini'
        results = self._validate_file(data_file, regex_config)
        assert_results(self, results, 3)

    def _validate_file(self, data_file, config_file = 'odevalidator/configs/config.ini'):
        validator = TestCase(config_file, )

        with open(data_file) as f:
            content = f.readlines()
        # remove whitespace characters like `\n` at the end of each line
        content = [x.strip() for x in content]
        #msgs = [json.loads(line) for line in content]
        q = queue.Queue()
        for msg in content:
            if msg and not msg.startswith('#'):
                q.put(msg)

        results = validator.validate_queue(q)

        return results
