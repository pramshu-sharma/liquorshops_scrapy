import asyncio
import scrapy
import csv
from scrapy_playwright.page import PageMethod
from scrapy.selector import Selector
import datetime


class cheersSpider(scrapy.Spider):
    name = 'cheers'
    domain = 'https://cheers.com.np'

    def start_requests(self):
        with open(
                '/home/pramshusharma/PycharmProjects/liquorshops_nepal/liquorshops_nepal/cheers_links.csv',
                'r') as file:
            urls = csv.reader(file)
            for row in urls:
                url = row[0]
                category = url.split('/')[4].replace('category?c=', '').title()
                yield scrapy.Request(url, callback=self.get_product_links,
                                     meta=dict(category=category,
                                               playwright=True,
                                               playwright_include_page=True,
                                               playwright_page_methods=[
                                                   PageMethod('wait_for_selector', 'div.text-center.product-list')
                                               ]))

    async def get_product_links(self, response):
        scroll_page = response.meta['playwright_page']
        category = response.meta['category']
        while True:
            previous_height = await scroll_page.evaluate('() => document.body.scrollHeight')
            await scroll_page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(5)
            new_height = await scroll_page.evaluate('() => document.body.scrollHeight')
            if previous_height == new_height:
                break
        html_content = await scroll_page.content()
        await scroll_page.close()
        page = Selector(text=html_content)
        links = page.css('.text-center.product-list')
        for link in links:
            url = self.domain + link.css('a::attr(href)').get()
            yield scrapy.Request(url, callback=self.get_details, meta={'category': category})

    def get_details(self, response):
        in_stock = 0
        if response.css('button.btn.addCart.btn-cheers').get():
            in_stock = 1
        alcohol = response.css('.row.home-product .col-sm-5 p::text')[3].get()
        if '%' not in alcohol:
            alcohol = 'N/A'
        specs = {
            'title': response.css('.col-sm-5 h4::text').get(),
            'category': response.meta['category'],
            'sub-category': response.css('.row.home-product .col-sm-5 p a::text')[2].get(),
            'price': response.css('.col-sm-3.text-center.desktop-view h3::text').get().strip(),
            'sale_price': 'N/A',
            'in_stock': in_stock,
            'country': response.css('.row.home-product .col-sm-5 p::text')[2].get(),
            'volume': response.css('.row.home-product .col-sm-5 p::text')[0].get().strip(),
            'alcohol': alcohol,
            'brand': response.css('.row.home-product .col-sm-5 p a::text').get(),
            'url': response.url,
            'scrapped_time': datetime.datetime.now().date()
        }
        descriptions = response.css('.description p::text')
        for idx, description in enumerate(descriptions):
            specs[f'desc_{idx + 1}'] = description.get().strip()

        yield specs

    def error_close_page(self, response):
        page = response.meta['playwright_page']
        page.close()
