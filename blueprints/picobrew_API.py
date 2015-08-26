from flask import *
from webargs import Arg
from webargs.flaskparser import use_kwargs, FlaskParser
from frontend import get_recipes
import json, os, uuid, re

SESSION_PATH = "sessions"
SYSTEM_USER = "00000000000000000000000000000000"
arg_parser = FlaskParser()

picobrew_api = Blueprint("picobrew_api", __name__)

# Unfortunately the PicoBrew API ony consist of three overloaded routes.

# ----------- RECIPES -----------
@picobrew_api.route("/API/SyncUser")
@picobrew_api.route("/API/SyncUSer")
@use_kwargs({"user": Arg(str), "machine": Arg(str)})
def parse_recipe_request(user, machine):

    if user == SYSTEM_USER:
        return get_cleaning_recipes()
    else:
        if machine:
            return get_picobrew_recipes()

    # default response
    return "\r\n##"

@picobrew_api.route("/API/checksync")
@use_kwargs({"user": Arg(str)})
def check_sync(user):
    return "\r\n#!#"


def get_cleaning_recipes():

    return "#Cleaning v1/7f489e3740f848519558c41a036fe2cb/Heat Water,152,0,0,0/Clean Mash,152,15,1,5/Heat to Temp,152,0,0,0/Adjunct,152,3,2,1/Adjunct,152,2,3,1/Adjunct,152,2,4,1/Adjunct,152,2,5,1/Heat to Temp,207,0,0,0/Clean Mash,207,10,1,0/Clean Mash,207,2,1,0/Clean Adjunct,207,2,2,0/Chill,120,10,0,2/|Rinse v3/0160275741134b148eff90acdd5e462f/Rinse,0,2,0,5/|#"


def get_picobrew_recipes():

    all_recipes = get_recipes()
    filtered_recipes = filter(lambda recipe: recipe.steps, all_recipes)
    recipes = map(lambda recipe: recipe.serialize(), filtered_recipes)
    recipes = "|".join(recipes)

    return "#{0}|#".format(recipes)

# ----------- SESSION LOGGING -----------
@picobrew_api.route("/API/LogSession")
@picobrew_api.route("/API/logSession")
@picobrew_api.route("/API/logsession")
@use_kwargs({"session": Arg(str), "recipe": Arg(str)})
def parse_session_request(session, recipe):

    if recipe:
        args = arg_parser.parse({"user": Arg(str), "firm": Arg(str), "machine": Arg(str)})
        return create_new_session(recipe, args)

    if session:
        args = arg_parser.parse({"data": Arg(str), "state": Arg(str), "step": Arg(str), "code": Arg(int)})
        return log_to_session(session, args)

    # default fallthrough
    abort()


def create_new_session(recipe_id, args):

    session_id = uuid.uuid4().hex[:32]
    session_file = "{0}.json".format(session_id)

    session_data = {
        "recipe_id" : recipe_id,
        "session_id" : session_id,
        "steps" : []
    }

    try:
        with open(os.path.join(SESSION_PATH, session_file), 'w') as out_file:
            json.dump(session_data, out_file)

    except IOError:
        return "##"

    return "#{0}#".format(session_id)



def log_to_session(session_id, args):

    session_file = "{0}.json".format(session_id)
    data = args["data"]
    code = args["code"]

    try:
        if not os.path.exists(SESSION_PATH):
            os.mkdir(SESSION_PATH)

        with open(os.path.join(SESSION_PATH, session_file), 'r') as in_file:
            session = json.load(in_file)

            if code == 1:
                session_step = {
                    "name": data,
                    "temperatures": []
                }
                session["steps"].append(session_step)

            elif code == 2:

                temps = re.findall(r"/([0-9]+)", data)

                session_step = session["steps"][-1]
                session_step["temperatures"].append(temps)

            elif code == 3:
                session["steps"].append({"name": "Session Aborted"})

        with open(os.path.join(SESSION_PATH, session_file), 'w') as out_file:
            json.dump(session, out_file)

    except IOError:
        pass

    return ""

# ----------- SESSION RECOVERY -----------
@picobrew_api.route("/API/recoversession")
@use_kwargs({"session": Arg(str), "code": Arg(int)})
def parse_session_recovery_request(session, code):

    if code == 0:
        raise NotImplementedError()
        # return recipe

    elif code == 1:
        raise NotImplementedError()
        # return machine params

    # default fallthrough
    abort()
