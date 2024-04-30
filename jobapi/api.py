import requests

def search_jobs(keyword,location):

    url = "https://jobs-api14.p.rapidapi.com/list"

    querystring = {"query":keyword,"location":location,"distance":"1.0","language":"en_GB","remoteOnly":"false","datePosted":"month","employmentTypes":"fulltime;parttime;intern;contractor","index":"0"}

    headers = {
	"X-RapidAPI-Key": "6784c4fb6cmsh737f42f7239da09p1c99f4jsn82a15f83422e",
	"X-RapidAPI-Host": "jobs-api14.p.rapidapi.com"
}

    response = requests.get(url, headers=headers, params=querystring)

    jobs = response.json().get('jobs', [])

    return jobs
