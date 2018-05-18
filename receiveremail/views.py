from django.shortcuts import render

from django.http import HttpResponse

from . import parse_file_json

import requests
import base64


def index(request):
	json_results = parse_file_json.parse_file()

	headers = { 
		'Authorization': 'Basic ' + 'c21hcnRob3A6QEhpdGNoMjAxNg==',
		'Content-type': 'application/json'
	}
	response = requests.post('http://matcher2.smarthop.co:8080/hopmatcher/rest/hitchmatcher/trip/addmultitoplan', data = json_results, headers=headers)
	content = response.content
	return HttpResponse("Hello, world. You're at the polls index.")