# coding:utf-8
import requests
from requests.auth import HTTPBasicAuth
import json
import pickle
from consts import ZENDESK_ENDPOINT, ZENDESK_USER, ZENDESK_PASS, ZENDESK_ORG, GOOGLE_APIKEY

# init
zendesk_endpoint = ZENDESK_ENDPOINT
zendesk_user = ZENDESK_USER
zendesk_password = ZENDESK_PASS
zendesk_organization_id = ZENDESK_ORG
google_apikey = GOOGLE_APIKEY

# zendesk utils
def request_zendesk(url):
    user = zendesk_user
    password = zendesk_password
    headers = {"content-type": "application/json"}
    r = requests.get(url, headers=headers, auth=HTTPBasicAuth(user, password))
    return r

# requests by org
def get_request_ids():
    org_id = zendesk_organization_id
    requests_url = zendesk_endpoint + "/api/v2/organizations/" + org_id + "/requests.json"
    r = request_zendesk(requests_url)
    data = r.json()
    requests = data["requests"]
    
    request_ids = []
    
    for i in range(0,len(requests)):
        request_ids.append(str(requests[i]['id']))

    print("first page retrieved.")
    while(data["next_page"] != None): # TODO: pagination process enhancements
        print("next page detected.")
        requests_url = data["next_page"]
        r = request_zendesk(requests_url)
        data = r.json()
        requests = data["requests"]

        for i in range(0,len(requests)):
            request_ids.append(str(requests[i]['id']))

    return request_ids

# request details
def get_request_details(request_id):
    request_details_url = zendesk_endpoint + "/api/v2/requests/" + request_id + ".json"
    r = request_zendesk(request_details_url)
    request = r.json()
    return request

# comments in requests
def get_requests_comments(request_id):
    comments_in_requests_url = zendesk_endpoint + "/api/v2/requests/" + request_id +"/comments.json"
    r = request_zendesk(comments_in_requests_url)
    comments = r.json()
    return comments

# concatenate comments to post somewhere else e.g. redmine
def concatenate_comments(comments):
    # extract request id list
    original_text = ""
    for i in range(0,len(comments['comments'])):
        original_text = original_text + comments['comments'][i]['plain_body'] + "\n" + "----------" + "\n"
    return original_text

# google translation
def google_translate(original_text):
    google_translate_url = "https://translation.googleapis.com/language/translate/v2?key=" + google_apikey

    payload = {
        "q": original_text,
        "source": "en",
        "target": "ja",
        "format": "text"
    }
    json_data = json.dumps(payload).encode("utf-8")
    headers = {"content-type": "application/json"}
    r = requests.post(google_translate_url, headers=headers, data=json_data)
    translated = r.json()
    return translated

# get requests by org/related comments/translations
def save_comments(zendesk_history, request_id):
    request = get_request_details(request_id)
    comments = get_requests_comments(request_id)
    original_text = concatenate_comments(comments)    
    zendesk_history[request_id] = request["request"]
    zendesk_history[request_id]["original_text"] = original_text

    return zendesk_history

def translate_comments(zendesk_history, request_id):
    original_text = zendesk_history[request_id]["original_text"]
    translated = google_translate(original_text)
    zendesk_history[request_id]["translated_text"] = translated["data"]["translations"][0]["translatedText"]

    return zendesk_history

# pickle the history json object
def save_object(object_to_save, filename):
    file = open(filename, 'wb')
    pickle.dump(object_to_save, file)
    file.close()

# read the history json object
def load_object(filename):
    file = open(filename, 'rb')
    loaded_object = pickle.load(file)
    return loaded_object

if __name__ == '__main__':
    print("...Get all request ids...")
# for testing
#    request_ids = ['10428', '11367']

    request_ids = get_request_ids()

    print("...Retrieved request ids...")
    print(request_ids)

    zendesk_history = {}

    print("...Start to retrieve all requests/comments...")
    for idx, request_id in enumerate(request_ids):
        print(str(idx) + "/" + str(len(request_ids)) + ": {:.2%}".format(idx/len(request_ids)))
        zendesk_history = save_comments(zendesk_history,  request_id)

    print("...Save to a file as pickle.dump...")
    save_object(zendesk_history, "zendesk_history.pickle")

    print("...Translate all requests/comments...")
    for idx, request_id in enumerate(request_ids):
        print(str(idx) + "/" + str(len(request_ids)) + ": {:.2%}".format(idx/len(request_ids)))
        zendesk_history = translate_comments(zendesk_history,  request_id)

    print("...Save to a file as pickle.dump...")
    save_object(zendesk_history, "zendesk_history.pickle")

    print("...Done...")

    print(load_object("zendesk_history.pickle"))


