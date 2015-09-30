import web
import wifidog

urls = (
    '/wifidog',         wifidog.app,
    '/(.*)',           'index',
    )

web.config.debug = True
app = web.application(urls, globals())

session = None
if web.config.debug == True:
    if web.config.get('_session') is None:
        session = web.session.Session(app, web.session.DiskStore('sessions'),
                                      initializer={"token":""})
        web.config._session = session
    else:
        session = web.config._session
else:
    session = web.session.Session(app, web.session.DiskStore('sessions'))

def session_hook():
    web.ctx.session = session

app.add_processor(web.loadhook(session_hook))

class redirect:
    def GET(self, path):
        print "redirect:"+path
        web.seeother('/' + path)

class index:
    def GET(self, name):
        return "TODO:redirect to a url that include free wifi introduce"

application = app.wsgifunc()

