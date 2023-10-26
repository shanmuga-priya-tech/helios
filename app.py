from flask import Flask, request, jsonify
import pymongo
import json
from bson import ObjectId
import time

# connection_client
client = pymongo.MongoClient(
        "")
# database
backend_db = client['Hotel_partner_DB']
# collections
users = backend_db['Users']
hotels = backend_db['Hotels']
tickets = backend_db['Tickets']
ticket_messages = backend_db['Ticket_messages']

app = Flask(__name__)

def user_addition_input_validator(input):        
    user_name = input.get("user_name")    
    if user_name == None or type(user_name) != str or len(user_name)<3:
        return "Invalid username"
    
    user_email = input.get("user_email")
    if user_email == None or type(user_email) != str:
        # TODO: email regex validation
        return "Invalid email"
    
    user_password = input.get("user_password")
    if user_password == None or type(user_password) != str:
        # TODO: password strength validation
        return "Invalid password"
    
    return ""

# Add partner (user)
@app.route("/api/v1/users/add", methods=["POST"])
def add_user():
    try:
        input = request.json
        validator_result = user_addition_input_validator(input)
        if validator_result != "":
            return jsonify({"message": validator_result}), 400

        redundancy_result = users.find_one({"user_email": input.get("user_email")})
        
        if redundancy_result != None:        
            return jsonify({"message":"Email has been used already. Please try again with different email"}), 400
            
        result = users.insert_one(input)
        # TODO: Send verification mail
        return jsonify({"message": "Successfully inserted", "userId": str(result.inserted_id)}), 200
    except Exception as e:
        print(e)
        return jsonify({"message": "Internal server error"}), 500
    
def hotel_creation_input_validator(input):        
    hotel_name = input.get("hotel_name")    
    if hotel_name == None or not isinstance(hotel_name, str) or len(hotel_name)<2:
        return "Invalid hotel name"
    
    address = input.get("address")
    if isinstance(address, dict):    
        address1 = address.get("address1", None)
        if address1 == None or not isinstance(address1, str) or len(address1)<5:            
            return "Invalid address1 in address"

        address2 = address.get("address2", None)
        if address2 == None or not isinstance(address2, str) or len(address2)<5:
            return "Invalid address2 in address"
    
        landmark = address.get("landmark", None)
        if landmark == None or not isinstance(landmark, str) or len(landmark)<5:
            return "Invalid landmark in address"
        
        district = address.get("district", None)
        if district == None or not isinstance(district, str) or district == "":
            # TODO: District value validation against available districts list
            return "Invalid district in address"
        
        pincode = address.get("pincode", None)
        if pincode == None or not isinstance(pincode, str) or len(pincode)!=6:
            return "Invalid pincode in address"
        
        state = address.get("state", None)
        if state == None or not isinstance(state, str) or len(state)=="":
            # TODO: State value validation against available states list
            return "Invalid state in address"
        
        # TOOD: enabling lat_long validation
        lat_long = address.get("lat_long", None)
        if lat_long == None or not isinstance(lat_long, list) or len(lat_long)!=2:
            # TODO: lat_long values reverse validation 
            return "Invalid lat_long in address"
    else:
        return "Invalid address"
    
    contact_info = input.get("contact_info")
    if isinstance(contact_info, dict):
        admin = contact_info.get("admin", None)
        if admin == None or not isinstance(admin, int) or len(str(admin))!=10:
            return "Invalid admin contact number"
        
        reception = contact_info.get("reception", None)
        if reception == None or not isinstance(reception, int) or len(str(reception))!=10:
            return "Invalid reception contact number"
    else:
        return "Invalid Contact info"
    
    user_id = input.get("user_id")
    if user_id == None or not isinstance(user_id, str) or len(user_id)=="":
        return "Invalid user_id"
    return ""    
    
# Create hotel
@app.route("/api/v1/hotels/add", methods=["POST"])
def create_hotel():
    try:
        input = request.json
        validator_result = hotel_creation_input_validator(input)
        if validator_result != "":
            return jsonify({"message": validator_result}), 400                
        result = hotels.insert_one(input)
        return jsonify({"message": "Hotel created successfully", "hotel_id": str(result.inserted_id)}), 200
    except Exception as e:
        print(e)

@app.route("/api/v1/users/", methods=["POST"])
def getAllUsers():
    try:
        input = request.json

        page_no = input.get("pageNo", 1)
        items_per_page = input.get("itemsPerPage", 10)
        search_text = input.get("searchText", "")
        sort_field = input.get("sortField", "userName")
        sort_direction = input.get("sortDirection", 1)

        # dynamic search filter
        search_condition = {}
        if search_text!="":
            # {$or:[{userName: {$regex: 'an', $options: 'i'}}, {userEmail: {$regex: 'an', $options: 'i'}}]}
            search_condition['$or'] = []
            # search in userName
            search_condition['$or'].append({"userName": {"$regex": search_text, "$options": 'i'}})
            # search in useremail
            search_condition['$or'].append({"userEmail": {"$regex": search_text, "$options": 'i'}})        

        users_data = list(users.find(search_condition).sort(sort_field, sort_direction).skip((page_no - 1)*items_per_page).limit(items_per_page))
        return jsonify({"data": json.loads(json.dumps(users_data, default=str))}), 200
    except Exception as e:
        print(e)
        return jsonify({"message": "Internal server error"}), 500
    
@app.route("/api/v1/users/<userId>", methods=["GET"])
def getUserById(userId):
    try:
        user_data = users.find_one({"_id": ObjectId(userId)})
        return jsonify({"data": json.loads(json.dumps(user_data, default=str))}), 200
    except Exception as e:
        print(e)
        return jsonify({"message": "Internal server error"}), 500
    
def ticket_creation_input_validator(input):
    user_id = input.get("user_id")    
    if user_id == None or type(user_id) != str:
        return "Invalid user_id"     
    
    return ""

@app.route("/api/v1/ticket/create", methods=["POST"])
def create_ticket():
    try:
        input = request.json        

        validator_result = ticket_creation_input_validator(input)
        if validator_result != "":
            return jsonify({"message": validator_result}), 400
        
        created_timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")
        status = 'initiated'
        
        new_ticket = tickets.insert_one({
            "user_id": input['user_id'],
            "created_timestamp": created_timestamp,
            "status": status
        })
        
        ticket_id = str(new_ticket.inserted_id)

        ticket_messages.insert_one(
            {
                "message_content": f"A ticket has been created for you with the following ticket_id: {ticket_id}. Please enter your query",
                "ticket_id": ticket_id,
                "created_timestamp": created_timestamp,           
                "user_id": None,     
                "user_role": "SUPPORT_TEAM_BOT",     
            }
        )

        return jsonify({"ticket_id": ticket_id}), 200

    except Exception as e:
        print(e)
        return jsonify({"message": "Internal server error"}), 500
    
def ticket_message_input_validator(input):
    message_content = input.get("message_content")    
    if message_content == None or type(message_content) != str or message_content=="":
        return "Invalid message_content" 

    ticket_id = input.get("ticket_id")    
    if ticket_id == None or type(ticket_id) != str or ticket_id=="":
        return "Invalid ticket_id"     
    
    user_id = input.get("user_id")    
    if user_id == None or type(user_id) != str or user_id=="":
        return "Invalid user_id"
    
    user_role = input.get("user_role")    
    if user_role == None or type(user_role) != str or user_role=="":
        return "Invalid user_role"
    
    return ""

@app.route("/api/v1/ticket/message/send", methods=["POST"])
def send_ticket_message():
    try:
        input = request.json        

        validator_result = ticket_message_input_validator(input)
        if validator_result != "":
            return jsonify({"message": validator_result}), 400        

        ticket=tickets.find_one({"ticket_id": input['ticket_id']})
        if ticket != None and ticket.get('status') == 'initiated':
            tickets.update_one({"ticket_id": input['ticket_id']}, {"$set": {"status": "open"}})

        created_timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")
        input['created_timestamp'] = created_timestamp
        
        ticket_messages.insert_one(input)

        return jsonify({"message": "sent successfully"}), 200

    except Exception as e:
        print(e)
        return jsonify({"message": "Internal server error"}), 500

@app.route("/api/v1/ticket/message/all/<ticket_id>", methods=["GET"])
def get_all_messages_by_ticket_id(ticket_id):     
    try:        
        if ticket_id == None or type(ticket_id) != str:
            return jsonify({"message": "Invalid ticket_id"}), 500     
        messages = list(ticket_messages.find({"ticket_id": ticket_id}))
        return jsonify({"data": json.loads(json.dumps(messages, default=str))}), 200
    except Exception as e:
        print(e)
        return jsonify({"message": "Internal server error"}), 500


def room_availability_validator(input):
        room_availability=input.get("room_availability")
        if room_availability == None or type(room_availability)!= int:
            return "Invalid room_availability"
        return ""

@app.route("/api/v1/hotels/update/<hotel_id>", methods=["POST"])
def update_hotel(hotel_id):
    try:
        input = request.json
        hotel_id = ObjectId(hotel_id)
        validation=room_availability_validator(input)
        if validation !="":
            return jsonify({"message": validation}), 400
           
        result =hotels.update_one({"_id": hotel_id}, {"$set": {"room_availability": input.get("room_availability")}})
        return jsonify({"message": "Hotel updated successfully"}), 200
            
    except Exception as e:
        print(e)
        return jsonify({"message": "Internal server error"}), 500

app.run(port=4650, debug=True)
