from google.appengine.ext import ndb
import webapp2
import json


class Fish(ndb.Model):
    name = ndb.StringProperty(required=True)
    ph_min = ndb.IntegerProperty()
    ph_max = ndb.IntegerProperty()




class FishHandler(webapp2.RequestHandler):
    def post(self):
        fish_data = json.loads(self.request.body)
        self.response.write("here's that data: " + json.dumps(fish_data))


class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Hello, World 2!')





allowed_methods = webapp2.WSGIApplication.allowed_methods
new_allowed_methods = allowed_methods.union(('PATCH',))
webapp2.WSGIApplication.allowed_methods = new_allowed_methods
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/fish', FishHandler)
], debug=True)
