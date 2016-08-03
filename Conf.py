#!/usr/bin/env python

import json

class conf_parser(object):

    def __init__(self):
        self.read_config()


    def read_config(self):
        c_f = open('config.json', 'r')
        self.config = json.loads(c_f.read())
        c_f.close()
        if 'debug' in self.config['global'] and self.config['global']['debug']:
            print json.dumps(self.config, sort_keys=True, indent=4, separators=(',', ': '))

    def get_config(self, module):
        res={}
        for key in self.config['global'].keys():
            res[key]=self.config['global'][key]
        for key in self.config[module].keys():
            res[key]=self.config[module][key]
        if 'debug' in self.config['global'] and self.config['global']['debug']>1:
            print json.dumps(res, sort_keys=True, indent=4, separators=(',', ': '))
        return res
