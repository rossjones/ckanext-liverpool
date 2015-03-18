# -*- coding: utf-8 -*-
import datetime
import logging
import os
import sys
import requests

import ckanapi
from lxml.html import fromstring

from ckan.lib.cli import CkanCommand
import slugify

class ScrapeCommand(CkanCommand):

    summary = "Scrapes some specific datasets from known URLS"
    usage = "paster scrape -c $CKAN_INI"
    max_args = 0
    min_args = 0

    def __init__(self, name):
        super(ScrapeCommand, self).__init__(name)

    def command(self):
        self._load_config()
        log = logging.getLogger(__name__)

        import ckan.model as model
        model.Session.remove()
        model.Session.configure(bind=model.meta.engine)

        print "Scraping!"
        l = LiverpoolCCScraper()
        l.scrape()

class Scraper(object):

    def scrape(self):
        pass

class LiverpoolCCScraper(Scraper):

    def __init__(self):
        self.url = u"http://liverpool.gov.uk/council/performance-and-spending/budgets-and-finance/transparency-in-local-government/"
        self.publisher = u"liverpool-city-council"
        self.ckan = ckanapi.LocalCKAN()

    def scrape(self):
        dom = fromstring(requests.get(self.url).content)
        h3s = dom.cssselect('.bodyContent h3')
        for h3 in h3s:
            label = h3.text_content().strip()
            links = h3.getnext().cssselect('li a')

            paras = dom.cssselect('.bodyContent p')[:10]
            description = "\n\n".join(p.text_content().strip() for p in paras)
            dataset = {
                "title": u"Payments of invoices to vendors over £500 - {}".format(label),
                "notes": unicode(description),
                "owner_org": self.publisher,
                "resources": [],
                "tags": [{"name": "spending"}],
                "license_id": "uk-ogl"
            }
            for l in links:
                href = l.get('href')
                name = href.split('/')[-1]
                ext = name[name.rfind('.')+1:]
                dataset["resources"].append({
                    'url': "http://liverpool.gov.uk" + href,
                    'name': name,
                    'description': l.text_content().strip(),
                    'format': ext.upper()
                })

            dataset["name"] = u"lcc-{}".format(slugify.slugify(dataset["title"]).lower())
            try:
                pkg = self.ckan.action.package_show(id=dataset['name'])
                pkg['tags'] = dataset['tags']
                pkg['notes'] = dataset['notes']
                pkg['license_id'] = dataset['license_id']
                pkg = self.ckan.action.package_update(**pkg)
            except Exception, e:
                pkg = self.ckan.action.package_create(**dataset)




