python_home = '/var/www/robvoigt/env'

import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/robvoigt/")

from robvoigt import app as application
