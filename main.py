from API import API
from Card import Card
from requests_html import AsyncHTMLSession
from string import Template
import asyncio
import datetime
import random
import shelve
import sys
import time
import tweepy
import Util

# Init global temp dict.
global card_set

# Print alert, tweet it if enabled.
def notify_difference(card, original_text):
    api = API()

    print("#######################################")
    print(f"            {card.get_model()} STOCK ALERT           ")
    print(f"           {time.ctime()}")
    print(f"Button has changed from {original_text} to {card.get_button_text()} for {card.get_name()}.")
    if "newegg" in card.get_url():
        print(f"Add it to your cart: https://secure.newegg.com/Shopping/AddToCart.aspx?ItemList={card.get_item_id()}&Submit=ADD&target=NEWEGGCART\n\n")
    print(f"Current price: {card.get_price()}.")
    print(f"Please visit {card.get_url()} for more information.")
    print("#######################################")
    print("")
    print("")

    # Open browser tab for purchase
    if "newegg" in card.get_url():
        webbrowser.open(f"https://secure.newegg.com/Shopping/AddToCart.aspx?ItemList={card.get_item_id()}&Submit=ADD&target=NEWEGGCART")
    else:
        webbrowser.open(card.getUrl(), new=2)

    if Util.get_tweepy_enabled():
        auth = tweepy.OAuthHandler(api.get_api_key(), api.get_api_secret())
        auth.set_access_token(api.get_access_token(), api.get_access_token_secret())

        api = tweepy.API(auth)

        tweet = f"{card.get_model()} STOCK ALERT\n\n"
        tweet += f"{card.get_name()[0:50]}...\n"
        tweet += f"Selling for {card.get_price()}.\n\n"
        if "newegg" in card.get_url():
            tweet += f"Add it to your cart: https://secure.newegg.com/Shopping/AddToCart.aspx?ItemList={card.get_item_id()}&Submit=ADD&target=NEWEGGCART\n\n"
        tweet += f"Visit {card.get_url()} for more info."

        try:
            api.update_status(tweet)
        except tweepy.error.TweepError as te:
            if te.api_code == 187:
                # duplicate tweet
                pass

# Build list of URLs to check
async def get_stock():
    bestbuy_base_url = "https://www.bestbuy.com/site/computer-cards-components/video-graphics-cards/abcat0507002.c?id=abcat0507002"
    bestbuy_model_stub = Template("qp=gpusv_facet%3DGraphics%20Processing%20Unit%20(GPU)~NVIDIA%20GeForce%20RTX%20$Model")

    # Get the current time and append to the end of the url just to add some minor difference
    # between scrapes.
    t = int(round(time.time() * 1000))

    urls = {
        # f"3070-={bestbuy_base_url}&{bestbuy_model_stub.substitute(Model='3070')}&t={t}",
        # f"3070-=https://www.newegg.com/p/pl?N=100007709%20601357250&PageSize=96&t={t}",
        f"3080-={bestbuy_base_url}&{bestbuy_model_stub.substitute(Model='3080')}&t={t}",
        f"3080-=https://www.newegg.com/p/pl?N=100007709%20601357247&PageSize=96&t={t}",
        f"3090-={bestbuy_base_url}&{bestbuy_model_stub.substitute(Model='3090')}&t={t}",
        f"3090-=https://www.newegg.com/p/pl?N=100007709%20601357248&PageSize=96&t={t}",
        f"5900x-=https://www.bestbuy.com/site/promo/amd-ryzen-5000?qp=numberofcores_facet%3DNumber%20of%20Cores~12-core&t={t}",
        f"5900x-=https://www.newegg.com/p/pl?N=100007671%20601359154%20601301117&t={t}",
    }
    s = AsyncHTMLSession()

    tasks = (parse_url(s, url.split("-=")[1], url.split("-=")[0]) for url in urls)

    return await asyncio.gather(*tasks)

# Determine whether or not to parse Best Buy or NewEgg.
async def parse_url(s, url, model):
    if "bestbuy" in url:
        await parse_bestbuy_url(s, url, model)
    if "newegg" in url:
        await parse_newegg_url(s, url, model)

async def parse_bestbuy_url(s, url, model):
    # Narrow HTML search down using HTML class selectors.
    r = await s.get(url)
    cards = r.html.find('.right-column')

    for item in cards:      
        card = Card.create_from_bestbuy(item, model)

        if card is not None:
            card_id = card.get_item_id()
            if card_id in card_set.keys():
                if card_set[card_id].get_button_text() != card.get_button_text():
                    original_text = card_set[card_id].get_button_text()
                    if card.is_in_stock():
                        notify_difference(card, original_text)

            card_set[card_id] = card

async def parse_newegg_url(s, url, model):
    r = await s.get(url)
    cards = r.html.find('.item-cell')

    for item in cards:
        card = Card.create_from_newegg(item, model)

        if card is not None:
            card_id = card.get_item_id()
            if card_id in card_set.keys():
                if card_set[card_id].get_button_text() != card.get_button_text():
                    original_text = card_set[card_id].get_button_text()
                    if card.is_in_stock():
                        notify_difference(card, original_text)

            card_set[card_id] = card

if __name__ == '__main__':
    print("Starting up")
    Util.clear_card_shelf()

    while True:
        print(f"{time.ctime()} ::: Checking Stock...")
        
        card_set = Util.get_card_dict()

        try:
            asyncio.run(get_stock())
        except Exception as e:
            if "SSLError" in type(e).__name__:
                # SSL Error. Wait 10-30 seconds and try again.
                print(f"{time.ctime()} ::: {type(e).__name__} error. Retrying in 10-30 seconds...")
            else:
                print(f"{type(e).__name__} Exception: {str(e)}")
        
        Util.set_card_shelf(card_set)
        time.sleep(random.randint(10, 30))
