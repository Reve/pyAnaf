# coding: utf-8

from __future__ import print_function
import sys
import os
import datetime
import pprint


try:
    from pyAnaf.api import Anaf
except:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from pyAnaf.api import Anaf


class MyPrettyPrinter(pprint.PrettyPrinter):
    def format(self, object, context, maxlevels, level):
        #print (type(object))
        #print (object)
        # if isinstance(object, str):
        #     return (object.encode('utf8'), True, False)
        return pprint.PrettyPrinter.format(self, object, context, maxlevels, level)

def print_err(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def main():
    if len(sys.argv) < 2:
        print_err("usage: %s <cuis_separated_by_comma> <limit>\n" % sys.argv[0])
        sys.exit(-255)

    limit = 5

    cuis = sys.argv[1].split(',')


    try:
        limit = int(sys.argv[2])
    except:
        pass

    today = datetime.date.today()

    anaf = Anaf()
    anaf.setLimit(limit)
    for cui in cuis:
        try:
            anaf.addCUI(int(cui), date=today)
        except Exception as e:
            print_err(e)

    anaf.Request()

    pp = MyPrettyPrinter(indent=4)
    for entry in anaf.result:
        pp.pprint(entry)

if __name__ == '__main__':
    main()
