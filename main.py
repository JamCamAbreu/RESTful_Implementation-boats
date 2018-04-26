import json
from google.appengine.ext import ndb
import webapp2

# EXAMPLE:
class Fish(ndb.Model):
    name = ndb.StringProperty(required=True)
    ph_min = ndb.IntegerProperty()
    ph_max = ndb.IntegerProperty(repeated=True) #repeated allows lists of properties (makes it an array)


class Boat(ndb.Model):
    id = ndb.StringProperty() # for this I should use the primary key
    name = ndb.StringProperty(required=True)
    type = ndb.StringProperty(required=True)
    length = ndb.IntegerProperty(required=True)
    at_sea = ndb.BooleanProperty(default=True)


class Departure_Ticket(ndb.Model):
    departure_date = ndb.DateProperty()
    departed_boat = ndb.KeyProperty()


class Slip(ndb.Model):
    id = ndb.StringProperty() # for this I should use the primary key
    number = ndb.IntegerProperty(required=True)
    current_boat = ndb.KeyProperty()
    arrival_date = ndb.StringProperty()
    # departure_history = 



# EXAMPLE:
class FishHandler(webapp2.RequestHandler):
    def post(self):

        parent_key = ndb.Key(Fish, "parent_fish")

        fish_data = json.loads(self.request.body)
        new_fish = Fish(name=fish_data['name'], parent=parent_key)
        new_fish.put()
        fish_dict = new_fish.to_dict()
        fish_dict['self'] = '/fish/' + new_fish.key.urlsafe()
        self.response.write("here's that data: " + json.dumps(fish_dict))

    def get(self, id=None):
        if id:
            f = ndb.Key(urlsafe=id).get()

            # aside: how to update a property on a model:
            f.ph_max = [100, 50]    # change property here
            f.put()                 # update model (final step)

            f_d = f.to_dict()
            f_d['self'] = "/fish/" + id
            self.response.write(json.dumps(f_d))




# +--------------------------------------+
# |              BOATS                   |
# +--------------------------------------+

class BoatHandler(webapp2.RequestHandler):

    # POST a NEW BOAT
    def post(self):

        # check unique boat name:


        # create the boat:
        parent_key = ndb.Key(Boat, "allBoats")
        boat_data = json.loads(self.request.body)

        # check data here

        new_boat = Boat()
        new_boat.name = boat_data['name']
        new_boat.type = boat_data['type']
        new_boat.length = boat_data['length']
        new_boat.parent = parent_key
        boat_key = new_boat.put()

        # store the id using the key:
        boat_id = boat_key.id()
        new_boat.id = str(boat_id)
        new_boat.put()

        # convert to dictionary:
        boat_dict = new_boat.to_dict()
        boat_dict['self'] = '/boat/' + new_boat.key.urlsafe()
        self.response.write("Here's the boat: " + json.dumps(boat_dict))

    # GET an existing BOAT
    def get(self, id=None):
        if id:
            b = ndb.Key(urlsafe=id).get()
            b_d = b.to_dict()
            b_d['self'] = "/boat/" + id
            self.response.write(json.dumps(b_d))

        # display ALL boats:
        else:
            # query all slips
            q = Boat.query()
            allBoats = q.order(Boat.name)

            # put all slips in a list for nice printing:
            boat_list = []
            for boat in allBoats:
                boat = boat.to_dict()
                boat_list.append(boat)
            self.response.headers["Content-Type"] = "application/json"
            self.response.write(json.dumps(boat_list))
            self.response.write("end of list")


    # delete a boat
    def delete(self, id=None):
        self.response.write("how dare you!")





# +--------------------------------------+
# |             SLIPS                    |
# +--------------------------------------+

class SlipHandler(webapp2.RequestHandler):

    # POST a NEW SLIP
    def post(self):

        # set parent
        parent_key = ndb.Key(Slip, "allSlips")

        # Get request data:
        slip_data = json.loads(self.request.body)

        # check data here:

        # create slip:
        new_slip = Slip()
        new_slip.name = slip_data['name']

        # generate unused number for slip:
        q = Slip.query()
        prevSlips = q.order(Slip.number)
        curNum = 1
        for slip in prevSlips.fetch():
            if (slip.number != curNum):
                unusedNum = curNum
                break
            else:
                curNum += 1

        #self.response.write("number To Use: " + str(curNum))
        new_slip.number = curNum
        new_slip.parent = parent_key
        slip_key = new_slip.put()

        # store the id using the key:
        slip_id = slip_key.id()
        new_slip.id = str(slip_id)
        new_slip.put()

        # convert to dictionary:
        slip_dict = new_slip.to_dict()
        slip_dict['self'] = '/slip/' + new_slip.key.urlsafe()
        self.response.headers["Content-Type"] = "application/json"
        self.response.write("Here's the slip: " + json.dumps(slip_dict))



    # GET an existing SLIP
    def get(self, id=None):
        if id:
            s = ndb.Key(urlsafe=id).get()
            s_d = s.to_dict()
            s_d['self'] = "/slip/" + id
            self.response.write(json.dumps(s_d))

        # display ALL slips:
        else:
            # query all slips
            q = Slip.query()
            allSlips = q.order(Slip.number)

            # put all slips in a list for nice printing:
            slip_list = []
            for slip in allSlips:
                slip = slip.to_dict()
                slip_list.append(slip)
            self.response.headers["Content-Type"] = "application/json"
            self.response.write(json.dumps(slip_list))


    # delete a slip
    def delete(self, id=None):
        if id:
            # look up slip with given id
            s = Slip.get_by_id(int(id))

            if s is None:
                self.response.set_status(404)
                self.response.write("Slip with given id could not be found")

            else:
                s.key.delete()
                self.response.set_status(200)
                self.response.write("Slip with given id was removed successfully")

        # no id supplied
        else:
            self.response.set_status(404)
            self.response.write("You must supply an id for the slip to be removed")















class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Hello, World 2!')




allowed_methods = webapp2.WSGIApplication.allowed_methods
new_allowed_methods = allowed_methods.union(('PATCH',))
webapp2.WSGIApplication.allowed_methods = new_allowed_methods
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/fish', FishHandler),
    ('/fish/(.*)', FishHandler),
    ('/boat', BoatHandler),
    ('/boat/(.*)', BoatHandler),
    ('/slip', SlipHandler),
    ('/slip/(.*)', SlipHandler)
], debug=True)
