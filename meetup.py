#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import urllib.request
import json
import csv
import time, dateutil.parser

from tkinter import *
from secrets import MEETUP_API

VERSION = (0,1,0)

class MeetupAPI:
	def __init__(self, api_key=MEETUP_API):
		self.api_key = api_key
		self.groups = []

	def _request_json(self, request):
		url = "https://api.meetup.com{}&sign=true&key={}".format(request, self.api_key)
		f = urllib.request.urlopen(url)
		str_response = f.read().decode('utf-8')
		obj = json.loads(str_response)
		return obj

	def get_categories(self):
		api_category = "/2/categories?"
		return self._request_json(api_category)

	def print_categories(self):
		results = self.get_categories()["results"]
		for result in results:
			print("{}: {}".format(result["id"], result["name"]))

	def get_groups(self, category, latitude, longitude, offset=0):
		page = 200 # seems like 200 is the maximum
		groups = self._request_json("/find/groups?&page={}&photo-host=public&category={}&lat={}&lon={}&order=most_active&offset={}".format(page, category, latitude, longitude, offset))
		if groups != []:
			self.get_groups(category, latitude, longitude, offset+1)
		self.groups += groups

		return self.groups

	def get_events(self, group_id, page=200, skip_before=0):
		next_event_page = "/2/events?&photo-host=public&group_id={}&page={}&time={},&status=upcoming,past".format(group_id, page, int(skip_before))
		results = []
		while next_event_page != "":
			events = self._request_json(next_event_page)
			results += events["results"]
			next_event_page = events["meta"]["next"]
		return events

	def get_lat_long(self, location_query):
		""" returns a tuple (lat, lon) with the latitude and longitude of the searched query (top result) """
		api_lat_long = "/2/cities?photo-host=public&query={}&page=1".format(location_query)
		json_lat_long = self._request_json(api_lat_long)
		print("Location selected: {}".format(json_lat_long["results"][0]["name_string"]))

		return (json_lat_long["results"][0]["lat"], json_lat_long["results"][0]["lon"])

def run_scraper(meetup, category, location, skip_before):
	filename = 'meetup.csv'
	lat, lon = meetup.get_lat_long(location)
	meetup.get_groups(category, lat, lon)
	print("Found {} groups".format(len(meetup.groups)))
	try:
		f = csv.writer(open(filename, 'w', newline=''))
	except PermissionError:
		print("Error! Is the spreadsheet being used?")
		return

	print("Pulling data from Meetup... This may take a while")

	f.writerow(["ID", "Name", "Category", "Members", "City", "Country", "Link", "Total Events (after {})".format(skip_before.strftime('%d/%m/%Y')), "Avg Attendees per Event", "Date Created"])

	counter = 0
	for x in meetup.groups:
		# try:
		counter += 1
		print("{}: {} ({} members)".format(counter, x["name"], x["members"]))
		events = meetup.get_events(x["id"], skip_before=(skip_before.timestamp()*1000))
		total_attendees = 0
		num_of_events = 0.001 # avoid divide by 0 error

		for event in events:
			print(event)
			total_attendees += int(event["yes_rsvp_count"])
			num_of_events += 1

		f.writerow([x["id"], x["name"], x["category"]["shortname"], x["members"],
		x["city"], x["country"], x["link"], total_count,
		int(total_attendees/num_of_events),
		time.strftime('%d/%m/%Y',  time.gmtime(x["created"]/1000.))])
		# except Exception as e:
		# 	print("Error: {}, skipping group".format(e))

	print("'{}' successfully saved".format(filename))

def main():
	meetup = MeetupAPI()
	meetup.print_categories()

	try:
		category = int(input("Choose your category (eg. 34): "))
		location = str(input("Choose your location: "))
		skip_before = dateutil.parser.parse(input("Skip events occurring before (YYYYMMDD): "))
	except ValueError:
		print("Error!")

	run_scraper(meetup, category, location, skip_before)

if __name__ == "__main__":
	main()
