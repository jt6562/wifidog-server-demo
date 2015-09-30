import web
import tempfile
import hashlib
from web.contrib.template import render_mako
from time import time, strftime, localtime, mktime, strptime

urls = (
    '/ping',        'wifidog_ping',
    '/ping/',        'wifidog_ping',
    '/auth',        'wifidog_auth',
    '/auth/',        'wifidog_auth',
    '/login',       'wifidog_login',
    '/login/',       'wifidog_login',
    '/portal',      'wifidog_portal',
    '/portal/',      'wifidog_portal',
    '/gw_message',  'wifidog_gwmessage',
    '/gw_message/',  'wifidog_gwmessage',
    '/(.*)/',               'redirect',
    )

app = web.application(urls, globals())

root= tempfile.mkdtemp()
print root
clientstatus = web.session.DiskStore(root)
client_log_max = 20

db = web.database(dbn='mysql',db='authdatabase',user='root',pw='1')
#db = web.database(dbn='mysql',db='authserver',user='wifidogn',pw='wifidognormal')

class redirect:
    def GET(self, path):
        print "redirect:"+path
        web.seeother('/' + path)

class wifidog_ping:
    def GET(self):
        req = web.input()
        status = []
        try:
            status= clientstatus[req.gw_id]
            if len(status) > client_log_max:
                status.pop(0)
        except:
            pass
        finally:
            status.append({"sys_uptime":req.sys_uptime,
                         "sys_memfree":req.sys_uptime,
                         "sys_load":req.sys_load,
                         "wifidog_uptime":req.wifidog_uptime})
        clientstatus[req.gw_id] = status
        return "Pong"

class wifidog_auth:
    def GET(self):
        req = web.input()

        #AUTH_ERROR = -1, /**< An error occured during the validation process*/
        #AUTH_DENIED = 0, /**< Client was denied by the auth server */
        #AUTH_ALLOWED = 1, /**< Client was granted access by the auth server */
        #AUTH_VALIDATION = 5, /**< A misnomer.  Client is in 15 min
        #       probation to validate his new account */
        #AUTH_VALIDATION_FAILED = 6, /**< Client had X minutes to
        #       validate account by email and didn't = too late */
        #AUTH_LOCKED = 254 /**< Account has been locked */

        print req
        tokenentry = db.select('token',
                       where="token=$token",
                       vars={"token":req.token}
                       )
        item = tokenentry.list()
        if len(item) == 0:
            print "invalid token"
            return "AUTH: 0"

        print "auth token", req.token
        print "token username:", item[0].username
        #Check user right
        #TODO:check kinds of user type
        if item[0].username == 'guest':
            logintime = item[0].logintime
            expiretime = mktime(logintime.timetuple()) + 5 * 60

            #Had expired
            if expiretime < time():
                print "Guest user had expired, token:"+req.token
                db.select('token',
                       where="token=$token",
                       vars={"token":req.token}
                       )
                return "Auth: 6"

        print "auth ok"
        return "Auth: 1"

class wifidog_login:
    def __init__(self):
        self.render = render_mako(
                directories=['views'],
                input_encoding='utf-8',
                output_encoding='utf-8'
                )

    def GET(self):
        req = web.input()
        web.ctx.session.gw_id = req.gw_id
        web.ctx.session.gw_address = req.gw_address
        web.ctx.session.gw_port = req.gw_port
        web.ctx.session.mac = req.mac
        web.ctx.session.url = req.url
        return self.render.login()

    def POST(self):
        post = web.input()
        print "login POST:",post
        if post.has_key("username") is False or post.has_key("password") is False:
            print "POST form is invlid"
            return self.render.login()

        pw = db.select('userinfo',
                       where="username=$name and passwd=$pw",
                       vars={"name":post.username,
                             "pw":hashlib.sha1(post.password).hexdigest()},
                       )

        authres = len(pw.list())
        if authres == 0:
            print "user and pwd donot match", post.username, hashlib.sha1(post.password).hexdigest()
            return self.render.login()

        token = None

        #Did the mac of client if exist? Yes! Remove it
        tokenentry = db.select('token',
                       where="clientmac=$mac",
                       vars={"mac":web.ctx.session.mac}
                       )
        item = tokenentry.list()
        if len(item)> 0:
            token = item[0].token
            print "This mac has logined ,token:"+token, "update logintime"
            r = db.delete('token',
                      where="clientmac=$mac",
                      vars={"mac":web.ctx.session.mac}
                      )

        token = hashlib.md5(str(time())).hexdigest()
        print "insert:", token, web.ctx.session.mac,post.username, type(post.username)
        db.insert("token",
                  token = token,
                  clientmac = web.ctx.session.mac,
                  username = post.username
                  )

        redirecturl = 'http://%s:%s/wifidog/auth?token=%s&url=%s' % (
                    web.ctx.session.gw_address,
                    web.ctx.session.gw_port,
                    token,
                    web.ctx.session.url
                )
        print redirecturl

        return web.seeother(redirecturl)


class wifidog_portal:
    def GET(self):
        if web.ctx.session.has_key("url"):
            print "portal", web.ctx.session.url
            web.seeother(web.ctx.session.url)
        else:
            print "portal to defalut page"
            web.seeother("http://www.baidu.com/")


class wifidog_gwmessage:
    def GET(self):
        return "gwmessage"

