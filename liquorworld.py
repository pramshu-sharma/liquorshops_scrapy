import scrapy
import csv
import datetime


class liquorworldSpider(scrapy.Spider):
    name = 'liquorworld'
    urls_to_not_scrape = ['https://liquorworld.com.np/product/heineken-beer-can-330ml/',
                          'https://liquorworld.com.np/product/bottega-glamour-birilli-gift-pack-4-x-200ml/']

    def start_requests(self):
        with open('/home/pramshusharma/PycharmProjects/liquorshops_nepal/liquorshops_nepal/liquorworld_links.csv',
                  'r') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                url = row[0]
                category = url.split('/')[4].title()
                yield scrapy.Request(url, callback=self.get_links, meta={'category': category})

    def get_links(self, response):
        links = response.css('.product-small.box')
        for link in links:
            url = link.css('.image-zoom a::attr(href)').get()
            category = response.meta['category']
            if url not in self.urls_to_not_scrape:
                yield scrapy.Request(url, callback=self.get_details, meta={'category': category})

        next_page = response.css(
            'ul.page-numbers.nav-pagination.links.text-center li a.next.page-number::attr(href)').get()
        try:
            category = response.meta['category']
            yield scrapy.Request(next_page, callback=self.get_links, meta={'category': category})
        except TypeError:
            pass

    def get_details(self, response):
        if response.css('p.price.product-page-price.price-on-sale').get():
            sale_price = response.css('p.price.product-page-price.price-on-sale ins bdi::text').get().strip()
            price = response.css('p.price.product-page-price.price-on-sale del bdi::text').get().strip()
        else:
            sale_price = 'N/A'
            price = response.xpath('//div/p/span/bdi/text()').get()
        specs = {
            'title': response.css('h1.product-title.product_title.entry-title::text').get().strip(),
            'category': response.meta['category'],
            'sub_category': response.css(
                '.woocommerce-Tabs-panel.woocommerce-Tabs-panel--description.panel.entry-content.active p a::text').get(),
            'price': price,
            'sale_price': sale_price,
            'country': response.xpath('//p/strong/following-sibling::text()')[3].get().strip(),
            'alcohol': response.xpath('//p/strong/following-sibling::text()')[4].get().strip(),
            'volume': response.xpath('//p/strong/following-sibling::text()')[0].get().strip(),
            'brand': response.xpath('//p/strong/following-sibling::text()')[1].get().strip(),
            'url': response.url,
            'scrapped_time': datetime.datetime.now().date()
        }
        description = response.css('.tab-panels p::text')
        for idx in range(5, len(description)):
            specs[f'desc_{idx - 4}'] = description[idx].get().strip()
        yield specs
