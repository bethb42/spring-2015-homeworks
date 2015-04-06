#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import time
import argparse
import logging
import requests
from BeautifulSoup import BeautifulSoup


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
loghandler = logging.StreamHandler(sys.stderr)
loghandler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))
log.addHandler(loghandler)

base_url = "http://www.tripadvisor.com/"
user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.76 Safari/537.36"
dict_hotels = {}
ht_urls = []


def get_city_page(city, state, datadir):
    """ Returns the URL of the list of the hotels in a city. Corresponds to
    STEP 1 & 2 of the slides.
    Parameters
    ----------
    city : str
    state : str
    datadir : str
    Returns
    -------
    url : str
        The relative link to the website with the hotels list.
    """
    # Build the request URL
    url = base_url + "city=" + city + "&state=" + state
    # Request the HTML page
    headers = {'User-Agent': user_agent}
    response = requests.get(url, headers=headers)
    html = response.text.encode('utf-8')
    with open(os.path.join(datadir, city + '-tourism-page.html'), "w") as h:
        h.write(html)

    # Use BeautifulSoup to extract the url for the list of hotels in
    # the city and state we are interested in.

    # For example in this case we need to get the following href
    # <li class="hotels twoLines">
    # <a href="/Hotels-g60745-Boston_Massachusetts-Hotels.html" data-trk="hotels_nav">...</a>
    soup = BeautifulSoup(html)
    li = soup.find("li", {"class": "hotels twoLines"})
    city_url = li.find('a', href=True)
    return city_url['href']


def get_hotellist_page(city_url, page_count, city, datadir='data/'):
    """ Returns the hotel list HTML. The URL of the list is the result of
    get_city_page(). Also, saves a copy of the HTML to the disk. Corresponds to
    STEP 3 of the slides.
    Parameters
    ----------
    city_url : str
        The relative URL of the hotels in the city we are interested in.
    page_count : int
        The page that we want to fetch. Used for keeping track of our progress.
    city : str
        The name of the city that we are interested in.
    datadir : str, default is 'data/'
        The directory in which to save the downloaded html.
    Returns
    -------
    html : str
        The HTML of the page with the list of the hotels.
    """

    url = base_url + city_url
    # Sleep 2 sec before starting a new http request
    time.sleep(2)
    # Request page
    headers = { 'User-Agent' : user_agent }
    response = requests.get(url, headers=headers)
    html = response.text.encode('utf-8')
    # Save the webpage
    with open(os.path.join(datadir, city + '-hotelist-' + str(page_count) + '.html'), "w") as h:
        h.write(html)
    return html



def parse_hotellist_page(html):
    """Parses the website with the hotel list and prints the hotel name, the
    number of stars and the number of reviews it has. If there is a next page
    in the hotel list, it returns a list to that page. Otherwise, it exits the
    script. Corresponds to STEP 4 of the slides.
    Parameters
    ----------
    html : str
        The HTML of the website with the hotel list.
    Returns
    -------
    URL : str
        If there is a next page, return a relative link to this page.
        Otherwise, exit the script.
    """
    soup = BeautifulSoup(html)
    # Extract hotel name, star rating and number of reviews
    hotel_boxes = soup.findAll('div', {'class' :'listing wrap reasoning_v5_wrap jfy_listing p13n_imperfect'})
    if not hotel_boxes:
        log.info("#################################### Option 2 ######################################")
        hotel_boxes = soup.findAll('div', {'class' :'listing_info jfy'})
    if not hotel_boxes:
        log.info("#################################### Option 3 ######################################")
        hotel_boxes = soup.findAll('div', {'class' :'listing easyClear  p13n_imperfect'})

    for hotel_box in hotel_boxes:
        hotel_name = hotel_box.find("a", {"target" : "_blank"}).find(text=True)
        log.info("Hotel name: %s" % hotel_name.strip())
        #dict_hotels[hotel_name.strip()] = {}
        stars = hotel_box.find("img", {"class" : "sprite-ratings"})
        if stars:
            log.info("Stars: %s" % stars['alt'].split()[0])
            #dict_hotels[hotel_name.strip()]["Stars"] = stars['alt'].split()[0]

        num_reviews = hotel_box.find("span", {'class': "more"}).findAll(text=True)
        if num_reviews:
            log.info("Number of reviews: %s " % [x for x in num_reviews if "review" in x][0].strip())
        
        #find the url for the hotel, append it to a list of urls
        hotel_url = hotel_box.find("a", {"class" : "property_title"})['href']
        ht_urls.append(hotel_url)

    #this didn't work :(
    #Get the url of the hotel page
    # hotel_pages = soup.findAll('div', {'class': 'qualilty wrap'})
    # print "going to start parsing hotels"
    # i = 0
    # for hotel_page in hotel_pages:
    #     print "parsing hotel #", i
    #     hotel_url = hotel_page.find('a', {'target': '_blank'}).find(text=True)
    #     url = base_url + hotel_url
    #     headers = { 'User-Agent' : user_agent }
    #     time.sleep(2)
    #     response = requests.get(url, headers=headers)
    #     #html now holds the webpage for a specific website. 
    #     html = response.text.encode('utf-8')
    #     parse_hotel_page(html)  #will find the needed data and parse it. 
        

    # Get next URL page if exists, otherwise exit
    div = soup.find("div", {"class" : "pagination paginationfillbtm"})
    # check if this is the last page
    if div.find('span', {'class' : 'guiArw pageEndNext'}):
        log.info("We reached last page")
        # print "We reached last page"
        sys.exit()
    # If not, return the url to the next page
    hrefs = div.findAll('a')
    for href in hrefs:
        cl = href['class'].strip()
        # print "cl ", cl
        if cl == "guiArw sprite-pageNext":
            # print "href ", href['href']
            return href['href']
            
def parse_hotelpages(ht_urls):
        # i = 0
        for ht_url in ht_urls:
            # if i < 10:
                # print "parsing hotel #", i
                url = base_url + ht_url
                # print ht_url
                headers = { 'User-Agent' : user_agent }
                time.sleep(2)
                response = requests.get(url, headers=headers)

                #html now holds the webpage for a specific website. 
                html = response.text.encode('utf-8')
                #will build the dictionary for a specific hotel
                soup = BeautifulSoup(html)

                #get name
                ht_name = soup.find("h1", {"class" : "heading_name "}).text.strip()
                dict_hotels[ht_name] = {}
                # print ht_name

                #get rating
                rating = soup.find("img", {'property': "v:average"})
                dict_hotels[ht_name]['total rating'] = float(rating['content'])
                # print float(rating['content'])

                #get total number of ratings
                num_rating = soup.find("h3", {'class': 'reviews_header'}).text.encode('ascii','ignore')
                ls_rating = num_rating.split()
                tot_rating = ls_rating[0].replace(",", "")
                dict_hotels[ht_name]['total number rating'] = float(tot_rating)

                #gets the number for each type of rating. 
                travelRating = soup.find("div", {"class" : "col2of2 composite"})
                ratingTitle = soup.find("div", {"class" : "colTitle"}).text
                # print ratingTitle
                ratingRows = travelRating.findAll("div", {"class": "wrap row"})
                for row in ratingRows:
                    rowTitle = row.find("span", {"class" : "rdoSet"}).text
                    # print rowTitle
                    numRatings = row.find("span", {"class" : "compositeCount"}).text
                    # print numRatings
                    dict_hotels[ht_name][rowTitle] = getNumFromString(numRatings)
                #Find types of review

                #families
                travelRow = soup.find("div", {"class": "segment segment1"})
                num_families = travelRow.find("div", {"class": "value"}).text
                # print "Families"
                # print num_families
                dict_hotels[ht_name]["Families"]= getNumFromString(num_families)


                #couples
                travelRow = soup.find("div", {"class": "segment segment2"})
                num_families = travelRow.find("div", {"class": "value"}).text
                # print "Couples"
                # print num_families
                dict_hotels[ht_name]["Couples"]= getNumFromString(num_families)

                #solo
                travelRow = soup.find("div", {"class": "segment segment3"})
                num_families = travelRow.find("div", {"class": "value"}).text
                # print "Solo"
                # print num_families
                dict_hotels[ht_name]["Solo"]= getNumFromString(num_families)

                #business
                travelRow = soup.find("div", {"class": "segment segment4"})
                num_families = travelRow.find("div", {"class": "value"}).text
                # print "Business"
                # print num_families
                dict_hotels[ht_name]["Business"]= getNumFromString(num_families)

                #Finding the Quality of features
                features = ["Location", "Sleep Quality", "Rooms", "Service", "Value", "Cleanliness"]
                count = 0
                qualities = soup.find("div", {"id" :"SUMMARYBOX"})
                stars = qualities.findAll("img", {"src": "http://e2.tacdn.com/img2/x.gif"})
                for sta in stars:
                    # print sta["alt"]
                    
                    dict_hotels[ht_name][features[count]]= getNumFromString(sta["alt"])
                    count += 1

        


                # i += 1

#parses a string into a useful piece of data 
def getNumFromString(s):
    s= s.encode('ascii','ignore')
    s= s.replace(",", "")
    ls = s.split()
    num = float(ls[0])
    return num

def scrape_hotels(city, state, datadir='data/'):
    """Runs the main scraper code
    Parameters
    ----------
    city : str
        The name of the city for which to scrape hotels.
    state : str
        The state in which the city is located.
    datadir : str, default is 'data/'
        The directory under which to save the downloaded html.
    """
    dict_hotels = {}
    # Get current directory
    current_dir = os.getcwd()
    # Create datadir if does not exist
    if not os.path.exists(os.path.join(current_dir, datadir)):
        os.makedirs(os.path.join(current_dir, datadir))

    # Get URL to obtaint the list of hotels in a specific city
    city_url = get_city_page(city, state, datadir)
    c = 0
    while(True):
        c += 1
        html = get_hotellist_page(city_url, c, city, datadir)
        city_url = parse_hotellist_page(html)
        #call get hotel
        #parse hotel
    
def getDict():
    return dict_hotels

def getUrls():
    return ht_urls

# def parseHotels():
#     for url in ht_urls:



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrape tripadvisor')
    parser.add_argument('-datadir', type=str,
                        help='Directory to store raw html files',
                        default="data/")
    parser.add_argument('-state', type=str,
                        help='State for which the hotel data is required.',
                        required=True)
    parser.add_argument('-city', type=str,
                        help='City for which the hotel data is required.',
                        required=True)

    args = parser.parse_args()
    scrape_hotels(args.city, args.state, args.datadir)