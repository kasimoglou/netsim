'''
Created on Mar 3, 2014

@author: vsam
@author:juls
'''


import logging
import bottle
from beaker.middleware import SessionMiddleware

#from runner.config import gui_file_path, nsdEdit_file_path
from runner.config import cfg

# importing these declares their functions
import runner.admingui
import runner.restapi
import runner.nsdgui
import runner.AAA as AAA

logger = logging.getLogger('GUI')

root = bottle.Bottle()

@root.get('/')
def index():
	bottle.redirect("/admin/")



def start_gui(args, guiaddr):
    global root

    root.mount('/api', runner.restapi.app)
    root.mount('/admin', runner.admingui.app)
    root.mount('/nsdEdit', runner.nsdgui.app)

    root = SessionMiddleware(root, {
        'session.type': 'cookie',
        'session.validate_key': 'zavarakadfasdfasdfasdfasdfasdfasdfasdfasgsgfhdgjgeyjhuhrty54y454hqqbrtbsdbsbdfatranemia',
        'session.encrypt_key': 'dagfasvgavnhcfdngcfcaewancanogfogasdfdasfadsafdfadfadfdfdafadfdasncfeonawhcmcmhcfmhcfewopqwfeom',
        'session.secret': 'dagfasvfdasfdasfadsdfasfafadsffdasfadsgavnhcfdngcfcaewancanogfogncfeonawhcmcmhcfmhcfewopqwfeom'
    })

    bottle.debug(True)
    bottle.TEMPLATE_PATH.insert(0, cfg.gui_file_path)
    bottle.run(server=cfg.http_server, 
        app = root, 
        host=guiaddr[0], port=guiaddr[1], 
        quiet=True)
    logging.info("Stopped web server")

