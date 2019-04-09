from argparse import ArgumentParser
import odevalidator

# Tests go here
print("Executing local tests...")

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("--data-file", dest="data_file_path", help="Path to log data file that will be sent to the ODE for validation.", metavar="DATAFILEPATH", required=True)
    args = parser.parse_args()

    odevalidator.validator.test(args.data_file_path)

