class Card:
    def __init__(self, model, price, item_number, name, url, btn_text):
        self.name = name
        self.model = model
        self.price = price
        self.item_number = item_number
        self.url = url
        self.btn_text = btn_text

    def get_name(self):
        return self.name

    def get_url(self):
        return self.url

    def get_button_text(self):
        return self.btn_text

    def get_model(self):
        return self.model

    def get_item_id(self):
        return self.item_number

    def get_price(self):
        return self.price

    def is_in_stock(self):
        return "cart" in self.btn_text.lower()

    def get_founders_price(self):
        founders_price = {
            "3070": 500,
            "3080": 700,
            "3090": 1500,
            "5900X": 550,
        }

        return founders_price[self.model]
    
    def create_from_bestbuy(html, model):
        header = html.find('.sku-header', first=True)
        price_parent = html.find('.priceView-customer-price', first=True)
        price = price_parent.find('span', first=True).text

        stock_button = html.find('.sku-list-item-button', first=True).find('.btn', first=True)
        header_text = header.text
        card_url = f"https://www.bestbuy.com{header.find('a', first=True).attrs['href']}"
        card_id = card_url.split("skuId=")[1]

        new_card = Card(model, price, card_id, header_text, card_url, stock_button.text)    

        # Check price. Make sure it's within at least $300 of the FE price.
        price_as_float = float(''.join(d for d in price if d.isdigit() or d == '.'))
        if abs(price_as_float - new_card.get_founders_price()) > 300:
            return None
        
        return new_card

    def create_from_newegg(html, model):
        header = html.find('.item-info', first=True)
        name = html.find('.item-title', first=True)
        price_parent = html.find('.price-current', first=True)

        # NewEgg sometimes adjusts the location of its prices. This will
        # get it in the vast majority of situations.
        try:
            price = f"{price_parent.text.split('.')[0]}.{price_parent.text.split('.')[1][0:2]}"
        except:
            # If the price can't be gathered, just set it to 'unknown' for now.
            price = "Unknown"

        stock_button = html.find('.item-button-area', first=True).find('.btn', first=True)
        card_url = html.find('.item-container', first=True).find('a', first=True).attrs['href']

        item_features = html.find('.item-features', first=True).find('li')
        for feature in item_features:
            if "item #" in feature.text.lower():
                item_id = feature.text.split(": ")[1]
                break

        if "item_id" not in locals():
            return None
            
        new_card = Card(model, price, item_id, name.text, card_url, stock_button.text)

        # Check price. Make sure it's within at least $300 of the FE price.
        if "Unknown" not in price:
            price_as_float = float(''.join(d for d in price if d.isdigit() or d == '.'))
            if abs(price_as_float - new_card.get_founders_price()) > 300:
                return None
        
        return new_card

    def create_from_amazon(html, model):
        try:
            price_parent = html.find('.a-price', first=True)
            price = price_parent.find('span', first=True).text.split('$')[2]
        except:
            # If the price can't be gathered, just set it to 'unknown' for now.
            price = "Unknown"

        try:
            name = html.find('h2', first=True).text
        except:
            name = "Unknown"

        if "Unknown" in name:
            return None

        if model not in name:
            return None

        if "Unknown" in price:
            stock_button = "Out of stock"
        else:
            stock_button = "In stock"
        
        try:
            title = html.find('h2', first=True)
            card_url = title.absolute_links.pop()
        except:
            card_url = "Unknown"

        try:
            item_id = html.attrs['data-asin']
        except:
            item_id = "Unknown"

        if "Unknown" in item_id:
            return None

        new_card = Card(model, price, item_id, name, card_url, stock_button)

        # Check price. Make sure it's within at least $300 of the FE price.
        if "Unknown" not in price:
            price_as_float = float(''.join(d for d in price if d.isdigit() or d == '.'))
            if abs(price_as_float - new_card.get_founders_price()) > 300:
                return None
        
        return new_card
