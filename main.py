import json
import datetime
from google.appengine.ext import ndb
import webapp2


# +--------------------------------------+
# |          Modules Used                |
# +--------------------------------------+

class Boat(ndb.Model):
    id = ndb.StringProperty() # for this I should use the primary key
    name = ndb.StringProperty(required=True)
    type = ndb.StringProperty(required=True)
    length = ndb.IntegerProperty(required=True)
    at_sea = ndb.BooleanProperty(default=True)


class Slip(ndb.Model):
    id = ndb.StringProperty() # for this I should use the primary key
    number = ndb.IntegerProperty(required=True)
    current_boat = ndb.StringProperty()
    arrival_date = ndb.StringProperty()










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
            idInt = int(id)
            b = Boat.get_by_id(idInt)
            b_d = b.to_dict()
            b_d['self'] = "/boat/" + id
            self.response.headers["Content-Type"] = "application/json"
            self.response.write(json.dumps(b_d))

        # display ALL boats:
        else:
            # query all slips
            q = Boat.query()
            allBoats = q.order(Boat.name)

            # put all slips in a list for nice printing:
            boat_list = []
            for boat in allBoats:
                boatID = boat.id
                boat = boat.to_dict()
                boat['self'] = "/boat/" + boatID
                boat_list.append(boat)
            self.response.headers["Content-Type"] = "application/json"
            self.response.write(json.dumps(boat_list))


    # delete a boat
    def delete(self, id=None):

        if id:
            # look up slip with given id
            b = Boat.get_by_id(int(id))

            if b is None:
                self.response.set_status(404)
                self.response.write("Boat with given id could not be found")

            else:
                # Boat at sea. Just delete boat:
                if (b.at_sea == True):
                    b.key.delete()
                    self.response.set_status(200)
                    self.response.write("Boat with given id was removed successfully")

                # boat is docked. Remove reference to boat first:
                else:
                    # query for slip that has this boat attached
                    q = Slip.query().filter(Slip.current_boat == b.id)
                    slips = q.fetch()
                    

                    # 'undock' boat from slip(s) before remove:
                    for slip in slips:
                        slip.current_boat = None
                        slip.arrival_date = None
                        slip.put()

                    # finally delete boat:
                    b.key.delete()
                    self.response.set_status(200)
                    self.response.write("Boat with given id was removed successfully")

        # no id supplied
        else:
            self.response.set_status(404)
            self.response.write("You must supply an id for the boat to be removed")


    # Modify a boat
    def patch(self, id=None):
        if id:
            # look up boat with given id
            b = Boat.get_by_id(int(id))
            if (b != None):

                # used for docking
                slipNum = 0     # start with 0

                # get current date:
                now = datetime.datetime.now().date()

                # get body data:
                boat_data = json.loads(self.request.body)

                # check for provided date:
                if boat_data.has_key("date"):
                    date = boat_data['date']
                else:
                    date = str(now)

                status = True   # default value (for scope reasons)
                # check for provided boat status:
                if boat_data.has_key("at_sea"):
                    statusStr = boat_data['at_sea']
                    status = statusStr.lower() in ("yes", "true", "t", "1")
                else:
                    statusStr = b.at_sea #previus value
                    status = statusStr.lower() in ("yes", "true", "t", "1")


                # UN-dock boat:
                if status:
                    # query for any slips that have this boat docked (ALL in case of error)
                    q = Slip.query().filter(Slip.current_boat == b.id)
                    slips = q.fetch()

                    # 'undock' boat from slip(s):
                    for slip in slips:
                        slip.current_boat = None
                        slip.arrival_date = None
                        slip.put()

                    # put boat out to sea:
                    b.at_sea = True
                    b.put()
                    self.response.set_status(200)
                    self.response.write("Boat successfully undocked!")

                # DOCK the boat:
                else:

                    if not b.at_sea:
                        self.response.set_status(200)
                        self.response.write("Boat was already docked")

                    else:
                        # check for provided slip number:
                        foundSlip = False       # true until proven false
                        if boat_data.has_key("number"):
                            num = int(boat_data['number'])
                            q = Slip.query().filter(Slip.number == num)
                            amount = q.count()
                            if amount == 1:
                                slips = q.fetch()
                                for slip in slips:
                                    slip.current_boat = b.id
                                    slip.arrival_date = date
                                    slipNum = slip.number
                                    b.at_sea = False
                                    b.put()
                                    slip.put()
                                    foundSlip = True

                        # no providede slip number, will find an open slip for you:
                        else:
                            # query all slips, find one without a boat:
                            q = Slip.query()
                            allSlips = q.order(Slip.number)
                            for slip in allSlips.fetch():
                                if (slip.current_boat is None):
                                    slip.current_boat = b.id
                                    slip.arrival_date = date
                                    slipNum = slip.number
                                    b.at_sea = False
                                    b.put()
                                    slip.put()
                                    foundSlip = True
                                    break

                        if foundSlip == False:
                            self.response.set_status(403)
                            self.response.write("There was no slip available for dock!")
                        else:
                            self.response.set_status(200)
                            self.response.write("boat was docked successfully at slip number: " + str(slipNum))

            # boat with given id does not exist:
            else:
                self.response.set_status(404)
                self.response.write("The provided boat id could not be found")

        # no id provided in URL:
        else:
            self.response.set_status(404)
            self.response.write("You must provide a boat with an id")










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
            idInt = int(id)
            s = Slip.get_by_id(idInt)
            if (s != None):
                s_d = s.to_dict()
                s_d['self'] = "/slip/" + id

                if (s.current_boat != None):
                    s_d['current_boat_link'] = "/boat/" + s.current_boat

                self.response.headers["Content-Type"] = "application/json"
                self.response.write(json.dumps(s_d))

            else:
                self.response.set_status(404)
                self.response.write("The slip with the given id could not be found")

        # display ALL slips:
        else:
            # query all slips
            q = Slip.query()
            allSlips = q.order(Slip.number)

            # put all slips in a list for nice printing:
            slip_list = []
            for slip in allSlips:
                slipID = slip.id
                slip_d = slip.to_dict()
                slip_d['self'] = "/slip/" + slipID
                if (slip.current_boat != None):
                    slip_d['current_boat_link'] = "/boat/" + slip.current_boat
                slip_list.append(slip_d)
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
                # remove boat from slip it's docked at
                if (s.current_boat != None):
                    bID = int(s.current_boat)
                    b = Boat.get_by_id(bID)

                    b.at_sea = True
                    b.put()

                    s.key.delete()
                    self.response.set_status(200)
                    self.response.write("Slip with given id was removed successfully")

                else:
                    self.response.write("No boat attached!")


        # no id supplied
        else:
            self.response.set_status(404)
            self.response.write("You must supply an id for the slip to be removed")


    # Modify a slip
    def patch(self, id=None):
        if id:
                # look up slip with given id
                s = Slip.get_by_id(int(id))

                # TODO don't actually do this, debug
                newNumber = s.number + 10
                s.number = newNumber
                s.put()

                self.response.set_status(200)
                self.response.write("I've updated your slip!")

        else:
            self.response.set_status(404)
            self.response.write("You must provide a slip with an id")









# +--------------------------------------+
# |          Main Page (Home)            |
# +--------------------------------------+

class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write(  'CS 496-400, Spring 2018: RESTful implementation\n'
                            + '\n'
                            + 'Site usage:\n'
                            + 'GET      "/"                 - Home Directory (here)\n'
                            + 'GET      "/boat"             - view all boats\n'
                            + 'GET      "/boat/:boat_id"    - view a specific boat\n'
                            + 'GET      "/slip"             - view all slips\n'
                            + 'GET      "/slip/:slip_id"    - view a specific slip\n'
                            + '\n'
                            + 'POST     "/boat/"            - Create a new boat with given name, type, and length (all required)\n'
                            + 'POST     "/slip/"            - Create a new slip\n'
                            + 'DELETE   "/boat/:boat_id"    - delete a specific boat\n'
                            + 'DELETE   "/slip/:slip_id"    - delete a specific slip\n'
                            + 'PATCH    "/boat/:boat_id"    - dock/undock a specific boat (docking done manually or automatically)\n'
                        )









# +--------------------------------------+
# |              Create App              |
# +--------------------------------------+

allowed_methods = webapp2.WSGIApplication.allowed_methods
new_allowed_methods = allowed_methods.union(('PATCH',))
webapp2.WSGIApplication.allowed_methods = new_allowed_methods
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/boat', BoatHandler),
    ('/boat/(.*)', BoatHandler),
    ('/slip', SlipHandler),
    ('/slip/(.*)', SlipHandler)
], debug=True)
