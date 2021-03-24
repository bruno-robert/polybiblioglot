import argparse
import logging

from polybiblioglot import Polybiblioglot

# Parse the arguments
parser = argparse.ArgumentParser(
    prog='Polybiblioglot',
    usage='%(prog)s [OPTION}',
    description='A tool used to convert scanned documents to text and translate them.'
)

parser.add_argument('-l', '--log-level', action='store', default='INFO', dest='log_level')
args = parser.parse_args()

# Initialize the logger
logger = logging.getLogger(__name__)
if args.log_level:
    logger.setLevel(args.log_level)

# Create the console handler
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

# Create and start PolyBiblioGlot
pbg = Polybiblioglot(logger=logger)
pbg.start()