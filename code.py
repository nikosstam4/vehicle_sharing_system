import requests
import geopy.distance
import gmaps
from datetime import datetime
import pandas as pd
import random
api_file = open("api.txt", "r")
api_key = api_file.read()
api_file.close()

class Admin():
    r_trips = []
    s_trips = []
    final_s_trips = []
    final_r_trips = []
    reachable_scoots = []
    reachable_stations = []
    candidate_trips = []
    trips_in_progress = {}
    best_system_trip = None
    closest_trip = None
    fastest_trip = None
    awaiting_offers = {}
    suggested_trips = []
    tolerance = 15
    
    def add_user(user):
        Admin.awaiting_offers[user] = ""
        Admin.trips_in_progress[user] = ""

    def clear_lists(self):   
        del Request.user_requests[0]
        self.final_s_trips.clear() 
        self.reachable_scoots.clear()
        self.s_trips.clear()
        self.reachable_stations.clear() 
        self.r_trips.clear() 
        self.final_r_trips.clear() 
        self.candidate_trips.clear() 
        self.fastest_trip = None
        self.best_system_trip = None
     
    def find_reachable_scoots(self): 
        x = Request.user_requests[0]
        user_x = x.longitude 
        user_y = x.latitude
        coords_1 = (user_x, user_y)
        for index, item in enumerate(E_scooter.available_scoots):
            # early check if distance from vehicle is over 600 meters (in radius)
            coords_2 = (E_scooter.available_scoots[index].longitude, E_scooter.available_scoots[index].latitude)
            if geopy.distance.geodesic(coords_1, coords_2).km <= 0.6:  
                url = "https://maps.googleapis.com/maps/api/distancematrix/json?units=metric&"
                r = requests.get(url + "origins=" + user_x + "," + user_y 
                                 + "&destinations=" + E_scooter.available_scoots[index].longitude + "," + E_scooter.available_scoots[index].latitude
                                 + "&avoid=tolls|highways|ferries"
                                 + "&mode=walking" # Walking
                                 + "&key=" + api_key
                                ) 
                # return time and distance as text
                distance = r.json()["rows"][0]["elements"][0]["distance"]["value"]  
                # 4km average walking speed
                time = (distance*0.015)  
                # check if distance from vehicle is tolerable 15 minutes
                if time <= self.tolerance:
                    self.reachable_scoots.insert(0,item)
                    self.reachable_scoots[0].w_time = time

        if self.reachable_scoots == []:
            print("There are no scoots nearby!")
            self.clear_lists()

                    
    def user_destination(self): 
        x = Request.user_requests[0]
        user_x = x.dest_long 
        user_y = x.dest_lat
        coords_1 = (user_x, user_y)

        # (-scoot-,-destination-,-walking time-)
        for index, item in enumerate(self.reachable_scoots):
            a = (self.reachable_scoots[index], coords_1, self.reachable_scoots[index].w_time)
            self.r_trips.append(a)
            
        x = self.r_trips
        for trip in x:
            start = trip[0]
            finish = trip[1]
            url = "https://maps.googleapis.com/maps/api/distancematrix/json?units=metric&"
            r = requests.get(url + "origins=" + start.longitude + "," + start.latitude
                             + "&destinations=" + finish[0] + "," + finish[1]
                             + "&avoid=tolls|highways|ferries"
                             + "&mode=driving" #---not Walking
                             + "&key=" + api_key
                            ) 
            # return distance as text
            distance = r.json()["rows"][0]["elements"][0]["distance"]["value"]  
            
            # check if battery is enough for the trip, 1 percent of battery equals 200 meters, 10 percent margine
            # (-scoot-,-destination-,-walking time-,-distance-)
            if trip[0].battery * 200 > distance + 2000:
                y = (trip[0], trip[1], trip[2],distance)
                self.final_r_trips.append(y)  

            
    def find_reachable_stations(self): 
        x = Request.user_requests[0]
        user_x = x.dest_long 
        user_y = x.dest_lat
        coords_1 = (user_x, user_y)

        for index, item in enumerate(Station.stations):
            # early check if distance from station is over 600 meters in radius
            coords_2 = (Station.stations[index].longitude, Station.stations[index].latitude)
            if geopy.distance.geodesic(coords_1, coords_2).km <= 0.6:       
                url = "https://maps.googleapis.com/maps/api/distancematrix/json?units=metric&"
                r = requests.get(url + "origins=" + user_x + "," + user_y 
                                 + "&destinations=" + Station.stations[index].longitude + "," + Station.stations[index].latitude
                                 + "&avoid=tolls|highways|ferries"
                                 + "&mode=walking" # Walking
                                 + "&key=" + api_key
                                ) 
                # return time and distance as text
                distance = r.json()["rows"][0]["elements"][0]["distance"]["value"]  
                time = (distance*0.015)  

                # check if distance from vehicle is tolerable
                if time <= self.tolerance:
                    self.reachable_stations.insert(0,item)
                    self.reachable_stations[0].w_time = time
                    
    def is_trip_tolerable(self):
        for index1, item1 in enumerate(self.reachable_stations):
            for index2, item2 in enumerate(self.reachable_scoots):
                self.total_time = self.reachable_stations[index1].w_time + self.reachable_scoots[index2].w_time
                if self.total_time <= self.tolerance:
                    a = (self.reachable_scoots[index2], self.reachable_stations[index1], self.total_time)
                    self.s_trips.append(a)

    def enough_battery_for_trips(self):
        x = self.s_trips
        for trip in x:
            start = trip[0]
            finish = trip[1]
            url = "https://maps.googleapis.com/maps/api/distancematrix/json?units=metric&"
            r = requests.get(url + "origins=" + trip[0].longitude + "," + trip[0].latitude
                             + "&destinations=" + trip[1].longitude + "," + trip[1].latitude
                             + "&avoid=tolls|highways|ferries"
                             + "&mode=driving" # not Walking 
                             + "&key=" + api_key
                            ) 
            # return time and distance as text
            distance = r.json()["rows"][0]["elements"][0]["distance"]["value"]  
            # check if battery is enough for the trip, 1 percent of battery equals 200 meters, 10 percent margine
            # (-scoot-,-station-,-walking time-,-distance-)
            if trip[0].battery * 200 > distance + 2000:
                y = (trip[0], trip[1], trip[2],distance)
                self.final_s_trips.append(y)
 
    
    def find_trip_points(self):
        x = Request.user_requests[0]
        user_x = x.dest_long 
        user_y = x.dest_lat
        coords = (user_x, user_y)
        
        x= self.final_r_trips
        self.least_walking = 15 
        # find the remaining battery of the least walking value
        for trip in x:
            if trip[2] < self.least_walking:
                self.least_walking = trip[2]
                self.closest_trip = trip
            # equal walking time
            elif trip[2] == self.least_walking and (trip[0].battery - trip[3]/200) > (self.closest_trip[0].battery - self.closest_trip[3]/200):
                self.least_walking = trip[2]
                self.closest_trip = trip

        self.rmn_btr_closest_sc = self.closest_trip[0].battery - self.closest_trip[3]/200
        # calculating the cost of all trips based on the closest trip distance
        cost = self.closest_trip[3]*0.001

        for trip in x:
            # calculating the remaining battery 
            remaining_battery = trip[0].battery - trip[3]/200
            points = round(remaining_battery - self.rmn_btr_closest_sc)
            # max points are 50
            if points > 50:
                points = 50
            if points >= 0:
                y = (trip[0],trip[1],trip[2],trip[3],cost, points)
                self.candidate_trips.append(y)

        x = self.final_s_trips
        for trip in x:
            # calculating the remaining battery 
            remaining_battery = trip[0].battery - trip[3]/200
            points = round(100 - remaining_battery)
            occ_points = round((trip[1].dsrd_occupancy-trip[1].crnt_occupancy)/trip[1].capacity*100)
            if occ_points > 0:
                points = points + occ_points
                if points>100:
                    points = 100
                y = (trip[0],trip[1],trip[2],trip[3],cost, points, coords)
                self.candidate_trips.append(y)
            # we can surpass the limit if vehicle has extremely low battery
            elif occ_points <= 0 and remaining_battery <= 25:
                if points>100:
                    points = 100
                y = (trip[0],trip[1],trip[2],trip[3],cost, points, coords)
                self.candidate_trips.append(y)


    def suggestions(self):   
        x = self.candidate_trips
        if len(x) == 1:    
            self.suggested_trips.append(x[0])
        elif len(x)>= 2:    
            # find the best trip
            best_score = 0 
            for trip in x:
                if trip[5] > best_score:
                    best_score = trip[5]
                    self.best_system_trip = (trip)
            self.suggested_trips.append(self.best_system_trip)
            self.candidate_trips.remove(self.best_system_trip)  

            x = self.candidate_trips
            for trip in x:
                if trip[2] > self.best_system_trip[2]:
                    self.candidate_trips.remove(trip)
                    
            if not self.candidate_trips :
                return

            # find the fastest trip
            walking_time = 15 
            for trip in x:
                if trip[2] < walking_time:
                    walking_time = trip[2]
                    self.fastest_system_trip = (trip)
            self.suggested_trips.append(self.fastest_system_trip)
            self.candidate_trips.remove(self.fastest_system_trip)

            if not self.candidate_trips :
                return

            x = self.candidate_trips
            for trip in x:
                if trip[2] > self.best_system_trip[2]:
                    self.candidate_trips.remove(trip)

            if not self.candidate_trips :
                return

            x = self.candidate_trips
            walking_time = 15
            flag = 0
            for trip in x:
                if (trip[5] < 100) and (trip[5] >= 75) and (trip[2] < walking_time):
                    self.selected_trip = trip
                    walking_time = trip[2]
                    flag = 1
            if flag == 1:
                self.suggested_trips.append(self.selected_trip)
                self.candidate_trips.remove(self.selected_trip) # extra, doesnt matter
                x = self.candidate_trips
                for trip in x:
                    if trip[2] > self.selected_trip[2]:
                        self.candidate_trips.remove(trip)

            if not self.candidate_trips :
                return

            x = self.candidate_trips
            flag = 0
            for trip in x:
                if (trip[5] < 75) and (trip[5] >= 50) and (trip[2] < walking_time):
                    self.selected_trip = trip
                    walking_time = trip[2]
                    flag = 1

            if flag == 1:
                self.suggested_trips.append(self.selected_trip)
                self.candidate_trips.remove(self.selected_trip)
                x = self.candidate_trips
                for trip in x:
                    if trip[2] > self.selected_trip[2]:
                        self.candidate_trips.remove(trip)

            if not self.candidate_trips :
                return

            x = self.candidate_trips
            flag = 0
            for trip in x:
                if (trip[5] < 50) and (trip[5] >= 30) and (trip[2] < walking_time):
                    self.selected_trip = trip
                    walking_time = trip[2]
                    flag = 1

            if flag == 1:
                self.suggested_trips.append(self.selected_trip)
                self.candidate_trips.remove(self.selected_trip)
                x = self.candidate_trips
                for trip in x:
                    if trip[2] > self.selected_trip[2]:
                        self.candidate_trips.remove(trip)
                        
            if not self.candidate_trips :
                return
            
            x = self.candidate_trips
            flag = 0
            for trip in x:
                if (trip[5] < 30) and (trip[5] >= 10) and (trip[2] < walking_time):
                    self.selected_trip = trip
                    walking_time = trip[2]
                    flag = 1
            
            if flag == 1:
                self.suggested_trips.append(self.selected_trip)
                self.candidate_trips.remove(self.selected_trip)

        else:           
            print("zero possible trips")  
            del Request.user_requests[0]

        #check if fastest trip is giving more points than other trips with more time 
        x = self.suggested_trips
        for trip in x:
            if self.fastest_system_trip[5] > trip[5]:
                self.suggested_trips.remove(trip)

        x = self.suggested_trips
        for trip in x:
            trip[0].vech_not_available() # set vechicle unavailable for possible use  

        #order the suggested trips
        x = self.suggested_trips
        if len(x)>2:
            x.sort(key=lambda x: x[5], reverse=True)

        x = self.suggested_trips
        for trip in x:    
            Request.user_requests[0].user.awaiting_offers.append(trip)

        # !clear multiple lists and variables!
        self.clear_lists()
          
    def present_trip(self,trip):

        t = trip
        gmaps.configure(api_key)
        # define scooter location and station location
        start = (float(t[0].longitude),float(t[0].latitude))
        if hasattr(t[1], 'longitude'):
            end = (float(t[1].longitude),float(t[1].latitude))
        else: 
            end = (float(t[1][0]),float(t[1][1]))
        # create the map
        fig = gmaps.figure()
        # create the layer
        layer = gmaps.directions.Directions(start, end, travel_mode='DRIVING')
        # add the layer
        fig.add_layer(layer)
        # add user mark
        x1 = float(t[1][0])
        y1 = float(t[1][1])
        # add destination mark
        if hasattr(t[1], 'longitude'):
            x2 = float(t[5][0])
            y2 = float(t[5][0])
        else: 
            x2 = float(t[1][0])
            y2 = float(t[1][0])        

        orig = (x1,y1)
        dest = (x2,y2)

        drawing1 = gmaps.drawing_layer(features=[
             gmaps.Marker(orig, label='U')])
        drawing2 = gmaps.drawing_layer(features=[
             gmaps.Marker(dest, label='D')])
        fig.add_layer(drawing1)
        fig.add_layer(drawing2)
        print("walking time: ",t[2],"mins")
        display(fig)
        return fig; 

class User():
    def __init__(self, username, user_id):
        self.username = username
        self.user_id = user_id
        self.points = 0
        self.quarter_points = 0
        self.level = "iron"
        Admin.add_user(self)
    
    awaiting_offers = []

    def info(self):
        return f"{self.username} ({self.user_id})"
    
    def make_request(self, longitude, latitude, dest_long, dest_lat):
        # priority to the golden members
        if self.level == "gold":
            Request.user_requests.insert(0,Request(self, longitude, latitude, dest_long, dest_lat))
        else:
            Request.user_requests.append(Request(self, longitude, latitude, dest_long, dest_lat))    
            
    def delete_request(self):
        for y in Request.user_requests:
            if self.user_id == y.user.user_id:
                Request.user_requests.remove(y)
                
    def see_offers(self):
        x = self.awaiting_offers
        
        if len(x) >= 1: 
            print("0 : I dont want to take any trip.")
            for i in range(0,len(x)):
                print(i+1 , " : total time: ",round(x[i][2]+x[i][3]*0.004), "mins, cost: ", round(x[i][4],2), "euros ,rewarding points: " , x[i][5], ",walking time: ",round(x[i][2]), "mins") 
            
            print("Do you want to take a trip?(0",end="")
            for i in range(1, len(x)+1):
                print ("/",i,end="")
            print("): ")
            i = int(input())
            
            if i != 0:
                Admin.trips_in_progress[self] = x[i-1]
                for n in range(0,len(x)-1):
                    if n != i:
                        x[n][0].vech_available()
                #admin.present_trip(x[i-1])
                Admin.present_trip(admin,x[i-1])
                

            else:
                for n in range(0,len(x)-1):
                    x[n][0].vech_available()      
        
        else:
            print("", self.username, " there are no trip offers available")
        
        admin.awaiting_offers[self] = ''   
        self.awaiting_offers = []
   
                
    def update_level(self):
        if self.quarter_points >= 40:
            self.level = "gold"
        elif 20 <= self.quarter_points <= 40:
            self.level = "silver"
        else:
            self.level = "iron"

class Request():
    user_requests = []
    def __init__(self, user, longitude, latitude, dest_long, dest_lat):
        self.user = user
        self.longitude = longitude  
        self.latitude = latitude
        self.dest_long = dest_long
        self.dest_lat = dest_lat
        self.tolerance = 15

class E_scooter:
    scoots = []
    available_scoots = []
    def __init__(self, id, longitude, latitude, battery):
        self.id = id          
        self.longitude = longitude  
        self.latitude = latitude
        self.battery = battery
        self.availability = 1
        self.w_time = None
        self.within_station = 0

    def vech_available(self):
        if self not in self.available_scoots:
            self.availability = 1
            self.available_scoots.append(self)    
        
    def vech_not_available(self):
        if self in self.available_scoots:
            self.availability = 0
            self.available_scoots.remove(self)
    
    def get_battery(self):
        return self.battery

    def charge(self):
        self.battery = 100
        self.vech_available()

class Station:
    stations = []
    def __init__(self, id, longitude, latitude, capacity, crnt_occupancy, dsrd_occupancy):
        self.id = id          
        self.longitude = longitude  
        self.latitude = latitude
        self.capacity = capacity
        self.crnt_occupancy = crnt_occupancy
        self.dsrd_occupancy = dsrd_occupancy
        self.w_time = None
      
    def set_desired_occupancy(self, x):
        self.dsrd_occupancy = x

##----------------------------------------------------------------------------
## data creation and testing

# create stations
s1 = Station(1, "38.241808", "21.727683", 8, 4, 5)#agiosandreas
Station.stations.append(s1)
s2 = Station(2, "38.275984", "21.762461", 6, 3, 5)#neopatrwnathinwn
Station.stations.append(s2)
s3 = Station(3, "38.246185", "21.735896", 12, 8 , 10)#plateiageorgiou
Station.stations.append(s3)
s4 = Station(6, "38.257234", "21.739822", 10, 7, 7)#agiassofias
Station.stations.append(s4)
s5 = Station(8, "38.263395", "21.743971", 8, 6, 7)#aguia stadio
Station.stations.append(s5)
s6 = Station(4, "38.286390", "21.785500", 12, 8, 10)#panepisthmio
Station.stations.append(s6)
s7 = Station(9, "38.269897", "21.751720", 8, 4, 6)#aguia notara
Station.stations.append(s7)
s8 = Station(5, "38.240885", "21.735494", 10, 8, 7)#psilalwnia
Station.stations.append(s8)
s9 = Station(7, "38.233776", "21.747390", 8, 2, 7)#noskomeioagiouandrea
Station.stations.append(s9)
s10 = Station(10, "38.251688", "21.742984", 6, 4, 5)#purosvestiou
Station.stations.append(s10)
s11 = Station(10, "38.232415", "21.724936", 10, 4, 6)#notioparko
Station.stations.append(s11)

# add the scoots
e1 = E_scooter(66, "38.247435", "21.731432", random.randint(0,100))
E_scooter.scoots.append(e1)
e2 = E_scooter(63, "38.245269", "21.728631", random.randint(0,100)) 
E_scooter.scoots.append(e2)
e3 = E_scooter(64, "38.249552", "21.734121", random.randint(0,100))
E_scooter.scoots.append(e3)
e4 = E_scooter(36, "38.245935", "21.7312607", random.randint(0,100))
E_scooter.scoots.append(e4)
e5 = E_scooter(34, "38.248566", "21.738447", random.randint(0,100))
E_scooter.scoots.append(e5)
e6 = E_scooter(22, "38.242578", "21.738661", random.randint(0,100)) 
E_scooter.scoots.append(e6)
e7 = E_scooter(16, "38.243179", "21.747226", random.randint(0,100)) 
E_scooter.scoots.append(e7)
e8 = E_scooter(76, "38.229845", "21.732697", random.randint(0,100)) 
E_scooter.scoots.append(e8)
e9 = E_scooter(27, "38.241497", "21.728874", random.randint(0,100)) 
E_scooter.scoots.append(e9)
e10 = E_scooter(40, "38.267159", "21.752508", random.randint(0,100)) 
E_scooter.scoots.append(e10)
e11 = E_scooter(89, "38.264802", "21.746597", random.randint(0,100)) 
E_scooter.scoots.append(e11)
e12 = E_scooter(90, "38.260983", "21.758692", random.randint(0,100)) 
E_scooter.scoots.append(e12)
e13 = E_scooter(72, "38.272192", "21.758510", random.randint(0,100)) 
E_scooter.scoots.append(e13)
e14 = E_scooter(92, "38.266088", "21.743915", random.randint(0,100)) 
E_scooter.scoots.append(e14)
e15 = E_scooter(29, "38.242523", "21.734594", random.randint(0,100)) 
E_scooter.scoots.append(e15)
e16 = E_scooter(31, "38.245023", "21.734412", random.randint(0,100)) 
E_scooter.scoots.append(e16)
e17 = E_scooter(54, "38.256805", "21.746143", random.randint(0,100)) 
E_scooter.scoots.append(e17)
e18 = E_scooter(72, "38.255413", "21.740550", random.randint(0,100)) 
E_scooter.scoots.append(e18)
e19 = E_scooter(18, "38.256234", "21.738868", random.randint(0,100)) 
E_scooter.scoots.append(e19)
e20 = E_scooter(5, "38.270679", "21.762060", random.randint(0,100)) 
E_scooter.scoots.append(e20)         
e21 = E_scooter(39, "38.242818", "21.732697", random.randint(0,100)) 
E_scooter.scoots.append(e21)            
e22 = E_scooter(36, "38.261674", "21.747073", random.randint(0,100)) 
E_scooter.scoots.append(e22)   
e23 = E_scooter(38, "38.275580", "21.761506", random.randint(0,100)) 
E_scooter.scoots.append(e23) 
e24 = E_scooter(90, "38.288577", "21.786188", random.randint(0,100)) 
E_scooter.scoots.append(e24) 
e25 = E_scooter(44, "38.291662", "21.790781", random.randint(0,100)) 
E_scooter.scoots.append(e25) 
e26 = E_scooter(19, "38.256169", "21.745435", random.randint(0,100)) 
E_scooter.scoots.append(e26) 
e27 = E_scooter(74, "38.243429", "21.741780", random.randint(0,100)) 
E_scooter.scoots.append(e27) 
e28 = E_scooter(5, "38.240312", "21.740716", random.randint(0,100)) 
E_scooter.scoots.append(e28) 
e29 = E_scooter(6, "38.246742", "21.732771", random.randint(0,100)) 
E_scooter.scoots.append(e29) 
e30 = E_scooter(55, "38.238363", "21.736858", random.randint(0,100)) 
E_scooter.scoots.append(e30) 

admin = Admin()

# users for testing
user1 = User("nikos s",43)
user2 = User("kwstas t",56)
user3 = User("giwrgos t",34)
user4 = User("georgia g",182)
user5 = User("mantha t",112)

# example of a request
user1.make_request("38.244929", "21.734995", "38.263862", "21.752077")

#find the available scoots #auto?
for index, item in enumerate(E_scooter.scoots):
    if E_scooter.scoots[index].vech_available() == 1:
        E_scooter.available_scoots.append(item)

admin.find_reachable_scoots()
admin.user_destination()
admin.find_reachable_stations()
admin.is_trip_tolerable()
admin.enough_battery_for_trips()
admin.find_trip_points()
admin.suggestions()

# seeing offers
user1.see_offers()

##----------------------------------------------------------------------------
## get stats
## extra

import folium

def stats_analysis():
    data = []
    for c in admin.suggested_trips: 
        if hasattr(c[1], 'longitude'):
            data.append([c[0].battery, (c[0].battery-round(c[3]/200)),round(c[2]),round(c[2]+(c[3]*0.004)),1,round(c[5])])  
        else:
            data.append([c[0].battery, (c[0].battery-round(c[3]/200)), round(c[2]),round(c[2]+(c[3]*0.004)),0,round(c[5])])  

    df = pd.DataFrame(data, columns =["battery","remaining bat", "walking time","total time","station","points"]) 
    df = df.reset_index(drop=True)
    return df

stats_analysis()

map = folium.Map(location=[38,25],tiles="cartodbpositron",zoom_start=4, control_scale=True)

for x in admin.final_scores:
    v = (float(x[0].longitude),float(x[0].latitude))   
    folium.Marker(location=v,icon=folium.Icon(color='green', icon='pushpin'),popup= "id: " + str(x[0].id) +"\n Battery of the vehicle: " + str(x[0].battery)).add_to(map)

for x in admin.final_scores:
    if hasattr(x[1], 'longitude'):
        d = (float(x[1].longitude),float(x[1].latitude))   
        folium.Marker(location=d,icon=folium.Icon(color='red', icon='pushpin'),popup= "id: " + str(x[1].id )+ "\n occupancy: " + str(x[1].crnt_occupancy) + "/" + str(x[1].capacity)).add_to(map)

    else:
        d = (float(x[1][0]),float(x[1][1]))
        folium.Marker(location=d,icon=folium.Icon(color='blue', icon='pushpin'),popup = 'destination').add_to(map)

s = (float(Request.user_requests[0].longitude),float(Request.user_requests[0].latitude))
folium.Marker(location=s,popup='User starting point').add_to(map)

map.save("MAP.html")
