"""
Used to get recipe information and images from the Edamam recipe api at:
https://api.edamam.com/search

Edamam developer portal: https://developer.edamam.com/edamam-recipe-api

Created as part of the backend of an app for the Just Eat Code Jam 2018.
"""
import os
import json
import urllib.request
import urllib.parse


class RecipeAPI():
    """
    A RecipeAPI handles requests to the api located at:
    https://api.edamam.com/search

    The api_key and app_id parameters can also be set via the operating system
    environment variables API_KEY and APP_ID.
    """

    def __init__(self, api_key=None, app_id=None):

        if api_key == None:
            try:
                self.api_key = os.environ["API_KEY"]
            except KeyError:
                raise KeyError("The api_key is not set.")
        else:
            self.api_key = api_key

        if app_id == None:
            try:
                self.app_id = os.environ["APP_ID"]
            except KeyError:
                raise KeyError("The app_id is not set.")
        else:
            self.app_id = app_id

        self.uri = "https://api.edamam.com/search"

        # set a default image in case once cannot be downloaded
        self.default_img_path = "default_img.jpg"

    def _http_get(self, url):
        """
        Make a http get request. Returns the data from the url.

        Note: Handles http errors by returning None.
        """

        req = urllib.request.Request(url)
        try:
            with urllib.request.urlopen(req) as response:
                return response.read()
        except urllib.error.HTTPError as e:
            return None

    def _download_file(self, url, name, dir="download"):
        """
        Downloads a file and returns its path as a string.
        Auto increments the number suffix.
        """

        # create the download folder if it does not exist
        if not os.path.exists(dir):
            os.makedirs(dir)

        # download the file
        data = self._http_get(url)
        if data != None and len(data) != 0:
            # save the file
            file_path = self._gen_file_name(dir, name)
            with open(file_path, "wb") as f:
                f.write(data)
            return file_path
        return None

    def _gen_file_name(self, dir, name, f_num=1):
        """
        Generates a valid filename for saving.
        Uses an incremental number system.
        """

        file_name = os.path.join(dir, name + "_" + str(f_num) + ".jpg")
        if os.path.exists(file_name):
            return self._gen_file_name(dir, name, f_num + 1)
        return file_name

    def _construct_api_query(self, query_list, max_res):
        """
        Returns a url as a string with the items in query list as search
        parameters.

        query_list is a list of food items as strings
        max_res is the maximum results to request as an integer
        """

        def clean_string(string):
            """Helper function to format the individual search terms."""
            return urllib.parse.quote_plus('"' + string.strip().lower() + '"')

        # concatenate food items in the query list to make a query string
        q_str = "+".join([clean_string(food) for food in query_list])

        # construct the url for the request
        url = "{0}?q={1}&app_id={2}&app_key={3}&from=0&to={4}"
        return url.format(self.uri, q_str, self.app_id, self.api_key, max_res)

    def search(self, query_list, max_results=3):
        """
        Returns a list of dictionaries.

        query_list is a list of strings i.e. the food items to search
        max_results is the maximum number of recipes to return in the dictionary

        Each dictionary has the following keys representing the recipe
        attributes:

        "name" - The name of the recipe.
        "image" - The path to the downloaded image file.
        "source" - The creator of the recipe.
        "url" - The link to the recipe.

        Returns an empty list if there are no matches or there is an error
        in the request.
        """

        # make the request to the api, return an empty list for bad requests
        url = self._construct_api_query(query_list, max_results)
        data = self._http_get(url)
        if data != None and len(data) != 0:
            dict = json.loads(data)
        else:
            return []

        # load cache
        if os.path.exists("cached.json"):
            with open("cached.json", "r") as f:
                cache = json.load(f)
        else:
            cache = {}

        # return a list of dictionaries which contain the data for each recipe
        rtn_list = []

        for result in dict["hits"]:

            d = {}
            img_url = result["recipe"]["image"]

            # use cached file, otherwise download it
            if img_url in cache:
                dl_file = cache[img_url]
                print("used cache")
            else:
                print("downloading imgs")
                dl_file = self._download_file(img_url, "img")
                if dl_file == None:
                    dl_file = self.default_img_path
                else:
                    # cache the result
                    print("saved cache")
                    cache[img_url] = dl_file

            d["name"] = result["recipe"]["label"]
            d["image"] = dl_file
            d["source"] = result["recipe"]["source"]
            d["url"] = result["recipe"]["url"]
            rtn_list.append(d)

        with open("cached.json", "w") as f:
            json.dump(cache, f)

        return rtn_list


if __name__ == '__main__':

    recipe_api = RecipeAPI()

    ingredients = input("Enter ingredients separated by a space: ").split()
    if ingredients == []:
        ingredients = ["apples", "butter", "cinnamon"]

    print("Searching for {} :".format(', '.join(ingredients)))

    results = recipe_api.search(ingredients)

    if results == []:
        print("No results.")
    else:
        for recipe in results:
            print(recipe["name"], "by", recipe["source"])
            print("Link: ", recipe["url"])
            print("Image: ", recipe["image"], end="\n\n")
