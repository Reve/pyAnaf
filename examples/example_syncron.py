from __future__ import unicode_literals

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pyAnaf.api import Anaf

anaf = Anaf()

anaf.addCUI('dddd')