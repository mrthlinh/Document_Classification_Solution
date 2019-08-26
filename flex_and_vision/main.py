# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from datetime import datetime
import logging
import os
import flask
from flask import Flask, redirect, render_template, request

# from google.cloud import datastore
# from google.cloud import storage
# from google.cloud import vision

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
import json

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "My First Project-e90e6b12d97d.json"
# https://codelabs.developers.google.com/codelabs/cloud-vision-app-engine/index.html?index=..%2F..index#7

CLOUD_STORAGE_BUCKET = os.environ.get('CLOUD_STORAGE_BUCKET')


app = Flask(__name__)

import pandas as pd
import numpy as np 

labels = ['DELETION OF INTEREST', 'RETURNED CHECK', 'BILL', 'POLICY CHANGE',
       'CANCELLATION NOTICE', 'DECLARATION', 'CHANGE ENDORSEMENT',
       'NON-RENEWAL NOTICE', 'BINDER', 'REINSTATEMENT NOTICE',
       'EXPIRATION NOTICE', 'INTENT TO CANCEL NOTICE', 'APPLICATION',
       'BILL BINDER']
CLASSES = {k:v for k,v in enumerate(labels)}
PROJECT = 'protean-unity-251012'

@app.route('/')
def homepage():
    
    # # Create a Cloud Datastore client.
    # datastore_client = datastore.Client()

    # # Use the Cloud Datastore client to fetch information from Datastore about
    # # each photo.
    # query = datastore_client.query(kind='Faces')
    # image_entities = list(query.fetch())

    # Return a Jinja2 HTML template and pass in image_entities as a parameter.
    # return render_template('homepage.html', image_entities=image_entities)
    return render_template('homepage.html')

@app.route('/prediction', methods=['GET', 'POST'])
def my_form_post():
    # df = pd.read_csv('eval.csv')
    # requests = [df.iloc[0,1]]
    # requests.append(df.iloc[1,1])

    text = request.form['words']

    model_name = request.form['model']
    # processed_text = text.upper()
    print(model_name)

    requests = [text]
    
    requests = [x.lower() for x in requests] 
    request_data = {'instances': requests}
    # Authenticate and call CMLE prediction API 
    credentials = GoogleCredentials.get_application_default()
    api = discovery.build('ml', 'v1', credentials=credentials,
                discoveryServiceUrl='https://storage.googleapis.com/cloud-ml/discovery/ml_v1_discovery.json')

    if model_name == 'ConvNN':
        parent = 'projects/%s/models/%s/versions/%s' % (PROJECT, 'txtcls', 'v1_finetune_native')
        layer_name = 'dense'
    elif model_name == 'LSTM':
        parent = 'projects/%s/models/%s/versions/%s' % (PROJECT, 'txtcls_LSTM', 'v1_finetune_native')
        layer_name = 'dense_1'
    response = api.projects().predict(body=request_data, name=parent).execute()

    new_response = {"predictions":[]}
    
    for prediction in response['predictions']:
        new_object = {}
        index = np.argmax(prediction[layer_name])
        label = CLASSES[index]
        print("index: {} label: {}".format(index,label))

        new_object['prediction'] = label

        new_dict = {}
        for i in range(14):
            prob = prediction[layer_name][i]
            label = CLASSES[i]
            new_dict[label] = prob

        new_object['condidence'] = new_dict
        
        new_response['predictions'].append(new_object)
    
    return flask.jsonify(new_response)


@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500


if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
