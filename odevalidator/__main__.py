import json
import queue
from argparse import ArgumentParser
from odevalidator import TestCase

if __name__ == '__main__':
    """
    Provided for convenience. Allows users to perform validation using only the library.
    Arguments:
      --data-file (string): Newline-separated file containing records in json format.

    Output:
      Prints results in json.dumps format.
    """
    parser = ArgumentParser()
    parser.add_argument("--data-file", dest="data_file_path", help="Path to log data file that will be sent to the ODE for validation.", metavar="DATAFILEPATH", required=True)
    parser.add_argument("--config-file", dest="config_file_path", help="Path to config.ini file that will be used to validate the data file.", metavar="CONFIGFILEPATH", required=False)
    args = parser.parse_args()

    msg_list = []
    with open(args.data_file_path, 'r') as f:
        msg_list = f.read().splitlines()

    msg_queue = queue.Queue()
    for msg in msg_list:
        if msg and not msg.startswith('#'):
            msg_queue.put(msg)

    results = TestCase(args.config_file_path).validate_queue(msg_queue)
    #print(results[0].field_validations[0].valid)

    success = True
    for result in results:
        for field in result.field_validations:
            if field.valid == False:
                print("Invalid field '" + field.field_path + "' due to " + field.details + " at log id: " + str(result.serial_id))
            success = success and field.valid

    print ("\nSuccess: ", success,"\n")
